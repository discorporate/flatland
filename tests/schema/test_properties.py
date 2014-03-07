from flatland import String
from flatland._compat import iterkeys, itervalues
from flatland.schema.properties import Properties

from nose.tools import assert_raises


def test_empty():
    class Base(object):
        properties = Properties()

    assert not Base.properties
    b = Base()
    assert not b.properties
    assert not Base.properties

    assert Base.properties == {}
    assert Base().properties == {}

    class Sub(Base):
        pass

    assert Sub.properties == {}
    assert Sub().properties == {}

    Sub().properties['abc'] = 123

    assert Sub.properties == {}
    assert Sub().properties == {}
    assert Base.properties == {}
    assert Base().properties == {}

    Sub.properties['def'] = 456
    assert Base.properties == {}
    assert Base().properties == {}


def test_dictlike():
    class Base(object):
        properties = Properties({'def': 456}, abc=123)

    props = Base.properties
    assert sorted(props.items()) == [('abc', 123), ('def', 456)]

    assert sorted(props.keys()) == ['abc', 'def']
    assert sorted(iterkeys(props)) == ['abc', 'def']

    assert sorted(props.values()) == [123, 456]
    assert sorted(itervalues(props)) == [123, 456]

    assert props.get('abc') == 123
    assert props.get('abc', 'blah') == 123
    assert props.get('blah', 'default') == 'default'
    assert props.get('blah') is None

    assert_raises(NotImplementedError, props.popitem)

    assert 'abc' in props
    assert 'ghi' not in props

    assert props == {'abc': 123, 'def': 456}
    assert props != {'ghi': 789}

    assert props
    props.clear()
    assert not props

    assert repr(props) == '{}'


def test_instance_population():
    class Base(object):
        properties = Properties()

    assert not Base.properties
    b = Base()
    b.properties.update(a=1, b=2, c=3)

    assert b.properties == {'a': 1, 'b': 2, 'c': 3}
    assert Base.properties == {}

    class Sub(Base):
        pass

    assert Sub.properties == {}
    s = Sub()
    assert s.properties == {}

    s.properties['d'] = 4
    assert s.properties == {'d': 4}
    assert Sub.properties == {}
    assert Base.properties == {}
    assert Sub().properties == {}


def test_instance_overlay():
    class Base(object):
        properties = Properties()

    Base.properties['a'] = 1
    b = Base()
    b.properties['b'] = 2

    assert Base.properties == {'a': 1}
    assert b.properties == {'a': 1, 'b': 2}
    del b.properties['a']
    assert b.properties == {'b': 2}
    assert Base.properties == {'a': 1}

    b.properties.update(b='x', c=3, d=4)
    assert b.properties['b'] == 'x'
    assert b.properties == {'b': 'x', 'c': 3, 'd': 4}

    del b.properties['b']
    assert b.properties == {'c': 3, 'd': 4}
    assert_raises(KeyError, lambda: b.properties['b'])

    assert b.properties.setdefault('e', 5) == 5
    assert b.properties.setdefault('e', 'blah') == 5

    assert b.properties == {'c': 3, 'd': 4, 'e': 5}

    assert b.properties.pop('e', 'blah') == 5
    assert b.properties.pop('e', 'blah') == 'blah'
    assert_raises(KeyError, b.properties.pop, 'e')

    b.properties.clear()
    assert b.properties == {}
    assert Base.properties == {'a': 1}

    Base.properties['b'] = 2
    assert b.properties == {'b': 2}
    assert Base.properties == {'a': 1, 'b': 2}

    Base.properties.update(c=3, d=4, e=5)
    del Base.properties['e']
    assert b.properties == {'b': 2, 'c': 3, 'd': 4}
    assert Base.properties == {'a': 1, 'b': 2, 'c': 3, 'd': 4}


def test_instance_member_assignment():

    class Base(object):
        properties = Properties(abc=123)

    b = Base()
    assert b.properties == {'abc': 123}
    b.properties = {'abc': 'detached'}

    assert b.properties == {'abc': 'detached'}

    Base.properties['def'] = 456

    assert b.properties == {'abc': 'detached'}


def test_subclass_overlay():
    class Base(object):
        properties = Properties()

    class Middle(Base):
        pass

    class Lowest(Middle):
        pass

    Lowest.properties['def'] = 456

    assert Base.properties == {}
    assert Middle.properties == {}
    assert Lowest.properties == {'def': 456}

    Base.properties['abc'] = 123

    assert Base.properties == {'abc': 123}
    assert Middle.properties == {'abc': 123}
    assert Lowest.properties == {'abc': 123, 'def': 456}

    del Middle.properties['abc']

    assert Base.properties == {'abc': 123}
    assert 'abc' in Base.properties

    assert Middle.properties == {}
    assert 'abc' not in Middle.properties
    assert_raises(KeyError, lambda: Middle.properties['abc'])

    assert Lowest.properties == {'def': 456}
    assert 'abc' not in Lowest.properties
    assert_raises(KeyError, lambda: Lowest.properties['abc'])

    Middle.properties.setdefault('ghi', 789)
    Middle.properties.setdefault('ghi', 'blah')

    assert Base.properties == {'abc': 123}
    assert Middle.properties == {'ghi': 789}
    assert Lowest.properties == {'ghi': 789, 'def': 456}

    assert Lowest.properties.pop('def', 'blah') == 456
    assert Lowest.properties.pop('def', 'blah') == 'blah'
    assert_raises(KeyError, Lowest.properties.pop, 'def')

    assert Base.properties == {'abc': 123}
    assert Middle.properties == {'ghi': 789}
    assert Lowest.properties == {'ghi': 789}

    Lowest.properties.clear()

    assert Base.properties == {'abc': 123}
    assert Middle.properties == {'ghi': 789}
    assert Lowest.properties == {}


def test_subclass_override():
    class Base(object):
        properties = Properties()

    class Middle(Base):
        pass

    class Override(Middle):
        properties = Properties({'def': 456})

    assert Override.properties == {'def': 456}
    assert Middle.properties == {}
    assert Base.properties == {}

    Base.properties['abc'] = 123

    assert Base.properties == {'abc': 123}
    assert Middle.properties == {'abc': 123}
    assert Override.properties == {'def': 456}


def test_initialization():
    class Base(object):
        properties = Properties(abc=123)

    assert Base.properties == {'abc': 123}
    Base.properties['def'] = 456

    assert Base.properties == {'abc': 123, 'def': 456}
    del Base.properties['abc']
    assert Base.properties == {'def': 456}


def test_perverse():
    class Base(object):
        properties = Properties()

    descriptor = Base.__dict__['properties']
    props = Base.properties
    del Base.properties
    assert list(props._frames()) == []

    def unattached_properties():
        class Unrelated(object):
            pass

        return descriptor.__get__(None, Unrelated)

    lost = unattached_properties()
    assert lost == {}

    lost2 = unattached_properties()
    assert_raises(KeyError, lambda: lost2['abc'])

    class Broken(object):
        properties = 'something else'

    broken = descriptor.__get__(None, Broken)
    broken.update(abc=123)
    assert broken == {'abc': 123}
    assert Broken.properties == 'something else'


def test_perverse_slots():

    class Base(object):
        __slots__ = 'properties',
        properties = Properties()

    b = Base()
    assert_raises(AttributeError, lambda: b.properties['abc'])


def test_dsl():
    Sub = String.with_properties(abc=123)

    assert 'abc' not in String.properties
    assert Sub.properties['abc'] == 123

    Disconnected = Sub.using(properties={'def': 456})
    assert Disconnected.properties['def'] == 456
    assert 'abc' not in Disconnected.properties

    assert 'def' not in Sub.properties
    assert 'def' not in String.properties

    Sub.properties['ghi'] = 789
    assert Disconnected.properties == {'def': 456}

    Disconnected2 = Sub.using(properties=Properties(jkl=123))
    assert Disconnected2.properties == {'jkl': 123}

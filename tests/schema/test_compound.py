import datetime
import re

from flatland import (
    Compound,
    DateYYYYMMDD,
    Dict,
    Integer,
    JoinedString,
    String,
    element_set,
    )

import pytest


def test_compound_init_sequencing():

    class Canary(Exception):
        pass

    class InitNotCalledAtClassConstruction(Compound):

        @classmethod
        def __compound_init__(cls):
            raise Canary

    # __compound_init_ not called until an instance is constructed
    assert True

    # called when an instance is created
    with pytest.raises(Canary):
        InitNotCalledAtClassConstruction()

    # and again, if it fails
    with pytest.raises(Canary):
        InitNotCalledAtClassConstruction()


def test_compound_init_sequencing2():
    canary = []

    class MyCompound(Compound):
        field_schema = [String.named('x')]

        def __compound_init__(cls):
            assert isinstance(cls, type)
            canary.append(cls)

    # construction of a class will trigger it
    element = MyCompound()
    assert canary == [MyCompound]
    assert MyCompound.__dict__['_compound_prepared']

    # only called once per (known) unique class configuration
    element = MyCompound()
    assert canary == [MyCompound]

    # manual configuration doesn't trigger it
    MyCompound.name = 'set by hand'
    element = MyCompound()
    assert canary == [MyCompound]

    # a clone of the class will trigger it
    MyCompound2 = MyCompound.named('something')
    element = MyCompound2()
    assert canary == [MyCompound, MyCompound2]
    assert MyCompound2.__dict__['_compound_prepared']

    # instance-level configuration will also
    element = MyCompound2(name='instance')
    assert type(element) is not MyCompound2
    assert isinstance(element, MyCompound2)
    assert canary == [MyCompound, MyCompound2, type(element)]
    assert type(element).__dict__['_compound_prepared']

    del canary[:]

    # it can be run by hand
    MyCompound4 = MyCompound.named('somethingelse')
    assert not MyCompound4.__dict__.get('_compound_prepared')

    MyCompound4.__compound_init__()

    assert MyCompound4.__dict__['_compound_prepared']
    assert canary == [MyCompound4]

    # and it won't be re-run automatically
    element = MyCompound4()
    assert canary == [MyCompound4]

    class MyCompound5(Compound):
        field_schema = [String.named('x')]

        @classmethod
        def __compound_init__(cls):
            assert isinstance(cls, type)
            canary.append(cls)

    # it can be @classmethod or not
    element = MyCompound5()
    assert canary == [MyCompound4, MyCompound5]


def test_compound_snarfs_override_init_keywords():

    class MyCompound(Compound):
        field_schema = [String.named('x')]
        attr = 'value'

        def __init__(self, value='sentinel', abc=1):
            # __new__'s value= should not trump this one
            assert value == 'sentinel'
            self.abc = abc

    mc1 = MyCompound()
    assert mc1.abc == 1

    mc2 = MyCompound(attr='new value')
    assert mc2.abc == 1
    assert mc2.attr == 'new value'
    assert mc1.attr == 'value'
    assert type(mc2) is not type(mc1)

    with pytest.raises(TypeError):
        MyCompound(unknown='boom')


def test_compound_metaclass_calls_new():
    canary = []

    class MyCompound(Compound):
        name = 'abc'
        field_schema = [String.named('x')]

        def __new__(cls, *args, **kw):
            canary.append('new')
            return Compound.__new__(cls, *args, **kw)

        def __init__(self, *args, **kw):
            canary.append('init')

    assert MyCompound() is not None
    assert canary == ['new', 'init']

    del canary[:]

    class AltNewReturn(Compound):
        name = 'abc'
        field_schema = [String.named('x')]

        def __new__(cls, *args, **kw):
            canary.append('new')
            self = {}
            return self

        def __init__(self, *args, **kw):
            canary.append('init')

    assert AltNewReturn() is not None
    assert canary == ['new']


class TestDoubleField:

    def setup_method(self):

        class Double(Compound):

            field_schema = [Integer.named('x'), Integer.named('y')]

            def compose(self):
                ex, ey = self.get('x'), self.get('y')
                ux, uy = ex.u, ey.u
                if ex.u and ey.u:
                    string = f"{ex.u}x{ey.u}"
                else:
                    string = ''

                if ex.value is not None and ey.value is not None:
                    value = (ex.value, ey.value)
                else:
                    value = None

                return string, value

            def explode(self, value):
                if value == 'boom':
                    raise AttributeError('boom')
                if value == 'return-none':
                    return
                try:
                    x, y = value
                except (TypeError, ValueError):
                    return False
                res = True
                res &= self['x'].set(x)
                res &= self['y'].set(y)
                return res

        self.Double = Double

    def test_from_flat(self):
        s = self.Double.named('s')

        e = s.from_flat({})
        assert_values_(e, None, None, None)
        assert_us_(e, '', '', '')

        e = s.from_flat({'s': '1x2'})
        assert_values_(e, None, None, None)
        assert_us_(e, '', '', '')

        e = s.from_flat({'s_x': '1'})
        assert_values_(e, None, 1, None)
        assert_us_(e, '', '1', '')

        e = s.from_flat({'s_x': '1', 's_y': '2'})
        assert_values_(e, (1, 2), 1, 2)
        assert_us_(e, '1x2', '1', '2')

        e = s.from_flat({'s_x': '1', 's_y': '2', 's': '5x5'})
        assert_values_(e, (1, 2), 1, 2)
        assert_us_(e, '1x2', '1', '2')

    def test_flatten(self):
        s = self.Double.named('s')
        e = s('1x2')
        assert set(e.flatten()) == {('s', ''), ('s_y', ''), ('s_x', '')}

    def test_set(self):
        schema = self.Double.named('s')

        e = schema()
        assert not e.set({})
        assert_values_(e, None, None, None)
        assert_us_(e, '', '', '')

        # return-none and boom should get moved to their own test
        e = schema()
        assert e.set('return-none')
        assert_values_(e, None, None, None)
        assert_us_(e, '', '', '')

        e = schema()
        assert not e.set('boom')
        assert_values_(e, None, None, None)
        assert_us_(e, '', '', '')

        e = schema()
        assert not e.set('4x5')
        assert_values_(e, None, None, None)
        assert_us_(e, '', '', '')

        e = schema()
        assert e.set((4, 5))
        assert_values_(e, (4, 5), 4, 5)
        assert_us_(e, '4x5', '4', '5')

    def test_element_set(self):
        data = []
        sentinel = lambda sender, adapted: data.append((sender, adapted))

        schema = self.Double.named('s')

        schema((0, 0))
        with element_set.connected_to(sentinel):
            schema((1, 1))
            schema((2, 'bad child'))
            schema('bad root')

        assert len(data) == 7

        # 1, 1
        assert data[2][0].value == (1, 1)
        assert data[2][1] is True

        # 2, 'bad child'
        assert data[3][1] is True
        assert data[4][0].raw == 'bad child'
        assert data[4][1] is False
        assert data[5][1] is False

        # u'bad root
        assert data[6][0].raw == 'bad root'
        assert data[6][1] is False

    def test_set_default(self):
        s = self.Double.named('s').using(default=(4, 5))
        el = s()
        assert_values_(el, None, None, None)
        assert_us_(el, '', '', '')

        el.set_default()
        assert_values_(el, (4, 5), 4, 5)
        assert_us_(el, '4x5', '4', '5')

    def test_set_default_from_children(self):
        schema = self.Double.named('s')

        fields = {field.name: field for field in schema.field_schema}
        fields['x'].default = 4
        fields['y'].default = 5

        el = schema()
        assert_values_(el, None, None, None)
        assert_us_(el, '', '', '')

        el.set_default()
        assert_values_(el, (4, 5), 4, 5)
        assert_us_(el, '4x5', '4', '5')

    def test_update(self):
        s = self.Double.named('s')

        e = s((4, 5))
        assert_values_(e, (4, 5), 4, 5)
        assert_us_(e, '4x5', '4', '5')

        e['x'].set(6)
        assert_values_(e, (6, 5), 6, 5)
        assert_us_(e, '6x5', '6', '5')

        e.set((7, 8))
        assert_values_(e, (7, 8), 7, 8)
        assert_us_(e, '7x8', '7', '8')

    def test_explode_does_not_require_typechecks(self):
        s = self.Double.named('s')

        e = s((4, 5))
        assert_values_(e, (4, 5), 4, 5)
        assert_us_(e, '4x5', '4', '5')

        e.set((7, 'blagga'))
        assert_values_(e, None, 7, None)
        assert_us_(e, '7xblagga', '7', 'blagga')

    def test_value_assignement(self):
        s = self.Double.named('s')

        e = s()
        e.value = (1, 2)
        assert_values_(e, (1, 2), 1, 2)
        assert_us_(e, '1x2', '1', '2')

        e = s()
        e.u = "1x2"
        assert_values_(e, None, None, None)
        assert_us_(e, '', '', '')

    def test_repr(self):
        s = self.Double.named('s')
        e = s()
        assert repr(e)

        e.set((1, 2))
        assert repr(e)

        e.set(None)
        assert repr(e)


def test_repr_always_safe():
    # use the abstract class to emulate a subclass with broken compose.
    broken_impl = Compound.using(field_schema=[String.named('y')])
    e = broken_impl()
    assert repr(e)


def test_explode_abstract():
    schema = Compound.using(field_schema=[String.named('y')])
    el = schema()
    with pytest.raises(NotImplementedError):
        el.set('x')


def test_compose_abstract():
    schema = Compound.using(field_schema=[String.named('y')])
    el = schema()
    with pytest.raises(NotImplementedError):
        el.value


def test_compose_abstract_fixme():
    # really it'd be nice if serialize simply wasn't inherited. would
    # have to rejigger the hierarchy, not sure its worth it.
    schema = Compound.using(field_schema=[String.named('y')])
    el = schema()
    with pytest.raises(TypeError):
        schema.serialize(el, 'abc')


def assert_values_(el, top, x, y):
    assert el.value == top
    assert el['x'].value == x
    assert el['y'].value == y


def assert_us_(el, top, x, y):
    assert el.u == top
    assert el['x'].u == x
    assert el['y'].u == y


def test_sample_compound():
    s = DateYYYYMMDD.named('s')
    s.__compound_init__()

    assert ([field.name for field in s.field_schema] ==
            ['year', 'month', 'day'])

    e = s()
    assert e.value is None
    assert e['year'].value is None
    assert e.find_one('year').value is None

    when = datetime.date(2000, 10, 1)
    e.set(when)
    assert e.value == when
    assert e.find_one('year').value == 2000
    assert e.find_one('day').value == 1
    assert e.u == '2000-10-01'
    assert e.find_one('day').u == '01'

    e.find_one('day').set(5)
    assert e.value == datetime.date(2000, 10, 5)
    assert e.find_one('day').value == 5
    assert e.u == '2000-10-05'

    e = s()
    e.set(None)
    assert e.value is None
    assert e.u == ''
    assert e['year'].value is None
    assert e.find_one('year').value is None

    e = s()
    e.set('snaggle')
    assert e.value is None
    assert e.u == ''
    assert e['year'].value is None
    assert e.find_one('year').value is None


def test_compound_optional():

    required = Dict.of(DateYYYYMMDD.named('s').using(optional=False))

    f = required.from_defaults()
    assert not f.find_one('s/year').optional
    assert not f.find_one('s/month').optional
    assert not f.find_one('s/day').optional
    assert not f.validate()

    optional = Dict.of(DateYYYYMMDD.named('s').using(optional=True))

    f = optional.from_defaults()
    assert f.find_one('s/year').optional
    assert f.find_one('s/month').optional
    assert f.find_one('s/day').optional
    assert f.validate()


def test_compound_is_empty():
    element = DateYYYYMMDD()
    assert element.is_empty

    element.find_one('year').set(1979)
    assert not element.is_empty


def test_joined_string():
    el = JoinedString('abc')
    assert el.value == 'abc'
    assert [child.value for child in el] == ['abc']

    el = JoinedString('abc,def')
    assert el.value == 'abc,def'
    assert [child.value for child in el] == ['abc', 'def']

    el = JoinedString(['abc', 'def'])
    assert el.value == 'abc,def'
    assert [child.value for child in el] == ['abc', 'def']

    el = JoinedString(' abc,,ghi ')
    assert el.value == 'abc,ghi'
    assert [child.value for child in el] == ['abc', 'ghi']

    el = JoinedString('abc,,ghi', prune_empty=False)
    assert el.value == 'abc,,ghi'
    assert [child.value for child in el] == ['abc', '', 'ghi']

    # The child (String) strips by default
    el = JoinedString(' abc ,, ghi ', strip=False)
    assert el.value == 'abc,ghi'
    assert [child.value for child in el] == ['abc', 'ghi']

    # Try with a non-stripping String
    el = JoinedString(' abc ,, ghi ',
                      strip=False,
                      member_schema=String.using(strip=False))
    assert el.value == ' abc , ghi '
    assert [child.value for child in el] == [' abc ', ' ghi ']


def test_joined_string_flat():
    schema = JoinedString.named('js').of(Integer)

    for set_value, flat_value in [
        ([1], ('js', '1')),
        ('1', ('js', '1')),
        ([1, 2, 3], ('js', '1,2,3')),
        ('1,2,3', ('js', '1,2,3'))]:
        from_set = schema(set_value)
        assert from_set.flatten() == [flat_value]
        from_flat = schema.from_flat([flat_value])
        assert len(from_flat) == len(from_set)
        assert from_flat.flatten() == [flat_value]
        assert from_flat.value == from_set.value


def test_joined_string_regex():
    schema = JoinedString.using(separator=', ',
                                separator_regex=re.compile('X*,X*'))
    el = schema('abc')
    assert el.value == 'abc'
    assert [child.value for child in el] == ['abc']

    el = schema('abcX,Xdef')
    assert el.value == 'abc, def'
    assert [child.value for child in el] == ['abc', 'def']


def test_joined_non_string():
    schema = JoinedString.using(member_schema=Integer)
    el = schema('1')
    assert el.value == '1'
    assert [child.value for child in el] == [1]

    el = schema('1, 2, 3')
    assert el.value == '1,2,3'
    assert [child.value for child in el] == [1, 2, 3]

    el = schema([1, 2, 3])
    assert el.value == '1,2,3'
    assert [child.value for child in el] == [1, 2, 3]

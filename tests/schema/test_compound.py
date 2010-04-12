import datetime
import re

from flatland import (
    Compound,
    DateYYYYMMDD,
    Dict,
    Integer,
    JoinedString,
    String,
    )

from tests._util import assert_raises, eq_, raises


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
    assert_raises(Canary, InitNotCalledAtClassConstruction)

    # and again, if it fails
    assert_raises(Canary, InitNotCalledAtClassConstruction)


def test_compound_init_sequencing2():
    canary = []

    class MyCompound(Compound):
        field_schema = [String.named(u'x')]

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
    MyCompound.name = u'set by hand'
    element = MyCompound()
    assert canary == [MyCompound]

    # a clone of the class will trigger it
    MyCompound2 = MyCompound.named(u'something')
    element = MyCompound2()
    assert canary == [MyCompound, MyCompound2]
    assert MyCompound2.__dict__['_compound_prepared']

    # instance-level configuration will also
    element = MyCompound2(name=u'instance')
    assert type(element) is not MyCompound2
    assert isinstance(element, MyCompound2)
    assert canary == [MyCompound, MyCompound2, type(element)]
    assert type(element).__dict__['_compound_prepared']

    del canary[:]

    # it can be run by hand
    MyCompound4 = MyCompound.named(u'somethingelse')
    assert not MyCompound4.__dict__.get('_compound_prepared')

    MyCompound4.__compound_init__()

    assert MyCompound4.__dict__['_compound_prepared']
    assert canary == [MyCompound4]

    # and it won't be re-run automatically
    element = MyCompound4()
    assert canary == [MyCompound4]

    class MyCompound5(Compound):
        field_schema = [String.named(u'x')]

        @classmethod
        def __compound_init__(cls):
            assert isinstance(cls, type)
            canary.append(cls)

    # it can be @classmethod or not
    element = MyCompound5()
    assert canary == [MyCompound4, MyCompound5]


def test_compound_snarfs_override_init_keywords():

    class MyCompound(Compound):
        field_schema = [String.named(u'x')]
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

    assert_raises(TypeError, MyCompound, unknown='boom')


def test_compound_metaclass_calls_new():
    canary = []

    class MyCompound(Compound):
        name = u'abc'
        field_schema = [String.named(u'x')]

        def __new__(cls, *args, **kw):
            canary.append('new')
            return Compound.__new__(cls, *args, **kw)

        def __init__(self, *args, **kw):
            canary.append('init')

    assert MyCompound() is not None
    assert canary == ['new', 'init']

    del canary[:]

    class AltNewReturn(Compound):
        name = u'abc'
        field_schema = [String.named(u'x')]

        def __new__(cls, *args, **kw):
            canary.append('new')
            self = {}
            return self

        def __init__(self, *args, **kw):
            canary.append('init')

    assert AltNewReturn() is not None
    assert canary == ['new']


class TestDoubleField(object):

    def setup(self):

        class Double(Compound):

            field_schema = [Integer.named(u'x'), Integer.named(u'y')]

            def compose(self):
                ex, ey = self.get(u'x'), self.get(u'y')
                ux, uy = ex.u, ey.u
                if ex.u and ey.u:
                    string = u"%sx%s" % (ex.u, ey.u)
                else:
                    string = u''

                if ex.value is not None and ey.value is not None:
                    value = (ex.value, ey.value)
                else:
                    value = None

                return string, value

            def explode(self, value):
                if value == u'boom':
                    raise AttributeError('boom')
                if value == u'return-none':
                    return
                try:
                    x, y = value
                except (TypeError, ValueError):
                    return False
                self[u'x'].set(x)
                self[u'y'].set(y)
                return True

        self.Double = Double

    def test_from_flat(self):
        s = self.Double.named(u's')

        e = s.from_flat({})
        assert_values_(e, None, None, None)
        assert_us_(e, u'', u'', u'')

        e = s.from_flat({u's': u'1x2'})
        assert_values_(e, None, None, None)
        assert_us_(e, u'', u'', u'')

        e = s.from_flat({u's_x': u'1'})
        assert_values_(e, None, 1, None)
        assert_us_(e, u'', u'1', u'')

        e = s.from_flat({u's_x': u'1', u's_y': u'2'})
        assert_values_(e, (1, 2), 1, 2)
        assert_us_(e, u'1x2', u'1', u'2')

        e = s.from_flat({u's_x': u'1', u's_y': u'2', u's': u'5x5'})
        assert_values_(e, (1, 2), 1, 2)
        assert_us_(e, u'1x2', u'1', u'2')

    def test_flatten(self):
        s = self.Double.named(u's')
        e = s(u'1x2')
        eq_(set(e.flatten()),
            set([(u's', u''), (u's_y', u''), (u's_x', u'')]))

    def test_set(self):
        schema = self.Double.named(u's')

        e = schema()
        assert not e.set({})
        assert_values_(e, None, None, None)
        assert_us_(e, u'', u'', u'')

        # return-none and boom should get moved to their own test
        e = schema()
        assert e.set(u'return-none')
        assert_values_(e, None, None, None)
        assert_us_(e, u'', u'', u'')

        e = schema()
        assert not e.set(u'boom')
        assert_values_(e, None, None, None)
        assert_us_(e, u'', u'', u'')

        e = schema()
        assert not e.set(u'4x5')
        assert_values_(e, None, None, None)
        assert_us_(e, u'', u'', u'')

        e = schema()
        assert e.set((4, 5))
        assert_values_(e, (4, 5), 4, 5)
        assert_us_(e, u'4x5', u'4', u'5')

    def test_set_default(self):
        s = self.Double.named(u's').using(default=(4, 5))
        el = s()
        assert_values_(el, None, None, None)
        assert_us_(el, u'', u'', u'')

        el.set_default()
        assert_values_(el, (4, 5), 4, 5)
        assert_us_(el, u'4x5', u'4', u'5')

    def test_set_default_from_children(self):
        schema = self.Double.named(u's')

        fields = dict((field.name, field) for field in schema.field_schema)
        fields[u'x'].default = 4
        fields[u'y'].default = 5

        el = schema()
        assert_values_(el, None, None, None)
        assert_us_(el, u'', u'', u'')

        el.set_default()
        assert_values_(el, (4, 5), 4, 5)
        assert_us_(el, u'4x5', u'4', u'5')

    def test_update(self):
        s = self.Double.named(u's')

        e = s((4, 5))
        assert_values_(e, (4, 5), 4, 5)
        assert_us_(e, u'4x5', u'4', u'5')

        e[u'x'].set(6)
        assert_values_(e, (6, 5), 6, 5)
        assert_us_(e, u'6x5', u'6', u'5')

        e.set((7, 8))
        assert_values_(e, (7, 8), 7, 8)
        assert_us_(e, u'7x8', u'7', u'8')

    def test_explode_does_not_require_typechecks(self):
        s = self.Double.named(u's')

        e = s((4, 5))
        assert_values_(e, (4, 5), 4, 5)
        assert_us_(e, u'4x5', u'4', u'5')

        e.set((7, u'blagga'))
        assert_values_(e, None, 7, None)
        assert_us_(e, u'7xblagga', u'7', u'blagga')

    def test_value_assignement(self):
        s = self.Double.named(u's')

        e = s()
        e.value = (1, 2)
        assert_values_(e, (1, 2), 1, 2)
        assert_us_(e, u'1x2', u'1', u'2')

        e = s()
        e.u = u"1x2"
        assert_values_(e, None, None, None)
        assert_us_(e, u'', u'', u'')

    def test_repr(self):
        s = self.Double.named(u's')
        e = s()
        assert repr(e)

        e.set((1, 2))
        assert repr(e)

        e.set(None)
        assert repr(e)


def test_repr_always_safe():
    # use the abstract class to emulate a subclass with broken compose.
    broken_impl = Compound.using(field_schema=[String.named(u'y')])
    e = broken_impl()
    assert repr(e)


@raises(NotImplementedError)
def test_explode_abstract():
    schema = Compound.using(field_schema=[String.named(u'y')])
    el = schema()
    el.set(u'x')


@raises(NotImplementedError)
def test_compose_abstract():
    schema = Compound.using(field_schema=[String.named(u'y')])
    el = schema()
    el.value


@raises(TypeError)
def test_compose_abstract_fixme():
    # really it'd be nice if serialize simply wasn't inherited. would
    # have to rejigger the hierarchy, not sure its worth it.
    schema = Compound.using(field_schema=[String.named(u'y')])
    el = schema()
    schema.serialize(el, u'abc')


def assert_values_(el, top, x, y):
    eq_(el.value, top)
    eq_(el[u'x'].value, x)
    eq_(el[u'y'].value, y)


def assert_us_(el, top, x, y):
    eq_(el.u, top)
    eq_(el[u'x'].u, x)
    eq_(el[u'y'].u, y)


def test_sample_compound():
    s = DateYYYYMMDD.named(u's')
    s.__compound_init__()

    assert ([field.name for field in s.field_schema] ==
            [u'year', u'month', u'day'])

    e = s()
    assert e.value is None
    assert e[u'year'].value is None
    assert e.el(u'year').value is None

    when = datetime.date(2000, 10, 1)
    e.set(when)
    assert e.value == when
    assert e.el(u'year').value == 2000
    assert e.el(u'day').value == 1
    assert e.u == u'2000-10-01'
    assert e.el(u'day').u == u'01'

    e.el(u'day').set(5)
    assert e.value == datetime.date(2000, 10, 5)
    assert e.el(u'day').value == 5
    assert e.u == u'2000-10-05'

    e = s()
    e.set(None)
    assert e.value is None
    assert e.u == u''
    assert e[u'year'].value is None
    assert e.el(u'year').value is None

    e = s()
    e.set(u'snaggle')
    assert e.value is None
    assert e.u == u''
    assert e[u'year'].value is None
    assert e.el(u'year').value is None


def test_compound_optional():

    required = Dict.of(DateYYYYMMDD.named(u's').using(optional=False))

    f = required.from_defaults()
    assert not f.el(u's.year').optional
    assert not f.el(u's.month').optional
    assert not f.el(u's.day').optional
    assert not f.validate()

    optional = Dict.of(DateYYYYMMDD.named(u's').using(optional=True))

    f = optional.from_defaults()
    assert f.el(u's.year').optional
    assert f.el(u's.month').optional
    assert f.el(u's.day').optional
    assert f.validate()


def test_compound_is_empty():
    element = DateYYYYMMDD()
    assert element.is_empty

    element.el(u'year').set(1979)
    assert not element.is_empty


def test_joined_string():
    el = JoinedString(u'abc')
    assert el.value == u'abc'
    assert [child.value for child in el] == [u'abc']

    el = JoinedString(u'abc,def')
    assert el.value == u'abc,def'
    assert [child.value for child in el] == [u'abc', u'def']

    el = JoinedString([u'abc', u'def'])
    assert el.value == u'abc,def'
    assert [child.value for child in el] == [u'abc', u'def']

    el = JoinedString(u' abc,,ghi ')
    assert el.value == u'abc,ghi'
    assert [child.value for child in el] == [u'abc', u'ghi']

    el = JoinedString(u'abc,,ghi', prune_empty=False)
    assert el.value == u'abc,,ghi'
    assert [child.value for child in el] == [u'abc', u'', u'ghi']

    # The child (String) strips by default
    el = JoinedString(u' abc ,, ghi ', strip=False)
    assert el.value == 'abc,ghi'
    assert [child.value for child in el] == [u'abc', u'ghi']

    # Try with a non-stripping String
    el = JoinedString(u' abc ,, ghi ',
                      strip=False,
                      member_schema=String.using(strip=False))
    assert el.value == ' abc , ghi '
    assert [child.value for child in el] == [u' abc ', u' ghi ']


def test_joined_string_regex():
    schema = JoinedString.using(separator=u', ',
                                separator_regex=re.compile('X*,X*'))
    el = schema(u'abc')
    assert el.value == u'abc'
    assert [child.value for child in el] == [u'abc']

    el = schema(u'abcX,Xdef')
    assert el.value == u'abc, def'
    assert [child.value for child in el] == [u'abc', u'def']


def test_joined_non_string():
    schema = JoinedString.using(member_schema=Integer)
    el = schema(u'1')
    assert el.value == u'1'
    assert [child.value for child in el] == [1]

    el = schema(u'1, 2, 3')
    assert el.value == u'1,2,3'
    assert [child.value for child in el] == [1, 2, 3]

    el = schema([1, 2, 3])
    assert el.value == u'1,2,3'
    assert [child.value for child in el] == [1, 2, 3]

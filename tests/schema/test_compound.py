import datetime
from flatland import schema, util
from tests._util import eq_, assert_raises, raises


class TestDoubleField(object):
    def setup(self):
        class Double(schema.Compound):
            def __init__(self, name, **kw):
                children = [schema.Integer('x'), schema.Integer('y')]
                schema.Compound.__init__(self, name, *children, **kw)

            def compose(self, element):
                ex, ey = element.get('x'), element.get('y')
                ux, uy = ex.u, ey.u
                if ex.u and ey.u:
                    string = "%sx%s" % (ex.u, ey.u)
                else:
                    string = ''

                if ex.value is not None and ey.value is not None:
                    value = (ex.value, ey.value)
                else:
                    value = None

                return string, value

            def explode(self, element, value):
                try:
                    x, y = value
                except (TypeError, ValueError):
                    return
                element['x'].set(x)
                element['y'].set(y)
        self.Double = Double

    def test_from_flat(self):
        s = self.Double('s')

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
        s = self.Double('s')
        e = s.create_element(value='1x2')
        eq_(set(e.flatten()),
            set([(u's', u''), (u's_y', u''), (u's_x', u'')]))

    def test_set(self):
        s = self.Double('s')

        e = s.create_element(value={})
        assert_values_(e, None, None, None)
        assert_us_(e, u'', u'', u'')

        e = s.create_element(value=u'4x5')
        assert_values_(e, None, None, None)
        assert_us_(e, u'', u'', u'')

        e = s.create_element(value=(4, 5))
        assert_values_(e, (4, 5), 4, 5)
        assert_us_(e, u'4x5', u'4', u'5')

    def test_update(self):
        s = self.Double('s')

        e = s.create_element(value=(4, 5))
        assert_values_(e, (4, 5), 4, 5)
        assert_us_(e, u'4x5', u'4', u'5')

        e['x'].set(6)
        assert_values_(e, (6, 5), 6, 5)
        assert_us_(e, u'6x5', u'6', u'5')

        e.set((7,8))
        assert_values_(e, (7, 8), 7, 8)
        assert_us_(e, u'7x8', u'7', u'8')

    def test_explode_does_not_require_typechecks(self):
        s = self.Double('s')

        e = s.create_element(value=(4, 5))
        assert_values_(e, (4, 5), 4, 5)
        assert_us_(e, u'4x5', u'4', u'5')

        e.set((7, 'blagga'))
        assert_values_(e, None, 7, None)
        assert_us_(e, u'7xblagga', u'7', u'blagga')

    def test_value_assignement(self):
        s = self.Double('s')

        e = s.create_element()
        e.value = (1, 2)
        assert_values_(e, (1, 2), 1, 2)
        assert_us_(e, u'1x2', u'1', u'2')

        e = s.create_element()
        e.u = "1x2"
        assert_values_(e, None, None, None)
        assert_us_(e, u'', u'', u'')

    def test_repr(self):
        s = self.Double('s')
        e = s.create_element()
        assert repr(e)

        e.set((1, 2))
        assert repr(e)

        e.set(None)
        assert repr(e)

def test_repr_always_safe():
    # use the abstract class to emulate a subclass with broken compose.
    broken_impl = schema.Compound('x', schema.String('y'))
    e = broken_impl.create_element()
    assert repr(e)

@raises(NotImplementedError)
def test_explode_abstract():
    e = schema.Compound('x', schema.String('y')).create_element()
    e.set('x')

@raises(NotImplementedError)
def test_compose_abstract():
    e = schema.Compound('x', schema.String('y')).create_element()
    e.value

@raises(TypeError)
def test_compose_abstract():
    # really it'd be nice if serialize simply wasn't inherited. would
    # have to rejigger the hierarchy, not sure its worth it.
    s = schema.Compound('x', schema.String('y'))
    e = s.create_element()
    s.serialize(e, 'abc')

def assert_values_(el, top, x, y):
    eq_(el.value, top)
    eq_(el['x'].value, x)
    eq_(el['y'].value, y)

def assert_us_(el, top, x, y):
    eq_(el.u, top)
    eq_(el['x'].u, x)
    eq_(el['y'].u, y)

def test_sample_compound():
    s = schema.DateYYYYMMDD('s')
    assert 'year' in s.fields
    assert 'month' in s.fields
    assert 'day' in s.fields

    e = s.create_element()
    assert e.value is None
    assert e['year'].value is None
    assert e.el('year').value is None

    when = datetime.date(2000, 10, 1)
    e.set(when)
    assert e.value == when
    assert e.el('year').value == 2000
    assert e.el('day').value == 1
    assert e.u == u'2000-10-01'
    assert e.el('day').u == u'01'

    e.el('day').set(5)
    assert e.value == datetime.date(2000, 10, 5)
    assert e.el('day').value == 5
    assert e.u == u'2000-10-05'

    e = s.create_element()
    e.set(None)
    assert e.value is None
    assert e.u == u''
    assert e['year'].value is None
    assert e.el('year').value is None

    e = s.create_element()
    e.set('snaggle')
    assert e.value is None
    assert e.u == u''
    assert e['year'].value is None
    assert e.el('year').value is None

def test_compound_optional():
    class Form(schema.Form):
        schema = [schema.DateYYYYMMDD('s', optional=False)]

    f = Form.from_defaults()
    assert not f.el('s.year').schema.optional
    assert not f.el('s.month').schema.optional
    assert not f.el('s.day').schema.optional
    assert not f.validate()

    class Form(schema.Form):
        schema = [schema.DateYYYYMMDD('s', optional=True)]

    f = Form.from_defaults()
    assert f.el('s.year').schema.optional
    assert f.el('s.month').schema.optional
    assert f.el('s.day').schema.optional
    assert f.validate()

def test_compound_is_empty():
    s = schema.DateYYYYMMDD('s')
    e = s.create_element()
    assert e.is_empty

    e.el('year').set(1979)
    assert not e.is_empty

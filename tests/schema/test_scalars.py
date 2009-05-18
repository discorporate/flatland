import datetime
from flatland import schema, valid
from tests._util import eq_, assert_raises


def test_scalar_abstract():
    sc = schema.scalars.Scalar('foo')

    element = sc()
    assert_raises(NotImplementedError, element.set, 'blagga')


def test_scalar_assignments_are_independent():
    sc = schema.scalars.Scalar('foo')

    element = sc()
    assert not element.u
    assert not element.value
    element.u = u'abc'
    assert element.value is None

    element = sc()
    assert not element.u
    assert not element.value
    element.value = u'abc'
    eq_(element.u, u'')
    eq_(element.value, u'abc')


def test_scalar_set_flat():
    """Scalars take on the first value if duplicates are present."""

    class SimpleScalar(schema.scalars.Scalar):
        def adapt(self, element, value):
            return value

    data = ((u'a', 1),
            (u'b', 2),
            (u'a', 3))

    def element_for(name):
        s = SimpleScalar(name)
        element = s()
        element.set_flat(data)
        return element

    eq_(element_for(u'a').value, 1)
    eq_(element_for(u'b').value, 2)
    eq_(element_for(u'c').value, None)


def test_string():
    assert_raises(TypeError, schema.String)

    for value, expected in ((u'abc', u'abc'), ('abc', u'abc'), (123, u'123'),
                            (u'abc ', u'abc'), (' abc ', u'abc')):
        for st in schema.String('foo'), schema.String('foo', strip=True):
            element = st()
            element.set(value)
            eq_(element.u, expected)
            eq_(unicode(element), expected)
            eq_(element.value, expected)

    for value, expected in ((u'abc ', u'abc '), (' abc ', u' abc ')):
        st = schema.String('foo', strip=False)
        element = st()
        element.set(value)
        eq_(element.u, expected)
        eq_(unicode(element), expected)
        eq_(element.value, expected)

    for value, expected_value, expected_unicode in (
                        (u'', u'', u''), (None, None, u'')):
        st = schema.String('foo')
        element = st()
        element.set(value)
        eq_(element.u, expected_unicode)
        eq_(unicode(element), expected_unicode)
        eq_(element.value, expected_value)


def test_string_is_empty():
    st = schema.String('foo')
    element = st()
    element.set(u'')
    assert element.is_empty

    element = st()
    element.set(u'foo')
    assert not element.is_empty

    element = st()
    assert element.is_empty


def validate_element_set(type_, raw, value, uni, schema_opts={}):
    element = type_('i', **schema_opts).create_element()
    element.set(raw)
    eq_(element.value, value)
    eq_(element.u, uni)
    eq_(unicode(element), uni)
    eq_(element.__nonzero__(), bool(uni and value))


def test_scalar_set():
    # a variety of scalar set() failure cases, shoved through Integer
    for spec in (
        ([],         None, u'[]'),
        ('\xef\xf0', None, ur'\ufffd\ufffd'),
        (None,       None, u'')):
        yield (validate_element_set, schema.Integer) + spec


def test_integer():
    for spec in ((u'123',    123,  u'123'),
                 (u' 123 ',  123,  u'123'),
                 (u'xyz',    None, u'xyz'),
                 (u'xyz123', None, u'xyz123'),
                 ('123xyz',  None, u'123xyz'),
                 ('123.0',   None, u'123.0'),
                 (u'+123',   123,  u'123'),
                 (u'-123',   -123, u'-123'),
                 (u' +123 ', 123,  u'123'),
                 (u' -123 ', -123, u'-123'),
                 (u'+123',   123,  u'123', dict(signed=False)),
                 (u'-123',   None, u'-123', dict(signed=False)),
                 (123,       123,  u'123'),
                 (-123,      None, u'-123', dict(signed=False))):
        yield (validate_element_set, schema.Integer) + spec


def test_long():
    for spec in ((u'123',    123L,  u'123'),
                 (u' 123 ',  123L,  u'123'),
                 (u'xyz',    None,  u'xyz'),
                 (u'xyz123', None,  u'xyz123'),
                 ('123xyz',  None,  u'123xyz'),
                 ('123.0',   None,  u'123.0'),
                 (u'+123',   123L,  u'123'),
                 (u'-123',   -123L, u'-123'),
                 (u' +123 ', 123L,  u'123'),
                 (u' -123 ', -123L, u'-123'),
                 (u'+123',   123L,  u'123', dict(signed=False)),
                 (u'-123',   None,  u'-123', dict(signed=False))):
        yield (validate_element_set, schema.Long) + spec


def test_float():
    for spec in ((u'123',    123.0,  u'123.000000'),
                 (u' 123 ',  123.0,  u'123.000000'),
                 (u'xyz',    None,  u'xyz'),
                 (u'xyz123', None,  u'xyz123'),
                 ('123xyz',  None,  u'123xyz'),
                 ('123.0',   123.0,  u'123.000000'),
                 (u'+123',   123.0,  u'123.000000'),
                 (u'-123',   -123.0, u'-123.000000'),
                 (u' +123 ', 123.0,  u'123.000000'),
                 (u' -123 ', -123.0, u'-123.000000'),
                 (u'+123',   123.0,  u'123.000000', dict(signed=False)),
                 (u'-123',   None,  u'-123', dict(signed=False))):
        yield (validate_element_set, schema.Float) + spec

    class TwoDigitFloat(schema.Float):
        format = u'%0.2f'

    for spec in ((u'123',    123.0,  u'123.00'),
                 (u' 123 ',  123.0,  u'123.00'),
                 (u'xyz',    None,  u'xyz'),
                 (u'xyz123', None,  u'xyz123'),
                 ('123xyz',  None,  u'123xyz'),
                 ('123.0',   123.0,  u'123.00'),
                 ('123.00',   123.0,  u'123.00'),
                 ('123.005',   123.005,  u'123.00')):
        yield (validate_element_set, TwoDigitFloat) + spec


def test_boolean():
    for ok in schema.Boolean.true_synonyms:
        yield validate_element_set, schema.Boolean, ok, True, u'1'
        yield (validate_element_set, schema.Boolean, ok, True, u'baz',
               dict(true=u'baz'))

    for not_ok in schema.Boolean.false_synonyms:
        yield validate_element_set, schema.Boolean, not_ok, False, u''
        yield (validate_element_set, schema.Boolean, not_ok, False, u'quux',
               dict(false=u'quux'))

    for bogus in u'abc', u'1.0', u'0.0', u'None':
        yield validate_element_set, schema.Boolean, bogus, None, u''


def test_scalar_set_default():
    el = schema.Integer('i', ).create_element()
    el.set_default()
    assert el.value is None

    el = schema.Integer('i', default=10).create_element()
    el.set_default()
    assert el.value == 10

    el = schema.Integer('i', default_factory=lambda e: 20).create_element()
    el.set_default()
    assert el.value == 20


def test_constrained_is_abstract():
    c = schema.Constrained('foo')
    el = c.create_element()
    el.set(u'anything')
    assert el.value is None
    assert el.u == u'anything'


def test_constrained_instance_override():
    def valid(ok_values, eltype=schema.scalars.StringElement):
        def validator(element, value):
            assert isinstance(element, eltype)
            return value in ok_values
        return validator

    c = schema.Constrained('foo', valid_value=valid((u'a',)))
    el = c.create_element()
    assert el.set(u'a')
    assert el.value == u'a'
    assert el.u == u'a'

    assert not el.set(u'b')
    assert el.value is None
    assert el.u == u'b'

    c = schema.Constrained('foo', schema.Integer, valid_value=valid(
        (1,), eltype=schema.scalars.ScalarElement))
    el = c.create_element()
    assert el.set(u'1')
    assert el.value == 1
    assert el.u == u'1'

    for invalid in u'2', u'x':
        assert not el.set(invalid)
        assert el.value == None
        assert el.u == invalid


def test_constrained_instance_contrived():
    # check that fringe types that adapt as None can used in bounds
    class CustomInteger(schema.Integer):
        def adapt(self, element, value):
            try:
                return schema.Integer.adapt(self, element, value)
            except:
                return None

    c = schema.Constrained('foo', CustomInteger,
                           valid_value=lambda e, v: v in (1, None))
    el = c.create_element()
    assert el.set(u'1')

    for out_of_bounds in u'2', u'3':
        assert not el.set(out_of_bounds)

    for invalid in u'x', u'':
        assert el.set(invalid)
        assert el.value is None
        assert el.u == u''


def test_default_enum():
    good_values = ('a', 'b', 'c')
    for enum in (schema.Enum('abcs', *good_values),
                 schema.Enum('abcs', valid_values=good_values)):
        for good_val in good_values:
            el = enum.create_element()
            el.set(good_val)
            assert el.value == good_val
            assert el.u == good_val
            assert not el.errors

        el = enum.create_element()
        el.set('d')
        assert el.value is None
        assert el.u == u'd'


def test_typed_enum():
    good_values = range(1, 4)
    enum = schema.Enum('e', valid_values=good_values, child_type=schema.Integer)

    for good_val in good_values:
        el = enum.create_element()
        el.set(unicode(good_val))
        assert el.value == good_val
        assert el.u == unicode(good_val)
        assert not el.errors

    el = enum.create_element()
    el.set('x')
    assert el.value is None
    assert el.u == u'x'

    el = enum.create_element()
    el.set('5')
    assert el.value is None
    assert el.u == u'5'


def test_enum_with_dynamic_option():
    enum = schema.scalars.Enum('abcs', 'a', 'b', 'c')
    el = enum()
    el.valid_values = ('a', 'b')

    el.set('a')
    assert el.value == u'a'

    el.set('c')
    assert el.value == None
    assert el.u == u'c'


def test_date():
    t = datetime.date
    for spec in (
        (u'2009-10-10',   t(2009, 10, 10), u'2009-10-10'),
        (u'2010-08-02',   t(2010, 8, 2), u'2010-08-02'),
        (u' 2010-08-02 ', t(2010, 8, 2), u'2010-08-02'),
        (u' 2010-08-02 ', None, u' 2010-08-02 ', dict(strip=False)),
        (u'2011-8-2',     None, u'2011-8-2'),
        (u'blagga',       None, u'blagga')):
        yield (validate_element_set, schema.Date) + spec


def test_time():
    t = datetime.time
    for spec in (
        (u'08:09:10', t(8, 9, 10), u'08:09:10'),
        (u'23:24:25', t(23, 24, 25), u'23:24:25'),
        (u'24:25:26', None, u'24:25:26'),
        (u'bogus', None, u'bogus')):
        yield (validate_element_set, schema.Time) + spec


def test_datetime():
    t = datetime.datetime
    for spec in (
        (u'2009-10-10 08:09:10', t(2009, 10, 10, 8, 9, 10),
         u'2009-10-10 08:09:10'),
        (u'2010-08-02 25:26:27', None, u'2010-08-02 25:26:27'),
        (u'2010-13-22 09:09:09', None, u'2010-13-22 09:09:09')):
        yield (validate_element_set, schema.DateTime) + spec


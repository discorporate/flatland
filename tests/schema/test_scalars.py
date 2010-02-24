import datetime
import decimal

from flatland import (
    Boolean,
    Date,
    DateTime,
    Decimal,
    Float,
    Integer,
    Long,
    Scalar,
    String,
    Time,
    )

from tests._util import eq_, assert_raises, requires_unicode_coercion


def test_scalar_abstract():
    el = Scalar()
    assert_raises(NotImplementedError, el.set, 'blagga')


def test_scalar_assignments_are_independent():
    element = Scalar()

    assert not element.u
    assert not element.value
    element.u = u'abc'
    assert element.value is None

    element = Scalar()
    assert not element.u
    assert not element.value
    element.value = u'abc'
    eq_(element.u, u'')
    eq_(element.value, u'abc')


def test_scalar_set_flat():
    # Scalars take on the first value if duplicates are present.
    class SimpleScalar(Scalar):

        def adapt(self, value):
            return value

    data = ((u'a', u'1'),
            (u'b', u'2'),
            (u'a', u'3'))

    def element_for(name):
        element = SimpleScalar(name=name)
        element.set_flat(data)
        return element

    eq_(element_for(u'a').value, u'1')
    eq_(element_for(u'b').value, u'2')
    eq_(element_for(u'c').value, None)


@requires_unicode_coercion
def test_string():
    for value, expected in ((u'abc', u'abc'), ('abc', u'abc'), (123, u'123'),
                            (u'abc ', u'abc'), (' abc ', u'abc')):
        for element in String(), String(strip=True):
            element.set(value)
            eq_(element.u, expected)
            eq_(unicode(element), expected)
            eq_(element.value, expected)

    for value, expected in ((u'abc ', u'abc '), (' abc ', u' abc ')):
        element = String(value, strip=False)
        eq_(element.u, expected)
        eq_(unicode(element), expected)
        eq_(element.value, expected)

    for value, expected_value, expected_unicode in ((u'', u'', u''),
                                                    (None, None, u'')):
        element = String(value)
        eq_(element.u, expected_unicode)
        eq_(unicode(element), expected_unicode)
        eq_(element.value, expected_value)


def test_string_is_empty():
    element = String(u'')
    assert element.is_empty

    element = String(u'foo')
    assert not element.is_empty


def validate_element_set(type_, raw, value, uni, schema_opts={}):
    element = type_(raw, **schema_opts)
    eq_(element.value, value)
    eq_(element.u, uni)
    eq_(unicode(element), uni)
    eq_(element.__nonzero__(), bool(uni and value))


coerced_validate_element_set = requires_unicode_coercion(validate_element_set)


def test_scalar_set():
    # a variety of scalar set() failure cases, shoved through Integer
    for spec in (
        (None,       None, u''),
        ):
        yield (validate_element_set, Integer) + spec

    for spec in (
        ([],         None, u'[]'),
        ('\xef\xf0', None, ur'\ufffd\ufffd'),
        ):
        yield (coerced_validate_element_set, Integer) + spec


def test_integer():
    for spec in ((u'123',    123,  u'123'),
                 (u' 123 ',  123,  u'123'),
                 (u'xyz',    None, u'xyz'),
                 (u'xyz123', None, u'xyz123'),
                 (u'123xyz', None, u'123xyz'),
                 (u'123.0',  None, u'123.0'),
                 (u'+123',   123,  u'123'),
                 (u'-123',   -123, u'-123'),
                 (u' +123 ', 123,  u'123'),
                 (u' -123 ', -123, u'-123'),
                 (u'+123',   123,  u'123', dict(signed=False)),
                 (u'-123',   None, u'-123', dict(signed=False)),
                 (123,       123,  u'123')):
        yield (validate_element_set, Integer) + spec

    for spec in ((-123,      None, u'-123', dict(signed=False)),):
        yield (coerced_validate_element_set, Integer) + spec


def test_long():
    for spec in ((u'123',    123L,  u'123'),
                 (u' 123 ',  123L,  u'123'),
                 (u'xyz',    None,  u'xyz'),
                 (u'xyz123', None,  u'xyz123'),
                 (u'123xyz', None,  u'123xyz'),
                 (u'123.0',  None,  u'123.0'),
                 (u'+123',   123L,  u'123'),
                 (u'-123',   -123L, u'-123'),
                 (u' +123 ', 123L,  u'123'),
                 (u' -123 ', -123L, u'-123'),
                 (u'+123',   123L,  u'123', dict(signed=False)),
                 (u'-123',   None,  u'-123', dict(signed=False))):
        yield (validate_element_set, Long) + spec


def test_float():
    for spec in ((u'123',    123.0,  u'123.000000'),
                 (u' 123 ',  123.0,  u'123.000000'),
                 (u'xyz',    None,   u'xyz'),
                 (u'xyz123', None,   u'xyz123'),
                 (u'123xyz', None,   u'123xyz'),
                 (u'123.0',  123.0,  u'123.000000'),
                 (u'+123',   123.0,  u'123.000000'),
                 (u'-123',   -123.0, u'-123.000000'),
                 (u' +123 ', 123.0,  u'123.000000'),
                 (u' -123 ', -123.0, u'-123.000000'),
                 (u'+123',   123.0,  u'123.000000', dict(signed=False)),
                 (u'-123',   None,   u'-123', dict(signed=False))):
        yield (validate_element_set, Float) + spec

    class TwoDigitFloat(Float):
        format = u'%0.2f'

    for spec in ((u'123',     123.0,   u'123.00'),
                 (u' 123 ',   123.0,   u'123.00'),
                 (u'xyz',     None,    u'xyz'),
                 (u'xyz123',  None,    u'xyz123'),
                 (u'123xyz',  None,    u'123xyz'),
                 (u'123.0',   123.0,   u'123.00'),
                 (u'123.00',  123.0,   u'123.00'),
                 (u'123.005', 123.005, u'123.00')):
        yield (validate_element_set, TwoDigitFloat) + spec


def test_decimal():
    d = decimal.Decimal
    for spec in ((u'123',    d('123'),   u'123.000000'),
                 (u' 123 ',  d('123'),   u'123.000000'),
                 (u'xyz',    None,       u'xyz'),
                 (u'xyz123', None,       u'xyz123'),
                 (u'123xyz', None,       u'123xyz'),
                 (u'123.0',  d('123.0'), u'123.000000'),
                 (u'+123',   d('123'),   u'123.000000'),
                 (u'-123',   d('-123'), u'-123.000000'),
                 (u' +123 ', d('123'),   u'123.000000'),
                 (u' -123 ', d('-123'),  u'-123.000000'),
                 (123,       d('123'),   u'123.000000'),
                 (-123,      d('-123'),  u'-123.000000'),
                 (d(123),    d('123'),   u'123.000000'),
                 (d(-123),   d('-123'),  u'-123.000000'),
                 (123.456,   None,       u'123.456'),
                 (u'+123',   d('123'),   u'123.000000', dict(signed=False)),
                 (u'-123',   None,       u'-123', dict(signed=False))):
        yield (validate_element_set, Decimal) + spec

    TwoDigitDecimal = Decimal.using(format=u'%0.2f')

    for spec in ((u'123',     d('123.0'),   u'123.00'),
                 (u' 123 ',   d('123.0'),   u'123.00'),
                 (u'12.34',   d('12.34'),   u'12.34'),
                 (u'12.3456', d('12.3456'), u'12.35')):
        yield (validate_element_set, TwoDigitDecimal) + spec


def test_boolean():
    for ok in Boolean.true_synonyms:
        yield validate_element_set, Boolean, ok, True, u'1'
        yield (validate_element_set, Boolean, ok, True, u'baz',
               dict(true=u'baz'))

    for not_ok in Boolean.false_synonyms:
        yield validate_element_set, Boolean, not_ok, False, u''
        yield (validate_element_set, Boolean, not_ok, False, u'quux',
               dict(false=u'quux'))

    for bogus in u'abc', u'1.0', u'0.0', u'None':
        yield validate_element_set, Boolean, bogus, None, u''


def test_scalar_set_default():
    el = Integer()
    el.set_default()
    assert el.value is None

    el = Integer(default=10)
    el.set_default()
    assert el.value == 10

    el = Integer(default_factory=lambda e: 20)
    el.set_default()
    assert el.value == 20


def test_date():
    t = datetime.date
    for spec in (
        (u'2009-10-10',   t(2009, 10, 10), u'2009-10-10'),
        (u'2010-08-02',   t(2010, 8, 2), u'2010-08-02'),
        (u' 2010-08-02 ', t(2010, 8, 2), u'2010-08-02'),
        (u' 2010-08-02 ', None, u' 2010-08-02 ', dict(strip=False)),
        (u'2011-8-2',     None, u'2011-8-2'),
        (u'blagga',       None, u'blagga')):
        yield (validate_element_set, Date) + spec


def test_time():
    t = datetime.time
    for spec in (
        (u'08:09:10', t(8, 9, 10), u'08:09:10'),
        (u'23:24:25', t(23, 24, 25), u'23:24:25'),
        (u'24:25:26', None, u'24:25:26'),
        (u'bogus', None, u'bogus')):
        yield (validate_element_set, Time) + spec


def test_datetime():
    t = datetime.datetime
    for spec in (
        (u'2009-10-10 08:09:10', t(2009, 10, 10, 8, 9, 10),
         u'2009-10-10 08:09:10'),
        (u'2010-08-02 25:26:27', None, u'2010-08-02 25:26:27'),
        (u'2010-13-22 09:09:09', None, u'2010-13-22 09:09:09')):
        yield (validate_element_set, DateTime) + spec

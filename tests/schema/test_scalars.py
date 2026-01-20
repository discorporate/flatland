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
    Unset,
    element_set,
)
from flatland._compat import long_type

import pytest
from tests._util import requires_unicode_coercion


def test_scalar_abstract():
    el = Scalar()
    with pytest.raises(NotImplementedError):
        el.set("blagga")


def test_scalar_assignments_are_independent():
    element = Scalar()

    assert not element.u
    assert not element.value
    element.u = "abc"
    assert element.value is None

    element = Scalar()
    assert not element.u
    assert not element.value
    element.value = "abc"
    assert element.u == ""
    assert element.value == "abc"


def test_scalar_set_flat():
    # Scalars take on the first value if duplicates are present.
    class SimpleScalar(Scalar):

        def adapt(self, value):
            return value

    data = (("a", "1"), ("b", "2"), ("a", "3"))

    def element_for(name):
        element = SimpleScalar(name=name)
        element.set_flat(data)
        return element

    assert element_for("a").value == "1"
    assert element_for("a").raw == "1"
    assert element_for("b").value == "2"
    assert element_for("b").raw == "2"
    assert element_for("c").value == None
    assert element_for("c").raw == Unset


def test_string():
    for value, expected in (
        ("abc", "abc"),
        ("abc", "abc"),
        (123, "123"),
        ("abc ", "abc"),
        (" abc ", "abc"),
    ):
        for element in String(), String(strip=True):
            element.set(value)
            assert element.u == expected
            assert element.__unicode__() == expected
            assert element.value == expected

    for value, expected in (("abc ", "abc "), (" abc ", " abc ")):
        element = String(value, strip=False)
        assert element.u == expected
        assert element.__unicode__() == expected
        assert element.value == expected

    for value, expected_value, expected_unicode in (("", "", ""), (None, None, "")):
        element = String(value)
        assert element.u == expected_unicode
        assert element.__unicode__() == expected_unicode
        assert element.value == expected_value


def test_string_is_empty():
    element = String("")
    assert element.is_empty

    element = String("foo")
    assert not element.is_empty


def validate_element_set(type_, raw, value, uni, schema_opts={}, set_return=None):
    if set_return is None:
        set_return = value is not None
    element = type_(**schema_opts)
    assert element.set(raw) == set_return
    assert element.value == value
    assert element.u == uni
    assert element.__unicode__() == uni
    assert element.__nonzero__() == bool(uni and value)
    assert element.__bool__() == bool(uni and value)


coerced_validate_element_set = requires_unicode_coercion(validate_element_set)


def test_scalar_set():
    # a variety of scalar set() failure cases, shoved through Integer
    for spec in (
        (None, None, "", {}, True),
        ([], None, "[]"),
    ):
        validate_element_set(Integer, *spec)

    # TODO: test below fails on py3 and it is unclear what it is about.
    if False:
        for spec in (("\xef\xf0", None, "\ufffd\ufffd"),):
            coerced_validate_element_set(Integer, *spec)


def test_scalar_set_signal():
    data = []
    sentinel = lambda sender, adapted: data.append((sender, adapted))

    Integer(0)
    with element_set.connected_to(sentinel):
        Integer(1)
        Integer("bogus")

    assert len(data) == 2
    assert data[0][0].value == 1
    assert data[0][1] is True

    assert data[1][0].raw == "bogus"
    assert data[1][1] is False


def test_integer():
    for spec in (
        ("123", 123, "123"),
        (" 123 ", 123, "123"),
        ("xyz", None, "xyz"),
        ("xyz123", None, "xyz123"),
        ("123xyz", None, "123xyz"),
        ("123.0", None, "123.0"),
        ("+123", 123, "123"),
        ("-123", -123, "-123"),
        (" +123 ", 123, "123"),
        (" -123 ", -123, "-123"),
        ("+123", 123, "123", dict(signed=False)),
        ("-123", None, "-123", dict(signed=False)),
        (123, 123, "123"),
        (None, None, "", {}, True),
        (-123, None, "-123", dict(signed=False)),
    ):
        validate_element_set(Integer, *spec)


def test_long():
    L = long_type
    for spec in (
        ("123", L(123), "123"),
        (" 123 ", L(123), "123"),
        ("xyz", None, "xyz"),
        ("xyz123", None, "xyz123"),
        ("123xyz", None, "123xyz"),
        ("123.0", None, "123.0"),
        ("+123", L(123), "123"),
        ("-123", L(-123), "-123"),
        (" +123 ", L(123), "123"),
        (" -123 ", L(-123), "-123"),
        ("+123", L(123), "123", dict(signed=False)),
        ("-123", None, "-123", dict(signed=False)),
        (None, None, "", {}, True),
    ):
        validate_element_set(Long, *spec)


def test_float():
    for spec in (
        ("123", 123.0, "123.000000"),
        (" 123 ", 123.0, "123.000000"),
        ("xyz", None, "xyz"),
        ("xyz123", None, "xyz123"),
        ("123xyz", None, "123xyz"),
        ("123.0", 123.0, "123.000000"),
        ("+123", 123.0, "123.000000"),
        ("-123", -123.0, "-123.000000"),
        (" +123 ", 123.0, "123.000000"),
        (" -123 ", -123.0, "-123.000000"),
        ("+123", 123.0, "123.000000", dict(signed=False)),
        ("-123", None, "-123", dict(signed=False)),
        (None, None, "", {}, True),
    ):
        validate_element_set(Float, *spec)

    class TwoDigitFloat(Float):
        format = "%0.2f"

    for spec in (
        ("123", 123.0, "123.00"),
        (" 123 ", 123.0, "123.00"),
        ("xyz", None, "xyz"),
        ("xyz123", None, "xyz123"),
        ("123xyz", None, "123xyz"),
        ("123.0", 123.0, "123.00"),
        ("123.00", 123.0, "123.00"),
        ("123.005", 123.005, "123.00"),
        (None, None, "", {}, True),
    ):
        validate_element_set(TwoDigitFloat, *spec)


def test_decimal():
    d = decimal.Decimal
    for spec in (
        ("123", d("123"), "123.000000"),
        (" 123 ", d("123"), "123.000000"),
        ("xyz", None, "xyz"),
        ("xyz123", None, "xyz123"),
        ("123xyz", None, "123xyz"),
        ("123.0", d("123.0"), "123.000000"),
        ("+123", d("123"), "123.000000"),
        ("-123", d("-123"), "-123.000000"),
        (" +123 ", d("123"), "123.000000"),
        (" -123 ", d("-123"), "-123.000000"),
        (123, d("123"), "123.000000"),
        (-123, d("-123"), "-123.000000"),
        (d(123), d("123"), "123.000000"),
        (d(-123), d("-123"), "-123.000000"),
        ("+123", d("123"), "123.000000", dict(signed=False)),
        ("-123", None, "-123", dict(signed=False)),
        (None, None, "", {}, True),
    ):
        validate_element_set(Decimal, *spec)

    TwoDigitDecimal = Decimal.using(format="%0.2f")

    for spec in (
        ("123", d("123.0"), "123.00"),
        (" 123 ", d("123.0"), "123.00"),
        ("12.34", d("12.34"), "12.34"),
        ("12.3456", d("12.3456"), "12.35"),
    ):
        validate_element_set(TwoDigitDecimal, *spec)


def test_boolean():
    for ok in Boolean.true_synonyms:
        validate_element_set(Boolean, ok, True, "1")
        validate_element_set(Boolean, ok, True, "baz", dict(true="baz"))

    for not_ok in Boolean.false_synonyms:
        validate_element_set(Boolean, not_ok, False, "")
        validate_element_set(Boolean, not_ok, False, "quux", dict(false="quux"))

    for bogus in "abc", "1.0", "0.0", "None":
        validate_element_set(Boolean, bogus, None, bogus)

    for coercable in {}, 0:
        validate_element_set(Boolean, coercable, False, "")


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
        ("2009-10-10", t(2009, 10, 10), "2009-10-10"),
        ("2010-08-02", t(2010, 8, 2), "2010-08-02"),
        (" 2010-08-02 ", t(2010, 8, 2), "2010-08-02"),
        (" 2010-08-02 ", None, " 2010-08-02 ", dict(strip=False)),
        ("2011-8-2", None, "2011-8-2"),
        ("blagga", None, "blagga"),
        (None, None, "", {}, True),
    ):
        validate_element_set(Date, *spec)


def test_time():
    t = datetime.time
    for spec in (
        ("08:09:10", t(8, 9, 10), "08:09:10"),
        ("23:24:25", t(23, 24, 25), "23:24:25"),
        ("24:25:26", None, "24:25:26"),
        ("bogus", None, "bogus"),
        (None, None, "", {}, True),
    ):
        validate_element_set(Time, *spec)


def test_datetime():
    t = datetime.datetime
    for spec in (
        ("2009-10-10 08:09:10", t(2009, 10, 10, 8, 9, 10), "2009-10-10 08:09:10"),
        ("2010-08-02 25:26:27", None, "2010-08-02 25:26:27"),
        ("2010-13-22 09:09:09", None, "2010-13-22 09:09:09"),
        (None, None, "", {}, True),
    ):
        validate_element_set(DateTime, *spec)

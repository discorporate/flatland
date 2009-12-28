from flatland import (
    Constrained,
    Enum,
    Integer,
    )

from tests._util import eq_, assert_raises


def test_constrained_no_default_validity():
    el = Constrained(u'anything')
    assert el.value is None
    assert el.u == u'anything'


def test_constrained_instance_override():

    def make_checker(*ok_values):

        def is_valid(element, value):
            assert isinstance(element, Constrained)
            return value in ok_values
        return is_valid

    el = Constrained(valid_value=make_checker(u'a'))
    assert el.set(u'a')
    assert el.value == u'a'
    assert el.u == u'a'

    assert not el.set(u'b')
    assert el.value is None
    assert el.u == u'b'

    el = Constrained(child_type=Integer, valid_value=make_checker(1, 2))
    assert el.set(u'1')
    assert el.value == 1
    assert el.u == u'1'

    assert el.set(u'2')
    assert el.value == 2
    assert el.u == u'2'

    for invalid in u'3', u'x':
        assert not el.set(invalid)
        assert el.value == None
        assert el.u == invalid


def test_constrained_instance_contrived():
    # check that fringe types that adapt as None can used in bounds

    class CustomInteger(Integer):

        def adapt(self, value):
            try:
                return Integer.adapt(self, value)
            except:
                return None

    el = Constrained(child_type=CustomInteger,
                     valid_value=lambda e, v: v in (1, None))
    assert el.set(u'1')

    for out_of_bounds in u'2', u'3':
        assert not el.set(out_of_bounds)

    for invalid in u'x', u'':
        assert el.set(invalid)
        assert el.value is None
        assert el.u == u''


def test_default_enum():
    good_values = (u'a', u'b', u'c')
    for good_val in good_values:
        for schema in (Enum.using(valid_values=good_values),
                       Enum.valued(*good_values)):
            el = schema()
            assert el.set(good_val)
            assert el.value == good_val
            assert el.u == good_val
            assert el.validate()
            assert not el.errors

    schema = Enum.valued(*good_values)
    el = schema()
    assert not el.set(u'd')
    assert el.value is None
    assert el.u == u'd'
    # present but not converted
    assert el.validate()

    el = schema()
    assert not el.set(None)
    assert el.value is None
    assert el.u == u''
    # not present
    assert not el.validate()


def test_typed_enum():
    good_values = range(1, 4)
    schema = Enum.using(valid_values=good_values, child_type=Integer)

    for good_val in good_values:
        el = schema()
        assert el.set(unicode(str(good_val), 'ascii'))
        assert el.value == good_val
        assert el.u == unicode(str(good_val), 'ascii')
        assert not el.errors

    el = schema()
    assert not el.set(u'x')
    assert el.value is None
    assert el.u == u'x'

    el = schema()
    assert not el.set(u'5')
    assert el.value is None
    assert el.u == u'5'

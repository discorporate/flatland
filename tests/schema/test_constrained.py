from flatland import (
    Constrained,
    Enum,
    Integer,
    )
from flatland._compat import text_transform



def test_constrained_no_default_validity():
    el = Constrained('anything')
    assert el.value is None
    assert el.u == 'anything'


def test_constrained_instance_override():

    def make_checker(*ok_values):

        def is_valid(element, value):
            assert isinstance(element, Constrained)
            return value in ok_values
        return is_valid

    el = Constrained(valid_value=make_checker('a'))
    assert el.set('a')
    assert el.value == 'a'
    assert el.u == 'a'

    assert not el.set('b')
    assert el.value is None
    assert el.u == 'b'

    el = Constrained(child_type=Integer, valid_value=make_checker(1, 2))
    assert el.set('1')
    assert el.value == 1
    assert el.u == '1'

    assert el.set('2')
    assert el.value == 2
    assert el.u == '2'

    for invalid in '3', 'x':
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
    assert el.set('1')

    for out_of_bounds in '2', '3':
        assert not el.set(out_of_bounds)

    for invalid in 'x', '':
        assert el.set(invalid)
        assert el.value is None
        assert el.u == ''


def test_default_enum():
    good_values = ('a', 'b', 'c')
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
    assert not el.set('d')
    assert el.value is None
    assert el.u == 'd'
    # present but not converted
    assert el.validate()

    el = schema()
    assert not el.set(None)
    assert el.value is None
    assert el.u == ''
    # not present
    assert not el.validate()


def test_typed_enum():
    good_values = range(1, 4)
    schema = Enum.using(valid_values=good_values, child_type=Integer)

    for good_val in good_values:
        el = schema()
        assert el.set(text_transform(good_val))
        assert el.value == good_val
        assert el.u == text_transform(good_val)
        assert not el.errors

    el = schema()
    assert not el.set('x')
    assert el.value is None
    assert el.u == 'x'

    el = schema()
    assert not el.set('5')
    assert el.value is None
    assert el.u == '5'

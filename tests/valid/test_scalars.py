from datetime import date, timedelta
from flatland import String, Integer, Date, Dict, List
from flatland.valid import scalars
from tests._util import eq_


def form(value):
    schema = Dict('test',
                  String('x'),
                  String('y'),
                  String('z'),
                  Dict('sub', String('xx')))
    return schema.create_element(value=value)

def scalar(value):
    return String('test').create_element(value=value)

def integer_scalar(value):
    return Integer('test').create_element(value=value)

def date_scalar(value):
    return Date('test').create_element(value=value)

def test_is_true():
    i = integer_scalar(1)
    z = integer_scalar(0)
    v = scalars.IsTrue()
    assert v.validate(i, None)
    assert not v.validate(z, None)

def test_is_false():
    i = integer_scalar(1)
    z = integer_scalar(0)
    v = scalars.IsFalse()
    assert not v.validate(i, None)
    assert v.validate(z, None)

def test_value_in():
    v = scalars.ValueIn(('a', 'b', 'c'))

    for good_val in ('a', 'b', 'c'):
        s = scalar(good_val)
        assert v.validate(s, None)

    for bad_val in (None, 'x', -1):
        s = scalar(bad_val)
        assert not v.validate(s, None)

def test_value_less_than():
    i = integer_scalar(1)
    V = scalars.ValueLessThan
    assert V(2).validate(i, None)
    assert not V(1).validate(i, None)
    assert i.errors == ['test must be less than 1.']

    d = date_scalar(date.today())
    assert V(date.today() + timedelta(days=2)).validate(d, None)
    two_days_ago = date.today() - timedelta(days=2)
    assert not V(two_days_ago).validate(d, None)
    assert d.errors == ['test must be less than %s.' % two_days_ago]

def test_value_at_most():
    i = integer_scalar(1)
    V = scalars.ValueAtMost
    assert V(2).validate(i, None)
    assert V(1).validate(i, None)
    assert not V(0).validate(i, None)
    assert i.errors == ['test must be less than or equal to 0.']

def test_value_greater_than():
    i = integer_scalar(1)
    V = scalars.ValueGreaterThan
    assert V(0).validate(i, None)
    assert not V(1).validate(i, None)
    assert i.errors == ['test must be greater than 1.']

def test_value_at_least():
    i = integer_scalar(1)
    V = scalars.ValueAtLeast
    assert V(0).validate(i, None)
    assert V(1).validate(i, None)
    assert not V(2).validate(i, None)
    assert i.errors == ['test must be greater than or equal to 2.']

def test_value_between():
    i = integer_scalar(1)
    V = scalars.ValueBetween
    assert V(0, 2).validate(i, None)
    assert V(0, 1, inclusive=True).validate(i, None)
    assert V(1, 2, inclusive=True).validate(i, None)
    assert not V(2, 3).validate(i, None)
    assert i.errors == ['test must be in the range 2 to 3.']
    i.errors = []
    assert not V(-1, 0).validate(i, None)
    assert i.errors == ['test must be in the range -1 to 0.']
    i.errors = []
    assert not V(1, 2, inclusive=False).validate(i, None)
    assert i.errors == ['test must be greater than 1 and less than 2.']
    i.errors = []
    assert not V(0, 1, inclusive=False).validate(i, None)
    assert i.errors == ['test must be greater than 0 and less than 1.']

def test_map_equal():
    v = scalars.MapEqual('x', 'y',
                         transform=lambda el: el.value.upper(),
                         unequal='%(labels)s/%(last_label)s')
    el = form(dict(x='a', y='A'))
    assert v.validate(el, None)

    el = form(dict(x='a', y='B'))
    assert not v.validate(el, None)
    eq_(el.errors, ['x/y'])

def test_values_equal_two():
    v = scalars.ValuesEqual('x', 'y')
    el = form(dict(x='a', y='a', z='a'))
    assert v.validate(el, None)

    el = form(dict(x='a', y='b', z='c'))
    assert not v.validate(el, None)
    eq_(el.errors, ['x and y do not match.'])

    el = form(dict(x='a'))
    assert not v.validate(el, None)
    eq_(el.errors, ['x and y do not match.'])

def test_values_equal_three():
    v = scalars.ValuesEqual('x', 'y', 'z')
    el = form(dict(x='a', y='a', z='a'))
    assert v.validate(el, None)

    el = form(dict(x='a', y='b', z='c'))
    assert not v.validate(el, None)
    eq_(el.errors, ['x, y and z do not match.'])

    el = form(dict(x='a'))
    assert not v.validate(el, None)
    eq_(el.errors, ['x, y and z do not match.'])

def test_values_equal_resolution():
    v = scalars.ValuesEqual('x', '.sub.xx')
    el = form(dict(x='a', sub=dict(xx='a')))
    assert v.validate(el, None)

    v = scalars.ValuesEqual('.x', 'xx')
    el = form(dict(x='a', sub=dict(xx='a')))
    assert v.validate(el['sub'], None)

    # unhashable
    v = scalars.ValuesEqual('a', 'b')
    schema = Dict('test',
                  List('a', String('x')),
                  List('b', String('x')))
    el = schema.create_element(value=dict(a=['a', 'b'], b=['a', 'b']))
    assert v.validate(el, None)

    el = schema.create_element(value=dict(a=['a', 'b'], b=['x', 'y']))
    assert not v.validate(el, None)

def test_unis_equal():
    schema = Dict('test', String('s'), Integer('i'))
    el = schema.create_element(value=dict(s='abc', i='abc'))

    v = scalars.UnisEqual('s', 'i')
    assert v.validate(el, None)

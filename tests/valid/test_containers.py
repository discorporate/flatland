from flatland import String, Integer, Dict, List, Array
from flatland.valid import containers
from tests._util import assert_raises


def valid_of_children(element):
    return [e.valid for e in element.children]


def test_no_duplicates_message():
    schema = List('test',
                  String('foo', validators=[containers.NotDuplicated()]))
    el = schema.create_element(value=[u'foo', u'foo'])
    assert not el.validate()
    assert el[1].errors == [u'foo may not be repeated within test.']


def test_no_duplicates_context():
    schema = String('foo', validators=[containers.NotDuplicated()])
    assert_raises(TypeError, schema.create_element().validate)


def test_no_duplicates_comparator():
    comparator = lambda a, b: True
    schema = List('test',
                  String('foo', validators=[
                      containers.NotDuplicated(comparator=comparator)]))
    el = schema.create_element(value=[u'a', u'b'])
    assert not el.validate()


def _test_no_duplicates(schema, a, b):
    label = schema.name
    el = schema.create_element(value=[a, b])
    assert el.validate()
    assert valid_of_children(el) == [True, True]

    el = schema.create_element(value=[a, b, a])
    assert not el.validate()
    assert valid_of_children(el) == [True, True, False]
    assert el[2].errors == [u'%s %s' % (label, 3)]

    el = schema.create_element(value=[a, b, a, b])
    assert not el.validate()
    assert valid_of_children(el) == [True, True, False, False]
    assert el[2].errors == [u'%s %s' % (label, 3)]
    assert el[3].errors == [u'%s %s' % (label, 4)]

    el = schema.create_element(value=[a, a, a, a])
    assert not el.validate()
    assert valid_of_children(el) == [True, False, False, False]
    assert el[1].errors == [u'%s %s' % (label, 2)]
    assert el[2].errors == [u'%s %s' % (label, 3)]
    assert el[3].errors == [u'%s %s' % (label, 4)]


def test_no_duplicates_list_scalar():
    nd = containers.NotDuplicated(failure=u'%(container_label)s %(position)s')
    schema = List('test', String('foo', validators=[nd]))
    _test_no_duplicates(schema, u'foo', u'bar')


def test_no_duplicates_array():
    nd = containers.NotDuplicated(failure=u'%(container_label)s %(position)s')
    schema = Array(String('foo', validators=[nd]))
    _test_no_duplicates(schema, u'foo', u'bar')


def test_no_duplicates_list_anon_dict():
    nd = containers.NotDuplicated(failure=u'%(container_label)s %(position)s')
    schema = List('test',
                  Dict(None, Integer('x'), Integer('y'), validators=[nd]))
    _test_no_duplicates(schema, {'x': 1, 'y': 2}, {'x': 3, 'y': 4})


def test_no_duplicates_list_dict():
    nd = containers.NotDuplicated(failure=u'%(container_label)s %(position)s')
    schema = List('test',
                  Dict('xyz', Integer('x'), Integer('y'), validators=[nd]))
    _test_no_duplicates(schema, {'x': 1, 'y': 2}, {'x': 3, 'y': 4})


def test_has_at_least_none():
    al = containers.HasAtLeast(minimum=0)
    schema = List('outer', String('inner'), validators=[al])

    el = schema.create_element(value=['a'])
    assert el.validate()

    el = schema.create_element()
    assert el.validate()


def test_has_at_least_one():
    al = containers.HasAtLeast()
    schema = List('outer', String('inner'), validators=[al])

    el = schema.create_element()
    assert not el.validate()
    assert el.errors == [u'outer must contain at least one inner']

    el = schema.create_element(value=['a'])
    assert el.validate()


def test_has_at_least_two():
    al = containers.HasAtLeast(minimum=2)
    schema = List('outer', String('inner'), validators=[al])

    el = schema.create_element(value=['a'])
    assert not el.validate()
    assert el.errors == [u'outer must contain at least 2 inners']

    el = schema.create_element(value=['a', 'b'])
    assert el.validate()


def test_has_at_most_none():
    am = containers.HasAtMost(maximum=0)
    schema = List('outer', String('inner'), validators=[am])

    el = schema.create_element(value=['a'])
    assert not el.validate()
    assert el.errors == [u'outer must contain at most 0 inners']

    el = schema.create_element()
    assert el.validate()


def test_has_at_most_one():
    am = containers.HasAtMost(maximum=1)
    schema = List('outer', String('inner'), validators=[am])

    el = schema.create_element()
    assert el.validate()

    el = schema.create_element(value=['a'])
    assert el.validate()

    el = schema.create_element(value=['a', 'b'])
    assert not el.validate()
    assert el.errors == [u'outer must contain at most one inner']


def test_has_at_most_two():
    am = containers.HasAtMost(maximum=2)
    schema = List('outer', String('inner'), validators=[am])

    el = schema.create_element()
    assert el.validate()

    el = schema.create_element(value=['a', 'b'])
    assert el.validate()

    el = schema.create_element(value=['a', 'b', 'c'])
    assert not el.validate()
    assert el.errors == [u'outer must contain at most 2 inners']


def test_has_between_none():
    bw = containers.HasBetween(minimum=0, maximum=0)
    schema = List('outer', String('inner'), validators=[bw])

    el = schema.create_element()
    assert el.validate()

    el = schema.create_element(value=['a'])
    assert not el.validate()
    assert el.errors == [u'outer must contain exactly 0 inners']


def test_has_between_one():
    bw = containers.HasBetween(minimum=1, maximum=1)
    schema = List('outer', String('inner'), validators=[bw])

    el = schema.create_element()
    assert not el.validate()
    assert el.errors == [u'outer must contain exactly one inner']

    el = schema.create_element(value=['a'])
    assert el.validate()

    el = schema.create_element(value=['a', 'b'])
    assert not el.validate()
    assert el.errors == [u'outer must contain exactly one inner']


def test_has_between_two():
    bw = containers.HasBetween(minimum=2, maximum=2)
    schema = List('outer', String('inner'), validators=[bw])

    el = schema.create_element()
    assert not el.validate()
    assert el.errors == [u'outer must contain exactly 2 inners']

    el = schema.create_element(value=['b'])
    assert not el.validate()
    assert el.errors == [u'outer must contain exactly 2 inners']

    el = schema.create_element(value=['a', 'b'])
    assert el.validate()


def test_has_between_none_and_one():
    bw = containers.HasBetween(minimum=0, maximum=1)
    schema = List('outer', String('inner'), validators=[bw])

    el = schema.create_element()
    assert el.validate()

    el = schema.create_element(value=['b'])
    assert el.validate()

    el = schema.create_element(value=['a', 'b'])
    assert not el.validate()
    assert el.errors == [u'outer must contain at least 0 and at most 1 inner']


def test_has_between_none_and_two():
    bw = containers.HasBetween(minimum=0, maximum=2)
    schema = List('outer', String('inner'), validators=[bw])

    el = schema.create_element()
    assert el.validate()

    el = schema.create_element(value=['a', 'b'])
    assert el.validate()

    el = schema.create_element(value=['a', 'b', 'c'])
    assert not el.validate()
    assert el.errors == [u'outer must contain at least 0 and at most 2 inners']


def test_has_between_one_and_two():
    bw = containers.HasBetween(minimum=1, maximum=2)
    schema = List('outer', String('inner'), validators=[bw])

    el = schema.create_element()
    assert not el.validate()
    assert el.errors == [u'outer must contain at least 1 and at most 2 inners']

    el = schema.create_element(value=['b'])
    assert el.validate()

    el = schema.create_element(value=['a', 'b'])
    assert el.validate()

    el = schema.create_element(value=['a', 'b', 'c'])
    assert not el.validate()
    assert el.errors == [u'outer must contain at least 1 and at most 2 inners']

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


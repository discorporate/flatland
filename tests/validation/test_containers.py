from flatland import (
    Array,
    Dict,
    Integer,
    List,
    String,
    )
from flatland.validation import (
    HasAtLeast,
    HasAtMost,
    HasBetween,
    NotDuplicated,
    )

from tests._util import assert_raises


def valid_of_children(element):
    return [e.valid for e in element.children]


def validated_string(*validators):
    return List.named('test').of(String.using(name=u'foo',
                                             validators=validators))

def test_no_duplicates_message():
    schema = validated_string(NotDuplicated())
    el = schema([u'foo', u'foo'])
    assert not el.validate()
    assert el[1].errors == [u'foo may not be repeated within test.']


def test_no_duplicates_context():
    el = String(validators=[NotDuplicated()])
    assert_raises(TypeError, el.validate)


def test_no_duplicates_comparator():
    comparator = lambda a, b: True
    schema = validated_string(NotDuplicated(comparator=comparator))
    el = schema([u'a', u'b'])
    assert not el.validate()


def _test_no_duplicates(schema, a, b):
    label = schema.label
    el = schema([a, b])
    assert el.validate()
    assert valid_of_children(el) == [True, True]

    el = schema([a, b, a])
    assert not el.validate()
    assert valid_of_children(el) == [True, True, False]
    assert el[2].errors == [u'%s %s' % (label, 3)]

    el = schema([a, b, a, b])
    assert not el.validate()
    assert valid_of_children(el) == [True, True, False, False]
    assert el[2].errors == [u'%s %s' % (label, 3)]
    assert el[3].errors == [u'%s %s' % (label, 4)]

    el = schema([a, a, a, a])
    assert not el.validate()
    assert valid_of_children(el) == [True, False, False, False]
    assert el[1].errors == [u'%s %s' % (label, 2)]
    assert el[2].errors == [u'%s %s' % (label, 3)]
    assert el[3].errors == [u'%s %s' % (label, 4)]


def test_no_duplicates_list_scalar():
    nd = NotDuplicated(failure=u'%(container_label)s %(position)s')
    schema = validated_string(nd)
    _test_no_duplicates(schema, u'foo', u'bar')


def test_no_duplicates_array():
    nd = NotDuplicated(failure=u'%(container_label)s %(position)s')
    schema = validated_string(nd)
    _test_no_duplicates(schema, u'foo', u'bar')


def test_no_duplicates_list_anon_dict():
    nd = NotDuplicated(failure=u'%(container_label)s %(position)s')
    schema = (List.named('test').
              of(Dict.of(Integer.named('x'),
                         Integer.named('y')).
                 using(validators=[nd])))
    _test_no_duplicates(schema, {'x': 1, 'y': 2}, {'x': 3, 'y': 4})


def test_no_duplicates_list_dict():
    nd = NotDuplicated(failure=u'%(container_label)s %(position)s')
    schema = (List.named('test').
              of(Dict.named('xyz').
                 of(Integer.named('x'),
                    Integer.named('y')).
                 using(validators=[nd])))
    _test_no_duplicates(schema, {'x': 1, 'y': 2}, {'x': 3, 'y': 4})


def validated_list(*validators):
    return List.named('outer').of(String.named('inner')).using(
        validators=validators)


def test_has_at_least_none():
    schema = validated_list(HasAtLeast(minimum=0))

    el = schema(['a'])
    assert el.validate()

    el = schema()
    assert el.validate()


def test_has_at_least_one():
    schema = validated_list(HasAtLeast())

    el = schema()
    assert not el.validate()
    assert el.errors == [u'outer must contain at least one inner']

    el = schema(['a'])
    assert el.validate()


def test_has_at_least_two():
    schema = validated_list(HasAtLeast(minimum=2))

    el = schema(['a'])
    assert not el.validate()
    assert el.errors == [u'outer must contain at least 2 inners']

    el = schema(['a', 'b'])
    assert el.validate()


def test_has_at_most_none():
    schema = validated_list(HasAtMost(maximum=0))

    el = schema(['a'])
    assert not el.validate()
    assert el.errors == [u'outer must contain at most 0 inners']

    el = schema()
    assert el.validate()


def test_has_at_most_one():
    schema = validated_list(HasAtMost(maximum=1))

    el = schema()
    assert el.validate()

    el = schema(['a'])
    assert el.validate()

    el = schema(['a', 'b'])
    assert not el.validate()
    assert el.errors == [u'outer must contain at most one inner']


def test_has_at_most_two():
    schema = validated_list(HasAtMost(maximum=2))

    el = schema()
    assert el.validate()

    el = schema(['a', 'b'])
    assert el.validate()

    el = schema(['a', 'b', 'c'])
    assert not el.validate()
    assert el.errors == [u'outer must contain at most 2 inners']


def test_has_between_none():
    schema = validated_list(HasBetween(minimum=0, maximum=0))

    el = schema()
    assert el.validate()

    el = schema(['a'])
    assert not el.validate()
    assert el.errors == [u'outer must contain exactly 0 inners']


def test_has_between_one():
    schema = validated_list(HasBetween(minimum=1, maximum=1))

    el = schema()
    assert not el.validate()
    assert el.errors == [u'outer must contain exactly one inner']

    el = schema(['a'])
    assert el.validate()

    el = schema(['a', 'b'])
    assert not el.validate()
    assert el.errors == [u'outer must contain exactly one inner']


def test_has_between_two():
    schema = validated_list(HasBetween(minimum=2, maximum=2))

    el = schema()
    assert not el.validate()
    assert el.errors == [u'outer must contain exactly 2 inners']

    el = schema(['b'])
    assert not el.validate()
    assert el.errors == [u'outer must contain exactly 2 inners']

    el = schema(['a', 'b'])
    assert el.validate()


def test_has_between_none_and_one():
    schema = validated_list(HasBetween(minimum=0, maximum=1))

    el = schema()
    assert el.validate()

    el = schema(['b'])
    assert el.validate()

    el = schema(['a', 'b'])
    assert not el.validate()
    assert el.errors == [u'outer must contain at least 0 and at most 1 inner']


def test_has_between_none_and_two():
    schema = validated_list(HasBetween(minimum=0, maximum=2))

    el = schema()
    assert el.validate()

    el = schema(['a', 'b'])
    assert el.validate()

    el = schema(['a', 'b', 'c'])
    assert not el.validate()
    assert el.errors == [u'outer must contain at least 0 and at most 2 inners']


def test_has_between_one_and_two():
    schema = validated_list(HasBetween(minimum=1, maximum=2))

    el = schema()
    assert not el.validate()
    assert el.errors == [u'outer must contain at least 1 and at most 2 inners']

    el = schema(['b'])
    assert el.validate()

    el = schema(['a', 'b'])
    assert el.validate()

    el = schema(['a', 'b', 'c'])
    assert not el.validate()
    assert el.errors == [u'outer must contain at least 1 and at most 2 inners']

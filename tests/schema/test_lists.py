from flatland import (
    Integer,
    List,
    String,
    Unset,
    element_set,
)
from flatland._compat import xrange, text_type
from flatland.schema.base import Unspecified




def test_set_flat_linear():
    pairs = [('l_0_i', 1), ('l_1_i', 2), ('l_2_i', 3)]

    schema = List.named('l').of(Integer.named('i'))
    el = schema.from_flat(pairs)

    assert len(el) == len(pairs)
    assert el.value == list(pair[1] for pair in pairs)


def test_set_flat_miss():
    pairs = [('l_galump', '3'), ('l_snorgle', '4')]

    schema = List.named('l').of(Integer.named('i'))
    el = schema.from_flat(pairs)

    assert len(el) == 0
    assert el.value == []


def test_set_flat_scalar():
    pairs = [('l', '1')]

    schema = List.named('l').of(Integer.named('i'))
    el = schema()
    canary = []
    def setter(self, value):
        canary.append(value)
        return type(el).set(self, value)
    el.set = setter.__get__(el, type(el))

    el.set_flat(pairs)
    assert len(el) == 0
    assert el.value == []
    assert canary == []


def test_set_flat_pruned():
    # pruned won't insert empty elements for a skipped index or empty rhs
    pairs = [('l_0_i', '0'), ('l_2_i', ''), ('l_3_i', '3')]

    schema = List.named('l').of(Integer.named('i'))
    el = schema.from_flat(pairs)

    assert len(el) == 2
    assert el.value == [0, 3]

    schema2 = schema.using(maximum_set_flat_members=1)
    el = schema2.from_flat(pairs)

    assert len(el) == 1
    assert el.value == [0]


def test_set_flat_unpruned():
    pairs = [('l_0_i', '0'), ('l_2_i', ''), ('l_3_i', '3')]

    schema = List.named('l').of(Integer.named('i')).using(prune_empty=False)
    el = schema.from_flat(pairs)

    assert len(el) == 4
    assert el.value == [0, None, None, 3]

    schema2 = schema.using(maximum_set_flat_members=2)
    el = schema2.from_flat(pairs)

    assert len(el) == 2
    assert el.value == [0, None]


def _assert_set_flat(schema, pairs, bogus=[]):
    el = schema.from_flat(pairs + bogus)
    assert len(el) == len(pairs)
    assert el.value == list(pair[1] for pair in pairs)
    assert el.flatten() == pairs


def test_set_flat_unnamed_child():
    schema = List.named('s').of(String)
    pairs = [('s_0', 'abc'), ('s_1', 'def')]
    bogus = [('s', 'xxx')]

    _assert_set_flat(schema, pairs, bogus)


def test_set_flat_anon_list_named_child():
    schema = List.of(String.named('s'))
    pairs = [('0_s', 'abc'), ('1_s', 'def')]
    bogus = [('s', 'xxx'), ('0', 'yyy')]

    _assert_set_flat(schema, pairs, bogus)


def test_set_flat_fully_anonymous():
    schema = List.of(String)
    pairs = [('0', 'abc'), ('1', 'def')]
    bogus = [('x', 'xxx')]

    _assert_set_flat(schema, pairs, bogus)


def test_set_flat_anonymous_dict():
    pairs = (('l_0_x', 'x0'), ('l_0_y', 'y0'),
             ('l_1_x', 'x1'), ('l_1_y', 'y1'),
             ('l_2_x', 'x2'), )

    schema = List.named('l').of(String.named('x'), String.named('y'))
    el = schema.from_flat(pairs)

    assert len(el) == 3
    assert el[0].value == {k[-1]: v for k, v in pairs[0:2]}
    assert el[1].value == {k[-1]: v for k, v in pairs[2:4]}
    assert el[2].value == {'x': 'x2', 'y': None}


def test_set_flat_doubly_anonymous_dict():
    pairs = (('0_x', 'x0'), ('0_y', 'y0'),
             ('1_x', 'x1'), ('1_y', 'y1'),
             ('2_x', 'x2'), )

    schema = List.of(String.named('x'), String.named('y'))
    el = schema.from_flat(pairs)

    assert len(el) == 3
    assert el[0].value == {k[-1]: v for k, v in pairs[0:2]}
    assert el[1].value == {k[-1]: v for k, v in pairs[2:4]}
    assert el[2].value == {'x': 'x2', 'y': None}


def test_set_default_int():

    def factory(count, **kw):
        return List.named('l').using(default=count, **kw).of(
            String.named('s').using(default='val'))

    schema = factory(3)
    el = schema()
    assert len(el) == 0
    assert el.value == []

    el = schema()
    el.set_default()
    assert len(el) == 3
    assert el.value == ['val'] * 3

    el.append(None)
    assert len(el) == 4
    assert el[-1].value == None
    el[-1].set_default()
    assert el[-1].value == 'val'

    el = schema(['a', 'b'])
    assert len(el) == 2
    assert el.value == ['a', 'b']
    el.set_default()
    assert len(el) == 3
    assert el.value == ['val'] * 3

    schema0 = factory(0)

    el = schema0()
    el.set_default()
    assert len(el) == 0
    assert el.value == []

    def calculated_default(element):
        assert isinstance(element, List)
        return 2

    schemaf = List.named('l').using(default_factory=calculated_default).of(
        String.named('s').using(default='val'))

    el = schemaf()
    el.set_default()
    assert len(el) == 2
    assert el.value == ['val'] * 2


def test_set_default_value():

    def factory(default, **kw):
        return List.using(default=default, **kw).of(
            String.using(default='val'))

    schema = factory(['a', 'b'])
    el = schema()
    assert len(el) == 0
    assert el.value == []

    el = schema()
    el.set_default()
    assert len(el) == 2
    assert el.value == ['a', 'b']

    el = schema(['c', 'd'])
    assert el.value == ['c', 'd']
    el.set_default()
    assert el.value == ['a', 'b']

    schema0 = factory([])
    el = schema0()
    el.set_default()
    assert len(el) == 0
    assert el.value == []


def test_set_default_none():

    def factory(default, **kw):
        return List.using(default=default, **kw).of(
            String.using(default='val'))

    for default in None, Unspecified:
        schema = factory(default)
        el = schema()
        assert el.value == []

        el = schema()
        el.set_default()
        assert el.value == []

    # TODO: exercising this here (set_default of None doesn't reset
    # the value), but unsure if this is the correct behavior
    schema = factory(None)
    el = schema(['a', 'b'])
    assert el.value == ['a', 'b']
    el.set_default()
    assert el.value == ['a', 'b']


def test_set():
    schema = List.of(Integer)

    el = schema()
    assert list(el) == []

    el = schema()
    assert not el.set(1)
    assert el.value == []

    el = schema()
    assert not el.set(None)
    assert el.value == []

    el = schema()
    assert el.set(range(3))
    assert el.value == [0, 1, 2]

    el = schema()
    assert el.set(xrange(3))
    assert el.value == [0, 1, 2]

    el = schema([0, 1, 2])
    assert el.value == [0, 1, 2]

    el = schema()
    el.extend([1, 2, 3])
    assert el.value == [1, 2, 3]
    el.set([4, 5, 6])
    assert el.value == [4, 5, 6]
    assert el.set([])
    assert el.value == []


def test_element_set():
    data = []
    sentinel = lambda sender, adapted: data.append((sender, adapted))

    schema = List.of(Integer)
    schema([0])

    with element_set.connected_to(sentinel):
        schema([1])
        schema(['bogus'])

    assert len(data) == 4  # Integer, List, Integer, List
    assert data[1][0].value == [1]
    assert data[1][1] is True

    assert data[2][0].raw == 'bogus'
    assert data[2][1] is False

    assert data[3][1] is False


def test_raw():
    schema = List.of(Integer)
    el = schema()
    assert el.raw is Unset

    el = schema('foo')
    assert el.raw == 'foo'

    el = schema([1, 2, 3])
    assert el.raw == [1, 2, 3]

    el = schema((1, 2, 3))
    assert el.raw == (1, 2, 3)

    el = schema({'x': 'bar'})
    assert el.raw == {'x': 'bar'}


def test_access():
    pairs = (('l_0_i', '10'), ('l_1_i', '11'), ('l_2_i', '12'),)

    schema = List.named('l').of(Integer.named('i'))
    el = schema.from_flat(pairs)

    elements = list(Integer.named('i')(val)
                    for val in ('10', '11', '12'))

    assert len(el) == 3
    assert el[0] == elements[0]
    assert el[1] == elements[1]
    assert el[2] == elements[2]

    assert el[0].value == 10

    assert el[:0] == elements[:0]
    assert el[:1] == elements[:1]
    assert el[0:5] == elements[0:5]
    assert el[-2:-1] == elements[-2:-1]

    assert el[0] in el
    assert elements[0] in el
    assert '10' in el
    assert 10 in el

    assert el.count(elements[0]) == 1
    assert el.count('10') == 1
    assert el.count(10) == 1

    assert el.index(elements[0]) == 0
    assert el.index('10') == 0
    assert el.index(10) == 0


def test_mutation():
    schema = List.named('l').of(Integer.named('i'))
    el = schema()

    new_element = Integer.named('i')

    def order_ok():
        slot_names = list(_.name for _ in el._slots)
        for idx, name in enumerate(slot_names):
            assert name == text_type(str(idx))

    assert not el
    order_ok()

    # FIXME:? seems to want parsable data, not elements
    el.append(new_element('0'))
    assert el.value == [0]
    order_ok()

    el.append('123')
    assert el.value == [0, 123]
    order_ok()

    el.extend(['4', '5'])
    assert el.value == [0, 123, 4, 5]
    order_ok()

    el[0] = '3'
    assert el.value == [3, 123, 4, 5]
    order_ok()

    el.insert(0, '2')
    assert el.value == [2, 3, 123, 4, 5]
    order_ok()

    v = el.pop()
    assert v.value == 5
    assert not v.parent
    order_ok()

    v = el.pop(0)
    assert v.value == 2
    assert el.value == [3, 123, 4]
    order_ok()

    el.remove('3')
    assert el.value == [123, 4]
    order_ok()

    del el[:]
    assert el.value == []
    order_ok()


def test_mutate_slices():
    schema = List.named('l').of(Integer.named('i'))
    el = schema()

    canary = []

    el.extend(['3', '4'])
    canary.extend([3, 4])

    el[0:1] = ['1', '2', '3']
    canary[0:1] = [1, 2, 3]
    assert el.value == [1, 2, 3, 4]
    assert canary == [1, 2, 3, 4]

    del el[2:]
    del canary[2:]
    assert el.value == [1, 2]
    assert canary == [1, 2]


def test_reverse():
    schema = List.named('l').of(Integer.named('i'))
    el = schema([2, 1])
    assert el.flatten() == [('l_0_i', '2'), ('l_1_i', '1')]

    el.reverse()
    assert el.value == [1, 2]
    assert el.flatten() == [('l_0_i', '1'), ('l_1_i', '2')]


def test_sort():
    schema = List.named('l').of(Integer.named('i'))
    el = schema([2, 1])

    el.sort(key=lambda el: el.value)
    assert el.value == [1, 2]
    assert el.flatten() == [('l_0_i', '1'), ('l_1_i', '2')]

    el.sort(key=lambda el: el.value, reverse=True)
    assert el.value == [2, 1]
    assert el.flatten() == [('l_0_i', '2'), ('l_1_i', '1')]


def test_slots():
    schema = List.named('l').of(Integer.named('i'))
    el = schema([1, 2])

    assert len(list(el._slots)) == 2
    for slot in el._slots:
        # don't really care what it says, just no crashy.
        assert repr(slot)

    assert [slot.value for slot in el._slots] == [1, 2]


def test_u():
    schema = List.of(String)
    el = schema(['x', 'x'])
    assert el.u == "[u'x', u'x']"


def test_value():
    schema = List.of(String)
    el = schema(['x', 'x'])
    assert el.value == ['x', 'x']

from flatland import (
    Integer,
    List,
    String,
)

from tests._util import eq_, assert_raises


def test_set_flat_linear():
    pairs = [('l_0_i', 1), ('l_1_i', 2), ('l_2_i', 3)]

    schema = List.named('l').of(Integer.named('i'))
    el = schema.from_flat(pairs)

    eq_(len(el), len(pairs))
    eq_(el.value, list(pair[1] for pair in pairs))


def test_set_flat_miss():
    pairs = [(u'l_galump', u'3'), (u'l_snorgle', u'4')]

    schema = List.named('l').of(Integer.named('i'))
    el = schema.from_flat(pairs)

    eq_(len(el), 0)
    eq_(el.value, [])


def test_set_flat_lossy():
    # lossy won't insert empty elements for a skipped index
    pairs = [('l_0_i', 1), ('l_2_i', 3)]

    schema = List.named('l').of(Integer.named('i'))
    el = schema.from_flat(pairs)

    eq_(len(el), len(pairs))
    eq_(el.value, list(pair[1] for pair in pairs))


def test_set_flat_linear_dict():
    pairs = ((u'l_0_x', u'x0'), (u'l_0_y', u'y0'),
             (u'l_1_x', u'x1'), (u'l_1_y', u'y1'),
             (u'l_2_x', u'x2'), )

    schema = List.named('l').of(String.named('x'), String.named('y'))
    el = schema.from_flat(pairs)

    eq_(len(el), 3)
    eq_(el[0].value, dict((k[-1], v) for k, v in pairs[0:2]))
    eq_(el[1].value, dict((k[-1], v) for k, v in pairs[2:4]))
    eq_(el[2].value, {u'x': u'x2', u'y': None})


def test_set_default():

    def factory(count, **kw):
        return List.named('l').using(default=count, **kw).of(
            String.named('s').using(default=u'val'))

    schema = factory(3)
    el = schema()
    eq_(len(el), 0)
    eq_(el.value, [])

    el = schema()
    el.set_default()
    eq_(len(el), 3)
    eq_(el.value, [u'val'] * 3)

    el.append(None)
    eq_(len(el), 4)
    eq_(el[-1].value, None)
    el[-1].set_default()
    eq_(el[-1].value, u'val')

    el = schema([u'a', u'b'])
    eq_(len(el), 2)
    eq_(el.value, [u'a', u'b'])
    el.set_default()
    eq_(len(el), 3)
    eq_(el.value, [u'val'] * 3)

    schema0 = factory(0)

    el = schema0()
    el.set_default()
    eq_(len(el), 0)
    eq_(el.value, [])

    def calculated_default(element):
        assert isinstance(element, List)
        return 2

    schemaf = List.named('l').using(default_factory=calculated_default).of(
        String.named('s').using(default=u'val'))

    el = schemaf()
    el.set_default()
    eq_(len(el), 2)
    eq_(el.value, [u'val'] * 2)


def test_set():
    schema = List.of(Integer)

    el = schema()
    assert list(el) == []
    assert_raises(TypeError, el.set, 1)
    assert_raises(TypeError, el.set, None)

    el = schema()
    el.set(range(3))
    assert el.value == [0, 1, 2]

    el = schema()
    el.set(xrange(3))
    assert el.value == [0, 1, 2]

    el = schema([0, 1, 2])
    assert el.value == [0, 1, 2]

    el = schema()
    el.extend([1, 2, 3])
    assert el.value == [1, 2, 3]
    el.set([4, 5, 6])
    assert el.value == [4, 5, 6]
    el.set([])
    assert el.value == []


def test_access():
    pairs = ((u'l_0_i', u'10'), (u'l_1_i', u'11'), (u'l_2_i', u'12'),)

    schema = List.named('l').of(Integer.named('i'))
    el = schema.from_flat(pairs)

    elements = list(Integer.named('i')(val)
                    for val in (u'10', u'11', u'12'))

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
    assert u'10' in el
    assert 10 in el

    assert el.count(elements[0]) == 1
    assert el.count(u'10') == 1
    assert el.count(10) == 1

    assert el.index(elements[0]) == 0
    assert el.index(u'10') == 0
    assert el.index(10) == 0


def test_mutation():
    schema = List.named('l').of(Integer.named('i'))
    el = schema()

    new_element = Integer.named('i')

    def order_ok():
        slot_names = list(_.name for _ in el._slots)
        for idx, name in enumerate(slot_names):
            assert name == unicode(idx)

    assert not el
    order_ok()

    # FIXME:? seems to want parsable data, not elements
    el.append(new_element(u'0'))
    assert el.value == [0]
    order_ok()

    el.append(u'123')
    assert el.value == [0, 123]
    order_ok()

    el.extend([u'4', u'5'])
    assert el.value == [0, 123, 4, 5]
    order_ok()

    el[0] = u'3'
    assert el.value == [3, 123, 4, 5]
    order_ok()

    el.insert(0, u'2')
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

    el.remove(u'3')
    assert el.value == [123, 4]
    order_ok()

    del el[:]
    assert el.value == []
    order_ok()


def test_mutate_slices():
    schema = List.named('l').of(Integer.named('i'))
    el = schema()

    canary = []

    el.extend([u'3', u'4'])
    canary.extend([3, 4])

    el[0:1] = [u'1', u'2', u'3']
    canary[0:1] = [1, 2, 3]
    eq_(el.value, [1, 2, 3, 4])
    eq_(canary, [1, 2, 3, 4])

    del el[2:]
    del canary[2:]
    assert el.value == [1, 2]
    assert canary == [1, 2]


def test_unimplemented():
    schema = List.named('l').of(Integer.named('i'))
    el = schema([2, 1])

    assert_raises(TypeError, el.sort)
    assert_raises(TypeError, el.reverse)


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
    el = schema([u'x', u'x'])
    eq_(el.u, u"[u'x', u'x']")


def test_value():
    schema = List.of(String)
    el = schema([u'x', u'x'])
    eq_(el.value, [u'x', u'x'])

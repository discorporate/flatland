from flatland import schema
from tests._util import eq_, assert_raises


def test_list_linear_set_scalars():
    s = schema.List('l', schema.String('s'))
    el = s.create_element()

    pairs = list(('l_%s_s' % i, 'val%s' % i) for i in xrange(1, 10))
    el.set_flat(pairs)
    eq_(len(el), len(pairs))
    eq_(el.value, list(pair[1] for pair in pairs))


def test_list_miss_set_flat():
    s = schema.List('l', schema.String('s'))
    el = s.create_element()

    pairs = ((u'l_galump', u'foo'), (u'l_snorgle', u'bar'))
    el.set_flat(pairs)
    eq_(len(el), 0)
    eq_(el.value, [])


def test_list_lossy_set_scalars():
    s = schema.List('l', schema.String('s'))
    el = s.create_element()

    pairs = list(('l_%s_s' % i, 'val%s' % i) for i in xrange(1, 10, 2))
    el.set_flat(pairs)

    eq_(len(el), len(pairs))
    eq_(el.value, list(pair[1] for pair in pairs))

    # lossy won't insert empty elements
    eq_(el[1].value, pairs[1][1])


def test_list_linear_set_dict():
    s = schema.List('l', schema.String('x'), schema.String('y'))
    el = s.create_element()

    pairs = ((u'l_0_x', u'x0'), (u'l_0_y', u'y0'),
             (u'l_1_x', u'x1'), (u'l_1_y', u'y1'),
             (u'l_2_x', u'x2'), )
    el.set_flat(pairs)

    eq_(len(el), 3)
    eq_(el[0].value, dict((k[-1], v) for k, v in pairs[0:2]))
    eq_(el[1].value, dict((k[-1], v) for k, v in pairs[2:4]))
    eq_(el[2].value, {u'x': u'x2', u'y': None})


def test_list_set_default():
    def factory(count):
        return schema.List('l', schema.String('s', default=u'val'),
                           default=count)
    s = factory(3)

    el = s.create_element()
    eq_(len(el), 0)
    eq_(el.value, [])

    el = s.create_element()
    el.set_default()
    eq_(len(el), 3)
    eq_(el.value, [u'val'] * 3)

    el.append(None)
    eq_(len(el), 4)
    eq_(el[-1].value, None)
    el[-1].set_default()
    eq_(el[-1].value, u'val')

    el = s.create_element(value=[u'a', u'b'])
    eq_(len(el), 2)
    eq_(el.value, [u'a', u'b'])
    el.set_default()
    eq_(len(el), 3)
    eq_(el.value, [u'val'] * 3)

    s = factory(0)
    el = s.create_element()
    el.set_default()
    eq_(len(el), 0)
    eq_(el.value, [])

    def default_generator(element):
        assert isinstance(element, schema.containers.ListElement)
        return 2

    s = factory(default_generator)
    el = s.create_element()
    el.set_default()
    eq_(len(el), 2)
    eq_(el.value, [u'val'] * 2)


def test_list_set():
    def new_element(**kw):
        s = schema.List('l', schema.Integer('i'))
        return s.create_element(**kw)

    el = new_element()
    assert list(el) == []
    assert_raises(TypeError, el.set, 1)
    assert_raises(TypeError, el.set, None)

    el = new_element()
    el.set(range(3))
    assert el.value == [0, 1, 2]

    el = new_element()
    el.set(xrange(3))
    assert el.value == [0, 1, 2]

    el = new_element(value=[0, 1, 2])
    assert el.value == [0, 1, 2]

    el = new_element()
    el.extend([1, 2, 3])
    assert el.value == [1, 2, 3]
    el.set([4, 5, 6])
    assert el.value == [4, 5, 6]
    el.set([])
    assert el.value == []


def test_list_access():
    s = schema.List('l', schema.Integer('i'))
    el = s.create_element()

    pairs = ((u'l_0_i', u'10'), (u'l_1_i', u'11'), (u'l_2_i', u'12'),)
    el.set_flat(pairs)

    elements = list(schema.Integer('i').create_element(value=val)
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


def test_list_mutation():
    s = schema.List('l', schema.Integer('i'))
    el = s.create_element()

    new_element = lambda val: schema.Integer('i').create_element(value=val)

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


def test_list_mutate_slices():
    s = schema.List('l', schema.Integer('i'))
    el = s.create_element()
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


def test_list_unimplemented():
    s = schema.List('l', schema.Integer('i'))
    el = s.create_element()

    assert_raises(TypeError, el.sort)
    assert_raises(TypeError, el.reverse)


def test_list_slots():
    s = schema.List('l', schema.String('s'))
    n = s.create_element(value=[u'x'])
    for slot in n._slots:
        # don't really care what it says, just no crashy.
        assert repr(slot)
        assert slot.value == u'x'
        assert slot.value != u'y'


def test_list_u():
    s = schema.List('l', schema.String('s'))
    n = s.create_element()
    n[:] = [u'x', u'x']
    eq_(n.u, u"[u'x', u'x']")


def test_list_value():
    s = schema.List('l', schema.String('s'))
    n = s.create_element()
    n[:] = [u'x', u'x']
    eq_(n.value, [u'x', u'x'])

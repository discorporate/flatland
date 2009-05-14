from flatland import schema
from tests._util import eq_, assert_raises


def test_set_flat_pruned():
    sub = schema.String('s')
    pairs = list((u's', u'val%s' % i if i % 2 else u'')
                 for i in xrange(1, 10))
    wanted = list(pair[1] for pair in pairs if pair[1])

    for s in schema.Array(sub), schema.Array(sub, prune_empty=True):
        el = s.create_element()
        el.set_flat(pairs)

        eq_(len(el), len(wanted))
        eq_(el.value, wanted)


def test_set_flat_unpruned():
    pairs = list((u's', u'val%s' % i if i % 2 else u'')
                 for i in xrange(1, 10))

    s = schema.Array(schema.String('s'), prune_empty=False)
    el = s.create_element()
    el.set_flat(pairs)

    eq_(len(el), len(pairs))
    eq_(el.value, list(pair[1] for pair in pairs))


def test_set():
    s = schema.Array(schema.Integer('i'))
    el = s.create_element()
    assert not el

    assert_raises(TypeError, el.set, 1)

    el.set([1])
    assert el[0].u == u'1'
    assert el.value == [1]
    assert el[0].parent is el

    el.set([1, 2, 3])
    assert el[0].u == u'1'
    assert el[0].value == 1
    assert el.value == [1, 2, 3]


def test_set_default():
    s = schema.Array(schema.String('s'), default=[u'x', u'y'])
    el = s.create_element()

    eq_(el.value, [])
    el.set_default()
    eq_(el.value, [u'x', u'y'])

    el.append(u'z')
    eq_(el.value, [u'x', u'y', u'z'])
    el.set_default()
    eq_(el.value, [u'x', u'y'])

    s = schema.Array(schema.String('s', default='not triggered'),
                     default=[u'x'])
    el = s.create_element()
    el.set_default()
    eq_(el.value, [u'x'])

    s = schema.Array(schema.String('s', default=u'x'))
    el = s.create_element()
    el.set_default()
    eq_(el.value, [])


def test_array_mutation():
    s = schema.Array(schema.String('s'))
    n = s.create_element()
    assert not n

    n.set([u'b'])
    assert n[0].u == u'b'
    assert n.value == [u'b']

    n.append(u'x')
    assert n[1].u == u'x'
    assert n.value == [u'b', u'x']
    assert n[1].parent is n

    n[1] = u'a'
    assert n[1].u == u'a'
    assert n.value == [u'b', u'a']
    assert n[1].parent is n

    n.remove(u'b')
    assert n.value == [u'a']

    n.extend(u'bcdefg')

    eq_(n.value[0:4], [u'a', u'b', u'c', u'd'])
    assert n[2].parent is n

    del n[0]
    eq_(n.value[0:4], [u'b', u'c', u'd', u'e'])

    del n[0:4]
    eq_(n.value, [u'f', u'g'])

    n.pop()
    eq_(n.value, [u'f'])
    eq_(n[0].u, u'f')
    eq_(n.u, repr([u'f']))

    del n[:]
    eq_(list(n), [])
    eq_(n.value, [])
    eq_(n.u, u'[]')

    n[:] = u'abc'
    eq_(n.value, [u'a', u'b', u'c'])
    assert n[1].parent is n

    n.insert(1, u'z')
    eq_(n.value, [u'a', u'z', u'b', u'c'])
    assert n[1].parent is n

    def assign():
        n.u = u'z'
    assert_raises(AttributeError, assign)
    eq_(n.value, [u'a', u'z', u'b', u'c'])

    def assign2():
        n.value = u'abc'
    del n[:]
    assert_raises(AttributeError, assign2)
    eq_(n.value, [])


def test_el():
    s = schema.Array(schema.String('s'))
    n = s.create_element()
    n[:] = u'abc'
    eq_(list(n.value), [u'a', u'b', u'c'])

    eq_(n.el('0').value, u'a')
    eq_(n.el('2').value, u'c')
    assert_raises(KeyError, n.el, 'a')


def test_multivalue_set():
    s = schema.MultiValue(schema.Integer('s'))
    el = s.create_element()

    eq_(el.value, None)
    eq_(el.u, u'')
    eq_(list(el), [])
    eq_(len(el), 0)
    assert not el

    assert_raises(TypeError, el.set, 0)

    el.set([0])
    eq_(el.value, 0)
    eq_(el.u, u'0')
    assert len(el) == 1
    assert el

    el = s.create_element(value=[0, 1])
    eq_(el.value, 0)
    eq_(el.u, u'0')
    assert len(el) == 2
    assert el


def test_multivalue_mutation():
    s = schema.MultiValue(schema.Integer('s'))
    e = s.create_element()

    eq_(e.value, None)
    eq_(e.u, u'')
    eq_(list(e), [])
    eq_(len(e), 0)
    assert not e

    e.set([1, 2])
    eq_(e.value, 1)
    eq_(e.u, u'1')
    eq_(len(e), 2)
    assert e

    e.insert(0, 0)
    eq_(e.value, 0)
    eq_(e.u, u'0')
    eq_(len(e), 3)

    e[0].set(9)
    eq_(e.value, 9)
    eq_(e.u, u'9')
    eq_([el.value for el in e], [9, 1, 2])
    eq_(len(e), 3)

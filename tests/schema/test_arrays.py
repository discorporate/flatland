from flatland import (
    Array,
    Integer,
    MultiValue,
    String,
    )

from tests._util import eq_, assert_raises


def test_set_flat_pruned():
    sub = String.named('s')
    pairs = [(u's', u'val0'), (u's', ''), (u's', u'val1'), (u's', u'')]
    wanted = [u'val0', u'val1']

    for schema in Array.of(sub), Array.of(sub).using(prune_empty=True):
        el = schema.from_flat(pairs)

        eq_(len(el), len(wanted))
        eq_(el.value, wanted)


def test_set_flat_unpruned():
    pairs = [(u's', u'val0'), (u's', ''), (u's', u'val1'), (u's', u'')]

    schema = Array.of(String.named('s')).using(prune_empty=False)
    el = schema.from_flat(pairs)

    eq_(len(el), len(pairs))
    eq_(el.value, list(pair[1] for pair in pairs))


def test_set():
    schema = Array.of(Integer)
    el = schema()
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
    schema = Array.of(String).using(default=[u'x', u'y'])
    el = schema()

    eq_(el.value, [])
    el.set_default()
    eq_(el.value, [u'x', u'y'])

    el.append(u'z')
    eq_(el.value, [u'x', u'y', u'z'])
    el.set_default()
    eq_(el.value, [u'x', u'y'])

    defaulted_child = String.using(default='not triggered')
    schema = Array.of(defaulted_child).using(default=[u'x'])

    el = schema.from_defaults()
    eq_(el.value, [u'x'])

    schema = Array.of(String.using(default=u'x'))
    el = schema.from_defaults()
    eq_(el.value, [])


def test_mutation():
    schema = Array.of(String)
    el = schema()
    assert not el

    el.set([u'b'])
    assert el[0].u == u'b'
    assert el.value == [u'b']

    el.append(u'x')
    assert el[1].u == u'x'
    assert el.value == [u'b', u'x']
    assert el[1].parent is el

    el[1] = u'a'
    assert el[1].u == u'a'
    assert el.value == [u'b', u'a']
    assert el[1].parent is el

    el.remove(u'b')
    assert el.value == [u'a']

    el.extend(u'bcdefg')

    eq_(el.value[0:4], [u'a', u'b', u'c', u'd'])
    assert el[2].parent is el

    del el[0]
    eq_(el.value[0:4], [u'b', u'c', u'd', u'e'])

    del el[0:4]
    eq_(el.value, [u'f', u'g'])

    el.pop()
    eq_(el.value, [u'f'])
    eq_(el[0].u, u'f')
    eq_(el.u, repr([u'f']))

    del el[:]
    eq_(list(el), [])
    eq_(el.value, [])
    eq_(el.u, u'[]')

    el[:] = u'abc'
    eq_(el.value, [u'a', u'b', u'c'])
    assert el[1].parent is el

    el.insert(1, u'z')
    eq_(el.value, [u'a', u'z', u'b', u'c'])
    assert el[1].parent is el

    def assign():
        el.u = u'z'
    assert_raises(AttributeError, assign)
    eq_(el.value, [u'a', u'z', u'b', u'c'])

    def assign2():
        el.value = u'abc'
    del el[:]
    assert_raises(AttributeError, assign2)
    eq_(el.value, [])


def test_el():
    schema = Array.of(String.named('s'))
    element = schema(u'abc')
    eq_(list(element.value), [u'a', u'b', u'c'])

    eq_(element.el('0').value, u'a')
    eq_(element.el('2').value, u'c')
    assert_raises(KeyError, element.el, 'a')


def test_multivalue_set():
    schema = MultiValue.of(Integer)
    el = schema()

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

    el = schema([0, 1])
    eq_(el.value, 0)
    eq_(el.u, u'0')
    assert len(el) == 2
    assert el


def test_multivalue_mutation():
    schema = MultiValue.of(Integer)
    el = schema()

    eq_(el.value, None)
    eq_(el.u, u'')
    eq_(list(el), [])
    eq_(len(el), 0)
    assert not el

    el.set([1, 2])
    eq_(el.value, 1)
    eq_(el.u, u'1')
    eq_(len(el), 2)
    assert el

    el.insert(0, 0)
    eq_(el.value, 0)
    eq_(el.u, u'0')
    eq_(len(el), 3)

    el[0].set(9)
    eq_(el.value, 9)
    eq_(el.u, u'9')
    eq_([child.value for child in el], [9, 1, 2])
    eq_(len(el), 3)

from flatland import (
    Array,
    Dict,
    Integer,
    MultiValue,
    String,
    )

from tests._util import eq_, assert_raises


def test_set_flat_pruned():
    sub = String.named(u's')
    pairs = [(u's', u'val0'), (u's', ''), (u's', u'val1'), (u's', u'')]
    wanted = [u'val0', u'val1']

    for schema in Array.of(sub), Array.of(sub).using(prune_empty=True):
        el = schema.from_flat(pairs)

        eq_(len(el), len(wanted))
        eq_(el.value, wanted)


def _assert_array_set_flat(schema, pairs, bogus=[]):
    el = schema.from_flat(pairs + bogus)
    eq_(len(el), len(pairs))
    eq_(el.value, list(pair[1] for pair in pairs))
    eq_(el.flatten(), pairs)


def test_set_flat_unpruned():
    pairs = [(u's', u'val0'), (u's', ''), (u's', u'val1'), (u's', u'')]
    schema = Array.of(String).named(u's').using(prune_empty=False)

    _assert_array_set_flat(schema, pairs)


def test_set_flat_like_named():
    pairs = [(u's_s', u'abc'), (u's_s', u'def')]
    bogus = [(u's', u'xxx')]
    schema = Array.named(u's').of(String.named(u's'))

    _assert_array_set_flat(schema, pairs, bogus)


def test_set_flat_unnamed_child():
    pairs = [(u's', u'abc'), (u's', u'def')]
    bogus = [(u'', 'xxx')]
    schema = Array.named(u's').of(String)

    _assert_array_set_flat(schema, pairs, bogus)


def test_set_flat_anonymous_array():
    schema = Array.of(String.named(u's'))
    pairs = [(u's', u'abc'), (u's', u'def')]
    bogus = [(u'', 'xxx')]

    _assert_array_set_flat(schema, pairs, bogus)


def test_set_flat_fully_anonymous_array():
    schema = Array.of(String)
    pairs = [(u'', u'abc'), (u'', u'def')]

    _assert_array_set_flat(schema, pairs)


def test_set_flat_anonymous_dict():
    schema = Array.of(Dict.of(String.named('x')))
    pairs = [(u'x', u'abc'), (u'x', u'def')]
    assert_raises(AssertionError, schema.from_flat, pairs)


def test_set():
    schema = Array.of(Integer)
    el = schema()
    assert not el

    el = schema()
    assert not el.set(1)
    assert not el.value

    el = schema()
    assert el.set([])
    assert not el.value

    el = schema()
    assert el.set([1])
    assert el[0].u == u'1'
    assert el.value == [1]
    assert el[0].parent is el

    el = schema()
    assert el.set([1, 2, 3])
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
    eq_(el.u.encode('ascii'), repr([u'f']))

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
    schema = Array.of(String.named(u's'))
    element = schema(u'abc')
    eq_(list(element.value), [u'a', u'b', u'c'])

    eq_(element.el(u'0').value, u'a')
    eq_(element.el(u'2').value, u'c')
    assert_raises(KeyError, element.el, u'a')


def test_multivalue_set():
    schema = MultiValue.of(Integer)
    el = schema()

    eq_(el.value, None)
    eq_(el.u, u'')
    eq_(list(el), [])
    eq_(len(el), 0)
    assert not el

    assert not el.set(0)
    assert el.value is None

    assert el.set([])
    assert not el.value

    assert el.set([0])
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


def _assert_multivalue_set_flat(schema, pairs, bogus=[]):
    el = schema.from_flat(pairs + bogus)
    eq_(len(el), len(pairs))
    eq_(el.value, pairs[0][1])
    eq_(list(e.value for e in el), list(pair[1] for pair in pairs))
    eq_(el.flatten(), pairs)


def test_multivalue_set_flat_unpruned():
    pairs = [(u's', u'val0'), (u's', ''), (u's', u'val1'), (u's', u'')]
    schema = MultiValue.of(String).named(u's').using(prune_empty=False)

    _assert_multivalue_set_flat(schema, pairs)


def test_multivalue_set_flat_like_named():
    pairs = [(u's_s', u'abc'), (u's_s', u'def')]
    bogus = [(u's', u'xxx')]
    schema = MultiValue.named(u's').of(String.named(u's'))

    _assert_multivalue_set_flat(schema, pairs, bogus)


def test_multivalue_set_flat_unnamed_child():
    pairs = [(u's', u'abc'), (u's', u'def')]
    bogus = [(u'', 'xxx')]
    schema = MultiValue.named(u's').of(String)

    _assert_multivalue_set_flat(schema, pairs, bogus)


def test_multivalue_set_flat_anonymous_array():
    schema = MultiValue.of(String.named(u's'))
    pairs = [(u's', u'abc'), (u's', u'def')]
    bogus = [(u'', 'xxx')]

    _assert_multivalue_set_flat(schema, pairs, bogus)


def test_multivalue_set_flat_fully_anonymous_array():
    schema = MultiValue.of(String)
    pairs = [(u'', u'abc'), (u'', u'def')]

    _assert_multivalue_set_flat(schema, pairs)


def test_multivalue_roundtrip():
    schema = MultiValue.of(String.named(u's'))
    data = [u'abc', u'def']
    el = schema(data)
    eq_([e.value for e in el], data)

    flat = el.flatten()
    eq_(flat, [(u's', u'abc'), (u's', u'def')])
    restored = schema.from_flat(flat)
    eq_(restored.value, u'abc')
    eq_([e.value for e in restored], data)

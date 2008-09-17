from nose.tools import eq_, assert_raises, set_trace

from flatland import schema
from flatland.util import Unspecified

def test_sequence():
    assert_raises(TypeError, schema.container.Sequence, 's',
                  schema.String('a'))

    s = schema.container.Sequence('s')
    assert hasattr(s, 'spec')

def test_list_linear_set_scalars():
    s = schema.List('l', schema.String('s'))
    n = s.node()

    pairs = list(('l_%s_s' % i, 'val%s' % i) for i in xrange(1, 10))
    n.set_flat(pairs)
    eq_(len(n), len(pairs))
    eq_(n, list(pair[1] for pair in pairs))


def test_list_lossy_set_scalars():
    s = schema.List('l', schema.String('s'))
    n = s.node()

    pairs = list(('l_%s_s' % i, 'val%s' % i) for i in xrange(1, 10, 2))
    n.set_flat(pairs)

    eq_(len(n), len(pairs))
    eq_(n, list(pair[1] for pair in pairs))

    # lossy won't insert empty nodes
    eq_(n[1].value, pairs[1][1])

def test_list_linear_set_dict():
    s = schema.List('l', schema.String('x'), schema.String('y'))
    n = s.node()

    pairs = ((u'l_0_x', u'x0'), (u'l_0_y', u'y0'),
             (u'l_1_x', u'x1'), (u'l_1_y', u'y1'),
             (u'l_2_x', u'x2'), )
    n.set_flat(pairs)

    eq_(len(n), 3)
    eq_(n[0], dict((k[-1], v) for k, v in pairs[0:2]))
    eq_(n[1], dict((k[-1], v) for k, v in pairs[2:4]))
    eq_(n[2], {u'x': u'x2', u'y': None})

def test_list_default():
    def factory(count):
        s = schema.List('l', schema.String('s', default=u'val'), default=count)
        return s.node()

    n = factory(3)
    eq_(len(n), 3)
    eq_(n, [u'val'] * 3)

    n = factory(0)
    eq_(len(n), 0)
    eq_(n, [])

def test_list_set():
    def new_node(**kw):
        s = schema.List('l', schema.Integer('i'))
        return s.node(**kw)

    n = new_node()
    assert list(n) == []
    assert_raises(TypeError, n.set, 1)
    assert_raises(TypeError, n.set, None)

    n = new_node()
    n.set(range(3))
    assert list(n) == [0, 1, 2]

    n = new_node()
    n.set(xrange(3))
    assert list(n) == [0, 1, 2]

    n = new_node(value=[0, 1, 2])
    assert list(n) == [0, 1, 2]

    n = new_node()
    n.extend([1,2,3])
    assert list(n) == [1, 2, 3]
    n.set([4, 5, 6])
    assert list(n) == [4, 5, 6]
    n.set([])
    assert list(n) == []

def test_list_access():
    s = schema.List('l', schema.Integer('i'))
    n = s.node()

    pairs = ((u'l_0_i', u'10'), (u'l_1_i', u'11'), (u'l_2_i', u'12'),)
    n.set_flat(pairs)

    nodes = list(schema.Integer('i').node(value=val)
                 for val in (u'10', u'11', u'12'))

    assert len(n) == 3
    assert n[0] == nodes[0]
    assert n[1] == nodes[1]
    assert n[2] == nodes[2]

    assert n[:0] == nodes[:0]
    assert n[:1] == nodes[:1]
    assert n[0:5] == nodes[0:5]
    assert n[-2:-1] == nodes[-2:-1]

    assert n[0] in n
    assert nodes[0] in n
    assert u'10' in n
    assert 10 in n

    assert n.count(nodes[0]) == 1
    assert n.count(u'10') == 1
    assert n.count(10) == 1

    assert n.index(nodes[0]) == 0
    assert n.index(u'10') == 0
    assert n.index(10) == 0

def test_list_mutation():
    s = schema.List('l', schema.Integer('i'))
    n = s.node()

    new_node = lambda val: schema.Integer('i').node(value=val)

    def order_ok():
        slot_names = list(_.name for _ in n._slots)
        for idx, name in enumerate(slot_names):
            assert name == unicode(idx)

    assert not n
    order_ok()

    # FIXME:? seems to want parsable data, not nodes
    n.append(new_node(u'0'))
    assert n == [0]
    order_ok()

    n.append(u'123')
    assert n == [0, 123]
    order_ok()

    n.extend([u'4', u'5'])
    assert n == [0, 123, 4, 5]
    order_ok()

    n[0] = u'3'
    assert n == [3, 123, 4, 5]
    order_ok()

    n.insert(0, u'2')
    assert n == [2, 3, 123, 4, 5]
    order_ok()

    v = n.pop()
    assert v == 5
    assert v == u'5'
    order_ok()

    v = n.pop(0)
    assert v == 2
    assert n == [3, 123, 4]
    order_ok()

    n.remove(u'3')
    assert n == [123, 4]
    order_ok()

    del n[:]
    assert n == []
    order_ok()

def test_list_mutate_slices():
    s = schema.List('l', schema.Integer('i'))
    n = s.node()
    canary = []

    n.extend([u'3', u'4'])
    canary.extend([3, 4])

    n[0:1] = [u'1', u'2', u'3']
    canary[0:1] = [1, 2, 3]
    eq_(n, [1, 2, 3, 4])
    eq_(canary, [1, 2, 3, 4])

    del n[2:]
    del canary[2:]
    assert n == [1, 2]
    assert canary == [1, 2]

def test_list_unimplemented():
    s = schema.List('l', schema.Integer('i'))
    n = s.node()

    assert_raises(TypeError, n.sort)
    assert_raises(TypeError, n.reverse)


def test_array_pruned_set_scalars():
    s = schema.Array(schema.String('s'))
    n = s.node()

    pairs = list((u's', u'val%s' % i if i %2 else u'')
                 for i in xrange(1, 10))
    n.set_flat(pairs)

    actual_data = list(pair[1] for pair in pairs if pair[1])
    eq_(len(n), len(actual_data))
    eq_(list(n), actual_data)
    eq_(n, actual_data[-1])

def test_array_unpruned_set_scalars():
    s = schema.Array(schema.String('s'), prune_empty=False)
    n = s.node()

    pairs = list((u's', u'val%s' % i if i %2 else u'')
                 for i in xrange(1, 10))
    n.set_flat(pairs)

    eq_(len(n), len(pairs))
    eq_(list(n), list(pair[1] for pair in pairs))
    eq_(n, pairs[-1][1])

def test_array_mutation():
    s = schema.Array(schema.String('s'))
    new_node = s.node

    n = new_node()
    assert not n

    n.set(u'a')
    assert n
    assert n == u'a'

    n.set('b')
    assert n == u'b'
    assert list(n) == [u'a', u'b']

    n[1] = u'c'
    assert list(n) == [u'a', u'c']

    n[1] = new_node(value='b')
    assert list(n) == [u'a', u'b']

    n.remove(u'b')
    assert list(n) == [u'a']

    n.extend(u'bcdefg')

    eq_(n[0:4], [u'a', u'b', u'c', u'd'])

    del n[0]
    eq_(n[0:4], [u'b', u'c', u'd', u'e'])

    del n[0:4]
    eq_(list(n), [u'f', u'g'])

    n.pop()
    eq_(list(n), [u'f'])
    eq_(n, u'f')

    del n[:]
    eq_(list(n), [])
    eq_(n, u'')

    n[:] = u'abc'
    eq_(list(n), [u'a', u'b', u'c'])
    eq_(n, u'c')

def test_dict():
    assert_raises(TypeError, schema.Dict, 's')

def test_dict_immutable_keys():
    s = schema.Dict(u's', schema.Integer(u'x'), schema.Integer(u'y'))
    n = s.node()

    assert_raises(TypeError, n.__setitem__, 'z', 123)
    assert_raises(TypeError, n.__delitem__, u'x')
    assert_raises(KeyError, n.__delitem__, u'z')
    assert_raises(TypeError, n.setdefault, u'x', 123)
    assert_raises(TypeError, n.setdefault, u'z', 123)
    assert_raises(TypeError, n.pop, u'x')
    assert_raises(KeyError, n.pop, u'z')
    assert_raises(TypeError, n.popitem)
    assert_raises(TypeError, n.clear)

def test_dict_reads():
    s = schema.Dict(u's', schema.Integer(u'x'), schema.Integer(u'y'))
    n = s.node()

    n[u'x'] = 10
    n[u'y'] = 20

    eq_(n[u'x'], 10)
    eq_(n[u'y'], 20)

    # the values are unhashable Nodes, so this is a little painful
    assert set(n.keys()) == set(u'xy')
    eq_(set([(u'x', 10), (u'y', 20)]),
        set([(_[0], _[1].value) for _ in n.items()]))
    eq_(set([10, 20]), set([_.value for _ in n.values()]))

    eq_(n.get(u'x'), 10)
    n[u'x'] = None
    eq_(n.get(u'x'), None)
    eq_(n.get(u'x', 'default is never used'), None)

    assert_raises(KeyError, n.get, u'z')
    assert_raises(KeyError, n.get, u'z', 'even with a default')

def test_dict_update():
    s = schema.Dict(u's', schema.Integer(u'x'), schema.Integer(u'y'))
    n = s.node()

    def value_dict(node):
        return dict((k, v.value) for k, v in node.iteritems())

    n.update(x=20, y=30)
    assert dict(x=20, y=30) == value_dict(n)

    n.update({u'y': 40})
    assert dict(x=20, y=40) == value_dict(n)

    n.update()
    assert dict(x=20, y=40) == value_dict(n)

    n.update((_, 100) for _ in u'xy')
    assert dict(x=100, y=100) == value_dict(n)

    n.update([(u'x', 1)], y=2)
    assert dict(x=1, y=2) == value_dict(n)

    n.update([(u'x', 10), (u'y', 10)], x=20, y=20)
    assert dict(x=20, y=20) == value_dict(n)

    assert_raises(TypeError, n.update, z=1)
    assert_raises(TypeError, n.update, x=1, z=1)
    assert_raises(TypeError, n.update, {u'z': 1})
    assert_raises(TypeError, n.update, {u'x': 1, u'z': 1})
    assert_raises(TypeError, n.update, ((u'z', 1),))
    assert_raises(TypeError, n.update, ((u'x', 1), (u'z', 1)))


class DictSetTest(object):
    policy = Unspecified
    x_default = Unspecified
    y_default = Unspecified
    empty = None

    def new_schema(self):
        dictkw, x_kw, y_kw = {}, {}, {}
        if self.policy is not Unspecified:
            dictkw['policy'] = self.policy
        if self.x_default is not Unspecified:
            x_kw['default'] = self.x_default
        if self.y_default is not Unspecified:
            y_kw['default'] = self.y_default

        return schema.Dict(u's',
                           schema.Integer(u'x', **x_kw),
                           schema.Integer(u'y', **y_kw),
                           **dictkw)
    def new_node(self, schema=Unspecified, **kw):
        if schema is Unspecified:
            schema = self.new_schema()
        return schema.node(**kw)

    def value_dict(self, node):
        return dict((k, v.value) for k, v in node.iteritems())

    def dict_eq_(self, node, wanted):
        as_dict = self.value_dict(node)
        eq_(as_dict, wanted)

    def test_empty_sets(self):
        n = self.new_node()
        self.dict_eq_(n, self.empty)
        n.set({})
        self.dict_eq_(n, self.empty)

        n = self.new_node(value={})
        self.dict_eq_(n, self.empty)

        n = self.new_node(value=iter(()))
        self.dict_eq_(n, self.empty)

        n = self.new_node(value=())
        self.dict_eq_(n, self.empty)

    def test_half_set(self):
        wanted = dict(self.empty, x=123)

        n = self.new_node()
        n.set(dict(x=123))
        self.dict_eq_(n, wanted)

        n = self.new_node()
        n.set([(u'x', 123)])
        self.dict_eq_(n, wanted)

    def test_full_set(self):
        wanted = {u'x': 101, u'y': 102}

        n = self.new_node()
        n.set(wanted)
        self.dict_eq_(n, wanted)

        n = self.new_node()
        n.set(dict(x=101, y=102))
        self.dict_eq_(n, wanted)

        n = self.new_node()
        n.set([(u'x', 101), (u'y', 102)])
        self.dict_eq_(n, wanted)

        n = self.new_node(value=wanted)
        self.dict_eq_(n, wanted)

    def test_over_set(self):
        too_much = {u'x': 1, u'y': 2, u'z': 3}

        n = self.new_node()
        assert_raises(KeyError, n.set, too_much)
        assert_raises(KeyError, self.new_node, value=too_much)

    def test_total_miss(self):
        miss = {u'z': 3}

        n = self.new_node()
        assert_raises(KeyError, n.set, miss)
        assert_raises(KeyError, self.new_node, value=miss)

class TestEmptyDictSet(DictSetTest):
    empty = {u'x': None, u'y': None}

class TestHalfDefaultDictSet(DictSetTest):
    x_default = 10
    empty = {u'x': 10, u'y': None}

class TestDefaultDictSet(DictSetTest):
    x_default = 10
    y_default = 20
    empty = {u'x': 10, u'y': 20}

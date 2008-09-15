from nose.tools import eq_, assert_raises

from flatland import schema


def test_sequence():
    s = schema.container.Sequence('s',
                                  schema.String('a'),
                                  schema.String('b'))

    n = s.new()
    # No, should be sequence of 1 schema
    # right?
    # self.schema.spec.new() is busted if not

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





from nose.tools import eq_, assert_raises, set_trace

from flatland import schema
from flatland.util import Unspecified


def test_sequence():
    assert_raises(TypeError, schema.containers.Sequence, 's',
                  schema.String('a'))

    s = schema.containers.Sequence('s')
    assert hasattr(s, 'spec')

def test_list_linear_set_scalars():
    s = schema.List('l', schema.String('s'))
    n = s.new()

    pairs = list(('l_%s_s' % i, 'val%s' % i) for i in xrange(1, 10))
    n.set_flat(pairs)
    eq_(len(n), len(pairs))
    eq_(n, list(pair[1] for pair in pairs))

def test_list_set_empty():
    s = schema.List('l', schema.String('s'))
    n = s.new()

    pairs = ((u'l_galump', u'foo'), (u'l_snorgle', u'bar'))
    n.set_flat(pairs)
    eq_(len(n), 0)
    eq_(n, [])

def test_list_lossy_set_scalars():
    s = schema.List('l', schema.String('s'))
    n = s.new()

    pairs = list(('l_%s_s' % i, 'val%s' % i) for i in xrange(1, 10, 2))
    n.set_flat(pairs)

    eq_(len(n), len(pairs))
    eq_(n, list(pair[1] for pair in pairs))

    # lossy won't insert empty elements
    eq_(n[1].value, pairs[1][1])

def test_list_linear_set_dict():
    s = schema.List('l', schema.String('x'), schema.String('y'))
    n = s.new()

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
        return s.new()

    n = factory(3)
    eq_(len(n), 3)
    eq_(n, [u'val'] * 3)

    n = factory(0)
    eq_(len(n), 0)
    eq_(n, [])

def test_list_set():
    def new_element(**kw):
        s = schema.List('l', schema.Integer('i'))
        return s.new(**kw)

    n = new_element()
    assert list(n) == []
    assert_raises(TypeError, n.set, 1)
    assert_raises(TypeError, n.set, None)

    n = new_element()
    n.set(range(3))
    assert list(n) == [0, 1, 2]

    n = new_element()
    n.set(xrange(3))
    assert list(n) == [0, 1, 2]

    n = new_element(value=[0, 1, 2])
    assert list(n) == [0, 1, 2]

    n = new_element()
    n.extend([1,2,3])
    assert list(n) == [1, 2, 3]
    n.set([4, 5, 6])
    assert list(n) == [4, 5, 6]
    n.set([])
    assert list(n) == []

def test_list_access():
    s = schema.List('l', schema.Integer('i'))
    n = s.new()

    pairs = ((u'l_0_i', u'10'), (u'l_1_i', u'11'), (u'l_2_i', u'12'),)
    n.set_flat(pairs)

    elements = list(schema.Integer('i').new(value=val)
                 for val in (u'10', u'11', u'12'))

    assert len(n) == 3
    assert n[0] == elements[0]
    assert n[1] == elements[1]
    assert n[2] == elements[2]

    assert n[:0] == elements[:0]
    assert n[:1] == elements[:1]
    assert n[0:5] == elements[0:5]
    assert n[-2:-1] == elements[-2:-1]

    assert n[0] in n
    assert elements[0] in n
    assert u'10' in n
    assert 10 in n

    assert n.count(elements[0]) == 1
    assert n.count(u'10') == 1
    assert n.count(10) == 1

    assert n.index(elements[0]) == 0
    assert n.index(u'10') == 0
    assert n.index(10) == 0

def test_list_mutation():
    s = schema.List('l', schema.Integer('i'))
    n = s.new()

    new_element = lambda val: schema.Integer('i').new(value=val)

    def order_ok():
        slot_names = list(_.name for _ in n._slots)
        for idx, name in enumerate(slot_names):
            assert name == unicode(idx)

    assert not n
    order_ok()

    # FIXME:? seems to want parsable data, not elements
    n.append(new_element(u'0'))
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
    n = s.new()
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
    n = s.new()

    assert_raises(TypeError, n.sort)
    assert_raises(TypeError, n.reverse)

def test_list_slots():
    s = schema.List('l', schema.String('s'))
    n = s.new(value=[u'x'])
    for slot in n._slots:
        # don't really care what it says, just no crashy.
        assert repr(slot)
        assert slot == u'x'
        assert slot != u'y'

def test_list_u():
    s = schema.List('l', schema.String('s'))
    n = s.new()
    n[:] = [u'x', u'x']
    eq_(n.u, u"[u'x', u'x']")

def test_list_value():
    s = schema.List('l', schema.String('s'))
    n = s.new()
    n[:] = [u'x', u'x']
    eq_(n.value, [u'x', u'x'])

def test_array_pruned_set_scalars():
    s = schema.Array(schema.String('s'))
    n = s.new()

    pairs = list((u's', u'val%s' % i if i %2 else u'')
                 for i in xrange(1, 10))
    n.set_flat(pairs)

    actual_data = list(pair[1] for pair in pairs if pair[1])
    eq_(len(n), len(actual_data))
    eq_(list(n), actual_data)
    eq_(n, actual_data[-1])

def test_array_unpruned_set_scalars():
    s = schema.Array(schema.String('s'), prune_empty=False)
    n = s.new()

    pairs = list((u's', u'val%s' % i if i %2 else u'')
                 for i in xrange(1, 10))
    n.set_flat(pairs)

    eq_(len(n), len(pairs))
    eq_(list(n), list(pair[1] for pair in pairs))
    eq_(n, pairs[-1][1])

def test_array_mutation():
    s = schema.Array(schema.String('s'))
    new_element = s.new

    n = new_element()
    assert not n

    n.set(u'a')
    assert n
    assert n == u'a'

    n.set('b')
    assert n == u'b'
    assert list(n) == [u'a', u'b']

    n[1] = u'c'
    assert list(n) == [u'a', u'c']

    n[1] = new_element(value='b')
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

    n.insert(1, u'z')
    eq_(list(n), [u'a', u'z', u'b', u'c'])
    eq_(n, u'c')

    # bogosity
    n.u = u'z'
    eq_(list(n), [u'a', u'z', u'b', u'c', u'z'])

    # bogosity part 2
    del n[:]
    n.value = u'abc'
    eq_(list(n), [u'abc'])

def test_array_el():
    s = schema.Array(schema.String('s'))
    n = s.new()
    n[:] = u'abc'
    eq_(list(n), [u'a', u'b', u'c'])

    eq_(n.el('0'), u'a')
    eq_(n.el('2'), u'c')

    assert_raises(KeyError, n.el, 'a')

def test_dict():
    assert_raises(TypeError, schema.Dict, 's')

def test_dict_immutable_keys():
    s = schema.Dict(u's', schema.Integer(u'x'), schema.Integer(u'y'))
    n = s.new()

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
    n = s.new()

    n[u'x'] = 10
    n[u'y'] = 20

    eq_(n[u'x'], 10)
    eq_(n[u'y'], 20)

    # the values are unhashable Elements, so this is a little painful
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
    n = s.new()

    def value_dict(element):
        return dict((k, v.value) for k, v in element.iteritems())

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
    def new_element(self, schema=Unspecified, **kw):
        if schema is Unspecified:
            schema = self.new_schema()
        return schema.new(**kw)

    def value_dict(self, element):
        return dict((k, v.value) for k, v in element.iteritems())

    def dict_eq_(self, element, wanted):
        as_dict = self.value_dict(element)
        eq_(as_dict, wanted)

    def test_empty_sets(self):
        n = self.new_element()
        self.dict_eq_(n, self.empty)
        eq_(n.value, self.empty)

        n.set({})
        self.dict_eq_(n, self.empty)
        eq_(n.value, self.empty)

        n = self.new_element(value={})
        self.dict_eq_(n, self.empty)

        n = self.new_element(value=iter(()))
        self.dict_eq_(n, self.empty)

        n = self.new_element(value=())
        self.dict_eq_(n, self.empty)

    def test_empty_set_flat(self):
        n = self.new_element()
        n.set_flat(())
        self.dict_eq_(n, self.empty)
        eq_(n.value, self.empty)

    def test_half_set(self):
        wanted = dict(self.empty, x=123)

        n = self.new_element()
        n.set(dict(x=123))
        self.dict_eq_(n, wanted)
        eq_(n.value, wanted)

        n = self.new_element()
        n.set([(u'x', 123)])
        self.dict_eq_(n, wanted)

    def test_half_set_flat(self):
        wanted = dict(self.empty, x=123)

        pairs = ((u's_x', u'123'),)
        n = self.new_element()
        n.set_flat(pairs)
        self.dict_eq_(n, wanted)
        eq_(n.value, wanted)

    def test_full_set(self):
        wanted = {u'x': 101, u'y': 102}

        n = self.new_element()
        n.set(wanted)
        self.dict_eq_(n, wanted)
        eq_(n.value, wanted)

        n = self.new_element()
        n.set(dict(x=101, y=102))
        self.dict_eq_(n, wanted)

        n = self.new_element()
        n.set([(u'x', 101), (u'y', 102)])
        self.dict_eq_(n, wanted)

        n = self.new_element(value=wanted)
        self.dict_eq_(n, wanted)

    def test_full_set_flat(self):
        wanted = {u'x': 101, u'y': 102}
        pairs = ((u's_x', u'101'), (u's_y', u'102'))

        n = self.new_element()
        n.set_flat(pairs)
        self.dict_eq_(n, wanted)
        eq_(n.value, wanted)

    def test_over_set(self):
        too_much = {u'x': 1, u'y': 2, u'z': 3}

        n = self.new_element()
        assert_raises(KeyError, n.set, too_much)
        assert_raises(KeyError, self.new_element, value=too_much)

    def test_over_set_flat(self):
        wanted = dict(self.empty, x=123)

        pairs = ((u's_x', u'123'), (u's_z', u'nope'))
        n = self.new_element()
        n.set_flat(pairs)
        self.dict_eq_(n, wanted)
        eq_(n.value, wanted)

    def test_total_miss(self):
        miss = {u'z': 3}

        n = self.new_element()
        assert_raises(KeyError, n.set, miss)
        assert_raises(KeyError, self.new_element, value=miss)

    def test_total_miss_flat(self):
        pairs = (('miss', u'10'),)

        n = self.new_element()
        n.set_flat(pairs)
        self.dict_eq_(n, self.empty)
        eq_(n.value, self.empty)

class TestEmptyDictSet(DictSetTest):
    empty = {u'x': None, u'y': None}

class TestHalfDefaultDictSet(DictSetTest):
    x_default = 10
    empty = {u'x': 10, u'y': None}

class TestDefaultDictSet(DictSetTest):
    x_default = 10
    y_default = 20
    empty = {u'x': 10, u'y': 20}

def test_dict_valid_policies():
    s = schema.Dict(u's', schema.Integer(u'x'), schema.Integer(u'y'))
    n = s.new()

    assert_raises(AssertionError, n.set, {}, policy='bogus')

def test_dict_strict():
    # a mini test, this policy thing may get whacked
    s = schema.Dict(u's', schema.Integer(u'x'), schema.Integer(u'y'),
                    policy='strict')

    n = s.new()
    n.set({u'x': 123, u'y': 456})

    n = s.new()
    assert_raises(TypeError, n.set, {u'x': 123})

    n = s.new()
    assert_raises(KeyError, n.set, {u'x': 123, u'y': 456, u'z': 7})

def test_dict_as_unicode():
    s = schema.Dict(u's', schema.Integer(u'x'), schema.Integer(u'y'))
    n = s.new()
    n.set(dict(x=1, y=2))

    uni = n.u

    assert uni in (u"{u'x': u'1', u'y': u'2'}", "{u'y': u'2', u'x': u'1'}")

def test_nested_dict_as_unicode():
    s = schema.Dict(u's', schema.Dict('d', schema.Integer(u'x', default=10)))
    n = s.new()

    eq_(n.value, {u'd': {u'x': 10}})
    eq_(n.u, u"{u'd': {u'x': u'10'}}")

def test_dict_el():
    # stub
    s = schema.Dict(u's', schema.Integer(u'x'), schema.Integer(u'y'))
    n = s.new()

    assert n.el('x').name == u'x'
    assert_raises(KeyError, n.el, 'not_x')

def test_mixed_all_children():
    data = {'A1': 1,
            'A2': 2,
            'A3': { 'A3B1': { 'A3B1C1': 1,
                              'A3B1C2': 2, },
                    'A3B2': { 'A3B2C1': 1 },
                    'A3B3': [ ['A3B3C0D0', 'A3B3C0D1'],
                              ['A3B3C1D0', 'A3B3C1D1'],
                              ['A3B3C2D0', 'A3B3C2D1'] ] } }

    s = schema.Dict(
        'R',
        schema.String('A1'),
        schema.String('A2'),
        schema.Dict('A3',
                    schema.Dict('A3B1',
                                schema.String('A3B1C1'),
                                schema.String('A3B1C2')),
                    schema.Dict('A3B2',
                                schema.String('A3B2C1')),
                    schema.List('A3B3',
                                schema.List('A3B3Cx',
                                            schema.String('A3B3x')))))
    top = s.from_value(data)

    names = list(e.name for e in top.all_children)

    assert set(names[0:3]) == set(['A1', 'A2', 'A3'])
    assert set(names[3:6]) == set(['A3B1', 'A3B2', 'A3B3'])
    # same-level order the intermediates isn't important
    assert set(names[12:]) == set(['A3B3x'])
    assert len(names[12:]) == 6

def test_corrupt_all_children():
    """all_children won't spin out if the graph becomes cyclic."""
    s = schema.List('R', schema.String('A1'))
    e = s.create_element()

    e.append('x')
    e.append('y')
    dupe = schema.String('A1').create_element(value='z')
    e.append(dupe)
    e.append(dupe)

    assert list(_.value for _ in e.children) == list('xyzz')
    assert list(_.value for _ in e.all_children) == list('xyz')


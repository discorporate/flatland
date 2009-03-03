from flatland import schema, util
from flatland.schema import base
from flatland.util import Unspecified
from tests._util import eq_, assert_raises


def test_simple_validation_shortcircuit():
    def boom(element, state):
        assert False
    skip_ok = lambda element, state: base.AllTrue
    skip_bad = lambda element, state: base.AllFalse

    el = schema.Dict('d', schema.Integer('i', validators=[boom]),
                     validators=[skip_ok]).create_element()

class TestContainerValidation(object):

    def setup(self):
        self.canary = []

    def validator(self, name, result):
        def fn(element, state):
            self.canary.append(name)
            return result
        fn.__name__ = name
        return fn

    def test_regular(self):
        s = schema.Dict('d', schema.Integer('i'),
                        validators=[self.validator('1', True)])
        assert not s.create_element().validate()
        eq_(self.canary, ['1'])

    def test_descent(self):
        s = schema.Dict('d', schema.Integer('i'),
                        descent_validators=[self.validator('1', True)])
        assert not s.create_element().validate()
        eq_(self.canary, ['1'])

    def test_paired(self):
        s = schema.Dict('d', schema.Integer('i'),
                        descent_validators=[self.validator('1', True)],
                        validators=[self.validator('2', True)])
        assert not s.create_element().validate()
        eq_(self.canary, ['1', '2'])

    def test_paired2(self):
        s = schema.Dict('d', schema.Integer('i'),
                        descent_validators=[self.validator('1', False)],
                        validators=[self.validator('2', True)])
        assert not s.create_element().validate()
        eq_(self.canary, ['1', '2'])

    def test_paired3(self):
        s = schema.Dict('d', schema.Integer('i', validators=[
                               self.validator('2', True)]),
                        descent_validators=[self.validator('1', True)],
                        validators=[self.validator('3', True)])
        assert s.create_element().validate()
        eq_(self.canary, ['1', '2', '3'])

    def test_shortcircuit_down_true(self):
        s = schema.Dict('d', schema.Integer('i', validators=[
                               self.validator('2', False)]),
                        descent_validators=[self.validator('1', base.AllTrue)],
                        validators=[self.validator('3', True)])
        assert s.create_element().validate()
        eq_(self.canary, ['1', '3'])

    def test_shortcircuit_down_false(self):
        s = schema.Dict('d', schema.Integer('i', validators=[
                               self.validator('2', False)]),
                        descent_validators=[self.validator('1', base.AllFalse)],
                        validators=[self.validator('3', True)])
        assert not s.create_element().validate()
        eq_(self.canary, ['1', '3'])

    def test_shortcircuit_up(self):
        s = schema.Dict('d', schema.Integer('i', validators=[
                               self.validator('2', True)]),
                        descent_validators=[self.validator('1', True)],
                        validators=[self.validator('3', base.AllTrue)])
        assert s.create_element().validate()
        eq_(self.canary, ['1', '2', '3'])


def test_sequence():
    assert_raises(TypeError, schema.containers.Sequence, 's',
                  schema.String('a'))

    s = schema.containers.Sequence('s')
    assert hasattr(s, 'spec')

def test_list_linear_set_scalars():
    s = schema.List('l', schema.String('s'))
    el = s.create_element()

    pairs = list(('l_%s_s' % i, 'val%s' % i) for i in xrange(1, 10))
    el.set_flat(pairs)
    eq_(len(el), len(pairs))
    eq_(el.value, list(pair[1] for pair in pairs))

def test_list_set_empty():
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

def test_list_default():
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

def test_array_pruned_set_scalars():
    s = schema.Array(schema.String('s'))
    n = s.create_element()

    pairs = list((u's', u'val%s' % i if i %2 else u'')
                 for i in xrange(1, 10))
    n.set_flat(pairs)

    actual_data = list(pair[1] for pair in pairs if pair[1])
    eq_(len(n), len(actual_data))
    eq_(n.value, actual_data)

def test_array_unpruned_set_scalars():
    s = schema.Array(schema.String('s'), prune_empty=False)
    n = s.create_element()

    pairs = list((u's', u'val%s' % i if i %2 else u'')
                 for i in xrange(1, 10))
    n.set_flat(pairs)

    eq_(len(n), len(pairs))
    eq_(n.value, list(pair[1] for pair in pairs))

def test_array_mutation():
    s = schema.Array(schema.String('s'))
    n = s.create_element()
    assert not n

    n.set(u'a')
    assert n[0].u == u'a'
    assert n.value == [u'a']

    n.set('b')
    assert n[0].u == u'b'
    assert n.value == [u'b']

    n.append(u'x')
    assert n[1].u == u'x'
    assert n.value == [u'b', u'x']

    n[1] = u'a'
    assert n[1].u == u'a'
    assert n.value == [u'b', u'a']

    n.remove(u'b')
    assert n.value == [u'a']

    n.extend(u'bcdefg')

    eq_(n.value[0:4], [u'a', u'b', u'c', u'd'])

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

    n.insert(1, u'z')
    eq_(n.value, [u'a', u'z', u'b', u'c'])

    def assign():
        n.u = u'z'
    assert_raises(AttributeError, assign)
    eq_(n.value, [u'a', u'z', u'b', u'c'])

    def assign():
        n.value = u'abc'
    del n[:]
    assert_raises(AttributeError, assign)
    eq_(n.value, [])

def test_array_set_default():
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

def test_array_el():
    s = schema.Array(schema.String('s'))
    n = s.create_element()
    n[:] = u'abc'
    eq_(list(n.value), [u'a', u'b', u'c'])

    eq_(n.el('0').value, u'a')
    eq_(n.el('2').value, u'c')
    assert_raises(KeyError, n.el, 'a')

def test_dict():
    assert_raises(TypeError, schema.Dict, 's')

def test_dict_immutable_keys():
    s = schema.Dict(u's', schema.Integer(u'x'), schema.Integer(u'y'))
    n = s.create_element()

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
    n = s.create_element()

    n[u'x'] = 10
    n[u'y'] = 20

    eq_(n[u'x'].value, 10)
    eq_(n[u'y'].value, 20)

    # the values are unhashable Elements, so this is a little painful
    assert set(n.keys()) == set(u'xy')
    eq_(set([(u'x', 10), (u'y', 20)]),
        set([(_[0], _[1].value) for _ in n.items()]))
    eq_(set([10, 20]), set([_.value for _ in n.values()]))

    eq_(n.get(u'x').value, 10)
    n[u'x'] = None
    eq_(n.get(u'x').value, None)
    eq_(n.get(u'x', 'default is never used').value, None)

    assert_raises(KeyError, n.get, u'z')
    assert_raises(KeyError, n.get, u'z', 'even with a default')

def test_dict_update():
    s = schema.Dict(u's', schema.Integer(u'x'), schema.Integer(u'y'))
    n = s.create_element()

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
        return schema.create_element(**kw)

    def test_empty_sets(self):
        wanted = {u'x': None, u'y': None}

        el = self.new_element()
        eq_(el.value, wanted)

        el.set({})
        eq_(el.value, wanted)

        el = self.new_element(value={})
        eq_(el.value, wanted)

        el = self.new_element(value=iter(()))
        eq_(el.value, wanted)

        el = self.new_element(value=())
        eq_(el.value, wanted)

    def test_empty_set_flat(self):
        el = self.new_element()
        el.set_flat(())
        eq_(el.value, {u'x': None, u'y': None})

    def test_half_set(self):
        wanted = {u'x': 123, 'y': None}

        el = self.new_element()
        el.set(dict(x=123))
        eq_(el.value, wanted)

        el = self.new_element()
        el.set([(u'x', 123)])
        eq_(el.value, wanted)

    def test_half_set_flat(self):
        wanted = {u'x': 123, 'y': None}

        pairs = ((u's_x', u'123'),)
        el = self.new_element()
        el.set_flat(pairs)
        eq_(el.value, wanted)

    def test_full_set(self):
        wanted = {u'x': 101, u'y': 102}

        el = self.new_element()
        el.set(wanted)
        eq_(el.value, wanted)

        el = self.new_element()
        el.set(dict(x=101, y=102))
        eq_(el.value, wanted)

        el = self.new_element()
        el.set([(u'x', 101), (u'y', 102)])
        eq_(el.value, wanted)

        el = self.new_element(value=wanted)
        eq_(el.value, wanted)

    def test_full_set_flat(self):
        wanted = {u'x': 101, u'y': 102}
        pairs = ((u's_x', u'101'), (u's_y', u'102'))

        el = self.new_element()
        el.set_flat(pairs)
        eq_(el.value, wanted)

    def test_over_set(self):
        too_much = {u'x': 1, u'y': 2, u'z': 3}

        el = self.new_element()
        assert_raises(KeyError, el.set, too_much)
        assert_raises(KeyError, self.new_element, value=too_much)

    def test_over_set_flat(self):
        wanted = {u'x': 123, 'y': None}

        pairs = ((u's_x', u'123'), (u's_z', u'nope'))
        el = self.new_element()
        el.set_flat(pairs)
        eq_(el.value, wanted)

    def test_total_miss(self):
        miss = {u'z': 3}

        el = self.new_element()
        assert_raises(KeyError, el.set, miss)
        assert_raises(KeyError, self.new_element, value=miss)

    def test_total_miss_flat(self):
        pairs = (('miss', u'10'),)

        el = self.new_element()
        el.set_flat(pairs)
        eq_(el.value, {u'x': None, u'y': None})


class TestEmptyDictSet(DictSetTest):
    pass


class TestDefaultDictSet(DictSetTest):
    x_default = 10
    y_default = 20


def test_dict_valid_policies():
    s = schema.Dict(u's', schema.Integer(u'x'), schema.Integer(u'y'))
    n = s.create_element()

    assert_raises(AssertionError, n.set, {}, policy='bogus')

def test_dict_strict():
    # a mini test, this policy thing may get whacked
    s = schema.Dict(u's', schema.Integer(u'x'), schema.Integer(u'y'),
                    policy='strict')

    n = s.create_element()
    n.set({u'x': 123, u'y': 456})

    n = s.create_element()
    assert_raises(TypeError, n.set, {u'x': 123})

    n = s.create_element()
    assert_raises(KeyError, n.set, {u'x': 123, u'y': 456, u'z': 7})

def test_dict_as_unicode():
    s = schema.Dict(u's', schema.Integer(u'x'), schema.Integer(u'y'))
    n = s.create_element()
    n.set(dict(x=1, y=2))

    uni = n.u

    assert uni in (u"{u'x': u'1', u'y': u'2'}", "{u'y': u'2', u'x': u'1'}")

def test_nested_dict_as_unicode():
    s = schema.Dict(u's', schema.Dict('d', schema.Integer(u'x', default=10)))
    el = s.create_element()
    el.set_default()

    eq_(el.value, {u'd': {u'x': 10}})
    eq_(el.u, u"{u'd': {u'x': u'10'}}")

def test_dict_el():
    # stub
    s = schema.Dict(u's', schema.Integer(u'x'), schema.Integer(u'y'))
    n = s.create_element()

    assert n.el('x').name == u'x'
    assert_raises(KeyError, n.el, 'not_x')

def test_update_object():
    class Obj(object):
        def __init__(self, **kw):
            for (k, v) in kw.items():
                setattr(self, k, v)

    s = schema.Dict(u's', schema.String(u'x'), schema.String(u'y'))

    o = Obj()
    assert not hasattr(o, 'x')
    assert not hasattr(o, 'y')

    def updated_(obj_factory, initial_value, wanted=None, **update_kw):
        e = s.create_element(value=initial_value)
        o = obj_factory()
        e.update_object(o, **update_kw)
        if wanted is None:
            wanted = initial_value
        have = dict(o.__dict__)
        assert have == wanted

    updated_(Obj, {'x': 'X', 'y': 'Y'})
    updated_(Obj, {'x': 'X'}, {'x': 'X', 'y': None})
    updated_(lambda: Obj(y='Y'), {'x': 'X'}, {'x': 'X', 'y': None})
    updated_(lambda: Obj(y='Y'), {'x': 'X'}, {'x': 'X', 'y': 'Y'}, omit=('y',))
    updated_(lambda: Obj(y='Y'), {'x': 'X'}, {'y': 'Y'}, include=('z',))
    updated_(Obj, {'x': 'X'}, {'y': None, 'z': 'X'}, rename=(('x', 'z'),))

def test_slice():
    s = schema.Dict(u's', schema.String(u'x'), schema.String(u'y'))

    def same_(source, kw):
        e = s.create_element(value=source)

        sliced = e.slice(**kw)
        wanted = dict(util.keyslice_pairs(e.value.items(), **kw))

        eq_(sliced, wanted)
        eq_(set(type(_) for _ in sliced.keys()),
            set(type(_) for _ in wanted.keys()))

    yield same_, {'x': 'X', 'y': 'Y'}, {}
    yield same_, {'x': 'X', 'y': 'Y'}, dict(key=str)
    yield same_, {'x': 'X', 'y': 'Y'}, dict(include=['x'])
    yield same_, {'x': 'X', 'y': 'Y'}, dict(omit=['x'])
    yield same_, {'x': 'X', 'y': 'Y'}, dict(omit=['x'], rename={'y': 'z'})

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

def test_naming_bogus():
    e = schema.String('s').create_element()

    assert_raises(LookupError, e.el, u'')
    assert_raises(TypeError, e.el, None)
    assert_raises(LookupError, e.el, ())
    assert_raises(LookupError, e.el, iter(()))
    assert_raises(TypeError, e.el)

def test_naming_shallow():
    s1 = schema.String('s')
    root = s1.create_element()
    assert root.fq_name() == '.'
    assert root.flattened_name() == 's'
    assert root.el('.') is root

    s2 = schema.String(None)
    root = s2.create_element()
    assert root.fq_name() == '.'
    assert root.flattened_name() == ''
    assert root.el('.') is root
    assert_raises(LookupError, root.el, ())
    assert root.el([schema.base.Root]) is root

def test_naming_dict():
    for name, root_flat, leaf_flat in (('d', 'd', 'd_s'),
                                       (None, '', 's')):
        s1 = schema.Dict(name, schema.String('s'))
        root = s1.create_element()
        leaf = root['s']

        assert root.fq_name() == '.'
        assert root.flattened_name() == root_flat
        assert root.el('.') is root

        assert leaf.fq_name() == '.s'
        assert leaf.flattened_name() == leaf_flat
        assert root.el('.s') is leaf
        assert root.el('s') is leaf
        assert leaf.el('.s') is leaf
        assert_raises(LookupError, leaf.el, 's')
        assert leaf.el('.') is root

        assert root.el([schema.base.Root]) is root
        assert root.el(['s']) is leaf
        assert root.el([schema.base.Root, 's']) is leaf
        assert root.el(iter(['s'])) is leaf
        assert root.el(iter([schema.base.Root, 's'])) is leaf

def test_naming_dict_dict():
    for name, root_flat, leaf_flat in (('d', 'd', 'd_d2_s'),
                                       (None, '', 'd2_s')):
        s1 = schema.Dict(name, schema.Dict('d2', schema.String('s')))
        root = s1.create_element()
        leaf = root['d2']['s']

        assert root.fq_name() == '.'
        assert root.flattened_name() == root_flat
        assert root.el('.') is root

        assert leaf.fq_name() == '.d2.s'
        assert leaf.flattened_name() == leaf_flat
        assert root.el('.d2.s') is leaf
        assert root.el('d2.s') is leaf
        assert leaf.el('.d2.s') is leaf
        assert_raises(LookupError, leaf.el, 'd2.s')
        assert leaf.el('.') is root

        assert root.el(['d2', 's']) is leaf

def test_naming_list():
    for name, root_flat, leaf_flat in (('l', 'l', 'l_0_s'),
                                       (None, '', '0_s')):
        s1 = schema.List(name, schema.String('s'))
        root = s1.create_element(value=['x'])
        leaf = root[0]

        assert root.fq_name() == '.'
        assert root.flattened_name() == root_flat
        assert root.el('.') is root

        assert leaf.fq_name() == '.0'
        assert leaf.flattened_name() == leaf_flat
        assert root.el('.0') is leaf
        assert root.el('0') is leaf
        assert leaf.el('.0') is leaf
        assert_raises(LookupError, leaf.el, '0')
        assert_raises(LookupError, leaf.el, 's')
        assert leaf.el('.') is root

        assert root.el(['0']) is leaf

def test_naming_list_list():
    # make sure nested Slots-users don't bork
    for name, root_flat, leaf_flat in (('l', 'l', 'l_0_l2_0_s'),
                                       (None, '', '0_l2_0_s')):
        s1 = schema.List(name, schema.List('l2', schema.String('s')))

        root = s1.create_element(value=[['x']])
        leaf = root[0][0]

        assert root.fq_name() == '.'
        assert root.flattened_name() == root_flat
        assert root.el('.') is root

        assert leaf.fq_name() == '.0.0'
        assert leaf.flattened_name() == leaf_flat
        assert root.el('.0.0') is leaf
        assert root.el('0.0') is leaf
        assert leaf.el('.0.0') is leaf
        assert_raises(LookupError, leaf.el, '0')
        assert_raises(LookupError, leaf.el, 's')
        assert leaf.el('.') is root

        assert root.el(['0', '0']) is leaf

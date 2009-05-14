from flatland import schema, util
from flatland.util import Unspecified
from tests._util import eq_, assert_raises


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

    def test_set_default(self):
        wanted = {u'x': 11, u'y': 12}
        schema = self.new_schema()
        schema.default = wanted

        el = schema.create_element()
        el.set_default()
        eq_(el.value, wanted)

    def test_set_default_from_children(self):
        el = self.new_element()
        el.set_default()

        wanted = {
            u'x': self.x_default if self.x_default is not Unspecified else None,
            u'y': self.y_default if self.y_default is not Unspecified else None,
            }
        eq_(el.value, wanted)


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

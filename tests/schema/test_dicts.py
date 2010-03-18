from flatland import (
    Dict,
    Integer,
    String,
    )
from flatland.util import Unspecified, keyslice_pairs
from tests._util import (
    asciistr,
    assert_raises,
    eq_,
    udict,
    unicode_coercion_available,
    )


def test_dict():
    assert_raises(TypeError, Dict)


def test_dict_immutable_keys():
    schema = Dict.of(Integer.named(u'x'), Integer.named(u'y'))
    el = schema()

    assert_raises(TypeError, el.__setitem__, u'z', 123)
    assert_raises(TypeError, el.__delitem__, u'x')
    assert_raises(KeyError, el.__delitem__, u'z')
    assert_raises(TypeError, el.setdefault, u'x', 123)
    assert_raises(TypeError, el.setdefault, u'z', 123)
    assert_raises(TypeError, el.pop, u'x')
    assert_raises(KeyError, el.pop, u'z')
    assert_raises(TypeError, el.popitem)
    assert_raises(TypeError, el.clear)


def test_dict_reads():
    schema = Dict.of(Integer.named(u'x'), Integer.named(u'y'))
    el = schema()

    el[u'x'].set(u'10')
    el[u'y'].set(u'20')

    eq_(el[u'x'].value, 10)
    eq_(el[u'y'].value, 20)

    # the values are unhashable Elements, so this is a little painful
    assert set(el.keys()) == set(u'xy')
    eq_(set([(u'x', 10), (u'y', 20)]),
        set([(_[0], _[1].value) for _ in el.items()]))
    eq_(set([10, 20]), set([_.value for _ in el.values()]))

    eq_(el.get(u'x').value, 10)
    el[u'x'] = None
    eq_(el.get(u'x').value, None)
    eq_(el.get(u'x', 'default is never used').value, None)

    assert_raises(KeyError, el.get, u'z')
    assert_raises(KeyError, el.get, u'z', 'even with a default')


def test_dict_update():
    schema = Dict.of(Integer.named(u'x'), Integer.named(u'y'))
    el = schema()

    def value_dict(element):
        return dict((k, v.value) for k, v in element.iteritems())

    try:
        el.update(x=20, y=30)
    except UnicodeError:
        assert not unicode_coercion_available()
        el.update(udict(x=20, y=30))
    assert udict(x=20, y=30) == el.value

    el.update({u'y': 40})
    assert udict(x=20, y=40) == el.value

    el.update()
    assert udict(x=20, y=40) == el.value

    el.update((_, 100) for _ in u'xy')
    assert udict(x=100, y=100) == el.value

    try:
        el.update([(u'x', 1)], y=2)
        assert udict(x=1, y=2) == el.value
    except UnicodeError:
        assert not unicode_coercion_available()

    try:
        el.update([(u'x', 10), (u'y', 10)], x=20, y=20)
        assert udict(x=20, y=20) == el.value
    except UnicodeError:
        assert not unicode_coercion_available()

    if unicode_coercion_available():
        assert_raises(TypeError, el.update, z=1)
        assert_raises(TypeError, el.update, x=1, z=1)
    assert_raises(TypeError, el.update, {u'z': 1})
    assert_raises(TypeError, el.update, {u'x': 1, u'z': 1})
    assert_raises(TypeError, el.update, ((u'z', 1),))
    assert_raises(TypeError, el.update, ((u'x', 1), (u'z', 1)))


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

        return Dict.named(u's').using(**dictkw).of(
            Integer.named(u'x').using(**x_kw),
            Integer.named(u'y').using(**y_kw))

    def new_element(self, schema=Unspecified, **kw):
        if schema is Unspecified:
            schema = self.new_schema()
        return schema(**kw)

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
        wanted = {u'x': 123, u'y': None}

        el = self.new_element()
        el.set({u'x': 123})
        eq_(el.value, wanted)

        el = self.new_element()
        el.set([(u'x', 123)])
        eq_(el.value, wanted)

    def test_half_set_flat(self):
        wanted = {u'x': 123, u'y': None}

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
        el.set(udict(x=101, y=102))
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

    def test_scalar_set_flat(self):
        wanted = {u'x': None, u'y': None}
        pairs = ((u's', u'xxx'),)

        el = self.new_element()

        canary = []
        def setter(self, value):
            canary.append(value)
            return type(el).set(self, value)

        el.set = setter.__get__(el, type(el))
        el.set_flat(pairs)
        eq_(el.value, wanted)
        assert canary == []

    def test_over_set(self):
        too_much = {u'x': 1, u'y': 2, u'z': 3}

        el = self.new_element()
        assert_raises(KeyError, el.set, too_much)
        assert_raises(KeyError, self.new_element, value=too_much)

    def test_over_set_flat(self):
        wanted = {u'x': 123, u'y': None}

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
        pairs = ((u'miss', u'10'),)

        el = self.new_element()
        el.set_flat(pairs)
        eq_(el.value, {u'x': None, u'y': None})

    def test_set_default(self):
        wanted = {u'x': 11, u'y': 12}
        schema = self.new_schema()
        schema.default = wanted

        el = schema()
        el.set_default()
        eq_(el.value, wanted)

    def test_set_default_from_children(self):
        el = self.new_element()
        el.set_default()

        wanted = {
            u'x': self.x_default if self.x_default is not Unspecified
                                 else None,
            u'y': self.y_default if self.y_default is not Unspecified
                                 else None,
            }
        eq_(el.value, wanted)


class TestEmptyDictSet(DictSetTest):
    pass


class TestDefaultDictSet(DictSetTest):
    x_default = 10
    y_default = 20


def test_dict_valid_policies():
    schema = Dict.of(Integer)
    el = schema()

    assert_raises(AssertionError, el.set, {}, policy='bogus')


def test_dict_strict():
    # a mini test, this policy thing may get whacked
    schema = Dict.using(policy='strict').of(Integer.named(u'x'),
                                            Integer.named(u'y'))

    el = schema({u'x': 123, u'y': 456})

    el = schema()
    assert_raises(TypeError, el.set, {u'x': 123})

    el = schema()
    assert_raises(KeyError, el.set, {u'x': 123, u'y': 456, u'z': 7})


def test_dict_as_unicode():
    schema = Dict.of(Integer.named(u'x'), Integer.named(u'y'))
    el = schema({u'x': 1, u'y': 2})

    assert el.u in (u"{u'x': u'1', u'y': u'2'}", u"{u'y': u'2', u'x': u'1'}")


def test_nested_dict_as_unicode():
    schema = Dict.of(Dict.named(u'd').of(
        Integer.named(u'x').using(default=10)))
    el = schema.from_defaults()

    eq_(el.value, {u'd': {u'x': 10}})
    eq_(el.u, u"{u'd': {u'x': u'10'}}")


def test_nested_unicode_dict_as_unicode():
    schema = Dict.of(Dict.named(u'd').of(
        String.named(u'x').using(default=u'\u2308\u2309')))
    el = schema.from_defaults()
    eq_(el.value, {u'd': {u'x': u'\u2308\u2309'}})
    eq_(el.u, ur"{u'd': {u'x': u'\u2308\u2309'}}")


def test_dict_el():
    # stub
    schema = Dict.named(u's').of(Integer.named(u'x'), Integer.named(u'y'))
    element = schema()

    assert element.el(u'x').name == u'x'
    assert_raises(KeyError, element.el, u'not_x')


def test_update_object():

    class Obj(object):

        def __init__(self, **kw):
            for (k, v) in kw.items():
                setattr(self, k, v)

    schema = Dict.of(String.named(u'x'), String.named(u'y'))

    o = Obj()
    assert not hasattr(o, 'x')
    assert not hasattr(o, 'y')

    def updated_(obj_factory, initial_value, wanted=None, **update_kw):
        el = schema(initial_value)
        obj = obj_factory()
        update_kw.setdefault('key', asciistr)
        el.update_object(obj, **update_kw)
        if wanted is None:
            wanted = dict((asciistr(k), v) for k, v in initial_value.items())
        have = dict(obj.__dict__)
        assert have == wanted

    updated_(Obj, {u'x': u'X', u'y': u'Y'})
    updated_(Obj, {u'x': u'X'}, {'x': u'X', 'y': None})
    updated_(lambda: Obj(y=u'Y'), {u'x': u'X'}, {'x': u'X', 'y': None})
    updated_(lambda: Obj(y=u'Y'), {u'x': u'X'}, {'x': u'X', 'y': u'Y'},
             omit=('y',))
    updated_(lambda: Obj(y=u'Y'), {u'x': u'X'}, {'y': u'Y'},
             include=(u'z',))
    updated_(Obj, {u'x': u'X'}, {'y': None, 'z': u'X'},
             rename=(('x', 'z'),))


def test_slice():
    schema = Dict.of(String.named(u'x'), String.named(u'y'))

    def same_(source, kw):
        el = schema(source)

        sliced = el.slice(**kw)
        wanted = dict(keyslice_pairs(el.value.items(), **kw))

        eq_(sliced, wanted)
        eq_(set(type(_) for _ in sliced.keys()),
            set(type(_) for _ in wanted.keys()))

    yield same_, {u'x': u'X', u'y': u'Y'}, {}
    yield same_, {u'x': u'X', u'y': u'Y'}, dict(key=asciistr)
    yield same_, {u'x': u'X', u'y': u'Y'}, dict(include=[u'x'])
    yield same_, {u'x': u'X', u'y': u'Y'}, dict(omit=[u'x'])
    yield same_, {u'x': u'X', u'y': u'Y'}, dict(omit=[u'x'],
                                                rename={u'y': u'z'})

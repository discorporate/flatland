# portions of this file are derived from SQLAlchemy

from nose.tools import eq_, assert_raises
from flatland import util


def test_lazy_property():
    poison = False
    class Foo(object):
        @util.lazy_property
        def squiznart(self):
            assert not poison
            return 'abc'

    assert Foo.squiznart != 'abc'
    assert hasattr(Foo.squiznart, '__get__')

    f = Foo()
    assert 'squiznart' not in f.__dict__
    assert f.squiznart == 'abc'
    assert f.__dict__['squiznart'] == 'abc'

    poison = True
    assert f.squiznart == 'abc'

    new_foo = Foo()
    assert_raises(AssertionError, getattr, new_foo, 'squiznart')
    assert 'squiznart' not in new_foo.__dict__



def test_as_mapping():
    class Foo(object):
        clazz = 'c'
        def __init__(self):
            self.inzt = 'i'

    m = util.as_mapping(Foo)
    assert 'clazz' in m
    assert m['clazz'] == 'c'
    assert sorted(dir(Foo)) == sorted(m)
    assert_raises(KeyError, m.__getitem__, 'inzt')

    mi = util.as_mapping(Foo())
    assert 'clazz' in mi
    assert mi['clazz'] == 'c'
    assert 'inzt' in mi
    assert mi['inzt'] == 'i'
    assert sorted(dir(Foo())) == sorted(mi)



def test_luhn10():
    assert util.luhn10(0) is True
    assert util.luhn10(4100000000000001) is True
    assert util.luhn10(4100000000000009) is False



def test_to_pairs():
    to_pairs = util.to_pairs
    wanted = [('a', 1), ('b', 2)]

    assert list(to_pairs(wanted)) == wanted
    assert list(to_pairs(iter(wanted))) == wanted
    assert sorted(to_pairs(dict(wanted))) == wanted

    class Duck(object):
        def keys(self):
            return dict(wanted).keys()
        def __getitem__(self, key):
            return dict(wanted)[key]

    assert sorted(to_pairs(Duck())) == wanted



PAIRS = [('a', 1), ('b', 2), ('c', 3),
         ('d', 4), ('d', 4), ('d', 5)]

def test_keyslice_conflict():
    generator = util.keyslice_pairs((), include=[1], omit=[2])
    assert_raises(TypeError, list, generator)

def test_keyslice_pairs():
    assert list(util.keyslice_pairs(PAIRS)) == PAIRS
    assert list(util.keyslice_pairs(tuple(PAIRS))) == PAIRS
    assert list(util.keyslice_pairs(iter(PAIRS))) == PAIRS

def _keyslice_eq_(wanted, kw={}):
    got = list(util.keyslice_pairs(PAIRS, **kw))
    assert wanted == got

def test_keyslice_include():
    yield _keyslice_eq_, PAIRS, dict(include=[])
    yield _keyslice_eq_, [('a', 1)], dict(include=['a'])
    yield _keyslice_eq_, [('a', 1), ('b', 2)], dict(include=['a', 'b'])
    yield _keyslice_eq_, [('d', 4), ('d', 4), ('d', 5)], dict(include=['d'])
    yield _keyslice_eq_, [('a', 1)], dict(include=['a', 'e'])

def test_keyslice_omit():
    yield _keyslice_eq_, PAIRS, dict(omit=[])
    yield _keyslice_eq_, [('a', 1), ('b', 2), ('c', 3)], dict(omit=['d'])
    yield _keyslice_eq_, [('a', 1), ('b', 2)], dict(omit=['c', 'd'])
    yield _keyslice_eq_, [('a', 1), ('b', 2)], dict(omit=['c', 'd', 'e'])
    yield _keyslice_eq_, [], dict(omit=['a', 'b', 'c', 'd'])

def test_keyslice_rename():
    wanted = PAIRS[:3] + [('Z', 4), ('Z', 4), ('Z', 5)]
    yield _keyslice_eq_, wanted, dict(rename={'d': 'Z'})
    yield _keyslice_eq_, wanted, dict(rename=[('d', 'Z')])
    yield _keyslice_eq_, wanted, dict(rename={'d': 'Z', 'e': 'Y'})

    wanted = [('d', 1), ('c', 2), ('b', 3),
              ('a', 4), ('a', 4), ('a', 5)]

    yield _keyslice_eq_, wanted, dict(rename=zip('abcddd', 'dcbaaa'))

def test_keyslice_mixed():
    wanted = [('a', 1), ('X', 2)]

    yield _keyslice_eq_, wanted, dict(rename={'b': 'X'}, include=['a'])
    yield _keyslice_eq_, wanted, dict(rename={'b': 'X'}, omit=['b', 'c', 'd'])



def test_format_argspec_plus():
    def test(fn, wanted, grouped=None):
        if grouped is None:
            parsed = util.format_argspec_plus(fn)
        else:
            parsed = util.format_argspec_plus(fn, grouped=grouped)
        eq_(parsed, wanted)

    test(lambda: None,
         {'args': '()', 'self_arg': None,
          'apply_kw': '()', 'apply_pos': '()' })

    test(lambda: None,
         {'args': '', 'self_arg': None,
          'apply_kw': '', 'apply_pos': '' },
         grouped=False)

    test(lambda self: None,
         {'args': '(self)', 'self_arg': 'self',
          'apply_kw': '(self)', 'apply_pos': '(self)' })

    test(lambda self: None,
         {'args': 'self', 'self_arg': 'self',
          'apply_kw': 'self', 'apply_pos': 'self' },
         grouped=False)

    test(lambda *a: None,
         {'args': '(*a)', 'self_arg': 'a[0]',
          'apply_kw': '(*a)', 'apply_pos': '(*a)' })

    test(lambda **kw: None,
         {'args': '(**kw)', 'self_arg': None,
          'apply_kw': '(**kw)', 'apply_pos': '(**kw)' })

    test(lambda *a, **kw: None,
         {'args': '(*a, **kw)', 'self_arg': 'a[0]',
          'apply_kw': '(*a, **kw)', 'apply_pos': '(*a, **kw)' })

    test(lambda a, *b: None,
         {'args': '(a, *b)', 'self_arg': 'a',
          'apply_kw': '(a, *b)', 'apply_pos': '(a, *b)' })

    test(lambda a, **b: None,
         {'args': '(a, **b)', 'self_arg': 'a',
          'apply_kw': '(a, **b)', 'apply_pos': '(a, **b)' })

    test(lambda a, *b, **c: None,
         {'args': '(a, *b, **c)', 'self_arg': 'a',
          'apply_kw': '(a, *b, **c)', 'apply_pos': '(a, *b, **c)' })

    test(lambda a, b=1, **c: None,
         {'args': '(a, b=1, **c)', 'self_arg': 'a',
          'apply_kw': '(a, b=b, **c)', 'apply_pos': '(a, b, **c)' })

    test(lambda a=1, b=2: None,
         {'args': '(a=1, b=2)', 'self_arg': 'a',
          'apply_kw': '(a=a, b=b)', 'apply_pos': '(a, b)' })

    test(lambda a=1, b=2: None,
         {'args': 'a=1, b=2', 'self_arg': 'a',
          'apply_kw': 'a=a, b=b', 'apply_pos': 'a, b' },
         grouped=False)



def test_symbols():
    sym1 = util.symbol('foo')
    assert sym1.name == 'foo'
    sym2 = util.symbol('foo')

    assert sym1 is sym2
    assert sym1 == sym2

    sym3 = util.symbol('bar')
    assert sym1 is not sym3
    assert sym1 != sym3

    assert repr(sym3) == 'bar'

def test_symbol_pickle():
    import pickle
    try:
        import cPickle
    except ImportError:
        cPickle = pickle

    for mod in pickle, cPickle:
        sym1 = util.symbol('foo')
        sym2 = util.symbol('foo')

        assert sym1 is sym2

        # default
        s = pickle.dumps(sym1)
        sym3 = pickle.loads(s)

        for protocol in 0, 1, 2:
            serial = pickle.dumps(sym1)
            rt = pickle.loads(serial)
            assert rt is sym1
            assert rt is sym2

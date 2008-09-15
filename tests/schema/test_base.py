from nose.tools import eq_, assert_raises

from flatland.schema import base


def test_schema_naming():
    for arg in (u'unicode', 'sysencoding', None):
        s = base.Schema(arg)
        eq_(s.name, arg)
        eq_(s.label, arg)

    for arg in (u'unicode', 'sysencoding', None):
        s = base.Schema(arg, label=u'fleem')
        eq_(s.name, arg)
        eq_(s.label, u'fleem')

def test_schema_validators():
    """Validators may be inherited or supplied at construction."""

    s = base.Schema(None)
    assert not s.validators

    s = base.Schema(None, validators=(123, 456))
    eq_(s.validators, [123, 456])

    s = base.Schema(None, validators=xrange(3))
    eq_(s.validators, list(xrange(3)))

    canary = object()
    s = base.Schema(None, default=canary)
    assert s.default is canary

def test_schema_optional():
    """Required is the default."""

    s = base.Schema(None)
    assert not s.optional

    s = base.Schema(None, optional=False)
    assert not s.optional

    s = base.Schema(None, optional=True)
    assert s.optional

def test_node():

    s = base.Schema(u'abc', label=u'ABC')
    n = s.node()

    eq_(n.name, u'abc')
    eq_(n.label, u'ABC')
    eq_(n.errors, [])
    eq_(n.warnings, [])
    eq_(n.path, (u'abc',))
    eq_(n.root, n)
    eq_(n.fq_name(), u'abc')

def test_node_abstract():
    s = base.Schema(None)
    n = s.node()

    assert_raises(NotImplementedError, n.set, None)
    assert_raises(NotImplementedError, n.set_flat, ())

def test_node_validation():
    ok = lambda item, data: True
    not_ok = lambda item, data: False

    for res, validators in ((True, (ok,)),
                            (True, (ok, ok)),
                            (False, (not_ok,)),
                            (False, (ok, not_ok,)),
                            (False, (ok, not_ok, ok,))):
        s = base.Schema(None, validators=validators)
        n = s.node()
        assert bool(n.validate()) is res

    node = None
    def got_node(item, data):
        assert item is node, repr(item)
        return True
    s = base.Schema(None, validators=(got_node,))
    node = s.node()
    node.validate()

def test_node_validator_return():
    """Validator returns don't have to be actual bool() instances."""

    class Bool(object):
        def __init__(self, val):
            self.val = val
        def __nonzero__(self):
            return bool(self.val)

    # mostly we care about allowing None for False
    true = lambda *a: True
    one = lambda *a: 1
    yes = lambda *a: Bool(True)

    false = lambda *a: False
    zero = lambda *a: 0
    none = lambda *a: None
    no = lambda *a: Bool(False)

    for validator in true, one, yes:
        s = base.Schema(None, validators=(validator,))
        n = s.node()
        assert n.validate()

    for validator in false, zero, none, no:
        s = base.Schema(None, validators=(validator,))
        n = s.node()
        assert not n.validate()

def XXXtest_simple_nesting():
    # no, nesting is not so easily fooled
    s1 = base.Schema(u'1')
    s2 = base.Schema(u'2')
    s3a = base.Schema(u'3a')
    s3b = base.Schema(u'3b')

    n1 = s1.node()
    n2 = s2.node(parent=n1)
    n3a = s3a.node(parent=n2)
    n3b = s3b.node(parent=n2)

    eq_(n1.path, (u'1',))
    eq_(n2.path, (u'1', u'2',))
    eq_(n3a.path, (u'1', u'2', u'3a'))
    eq_(n3b.path, (u'1', u'2', u'3b'))

    eq_(n1.root, n1)
    eq_(n2.root, n1)
    eq_(n3a.root, n1)
    eq_(n3b.root, n1)

    eq_(n1.fq_name(), u'1')
    eq_(n2.fq_name(), u'1_2')
    eq_(n3a.fq_name(), u'1_2_3a')
    eq_(n3b.fq_name(), u'1_2_3b')

    eq_(n1.el('1'), n1)
    eq_(n1.el('1.2'), n2)
    eq_(n1.el('1.2.3a'), n3a)
    assert_raises(KeyError, n1.el, '1.2.3a.4')

    eq_(n2.el('2.3b'), n3b)
    assert_raises(KeyError, n1.el, '1.2')

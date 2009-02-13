from flatland.schema import base
from tests._util import eq_, assert_raises


def test_schema_naming():
    for arg in (u'unicode', 'sysencoding', None):
        s = base.FieldSchema(arg)
        eq_(s.name, arg)
        eq_(s.label, arg)

    for arg in (u'unicode', 'sysencoding', None):
        s = base.FieldSchema(arg, label=u'fleem')
        eq_(s.name, arg)
        eq_(s.label, u'fleem')

def test_schema_validators():
    """Validators may be inherited or supplied at construction."""

    s = base.FieldSchema(None)
    assert not s.validators

    s = base.FieldSchema(None, validators=(123, 456))
    eq_(s.validators, [123, 456])

    s = base.FieldSchema(None, validators=xrange(3))
    eq_(s.validators, list(xrange(3)))

    canary = object()
    s = base.FieldSchema(None, default=canary)
    assert s.default is canary

def test_schema_optional():
    """Required is the default."""

    s = base.FieldSchema(None)
    assert not s.optional

    s = base.FieldSchema(None, optional=False)
    assert not s.optional

    s = base.FieldSchema(None, optional=True)
    assert s.optional

def test_element():
    s = base.FieldSchema(u'abc', label=u'ABC')
    n = s.new()

    eq_(n.name, u'abc')
    eq_(n.label, u'ABC')
    eq_(n.errors, [])
    eq_(n.warnings, [])
    eq_(tuple(el.name for el in n.path), (u'abc',))
    eq_(n.root, n)
    eq_(n.flattened_name(), u'abc')

def test_element_message_buckets():
    s = base.FieldSchema(u'abc', label=u'ABC')
    n = s.new()

    n.add_error('error')
    eq_(n.errors, ['error'])
    n.add_error('error')
    eq_(n.errors, ['error'])

    n.add_warning('warning')
    eq_(n.warnings, ['warning'])
    n.add_warning('warning')
    eq_(n.warnings, ['warning'])

def test_element_abstract():
    s = base.FieldSchema(None)
    n = s.new()

    assert_raises(NotImplementedError, n.set, None)
    assert_raises(NotImplementedError, n.set_flat, ())
    assert_raises(NotImplementedError, n.el, 'foo')
    assert_raises(NotImplementedError, n.el, 'abc')

def test_element_validation():
    ok = lambda item, data: True
    not_ok = lambda item, data: False
    none = lambda item, data: None
    skip_ok = lambda item, data: base.AllTrue
    skip_not_ok = lambda item, data: base.AllFalse

    for res, validators in ((True, (ok,)),
                            (True, (ok, ok)),
                            (True, (skip_ok,)),
                            (True, (skip_ok, not_ok)),
                            (False, (none,)),
                            (False, (ok, none)),
                            (False, (not_ok,)),
                            (False, (ok, not_ok,)),
                            (False, (ok, not_ok, ok,)),
                            (False, (skip_not_ok,)),
                            (False, (ok, skip_not_ok, ok))):
        s = base.FieldSchema(None, validators=validators)
        n = s.new()
        valid = n.validate()
        assert valid == res
        assert bool(valid) is res

    element = None
    def got_element(item, data):
        assert item is element, repr(item)
        return True
    s = base.FieldSchema(None, validators=(got_element,))
    element = s.new()
    element.validate()

def test_element_validator_return():
    """Validator returns can be bool, int or None."""

    class Bool(object):
        """A truthy object that does not implement __and__"""
        def __init__(self, val):
            self.val = val
        def __nonzero__(self):
            return bool(self.val)

    # mostly we care about allowing None for False
    true = lambda *a: True
    alltrue = lambda *a: base.AllTrue
    one = lambda *a: 1

    false = lambda *a: False
    allfalse = lambda *a: base.AllFalse
    zero = lambda *a: 0
    none = lambda *a: None
    no = lambda *a: Bool(False)

    for validator in true, one, alltrue:
        s = base.FieldSchema(None, validators=(validator,))
        n = s.new()
        assert n.validate()

    for validator in false, zero, none, allfalse:
        s = base.FieldSchema(None, validators=(validator,))
        n = s.new()
        assert not n.validate()

    for validator in [no]:
        s = base.FieldSchema(None, validators=(validator,))
        n = s.new()
        assert_raises(TypeError, n.validate)


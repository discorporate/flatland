from flatland import (
    Element,
    Skip,
    SkipAll,
    SkipAllFalse,
    Unevaluated,
    )

from tests._util import assert_raises, eq_, requires_unicode_coercion


@requires_unicode_coercion
def test_naming():
    for arg in (u'unicode', 'sysencoding', None):
        schema = Element.named(arg)
        eq_(schema.name, arg)
        eq_(schema.label, arg)

    for arg in (u'unicode', 'sysencoding', None):
        schema = Element.named(arg).using(label=u'fleem')
        eq_(schema.name, arg)
        eq_(schema.label, u'fleem')


def test_validators():
    # Validators may be inherited or supplied at construction.
    el = Element()
    assert not el.validators

    # argument is transformed into a list copy
    el = Element(validators=(123, 456))
    eq_(el.validators, [123, 456])

    el = Element(validators=xrange(3))
    eq_(el.validators, list(xrange(3)))

    schema = Element.using(validators=xrange(3))
    eq_(schema.validators, list(xrange(3)))


def test_dsl_validated_by():
    s = Element.using(validators=(123, 456))
    eq_(s.validators, [123, 456])

    s = Element.validated_by(123, 456)
    eq_(s.validators, [123, 456])

    s = Element.using(validators=(123, 456)).validated_by(789)
    eq_(s.validators, [789])

    assert_raises(TypeError, Element.validated_by, int)


def test_dsl_including_validators():
    base = Element.validated_by(1, 2, 3)
    eq_(base.validators, [1, 2, 3])

    s = base.including_validators(4, 5, 6)
    eq_(s.validators, [1, 2, 3, 4, 5, 6])

    s = base.including_validators(4, 5, 6, position=0)
    eq_(s.validators, [4, 5, 6, 1, 2, 3])

    s = base.including_validators(4, 5, 6, position=1)
    eq_(s.validators, [1, 4, 5, 6, 2, 3])

    s = base.including_validators(4, 5, 6, position=-2)
    eq_(s.validators, [1, 2, 4, 5, 6, 3])

    s = Element.including_validators(1)
    eq_(s.validators, [1])


def test_optional():
    # Required is the default.
    el = Element()
    assert not el.optional

    el = Element(optional=True)
    assert el.optional

    el = Element(optional=False)
    assert not el.optional


def test_label():
    # .label fallback to .name works for instances and classes
    for item in Element.named(u'x'), Element.named(u'x')(), Element(name=u'x'):
        assert item.label == u'x'

    for item in (Element.using(name=u'x', label=u'L'),
                 Element.using(name=u'x', label=u'L')(),
                 Element(name=u'x', label=u'L')):
        assert item.label == u'L'


def test_instance_defaults():
    el = Element()

    eq_(el.name, None)
    eq_(el.label, None)
    eq_(el.optional, False)
    eq_(el.default, None)
    eq_(el.default_factory, None)
    eq_(el.default_value, None)
    eq_(el.validators, ())
    eq_(el.valid, Unevaluated)
    eq_(el.errors, [])
    eq_(el.warnings, [])
    eq_(tuple(_.name for _ in el.path), (None,))
    eq_(el.parent, None)
    eq_(el.root, el)
    eq_(el.flattened_name(), u'')
    eq_(el.value, None)
    eq_(el.u, u'')


def test_abstract():
    element = Element()

    assert_raises(NotImplementedError, element.set, None)
    assert_raises(NotImplementedError, element.set_flat, ())
    assert_raises(NotImplementedError, element.el, u'foo')


def test_message_buckets():
    el = Element()

    el.add_error('error')
    eq_(el.errors, ['error'])
    el.add_error('error')
    eq_(el.errors, ['error'])
    el.add_error('error2')
    eq_(el.errors, ['error', 'error2'])

    el.add_warning('warning')
    eq_(el.warnings, ['warning'])
    el.add_warning('warning')
    eq_(el.warnings, ['warning'])


def test_validation():
    ok = lambda item, data: True
    not_ok = lambda item, data: False
    none = lambda item, data: None
    skip = lambda item, data: Skip
    all_ok = lambda item, data: SkipAll
    all_not_ok = lambda item, data: SkipAllFalse

    for res, validators in ((True, (ok,)),
                            (True, (ok, ok)),
                            (True, (skip,)),
                            (True, (skip, not_ok)),
                            (True, (ok, skip, not_ok)),
                            (True, (all_ok,)),
                            (True, (all_ok, not_ok)),
                            (False, (none,)),
                            (False, (ok, none)),
                            (False, (not_ok,)),
                            (False, (ok, not_ok,)),
                            (False, (ok, not_ok, ok,)),
                            (False, (all_not_ok,)),
                            (False, (ok, all_not_ok, ok))):
        el = Element(validators=validators, validates_down='validators')
        valid = el.validate()
        assert valid == res
        assert bool(valid) is res
        assert el.valid is res
        assert el.all_valid is res

    element = None

    def got_element(item, data):
        assert item is element, repr(item)
        return True
    element = Element(validators=(got_element,), validates_down='validators')
    assert element.validate()


def test_validator_return():
    # Validator returns can be bool, int or None.

    class Bool(object):
        """A truthy object that does not implement __and__"""

        def __init__(self, val):
            self.val = val

        def __nonzero__(self):
            return bool(self.val)

    Validatable = Element.using(validates_down='validators')

    # mostly we care about allowing None for False
    true = lambda *a: True
    skip = lambda *a: Skip
    skipall = lambda *a: SkipAll
    one = lambda *a: 1

    false = lambda *a: False
    skipallfalse = lambda *a: SkipAllFalse
    zero = lambda *a: 0
    none = lambda *a: None
    no = lambda *a: Bool(False)

    for validator in true, one, skip, skipall:
        el = Validatable(validators=(validator,))
        assert el.validate()

    for validator in false, zero, none, skipallfalse:
        el = Validatable(validators=(validator,))
        assert not el.validate()

    for validator in [no]:
        el = Validatable(validators=(validator,))
        assert_raises(TypeError, el.validate)


def test_default_value():
    el = Element()
    assert el.default_value is None

    el = Element(default='abc')
    assert el.default_value == 'abc'

    el = Element(default_factory=lambda x: 'def')
    assert el.default_value == 'def'

    el = Element(default='ghi', default_factory=lambda x: 'jkl')
    assert el.default_value == 'jkl'

    # a default_factory may reference el.default
    el = Element(default='mno', default_factory=lambda x: x.default)
    assert el.default_value == 'mno'

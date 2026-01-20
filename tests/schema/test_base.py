from flatland import (
    Element,
    Skip,
    SkipAll,
    SkipAllFalse,
    Unevaluated,
)

import pytest
from tests._util import requires_unicode_coercion


def test_cloning():
    new_element = Element.named("x")
    assert isinstance(new_element, type)
    assert new_element.__module__ != Element.__module__
    assert "test_base" in new_element.__module__


@requires_unicode_coercion
def test_naming():
    for arg in ("unicode", "sysencoding", None):
        schema = Element.named(arg)
        assert schema.name == arg
        assert schema.label == arg

    for arg in ("unicode", "sysencoding", None):
        schema = Element.named(arg).using(label="fleem")
        assert schema.name == arg
        assert schema.label == "fleem"


def test_validators():
    # Validators may be inherited or supplied at construction.
    el = Element()
    assert not el.validators

    # argument is transformed into a list copy
    el = Element(validators=(123, 456))
    assert el.validators == [123, 456]

    el = Element(validators=range(3))
    assert el.validators == list(range(3))

    schema = Element.using(validators=range(3))
    assert schema.validators == list(range(3))


def test_dsl_validated_by():
    s = Element.using(validators=(123, 456))
    assert s.validators == [123, 456]

    s = Element.validated_by(123, 456)
    assert s.validators == [123, 456]

    s = Element.using(validators=(123, 456)).validated_by(789)
    assert s.validators == [789]

    with pytest.raises(TypeError):
        Element.validated_by(int)


def test_dsl_including_validators():
    base = Element.validated_by(1, 2, 3)
    assert base.validators == [1, 2, 3]

    s = base.including_validators(4, 5, 6)
    assert s.validators == [1, 2, 3, 4, 5, 6]

    s = base.including_validators(4, 5, 6, position=0)
    assert s.validators == [4, 5, 6, 1, 2, 3]

    s = base.including_validators(4, 5, 6, position=1)
    assert s.validators == [1, 4, 5, 6, 2, 3]

    s = base.including_validators(4, 5, 6, position=-2)
    assert s.validators == [1, 2, 4, 5, 6, 3]

    s = Element.including_validators(1)
    assert s.validators == [1]


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
    for item in Element.named("x"), Element.named("x")(), Element(name="x"):
        assert item.label == "x"

    for item in (
        Element.using(name="x", label="L"),
        Element.using(name="x", label="L")(),
        Element(name="x", label="L"),
    ):
        assert item.label == "L"


def test_instance_defaults():
    el = Element()

    assert el.name == None
    assert el.label == None
    assert el.optional == False
    assert el.default == None
    assert el.default_factory == None
    assert el.default_value == None
    assert el.validators == ()
    assert el.valid == Unevaluated
    assert el.errors == []
    assert el.warnings == []
    assert tuple(_.name for _ in el.path) == (None,)
    assert el.parent == None
    assert el.root == el
    assert el.flattened_name() == ""
    assert el.value == None
    assert el.u == ""


def test_abstract():
    element = Element()
    with pytest.raises(NotImplementedError):
        element.set(None)
    with pytest.raises(NotImplementedError):
        element.set_flat(())
    with pytest.raises(NotImplementedError):
        element.find_one("foo")


def test_message_buckets():
    el = Element()

    el.add_error("error")
    assert el.errors == ["error"]
    el.add_error("error")
    assert el.errors == ["error"]
    el.add_error("error2")
    assert el.errors == ["error", "error2"]

    el.add_warning("warning")
    assert el.warnings == ["warning"]
    el.add_warning("warning")
    assert el.warnings == ["warning"]


def test_validation():
    ok = lambda item, data: True
    not_ok = lambda item, data: False
    none = lambda item, data: None
    skip = lambda item, data: Skip
    all_ok = lambda item, data: SkipAll
    all_not_ok = lambda item, data: SkipAllFalse

    for res, validators in (
        (True, (ok,)),
        (True, (ok, ok)),
        (True, (skip,)),
        (True, (skip, not_ok)),
        (True, (ok, skip, not_ok)),
        (True, (all_ok,)),
        (True, (all_ok, not_ok)),
        (False, (none,)),
        (False, (ok, none)),
        (False, (not_ok,)),
        (
            False,
            (
                ok,
                not_ok,
            ),
        ),
        (
            False,
            (
                ok,
                not_ok,
                ok,
            ),
        ),
        (False, (all_not_ok,)),
        (False, (ok, all_not_ok, ok)),
    ):
        el = Element(validators=validators, validates_down="validators")
        valid = el.validate()
        assert valid == res
        assert bool(valid) is res
        assert el.valid is res
        assert el.all_valid is res

    element = None

    def got_element(item, data):
        assert item is element, repr(item)
        return True

    element = Element(validators=(got_element,), validates_down="validators")
    assert element.validate()


def test_validator_return():
    # Validator returns can be bool, int or None.

    class Bool:
        """A truthy object that does not implement __and__"""

        def __init__(self, val):
            self.val = val

        def __bool__(self):
            return bool(self.val)

        __nonzero__ = __bool__

    Validatable = Element.using(validates_down="validators")

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
        with pytest.raises(TypeError):
            el.validate()


def test_default_value():
    el = Element()
    assert el.default_value is None

    el = Element(default="abc")
    assert el.default_value == "abc"

    el = Element(default_factory=lambda x: "def")
    assert el.default_value == "def"

    el = Element(default="ghi", default_factory=lambda x: "jkl")
    assert el.default_value == "jkl"

    # a default_factory may reference el.default
    el = Element(default="mno", default_factory=lambda x: x.default)
    assert el.default_value == "mno"


def test_xml_helpers():
    el = Element()

    el.u = '<foo\t&\r\n"bar">'

    assert el.x == '&lt;foo\t&amp;\r\n"bar"&gt;'
    assert el.xa == "&lt;foo&#9;&amp;&#13;&#10;&quot;bar&quot;&gt;"

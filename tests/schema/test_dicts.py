from flatland import (
    Dict,
    Integer,
    String,
    SparseDict,
    Unset,
    element_set,
)
from flatland.util import Unspecified, keyslice_pairs

import pytest
from tests._util import (
    asciistr,
    udict,
    unicode_coercion_available,
)


def test_dict():
    with pytest.raises(TypeError):
        Dict()


def test_dict_immutable_keys():
    schema = Dict.of(Integer.named("x"), Integer.named("y"))
    el = schema()

    with pytest.raises(TypeError):
        el.__setitem__("z", 123)
    with pytest.raises(TypeError):
        el.__delitem__("x")
    with pytest.raises(KeyError):
        el.__delitem__("z")
    with pytest.raises(TypeError):
        el.setdefault("x", 123)
    with pytest.raises(TypeError):
        el.setdefault("z", 123)
    with pytest.raises(TypeError):
        el.pop("x")
    with pytest.raises(KeyError):
        el.pop("z")
    with pytest.raises(TypeError):
        el.popitem()
    with pytest.raises(TypeError):
        el.clear()


def test_dict_reads():
    schema = Dict.of(Integer.named("x"), Integer.named("y"))
    el = schema()

    el["x"].set("10")
    el["y"].set("20")

    assert el["x"].value == 10
    assert el["y"].value == 20

    # the values are unhashable Elements, so this is a little painful
    assert set(el.keys()) == set("xy")
    assert {("x", 10), ("y", 20)} == {(_[0], _[1].value) for _ in el.items()}
    assert {10, 20} == {_.value for _ in el.values()}

    assert el.get("x").value == 10
    el["x"] = None
    assert el.get("x").value == None
    assert el.get("x", "default is never used").value == None

    with pytest.raises(KeyError):
        el.get("z")
    with pytest.raises(KeyError):
        el.get("z", "even with a default")


def test_dict_update():
    schema = Dict.of(Integer.named("x"), Integer.named("y"))
    el = schema()

    def value_dict(element):
        return {k: v.value for k, v in element.items()}

    try:
        el.update(x=20, y=30)
    except UnicodeError:
        assert not unicode_coercion_available()
        el.update(udict(x=20, y=30))
    assert udict(x=20, y=30) == el.value

    el.update({"y": 40})
    assert udict(x=20, y=40) == el.value

    el.update()
    assert udict(x=20, y=40) == el.value

    el.update((_, 100) for _ in "xy")
    assert udict(x=100, y=100) == el.value

    try:
        el.update([("x", 1)], y=2)
        assert udict(x=1, y=2) == el.value
    except UnicodeError:
        assert not unicode_coercion_available()

    try:
        el.update([("x", 10), ("y", 10)], x=20, y=20)
        assert udict(x=20, y=20) == el.value
    except UnicodeError:
        assert not unicode_coercion_available()

    if unicode_coercion_available():
        with pytest.raises(TypeError):
            el.update(z=1)
        with pytest.raises(TypeError):
            el.update(x=1, z=1)
    with pytest.raises(TypeError):
        el.update({"z": 1})
    with pytest.raises(TypeError):
        el.update({"x": 1, "z": 1})
    with pytest.raises(TypeError):
        el.update((("z", 1),))
    with pytest.raises(TypeError):
        el.update((("x", 1), ("z", 1)))


class DictSetTest:
    schema = Dict
    policy = Unspecified
    x_default = Unspecified
    y_default = Unspecified

    def new_schema(self):
        dictkw, x_kw, y_kw = {}, {}, {}
        if self.policy is not Unspecified:
            dictkw["policy"] = self.policy
        if self.x_default is not Unspecified:
            x_kw["default"] = self.x_default
        if self.y_default is not Unspecified:
            y_kw["default"] = self.y_default

        return (
            self.schema.named("s")
            .using(**dictkw)
            .of(Integer.named("x").using(**x_kw), Integer.named("y").using(**y_kw))
        )

    def new_element(self, schema=Unspecified, **kw):
        if schema is Unspecified:
            schema = self.new_schema()
        return schema(**kw)

    def test_empty_sets(self):
        wanted = {"x": None, "y": None}

        el = self.new_element()
        assert el.value == wanted

        el.set({})
        assert el.value == wanted

        el = self.new_element(value={})
        assert el.value == wanted

        el = self.new_element(value=iter(()))
        assert el.value == wanted

        el = self.new_element(value=())
        assert el.value == wanted

    def test_empty_set_flat(self):
        el = self.new_element()
        el.set_flat(())
        assert el.value == {"x": None, "y": None}

    def test_half_set(self):
        wanted = {"x": 123, "y": None}

        el = self.new_element()
        el.set({"x": 123})
        assert el.value == wanted

        el = self.new_element()
        el.set([("x", 123)])
        assert el.value == wanted

    def test_half_set_flat(self):
        wanted = {"x": 123, "y": None}

        pairs = (("s_x", "123"),)
        el = self.new_element()
        el.set_flat(pairs)
        assert el.value == wanted

    def test_full_set(self):
        wanted = {"x": 101, "y": 102}

        el = self.new_element()
        el.set(wanted)
        assert el.value == wanted

        el = self.new_element()
        el.set(udict(x=101, y=102))
        assert el.value == wanted

        el = self.new_element()
        el.set([("x", 101), ("y", 102)])
        assert el.value == wanted

        el = self.new_element(value=wanted)
        assert el.value == wanted

    def test_full_set_flat(self):
        wanted = {"x": 101, "y": 102}
        pairs = (("s_x", "101"), ("s_y", "102"))

        el = self.new_element()
        el.set_flat(pairs)
        assert el.value == wanted

    def test_scalar_set_flat(self):
        wanted = {"x": None, "y": None}
        pairs = (("s", "xxx"),)

        el = self.new_element()

        canary = []

        def setter(self, value):
            canary.append(value)
            return type(el).set(self, value)

        el.set = setter.__get__(el, type(el))
        el.set_flat(pairs)
        assert el.value == wanted
        assert canary == []

    def test_over_set(self):
        too_much = {"x": 1, "y": 2, "z": 3}

        el = self.new_element()
        with pytest.raises(KeyError):
            el.set(too_much)
        with pytest.raises(KeyError):
            self.new_element(value=too_much)

    def test_over_set_flat(self):
        wanted = {"x": 123, "y": None}

        pairs = (("s_x", "123"), ("s_z", "nope"))
        el = self.new_element()
        el.set_flat(pairs)
        assert el.value == wanted

    def test_total_miss(self):
        miss = {"z": 3}

        el = self.new_element()
        with pytest.raises(KeyError):
            el.set(miss)
        with pytest.raises(KeyError):
            self.new_element(value=miss)

    def test_total_miss_flat(self):
        pairs = (("miss", "10"),)

        el = self.new_element()
        el.set_flat(pairs)
        assert el.value == {"x": None, "y": None}

    def test_set_return(self):
        el = self.new_element()
        assert el.set({"x": 1, "y": 2})

        el = self.new_element()
        assert not el.set({"x": "i am the new", "y": "number two"})

    def test_set_default(self):
        wanted = {"x": 11, "y": 12}
        schema = self.new_schema()
        schema.default = wanted

        el = schema()
        el.set_default()
        assert el.value == wanted

    def test_set_default_from_children(self):
        el = self.new_element()
        el.set_default()

        wanted = {
            "x": self.x_default if self.x_default is not Unspecified else None,
            "y": self.y_default if self.y_default is not Unspecified else None,
        }
        assert el.value == wanted


class TestEmptyDictSet(DictSetTest):
    pass


class TestDefaultDictSet(DictSetTest):
    x_default = 10
    y_default = 20


class TestEmptySparseDictRequiredSet(DictSetTest):
    schema = SparseDict.using(minimum_fields="required")


def test_dict_valid_policies():
    schema = Dict.of(Integer)
    el = schema()

    with pytest.raises(RuntimeError):
        el.set({}, policy="bogus")


def test_dict_strict():
    # a mini test, this policy thing may get whacked
    schema = Dict.using(policy="strict").of(Integer.named("x"), Integer.named("y"))

    el = schema({"x": 123, "y": 456})

    el = schema()
    with pytest.raises(TypeError):
        el.set({"x": 123})

    el = schema()
    with pytest.raises(KeyError):
        el.set({"x": 123, "y": 456, "z": 7})


def test_dict_raw():
    schema = Dict.of(Integer.named("x").using(optional=False))
    el = schema()
    assert el.raw is Unset

    el = schema({"x": "bar"})
    assert el.raw == {"x": "bar"}

    el = schema([("x", "bar")])
    assert el.raw == [("x", "bar")]
    el.set_flat([("x", "123")])
    assert el.raw is Unset

    el = schema.from_flat([("x", "123")])
    assert el.raw is Unset
    assert el["x"].raw == "123"


def test_dict_set_signal():
    data = []
    sentinel = lambda sender, adapted: data.append((sender, adapted))

    schema = Dict.of(Integer.named("x"))
    schema({"x": 0})

    with element_set.connected_to(sentinel):
        schema({"x": 1})
        schema({"x": "bogus"})

    assert len(data) == 4  # Integer, Dict, Integer, Dict
    assert data[1][0].value == {"x": 1}
    assert data[1][1] is True

    assert data[2][0].raw == "bogus"
    assert data[2][1] is False

    assert data[3][1] is False


def test_dict_as_unicode():
    schema = Dict.of(Integer.named("x"), Integer.named("y"))
    el = schema({"x": 1, "y": 2})

    assert el.u in ("{'x': '1', 'y': '2'}", "{'y': '2', 'x': '1'}")


def test_nested_dict_as_unicode():
    schema = Dict.of(Dict.named("d").of(Integer.named("x").using(default=10)))
    el = schema.from_defaults()

    assert el.value == {"d": {"x": 10}}
    assert el.u == "{'d': {'x': '10'}}"


def test_nested_unicode_dict_as_unicode():
    schema = Dict.of(
        Dict.named("d").of(String.named("x").using(default="\u2308\u2309"))
    )
    el = schema.from_defaults()
    assert el.value == {"d": {"x": "\u2308\u2309"}}
    assert el.u == "{'d': {'x': '\u2308\u2309'}}"


def test_dict_find():
    # stub
    schema = Dict.named("s").of(Integer.named("x"), Integer.named("y"))
    element = schema()

    assert element.find_one("x").name == "x"
    assert element.find_one("/x").name == "x"
    with pytest.raises(LookupError):
        element.find_one("not_x")


def test_update_object():

    class Obj:

        def __init__(self, **kw):
            for k, v in kw.items():
                setattr(self, k, v)

    schema = Dict.of(String.named("x"), String.named("y"))

    o = Obj()
    assert not hasattr(o, "x")
    assert not hasattr(o, "y")

    def updated_(obj_factory, initial_value, wanted=None, **update_kw):
        el = schema(initial_value)
        obj = obj_factory()
        keyfunc = lambda x: x
        update_kw.setdefault("key", keyfunc)
        el.update_object(obj, **update_kw)
        if wanted is None:
            wanted = {keyfunc(k): v for k, v in initial_value.items()}
        have = dict(obj.__dict__)
        assert have == wanted

    updated_(Obj, {"x": "X", "y": "Y"})
    updated_(Obj, {"x": "X"}, {"x": "X", "y": None})
    updated_(lambda: Obj(y="Y"), {"x": "X"}, {"x": "X", "y": None})
    updated_(lambda: Obj(y="Y"), {"x": "X"}, {"x": "X", "y": "Y"}, omit=("y",))
    updated_(lambda: Obj(y="Y"), {"x": "X"}, {"y": "Y"}, include=("z",))
    updated_(Obj, {"x": "X"}, {"y": None, "z": "X"}, rename=(("x", "z"),))


def test_slice():
    schema = Dict.of(String.named("x"), String.named("y"))

    def same_(source, kw):
        el = schema(source)

        sliced = el.slice(**kw)
        wanted = dict(keyslice_pairs(el.value.items(), **kw))

        assert sliced == wanted
        assert {type(_) for _ in sliced.keys()} == {type(_) for _ in wanted.keys()}

    same_({"x": "X", "y": "Y"}, {})
    same_({"x": "X", "y": "Y"}, dict(key=asciistr))
    same_({"x": "X", "y": "Y"}, dict(include=["x"]))
    same_({"x": "X", "y": "Y"}, dict(omit=["x"]))
    same_({"x": "X", "y": "Y"}, dict(omit=["x"], rename={"y": "z"}))


def test_sparsedict_key_mutability():
    schema = SparseDict.of(Integer.named("x"), Integer.named("y"))
    el = schema()

    ok, bogus = "x", "z"

    el[ok] = 123
    assert el[ok].value == 123
    with pytest.raises(TypeError):
        el.__setitem__(bogus, 123)

    del el[ok]
    assert ok not in el
    with pytest.raises(TypeError):
        el.__delitem__(bogus)

    assert el.setdefault(ok, 456)
    with pytest.raises(TypeError):
        el.setdefault(bogus, 456)

    el[ok] = 123
    assert el.pop(ok)
    with pytest.raises(KeyError):
        el.pop(bogus)

    with pytest.raises(NotImplementedError):
        el.popitem()
    el.clear()
    assert not el


def test_sparsedict_operations():
    schema = SparseDict.of(Integer.named("x"), Integer.named("y"))
    el = schema()

    el["x"] = 123
    del el["x"]
    with pytest.raises(KeyError):
        el.__delitem__("x")

    assert el.setdefault("x", 123) == 123
    assert el.setdefault("x", 456) == 123

    assert el.setdefault("y", 123) == 123
    assert el.setdefault("y", 456) == 123

    assert schema().is_empty
    assert not schema().validate()

    opt_schema = schema.using(optional=True)
    assert opt_schema().validate()


def test_sparsedict_required_operations():
    schema = SparseDict.using(minimum_fields="required").of(
        Integer.named("opt").using(optional=True), Integer.named("req")
    )

    el = schema({"opt": 123, "req": 456})

    del el["opt"]
    with pytest.raises(KeyError):
        el.__delitem__("opt")
    with pytest.raises(TypeError):
        el.__delitem__("req")

    el = schema()
    assert el.setdefault("opt", 123) == 123
    assert el.setdefault("opt", 456) == 123

    assert el.setdefault("req", 123) == 123
    assert el.setdefault("req", 456) == 123

    assert not schema().is_empty
    assert not schema().validate()


def test_sparsedict_set_default():
    schema = SparseDict.of(Integer.named("x").using(default=123), Integer.named("y"))
    el = schema()

    el.set_default()
    assert el.value == {}


def test_sparsedict_required_set_default():
    schema = SparseDict.using(minimum_fields="required").of(
        Integer.named("x").using(default=123),
        Integer.named("y").using(default=456, optional=True),
        Integer.named("z").using(optional=True),
    )
    el = schema()

    el.set_default()
    assert el.value == {"x": 123}


def test_sparsedict_bogus_set_default():
    schema = SparseDict.using(minimum_fields="bogus").of(Integer.named("x"))
    el = schema()
    with pytest.raises(RuntimeError):
        el.set_default()


def test_sparsedict_required_key_mutability():
    schema = SparseDict.of(
        Integer.named("x").using(optional=True), Integer.named("y")
    ).using(minimum_fields="required")
    el = schema()
    ok, required, bogus = "x", "y", "z"

    assert ok not in el
    assert required in el
    assert bogus not in el

    el[ok] = 123
    assert el[ok].value == 123
    el[required] = 456
    assert el[required].value == 456
    with pytest.raises(TypeError):
        el.__setitem__(bogus, 123)

    del el[ok]
    assert ok not in el
    with pytest.raises(TypeError):
        el.__delitem__(required)
    with pytest.raises(TypeError):
        el.__delitem__(bogus)

    assert el.setdefault(ok, 456)
    assert el.setdefault(required, 789)
    with pytest.raises(TypeError):
        el.setdefault(bogus, 456)

    el[ok] = 123
    assert el.pop(ok)
    el[required] = 456
    with pytest.raises(TypeError):
        el.pop(required)
    with pytest.raises(KeyError):
        el.pop(bogus)

    with pytest.raises(NotImplementedError):
        el.popitem()

    el.clear()
    assert list(el.keys()) == [required]


def test_sparsedict_from_flat():
    schema = SparseDict.of(Integer.named("x"), Integer.named("y"))

    el = schema.from_flat([])
    assert list(el.items()) == []

    el = schema.from_flat([("x", "123")])
    assert el.value == {"x": 123}

    el = schema.from_flat([("x", "123"), ("z", "456")])
    assert el.value == {"x": 123}


def test_sparsedict_required_from_flat():
    schema = SparseDict.of(
        Integer.named("x"), Integer.named("y").using(optional=True)
    ).using(minimum_fields="required")

    el = schema.from_flat([])
    assert el.value == {"x": None}

    el = schema.from_flat([("x", "123")])
    assert el.value == {"x": 123}

    el = schema.from_flat([("y", "456"), ("z", "789")])
    assert el.value == {"x": None, "y": 456}


def test_sparsedict_required_validation():
    schema = SparseDict.of(
        Integer.named("x"), Integer.named("y").using(optional=True)
    ).using(minimum_fields="required")

    el = schema()
    assert not el.validate()

    el = schema({"y": 456})
    assert not el.validate()

    el = schema({"x": 123, "y": 456})
    assert el.validate()


def test_sparsedict_flattening():
    schema = SparseDict.named("top").of(Integer.named("x"), Integer.named("y"))

    els = [
        schema({"x": 123, "y": 456}),
        schema(),
        schema(),
        schema(),
    ]
    els[1].set({"x": 123, "y": 456})
    els[2]["x"] = 123
    els[2]["y"] = 456
    els[3]["x"] = Integer(123)
    els[3]["y"] = Integer(456)

    wanted = [("top_x", "123"), ("top_y", "456")]
    for el in els:
        got = sorted(el.flatten())
        assert wanted == got

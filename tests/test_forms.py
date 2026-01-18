"""Exercise form features.

NOTE: form tests are in the tests.schema package.  This is a legacy
test file, now providing a sample of some possible usage patterns.

"""

from flatland import (
    Dict,
    Schema,
    Integer,
    List,
    String,
)

REQUEST_DATA = (
    ("abc", "123"),
    ("surname", "SN"),
    ("xjioj", "1232"),
    ("age", "99"),
    ("fname", "FN"),
    ("ns_fname", "ns_FN"),
    ("ns_surname", "ns_SN"),
    ("ns_snacks_0_name", "cheez"),
    ("ns_snacks_1_name", "chipz"),
    ("ns_snacks_2_name", "chimp"),
    ("ns_squiznart", "xyyzy"),
    ("ns_age", "23"),
)


class SimpleForm1(Schema):
    fname = String
    surname = String
    age = Integer
    snacks = List.of(String.named("name"))


def test_straight_parse():
    form = SimpleForm1.from_flat(REQUEST_DATA)
    assert set(form.flatten()) == {("fname", "FN"), ("surname", "SN"), ("age", "99")}

    assert form.value == dict(fname="FN", surname="SN", age=99, snacks=[])


def test_namespaced_parse():

    def load(fn):
        form = SimpleForm1.from_defaults(name="ns")
        fn(form)
        return form

    output = dict(
        fname="ns_FN", surname="ns_SN", age=23, snacks=["cheez", "chipz", "chimp"]
    )

    for form in (
        load(lambda f: f.set_flat(REQUEST_DATA)),
        load(lambda f: f.set(output)),
    ):

        assert set(form.flatten()) == {
            ("ns_fname", "ns_FN"),
            ("ns_surname", "ns_SN"),
            ("ns_age", "23"),
            ("ns_snacks_0_name", "cheez"),
            ("ns_snacks_1_name", "chipz"),
            ("ns_snacks_2_name", "chimp"),
        }
        assert form.value == output


def test_default_behavior():

    class SimpleForm2(Schema):
        fname = String.using(default="FN")
        surname = String

    form = SimpleForm2()
    assert form["fname"].value == None
    assert form["surname"].value == None

    form = SimpleForm2.from_defaults()
    assert form["fname"].value == "FN"
    assert form["surname"].value == None

    class DictForm(Schema):
        dict = Dict.of(
            String.named("fname").using(default="FN"), String.named("surname")
        )

    form = DictForm()
    assert form.find_one("dict/fname").value == None
    assert form.find_one("dict/surname").value == None

    form = DictForm.from_defaults()
    assert form.find_one("dict/fname").value == "FN"
    assert form.find_one("dict/surname").value == None

"""Exercise form features.

NOTE: form tests are in the tests.schema package.  This is a legacy
test file, now providing a sample of some possible usage patterns.

"""
from flatland import (
    Dict,
    Form,
    Integer,
    List,
    String,
    )

from tests._util import eq_


REQUEST_DATA = ((u'abc', u'123'),
                (u'surname', u'SN'),
                (u'xjioj', u'1232'),
                (u'age', u'99'),
                (u'fname', u'FN'),
                (u'ns_fname', u'ns_FN'),
                (u'ns_surname', u'ns_SN'),
                (u'ns_snacks_0_name', u'cheez'),
                (u'ns_snacks_1_name', u'chipz'),
                (u'ns_snacks_2_name', u'chimp'),
                (u'ns_squiznart', u'xyyzy'),
                (u'ns_age', u'23'))


class SimpleForm1(Form):
    fname = String
    surname = String
    age = Integer
    snacks = List.of(String.named('name'))


def test_straight_parse():
    form = SimpleForm1.from_flat(REQUEST_DATA)
    eq_(set(form.flatten()), set(((u'fname', u'FN'),
                                  (u'surname', u'SN'),
                                  (u'age', u'99'))))

    eq_(form.value, dict(fname=u'FN',
                         surname=u'SN',
                         age=99,
                         snacks=[]))


def test_namespaced_parse():

    def load(fn):
        form = SimpleForm1.from_defaults(name='ns')
        fn(form)
        return form

    output = dict(fname=u'ns_FN',
                  surname=u'ns_SN',
                  age=23,
                  snacks=[u'cheez', u'chipz', u'chimp'])

    for form in (load(lambda f: f.set_flat(REQUEST_DATA)),
                 load(lambda f: f.set(output))):

        eq_(set(form.flatten()),
            set(((u'ns_fname', u'ns_FN'),
                 (u'ns_surname', u'ns_SN'),
                 (u'ns_age', u'23'),
                 (u'ns_snacks_0_name', u'cheez'),
                 (u'ns_snacks_1_name', u'chipz'),
                 (u'ns_snacks_2_name', u'chimp'))))
        eq_(form.value, output)


def test_default_behavior():

    class SimpleForm2(Form):
        fname = String.using(default=u'FN')
        surname = String

    form = SimpleForm2()
    eq_(form['fname'].value, None)
    eq_(form['surname'].value, None)

    form = SimpleForm2.from_defaults()
    eq_(form['fname'].value, u'FN')
    eq_(form['surname'].value, None)

    class DictForm(Form):
        dict = Dict.of(String.named('fname').using(default=u'FN'),
                       String.named('surname'))

    form = DictForm()
    eq_(form.el('dict.fname').value, None)
    eq_(form.el('dict.surname').value, None)

    form = DictForm.from_defaults()
    eq_(form.el('dict.fname').value, u'FN')
    eq_(form.el('dict.surname').value, None)

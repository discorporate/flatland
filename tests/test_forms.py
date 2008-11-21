from nose.tools import eq_

import flatland as fl


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

class SimpleForm1(fl.Form):
    schema = [fl.String('fname'),
              fl.String('surname'),
              fl.Integer('age'),
              fl.List('snacks', fl.String('name'))]

def test_straight_parse():
    f = SimpleForm1.from_flat(REQUEST_DATA)
    eq_(set(f.flatten()),
        set(((u'fname', u'FN'),
             (u'surname', u'SN'),
             (u'age', u'99'))))

    eq_(f.value,
        dict(fname=u'FN',
             surname=u'SN',
             age=99,
             snacks=[]))

def test_namespaced_parse():
    def load(fn):
        f = SimpleForm1.from_defaults(name='ns')
        fn(f)
        return f

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
    class SimpleForm2(fl.Form):
        schema = [fl.String('fname', default=u'FN'),
                  fl.String('surname')]

    form = SimpleForm2.from_flat({})
    eq_(form['fname'].value, None)
    eq_(form['surname'].value, None)

    form = SimpleForm2.from_defaults()
    eq_(form['fname'].value, u'FN')
    eq_(form['surname'].value, None)

    class DictForm(fl.Form):
        schema = [fl.Dict('dict',
            fl.String('fname', default=u'FN'), fl.String('surname'))]

    form = DictForm.from_flat({})
    eq_(form.el('dict.fname').value, None)
    eq_(form.el('dict.surname').value, None)

    form = DictForm.from_defaults()
    eq_(form.el('dict.fname').value, u'FN')
    eq_(form.el('dict.surname').value, None)

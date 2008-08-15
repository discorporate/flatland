import flatland as fl


REQUEST_DATA = ((u'abc', u'123'),
                (u'surname', u'SN'),
                (u'xjioj', u'1232'),
                (u'age', u'99'),
                (u'fname', u'FN'),
                (u'ns_fname', u'ns_FN'),
                (u'ns_surname', u'ns_SN'),
                (u'ns_age', u'23'))

class SimpleForm1(fl.Form):
    schema = [fl.String('fname'),
              fl.String('surname'),
              fl.Integer('age')]

def fakey_to_py(node):
    # Doesn't look like export to full Python native is in from springy yet.
    pairs = []
    def extract(node, data):
        if node.flattenable:
            data.append((node.name, node.value))
    node.apply(extract, pairs)
    return pairs

def test_straight_parse():
    f = SimpleForm1()
    f.set_flat(REQUEST_DATA)
    assert set(f.flatten()) == set(((u'fname', u'FN'),
                                    (u'surname', u'SN'),
                                    (u'age', u'99')))

def test_namespaced_parse():
    f = SimpleForm1('ns')
    f.set_flat(REQUEST_DATA)

    assert set(f.flatten()) == set(((u'ns_fname', u'ns_FN'),
                                    (u'ns_surname', u'ns_SN'),
                                    (u'ns_age', u'23')))
    assert set(fakey_to_py(f)) == set(((u'fname', u'ns_FN'),
                                      (u'surname', u'ns_SN'),
                                      (u'age', 23)))

    assert dict(fakey_to_py(f)) == dict(fname=u'ns_FN',
                                        surname=u'ns_SN',
                                        age=23)

    assert f['age'].value == 23
    assert f['age'].u == u'23'


from flatland import valid

class Age(fl.Integer):
    class IsNumber(valid.Converted):
        message = valid.message(u'%(label) is not a valid number.')

    class ValidAge(valid.Validator):
        minage = 1
        maxage = 150

        too_young = valid.message(u'%(label)s must be at least %(minage)s.')
        too_old = valid.message(u'%(label)s may not be larger than %(maxage)s')

        at_min = valid.message('%(label)s is at the minimum age.',
                               'warning')
        at_max = valid.message('%(label)s is at the maximum age.',
                               'warning')

        def __init__(self, minage=None, maxage=None):
            if minage is not None:
                self.minage = minage
            if maxage is not None:
                self.maxage = maxage

    def validate(self, node, state):
        age = node.value
        print "age %r" % age
        if age < self.minage:
            print "too young"
            return self.failure(node, state, 'too_young')
        elif age == self.minage:
            print "exact"
            return self.failure(node, state, 'at_min')
        elif age == self.maxage:
            return self.failure(node, state, 'at_max')
        elif age > self.maxage:
            return self.failure(node, state, 'too_old')
        return True

    validators = (valid.Present(),
                  IsNumber(),
                  ValidAge())

class ThirtySomething(Age):
    validators = (valid.Present(),
                  Age.IsNumber(),
                  Age.ValidAge(30, 39))

#def test_some_validation():
if True:
    class MyForm(fl.Form):
        schema = [ThirtySomething('age')]

    f = MyForm()
    f.set_flat({})
    assert not f.validate()
    #assert f['age'].errors == ['age may not be blank.']

    f = MyForm()
    f.set_flat({u'age': u'10'})
    assert not f.validate()
    #assert f['age'].errors == ['age may not be blank.'], f['age'].errors


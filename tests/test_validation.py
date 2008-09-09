import flatland as fl
from flatland import valid


class Age(fl.Integer):
    class IsNumber(valid.Converted):
        correct = valid.message(u'%(label)s is not a valid number.')

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
            if age < self.minage:
                return self.failure(node, state, 'too_young')
            elif age == self.minage:
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

def test_custom_validation():
    class MyForm(fl.Form):
        schema = [ThirtySomething('age')]

    f = MyForm()
    f.set_flat({})
    assert not f.validate()
    assert f['age'].errors == ['age may not be blank.']

    f = MyForm()
    f.set_flat({u'age': u''})
    assert not f.validate()
    assert f['age'].errors == ['age may not be blank.']

    f = MyForm()
    f.set_flat({u'age': u'crunch'})
    assert not f.validate()
    assert f['age'].errors == ['age is not a valid number.']

    f = MyForm()
    f.set_flat({u'age': u'10'})
    assert not f.validate()
    assert f['age'].errors == ['age must be at least 30.']


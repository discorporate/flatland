import flatland as fl
from flatland import valid


class Age(fl.Integer):
    class IsNumber(valid.Converted):
        incorrect = u'%(label)s is not a valid number.'

    class ValidAge(valid.Validator):
        minage = 1
        maxage = 150

        too_young = u'%(label)s must be at least %(minage)s.'
        too_old = u'%(label)s may not be larger than %(maxage)s'

        at_min = '%(label)s is at the minimum age.'
        at_max = '%(label)s is at the maximum age.'

        def __init__(self, minage=None, maxage=None):
            if minage is not None:
                self.minage = minage
            if maxage is not None:
                self.maxage = maxage

        def validate(self, element, state):
            age = element.value
            if age < self.minage:
                return self.note_error(element, state, 'too_young')
            elif age == self.minage:
                return self.note_warning(element, state, 'at_min')
            elif age == self.maxage:
                return self.note_warning(element, state, 'at_max')
            elif age > self.maxage:
                return self.note_error(element, state, 'too_old')
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

    f = MyForm.from_flat({})
    assert not f.validate()
    assert f['age'].errors == ['age may not be blank.']

    f = MyForm.from_flat({u'age': u''})
    assert not f.validate()
    assert f['age'].errors == ['age may not be blank.']

    f = MyForm.from_flat({u'age': u'crunch'})
    assert not f.validate()
    assert f['age'].errors == ['age is not a valid number.']

    f = MyForm.from_flat({u'age': u'10'})
    assert not f.validate()
    assert f['age'].errors == ['age must be at least 30.']

def test_child_validation():
    s = fl.Dict('s', fl.Integer('x', validators=[valid.Present()]))
    n = s()

    assert not n.validate()

    n.set({u'x': 10})

    assert n.validate()

def test_nested_validation():
    s = fl.Dict('d1',
                fl.Integer('x', validators=[valid.Present()]),
                fl.Dict('d2',
                        fl.Integer('x2', validators=[valid.Present()])))
    n = s()

    assert not n.validate()

    n['x'].set(1)
    assert not n.validate()
    assert n.validate(recurse=False)

    n.el('d2.x2').set(2)
    assert n.validate()


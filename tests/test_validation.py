from flatland import (
    Dict,
    Form,
    Integer,
    )
from flatland.valid import (
    Converted,
    Present,
    Validator,
    )


class Age(Integer):

    class IsNumber(Converted):
        incorrect = u'%(label)s is not a valid number.'

    class ValidAge(Validator):
        minage = 1
        maxage = 150

        too_young = u'%(label)s must be at least %(minage)s.'
        too_old = u'%(label)s may not be larger than %(maxage)s'

        at_min = '%(label)s is at the minimum age.'
        at_max = '%(label)s is at the maximum age.'

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

    validators = (Present(),
                  IsNumber(),
                  ValidAge())


class ThirtySomething(Age):
    validators = (Present(),
                  Age.IsNumber(),
                  Age.ValidAge(minage=30, maxage=39))


def test_custom_validation():

    class MyForm(Form):
        age = ThirtySomething

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

    class MyForm(Form):
        x = Integer.using(validators=[Present()])

    form = MyForm()
    assert not form.validate()

    form.set({u'x': 10})
    assert form.validate()


def test_nested_validation():

    class MyForm(Form):
        x = Integer.using(validators=[Present()])

        d2 = Dict.of(Integer.named('x2').using(validators=[Present()]))

    form = MyForm()
    assert not form.validate()

    form['x'].set(1)
    assert not form.validate()
    assert form.validate(recurse=False)

    form.el('d2.x2').set(2)
    assert form.validate()

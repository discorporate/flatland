from . base import Validator


class Present(Validator):
    missing = u'%(label)s may not be blank.'

    def validate(self, element, state):
        if element.u != u'':
            return True

        return self.note_error(element, state, 'missing')


class Converted(Validator):
    correct = u'%(label)s is not correct.'

    def validate(self, element, state):
        if element.value is not None:
            return True

        return self.note_error(element, state, 'correct')


class ShorterThan(Validator):
    exceeded = u'%(label)s may not exceed %(maxlength)s characters.'

    def __init__(self, maxlength):
        self.maxlength = maxlength

    def validate(self, element, state):
        if len(element.u) > self.maxlength:
            return self.note_error(element, state, 'exceeded')
        return True
NoLongerThan = ShorterThan


class LongerThan(Validator):
    short = u'%(label)s must be at least %(minlength)s characters.'

    def __init__(self, minlength):
        self.minlength = minlength

    def validate(self, element, state):
        if len(element.u) < self.minlength:
            return self.note_error(element, state, 'short')
        return True


class LengthBetween(Validator):
    breached = (u'%(label)s must be between %(minlength)s and '
                u'%(maxlength)s characters long.')

    def __init__(self, minlength, maxlength):
        self.minlength = minlength
        self.maxlength = maxlength

    def validate(self, element, state):
        l = len(element.u)
        if l < self.minlength or l > self.maxlength:
            return self.note_error(element, state, 'breached')
        return True


class HumanName(Validator):
    # \w but not [\d_]

    pass

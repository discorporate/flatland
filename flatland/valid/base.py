from flatland.util import as_cascaded_mapping, re_ucompile


def message(format, bucket='error', result=None):
    assert bucket in ('error', 'warning')

    if result is None:
        result = False if bucket == 'error' else True

    return (format, bucket, result)

class Validator(object):

    def __call__(self, element, state):
        return self.validate(element, state)

    def validate(self, element, state):
        return False

    def failure(self, element, state, key=None, message=None):
        assert key or message
        if key and not hasattr(self, key):
            raise AssertionError('Message key "%s" not defined on %s.' %
                                 (key, type(self).__name__))
        elif not key:
            if message is False:
                return False
            elif callable(message):
                element.add_error(message(element, state))
            else:
                element.add_error(message)
            return False

        format, bucket, result = getattr(self, key)

        if format is False:
            return result
        elif callable(format):
            message = format(element, state)
        else:
            message = format % as_cascaded_mapping(element, self)

        if bucket == 'error':
            element.add_error(message)
        elif bucket == 'warning':
            element.add_warning(message)

        return result


class Present(Validator):
    missing = message(u'%(label)s may not be blank.')

    def validate(self, element, state):
        if element.u != u'':
            return True

        return self.failure(element, state, 'missing')


class Converted(Validator):
    correct = message(u'%(label)s is not correct.')

    def validate(self, element, state):
        if element.value is not None:
            return True

        return self.failure(element, state, 'correct')


class ShorterThan(Validator):
    exceeded = message(u'%(label)s may not exceed %(maxlength)s characters.')

    def __init__(self, maxlength):
        self.maxlength = maxlength

    def validate(self, element, state):
        if len(element.u) > self.maxlength:
            return self.failure(element, state, 'exceeded')
        return True
NoLongerThan = ShorterThan


class LongerThan(Validator):
    short = message(u'%(label)s must be at least %(minlength)s characters.')

    def __init__(self, minlength):
        self.minlength = minlength

    def validate(self, element, state):
        if len(element.u) < self.minlength:
            return self.failure(element, state, 'short')
        return True


class LengthBetween(Validator):
    breached = message(u'%(label)s must be between %(minlength)s and '
                       u'%(maxlength)s characters long.')

    def __init__(self, minlength, maxlength):
        self.minlength = minlength
        self.maxlength = maxlength

    def validate(self, element, state):
        l = len(element.u)
        if l < self.minlength or l > self.maxlength:
            return self.failure(element, state, 'breached')
        return True


class HumanName(Validator):
    # \w but not [\d_]

    pass

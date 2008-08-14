from flatland.util import GetitemGetattrMultiProxy, re_ucompile


def message(format, bucket='error', result=None):
    assert bucket in ('error', 'warning')

    if result is None:
        result = False if bucket == 'error' else True

    return (format, bucket, result)

class Validator(object):

    def __call__(self, node, state):
        return self.validate(node, state)

    def validate(self, node, state):
        return False

    def failure(self, node, state, key=None, message=None):
        assert key or message
        if key and not hasattr(self, key):
            raise AssertionError('Message key "%s" not defined on %s.' %
                                 (key, type(self).__name__))
        elif not key:
            if message is False:
                return False
            elif callable(message):
                node.add_error(message(node, state))
            else:
                node.add_error(message)
            return False

        format, bucket, result = getattr(self, key)

        if format is False:
            return result
        elif callable(format):
            message = format(node, state)
        else:
            message = format % GetitemGetattrMultiProxy(node, self)

        if bucket == 'error':
            node.add_error(message)
        elif bucket == 'warning':
            node.add_warning(message)

        return result


class Present(Validator):
    missing = message(u'%(label)s may not be blank.')

    def validate(self, node, state):
        if node.u <> u'':
            return True

        return self.failure(node, state, 'missing')

class Converted(Validator):
    correct = message(u'%(label)s is not correct.')

    def validate(self, node, state):
        if node.value is not None:
            return True

        return self.failure(node, state, 'correct')

class ShorterThan(Validator):
    exceeded = message(u'%(label)s may not exceed %(maxlength)s characters.')

    def __init__(self, maxlength):
        self.maxlength = maxlength

    def validate(self, node, state):
        if len(node.u) > self.maxlength:
            return self.failure(node, state, 'exceeded')
        return True
NoLongerThan = ShorterThan

class LongerThan(Validator):
    short = message(u'%(label)s must be at least %(minlength)s characters.')

    def __init__(self, minlength):
        self.minlength = minlength

    def validate(self, node, state):
        if len(node.u) < self.minlength:
            return self.failure(node, state, 'short')
        return True

class LengthBetween(Validator):
    breached = message(u'%(label)s must be between %(minlength)s and '
                       u'%(maxlength)s characters long.')

    def __init__(self, minlength, maxlength):
        self.minlength = minlength
        self.maxlength = maxlength

    def validate(self, node, state):
        l = len(node.u)
        if l < self.minlength or l > self.maxlength:
            return self.failure(node, state, 'breached')
        return True

class HumanName(Validator):
    # \w but not [\d_]

    pass

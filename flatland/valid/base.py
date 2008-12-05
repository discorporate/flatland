import __builtin__
import operator
from flatland.util import adict


N_ = lambda translatable: translatable

class Validator(object):

    _transform_finder = operator.attrgetter('ugettext')
    _tuple_transform_finder = operator.attrgetter('ungettext')
    _missing_but_inittable = set(('ugettext', 'ungettext'))

    def __init__(self, **kw):
        """Construct a validator.

        :param \*\*kw: override any extant class attribute on this instance.

        """
        cls, extra = type(self), self._missing_but_inittable
        for attr, value in kw.iteritems():
            if hasattr(cls, attr) or attr in extra:
                setattr(self, attr, value)
            else:
                raise TypeError("%s has no attribute %r, can not override." % (
                    cls.__name__, attr))

    def __call__(self, element, state):
        return self.validate(element, state)

    def validate(self, element, state):
        return False

    def note_error(self, element, state, key=None, message=None, **info):
        message = message or getattr(self, key)
        if message:
            element.add_error(
                self.expand_message(element, state, message, **info))
        return False

    def note_warning(self, element, state, key=None, message=None, **info):
        message = message or getattr(self, key)
        if message:
            element.add_warning(
                self.expand_message(element, state, message, **info))
        return False

    def find_transformer(self, element, state, message, finder):
        transform = finder(element.schema)
        if transform:
            return transform
        for parent in element.parents:
            transform = finder(parent.schema)
            if transform:
                return transform
        try:
            return finder(__builtin__)
        except AttributeError:
            return None

    def expand_message(self, element, state, message, **extra_format_args):
        if callable(message):
            message = message(element, state)

        message_transform = mapping_transform = self.find_transformer(
            element, state, message, self._transform_finder)

        if extra_format_args:
            extra_format_args = adict(extra_format_args)
            format_map = as_format_mapping(
                extra_format_args, element, self,
                transform=mapping_transform)
        else:
            format_map = as_format_mapping(
                element, self,
                transform=mapping_transform)

        if isinstance(message, tuple):
            # a transformer must be present if message is a tuple
            transform = self.find_transformer(
                element, state, message, self._tuple_transform_finder)

            single, plural, n_key = message
            try:
                n = format_map[n_key]
            except KeyError:
                n = n_key

            message = transform(single, plural, n)
        elif message_transform:
            message = message_transform(message)

        return message % format_map


class as_format_mapping(object):
    """A unified, optionally transformed, mapping view over multiple instances.

    Allows regular instance attributes to be accessed by "%(attrname)s" in
    string formats.  Optionally passes values through a ``transform`` (such
    ``gettext``) before returning.

    """

    __slots__ = 'targets', 'transform'

    def __init__(self, *targets, **kw):
        self.targets = targets
        self.transform = kw.pop('transform', None)
        if kw:
            raise TypeError('unexpected keyword argument')

    def __getitem__(self, item):
        for target in self.targets:
            try:
                value = getattr(target, item)
            except AttributeError:
                pass
            else:
                if self.transform:
                    return self.transform(value)
                else:
                    return value
        raise KeyError(item)

    def __contains__(self, item):
        try:
            self[item]
            return True
        except KeyError:
            return False

    def __iter__(self):
        keys = set()
        for target in self.targets:
            keys |= set(dir(target))
        return iter(keys)


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

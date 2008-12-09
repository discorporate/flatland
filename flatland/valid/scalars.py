from operator import attrgetter
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


class MapEqual(Validator):
    """A general field equality validator.

    Validates that two or more fields are equal.

    **Attributes**

    .. attribute:: field_paths

      A sequence of field names or field paths.  Path names will be
      evaluated at validation time and relative path names are
      resolved relative to the element holding this validator.  See
      :class:`ValuesEqual` for an example.

    .. attribute:: transform

      A 1-arg callable, passed a
      :class:`~flatland.schema.base.Element`, returning a value for
      equality testing.

    **Messages**

    .. attribute:: unequal

      Emitted if the ``transform(element)`` of all elements are not
      equal.  ``labels`` will substitute to a comma-separated list of
      the :attr:`~flatland.schema.base.Element.label` of all but the
      last element; ``last_label`` is the label of the last.

    """

    unequal = u'%(labels)s and %(last_label)s do not match.'

    field_paths = ()
    transform = lambda el: el

    def __init__(self, *field_paths, **kw):
        """Construct a MapEqual.

        :param \*field_paths: a sequence of 2 or more elements names or paths.

        :param \*\*kw: passed to :meth:`Validator.__init__`.

        """
        if not field_paths:
            assert self.field_paths, 'at least 2 element paths required.'
        else:
            assert len(field_paths) > 1, 'at least 2 element paths required.'
            self.field_paths = field_paths
        Validator.__init__(self, **kw)

    def validate(self, element, state):
        elements = [element.el(name) for name in self.field_paths]
        fn = self.transform
        sample = fn(elements[0])
        if all(fn(el) == sample for el in elements[1:]):
            return True
        labels = ', '.join(el.label for el in elements[:-1])
        last_label = elements[-1].label
        return self.note_error(element, state, 'unequal',
                               labels=labels, last_label=last_label)

class ValuesEqual(MapEqual):
    """Validates that the values of multiple elements are equal.

    A :class:`MapEqual` that compares the
    :attr:`~flatland.schema.base.Element.value` of each element.

    Example:

    .. testcode::

      import flatland
      from flatland.valid import ValuesEqual

      class MyForm(flatland.Form):
          schema = [ String('password'), String('password_again') ]
          validators = ValuesEqual('password', 'password_again')

    .. attribute:: transform()

      attrgettr('value')

    """

    transform = attrgetter('value')


class UnisEqual(MapEqual):
    """Validates that the Unicode values of multiple elements are equal.

    A :class:`MapEqual` that compares the
    :attr:`~flatland.schema.base.Element.u` of each element.

    .. attribute:: transform

      attrgettr('u')

    """

    transform = attrgetter('u')


class HumanName(Validator):
    # \w but not [\d_]
    pass

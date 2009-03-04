from ..schema import Slot
from . base import Validator


class NotDuplicated(Validator):
    """A sequence member validator that ensures all sibling values are unique.

    Marks the second and any subsequent occurrences of a value as
    invalid.  Only useful on immediate children of sequence fields
    such as :class:`flatland.List`.

    Example::

      import flatland
      from flatland.valid import NotDuplicated

      schema = flatland.List(
        String('favorite_color', validators=[
          NotDuplicated(failure="Please enter each color only once.")]))

    **Messages**

    .. attribute:: failure

      Emitted on an element that has already appeared in a parent
      sequence.  ``container_label`` will substitute the label of the
      container.  ``position`` is the position of the element in the
      parent sequence, counting up from 1.

    """

    failure = u'%(label)s may not be repeated within %(container_label)s.'

    def validate(self, element, state):
        if element.parent is None:
            raise TypeError(
                "%s validator must be applied to a child of a Container "
                "type; %s has no parent." % (
                    type(self).__name__,
                    element.name))
        container = element.parent
        if isinstance(container, Slot):
            container = container.parent
        valid, position = True, 0
        for idx, sibling in enumerate(container.children):
            if sibling is element:
                position = idx + 1
                break
            if valid and element == sibling:
                valid = False
        if not valid:
            return self.note_error(
                element, state, 'failure',
                position=position, container_label=container.label)
        return True

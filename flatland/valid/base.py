"""Base functionality for fancy validation."""
import __builtin__
import operator
from flatland.util import adict
from flatland.schema.util import find_i18n_function


N_ = lambda translatable: translatable

class Validator(object):
    """Base class for fancy validators."""

    _transform_finder = operator.attrgetter('ugettext')
    _tuple_transform_finder = operator.attrgetter('ungettext')

    def __init__(self, **kw):
        """Construct a validator.

        :param \*\*kw: override any extant class attribute on this instance.

        """
        cls = type(self)
        for attr, value in kw.iteritems():
            if hasattr(cls, attr):
                setattr(self, attr, value)
            else:
                raise TypeError("%s has no attribute %r, can not override." % (
                    cls.__name__, attr))

    def __call__(self, element, state):
        """Adapts Validator to the Element.validate callable interface."""
        return self.validate(element, state)

    def validate(self, element, state):
        """Validate an element returning True if valid.

        :param element:
          an :class:`~flatland.schema.base.Element` instance.

        :param state:
          an arbitrary object.  Supplied by
          :meth:`Element.validate <flatland.schema.base.Element.validate>`.

        :returns: True if valid

        """
        return False

    def note_error(self, element, state, key=None, message=None, **info):
        """Record a validation error message on an element.

        :param element:
          An :class:`~flatland.schema.base.Element` instance.

        :param state:
          an arbitrary object.  Supplied by :meth:`Element.validate
          <flatland.schema.base.Element.validate>`.

        :param key: semi-optional, default None.
          The name of a message-holding attribute on this instance.  Will be
          used to ``message = getattr(self, key)``.

        :param message: semi-optional, default None.
          A validation message.

        :param \*\*info: optional.
          Additional data to make available to validation message
          string formatting.

        :returns: False

        Either *key* or *message* is required.  The message will have
        formatting expanded by :meth:`expand_message` and be appended to
        :attr:`element.errors <flatland.schema.base.Element.errors>`.

        Always returns False.  This enables a convenient shorthand when
        writing validators:

        .. testcode::

          from flatland.valid import Validator

          class MyValidator(Validator):
              my_message = 'Oh noes!'

              def validate(self, element, state):
                  if not element.value:
                      return self.note_error(element, state, 'my_message')
                  else:
                      return True

        .. testcode:: :hide:

          from flatland import String
          el = String('x').create_element()
          v = MyValidator()
          assert not v.validate(el, None)
          assert el.errors == ['Oh noes!']
          el.set('foo')
          assert v.validate(el, None)
          assert el.errors == ['Oh noes!']

        """
        message = message or getattr(self, key)
        if message:
            element.add_error(
                self.expand_message(element, state, message, **info))
        return False

    def note_warning(self, element, state, key=None, message=None, **info):
        """Record a validation warning message on an element.

        :param element:
          An :class:`~flatland.schema.base.Element` instance.

        :param state:
          an arbitrary object.  Supplied by :meth:`Element.validate
          <flatland.schema.base.Element.validate>`.

        :param key: semi-optional, default None.
          The name of a message-holding attribute on this instance.  Will be
          used to ``message = getattr(self, key)``.

        :param message: semi-optional, default None.
          A validation message.

        :param \*\*info: optional.
          Additional data to make available to validation message
          string formatting.

        :returns: False

        Either *key* or *message* is required.  The message will have
        formatting expanded by :meth:`expand_message` and be appended to
        :attr:`element.warnings <flatland.schema.base.Element.warnings>`.

        Always returns False.
        """
        message = message or getattr(self, key)
        if message:
            element.add_warning(
                self.expand_message(element, state, message, **info))
        return False

    def find_transformer(self, element, state, message, finder):
        return find_i18n_function(element, finder)

    def expand_message(self, element, state, message, **extra_format_args):
        """Apply formatting to a validation message.

        :param element:
          an :class:`~flatland.schema.base.Element` instance.

        :param state:
          an arbitrary object.  Supplied by
          :meth:`Element.validate <flatland.schema.base.Element.validate>`.

        :param message: a string, 3-tuple or callable.
          If a 3-tuple, must be of the form ('single form', 'plural form',
          n_key).

          If callable, will be called with 2 positional arguments (*element*,
          *state*) and must return a string or 3-tuple.

        :param \*\*extra_format_args: optional.
          Additional data to make available to validation message
          string formatting.

        :returns: the formatted string

        See :ref:`validation_messaging` for full information on how messages
        are expanded.

        """
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
                try:
                    n = int(n)
                except TypeError:
                    pass
            except KeyError:
                n = n_key

            if transform:
                message = transform(single, plural, n)
            else:
                message = single if n == 1 else plural
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



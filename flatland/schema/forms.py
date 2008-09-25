from __future__ import absolute_import

from . import containers
from .. import util

__all__ = 'Form',


class Form(containers.Dict):
    """A collection of named fields or schema items.

    Forms are the most common top-level mapping.  They behave like
    :class:`flatland.Dict`, but do not need to be named.

    FIXME: Also magic schema holder?

    FIXME2: Assuming this means an inner class to do definitions on.
            Hard to do in a way that maintains the spirit of named,
            nested structures and DRY, e.g.

    ::

      # e.g. FIXME2
      class MyForm(Form):
          class schema:
              name = String('name')
              addresses = List('addresses',
                               Dict('address',
                                    String('street1'),
                                    String('street2')))

    """

    def __init__(self, name=None, **kw):
        try:
            members = self.schema
        except AttributeError:
            raise TypeError('a schema is required')

        if hasattr(self, 'validators'):
            if 'validators' in kw:
                v = self.validators[:]
                v.extend(kw['validators'])
                kw['validators'] = v
            else:
                kw['validators'] = self.validators[:]

        containers.Dict.__init__(self, name, *members, **kw)

    @classmethod
    def from_flat(cls, items, **kw):
        """Return a Form element initialized from a sequence of pairs.

        :param items: a sequence of ``(key, value)`` pairs, as for
           :meth:`Element.from_flat`.

        :param **kw: keyword arguments will be passed to the
            :class:`Form` constructor.

        """
        element = cls(**kw).create_element()
        element.set_flat(items)
        return element

    @classmethod
    def from_value(cls, value, **kw):
        """Return a Form element initialized from a compatible value.

        :param value: any value, will be passed to :meth:`Element.set`.

        :param **kw: keyword arguments will be passed to the
            :class:`Form` constructor.

        """
        element = cls(**kw).create_element()
        element.set(value)
        return element

    @classmethod
    def from_defaults(cls, **kw):
        """Return a Form element initialized with FieldSchema defaults."""
        return cls(**kw).create_element()

    @classmethod
    def from_object(cls, obj, include=None, omit=None, rename=None, **kw):
        """Return a Form element initialized with an object's attributes.

        :param obj: any object
        :param include: optional, an iterable of attribute names to
            pull from *obj*, if present on the object.  Only these
            attributes will be included.
        :param omit: optional, an iterable of attribute names to
            ignore on **obj**.  All other attributes matching a
            named field on the Form will be included.
        :param rename: optional, a mapping of attribute-to-field name
            transformations.  Attributes specified in the mapping will
            be included regardless of *include* or *omit*.
        :param **kw: keyword arguments will be passed to the
            :class:`Form` constructor.

        *include* and *omit* are mutually exclusive.

        Creates and initializes a Form element, using as many
        attributes as possible from *obj*.  Object attributes that do
        not correspond to field names are ignored.

        """

        self = cls(**kw)

        attributes = set(self.fields.iterkeys())
        if rename:
            rename = list(util.to_pairs(rename))
            attributes.update(key for key, value in rename
                                  if value in attributes)
        if omit:
            omit = list(omit)
            attributes.difference_update(omit)

        possible = ((attr, getattr(obj, attr))
                    for attr in attributes
                    if hasattr(obj, attr))

        sliced = util.keyslice_pairs(possible, include=include,
                                     omit=omit, rename=rename)
        final = dict((key, value)
                     for key, value in sliced
                     if key in set(self.fields.iterkeys()))
        return self.create_element(value=final)

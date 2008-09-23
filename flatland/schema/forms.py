from __future__ import absolute_import

from . import containers


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
        element = cls(**kw).create_element()
        element.set_flat(items)
        return element

    @classmethod
    def from_value(cls, value, **kw):
        element = cls(**kw).create_element()
        element.set(value)
        return element

    @classmethod
    def from_defaults(cls, **kw):
        return cls(**kw).create_element()

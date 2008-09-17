from __future__ import absolute_import

from . import containers


__all__ = 'Form',


class MetaForm(type):
    """Form() returns an Element, not a Form(FieldSchema) instance."""

    def __call__(cls, *args, **kw):
        form = cls.__new__(cls)
        form.__init__(*args, **kw)
        return form.new()


class Form(containers.Dict):
    """A collection of named fields or schema items.

    Forms are the most common top-level mapping.  They behave like
    Dicts, but do not need to be named.

    FIXME: Also magic schema holder?

    FIXME2: Assuming this means an inner class to do definitions on.
            Hard to do in a way that maintains the spirit of named,
            nested structures and DRY, e.g.

              class MyForm(Form):
                  class schema:
                      name = String('name')
                      addresses = List('addresses',
                                       Dict('address',
                                            String('street1'),
                                            String('street2')))

    """

    __metaclass__ = MetaForm

    def __init__(self, *args, **kw):
        if args and isinstance(args[0], basestring):
            name, args = args[0], args[1:]
        else:
            name = None

        if hasattr(self, 'schema'):
            members = self.schema[:]
            members.extend(args)
        else:
            members = args
        if not members:
            raise TypeError('a schema is required')

        if hasattr(self, 'validators'):
            if 'validators' in kw:
                v = self.validators[:]
                v.extend(kw['validators'])
                kw['validators'] = v
            else:
                kw['validators'] = self.validators[:]

        containers.Dict.__init__(self, name, *members, **kw)


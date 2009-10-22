# -*- coding: utf-8; fill-column: 78 -*-
from .base import Element
from .containers import Dict


__all__ = 'Form',


class _ElementCollection(object):
    """TODO"""

    def __init__(self):
        self.elements = []
        self.names = set()

    def add_unseen(self, iterable):
        """TODO"""
        for field in iterable:
            if field.name in self.names:
                continue
            self.elements.append(field)
            self.names.add(field.name)

    def add_and_overwrite(self, iterable):
        """TODO"""
        for field in iterable:
            if field.name in self.names:
                for have in self.elements:
                    if have.name == field.name:
                        self.elements.remove(have)
                        break
            self.elements.append(field)


class MetaForm(type):
    """TODO"""

    def __new__(self, class_name, bases, members):
        fields = _ElementCollection()

        # collect existing fields from super classes in __mro__ order
        for base in bases:
            fields.add_unseen(getattr(base, 'field_schema', ()))

        # add / replace fields supplied in a field_schema on this class
        fields.add_and_overwrite(members.get('field_schema', ()))

        # add / replace fields declared as attributes on this class
        declared_fields = []
        for name, value in members.items():
            if isinstance(value, type) and issubclass(value, Element):
                if name != value.name:
                    value = value.named(name)
                declared_fields.append(value)
                del members[name]
        fields.add_and_overwrite(declared_fields)

        # the new type's field_schema is the final result of all this
        members['field_schema'] = fields.elements
        return type.__new__(self, class_name, bases, members)


class Form(Dict):
    """A collection of named fields or schema items.

    Forms are the most common top-level mapping.  They behave like
    :class:`flatland.Dict`, but do not need to be named.  Forms are defined
    with Python class syntax:

    .. doctest::

      >>> import flatland
      >>> class HelloForm(flatland.Form):
      ...     schema = [ flatland.String('hello'),
      ...                flatland.String('world') ]
      ...

    Subclasses must define a :attr:`schema` property, containing an ordered
    sequence of fields.  Forms may embed other container fields and other
    forms:

    .. doctest::

      >>> class BigForm(flatland.Form):
      ...     schema = [
      ...       HelloForm('main_hello'),
      ...       flatland.List('alt_hellos',
      ...                     flatland.Dict('alt',
      ...                                   flatland.String('alt_name'),
      ...                                   HelloForm('alt_hello')))
      ...              ]
      ...

    This would create a form with one ``HelloForm`` embedded as
    ``main_hello``, and a list of zero or more dicts, each containing an
    ``alt_name`` and another ``HelloForm``.

    """

    __metaclass__ = MetaForm

    # TODO:
    #   some kind of validator merging helper?  or punt?
    # def __init__(self, name=None, **kw):
    #     try:
    #         members = self.schema
    #     except AttributeError:
    #         raise TypeError('a schema is required')
    #
    #     if hasattr(self, 'validators'):
    #         if 'validators' in kw:
    #             v = self.validators[:]
    #             v.extend(kw['validators'])
    #             kw['validators'] = v
    #         else:
    #             kw['validators'] = self.validators[:]
    #
    #     containers.Dict.__init__(self, name, *members, **kw)

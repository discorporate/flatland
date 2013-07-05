# -*- coding: utf-8; fill-column: 78 -*-
"""Class attribute-style declarative schema construction."""
from .base import Element
from .containers import Dict, SparseDict


__all__ = ['Schema', 'SparseSchema']


class _MetaSchema(type):
    """Allows elements to be declared as class attributes.

    Processes class declarations of the form:

      from flatland import Schema, String

      class MySchema(Schema):
          name = String
          favorite_color = String.using(optional=True)

    and converts them to a :attr:`~flatland.Dict.field_schema` specification
    at class construction time.  Schemas may inherit from other Schemas, with
    schema declarations following normal Python class property inheritance
    semantics.

    """

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


class _ElementCollection(object):
    """Internal helper collection for calculating Schema field inheritance."""

    def __init__(self):
        self.elements = []
        self.names = set()

    def add_unseen(self, iterable):
        """Add new items from *iterable*."""
        for field in iterable:
            if field.name in self.names:
                continue
            self.elements.append(field)
            self.names.add(field.name)

    def add_and_overwrite(self, iterable):
        """Add from *iterable*, replacing existing items of the same name."""
        for field in iterable:
            if field.name in self.names:
                for have in self.elements:
                    if have.name == field.name:
                        self.elements.remove(have)
                        break
            self.names.add(field.name)
            self.elements.append(field)


class Schema(Dict):
    """A declarative collection of named elements.

    Schemas behave like |Dict|, but are defined with Python class syntax:

    .. doctest::

      >>> from flatland import Schema, String
      >>> class HelloSchema(Schema):
      ...     hello = String
      ...     world = String
      ...

    Elements are assigned names from the attribute declaration.  If a named
    element schema is used, a renamed copy will be assigned to the Schema to
    match the declaration.

    .. doctest::

      >>> class HelloSchema(Schema):
      ...     hello = String.named('hello')    # redundant
      ...     world = String.named('goodbye')  # will be renamed 'world'
      ...
      >>> helloworld = HelloSchema()
      >>> sorted(helloworld.keys())
      [u'hello', u'world']

    Schemas may embed other container fields and other schemas:

    .. doctest::

      >>> from flatland import List
      >>> class BigSchema(Schema):
      ...     main_hello = HelloSchema
      ...     alt_hello = List.of(String.named('alt_name'),
      ...                         HelloSchema.named('alt_hello'))
      ...

    This would create a Schema with one ``HelloSchema`` embedded as
    ``main_hello``, and a list of zero or more dicts, each containing an
    ``alt_name`` and another ``HelloSchema`` named ``alt_hello``.

    Schemas may inherit from other Schemas or Dicts.  Element attributes
    declared in a subclass will override those of a superclass.  Multiple
    inheritance is supported.

    The special behavior of ``Schema`` is limited to class construction time
    only.  After construction, the ``Schema`` acts exactly like a |Dict|.  In
    particular, fields declared as class attributes as above do **not** remain
    class attributes.  They are removed from the class dictionary and placed
    in the `~flatland.schema.containers.Mapping.field_schema`:

    .. doctest::

      >>> hasattr(HelloSchema, 'hello')
      False
      >>> sorted([field.name for field in HelloSchema.field_schema])
      [u'hello', u'world']

    The order of ``field_schema`` is undefined.

    """

    __metaclass__ = _MetaSchema


class SparseSchema(SparseDict):
    """A sparse variant of `~flatland.schema.declarative.Schema`.

    Exactly as ``Schema``, but based upon
    ~flatland.schema.containers.SparseDict`.

    """
    __metaclass__ = _MetaSchema


class Form(Dict):
    """An alias for Schema, for older flatland version compatibility."""

    __metaclass__ = _MetaSchema

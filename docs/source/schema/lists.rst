=====
Lists
=====

.. currentmodule:: flatland.schema.containers

Instances of :class:`List` hold other elements and operate like Python
lists.  Lists are configured with a :attr:`~List.child_schema`, such
as an :class:`~flatland.schema.scalars.Integer`. Each list member will
be an instance of that type.  The :meth:`List.of` schema constructor
will set ``child_schema``:

.. doctest::

  >>> from flatland import List, Integer
  >>> Numbers = List.of(Integer)
  >>> Numbers.child_schema
  <class 'flatland.schema.scalars.Integer'>

Python list methods and operators may be passed instances of
:attr:`~List.child_schema` or plain Python values.  Using plain values
is a shorthand for creating a ``child_schema`` instance and
:meth:`set()ting<flatland.schema.base.Element.set>` it with the value:

.. doctest::

  >>> ones = Numbers()
  >>> ones.append(1)
  >>> ones.value
  [1]
  >>> another_one = Integer()
  >>> another_one.set(1)
  True
  >>> ones.append(another_one)
  >>> ones.value
  [1, 1]

List extends :class:`Sequence` and adds positional naming to its
elements.  Elements are addressable via their list index in
:meth:`~flatland.schema.base.Element.el` and their index in the list
is reflected in their flattened name:

Example:

.. doctest::

  >>> from flatland import List
  >>> Names = List.named('names').of(String.named('name'))
  >>> names = Names([u'a', u'b'])
  >>> names.value
  [u'a', u'b']
  >>> names.flatten()
  [(u'names_0_name', u'a'), (u'names_1_name', u'b')]
  >>> names.el('.1').value
  u'b'

Validation
----------

If :attr:`~Container.descent_validators` is defined, these validators
will be run first, before member elements are validated.

If :attr:`~flatland.schema.base.Element.validators` is defined, these
validators will be run after member elements are validated.

Schema Constructors
-------------------

.. automethod:: List.named

.. automethod:: List.of

.. automethod:: List.using

Factory Methods
---------------

.. automethod:: List.from_defaults

.. automethod:: List.from_flat

.. automethod:: List.from_value

Configurable Attributes
-----------------------

.. autoattribute:: Sequence.child_schema
  :noindex:

.. autoattribute:: Sequence.prune_empty
  :noindex:

.. autoattribute:: List.maximum_set_flat_members

``List``
--------

.. autoclass:: List
  :show-inheritance:
  :members:
  :inherited-members:
  :exclude-members: child_schema, prune_empty,
     slot_type, maximum_set_flat_members,
     from_defaults, from_flat, from_value,
     create_blank


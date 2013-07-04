=====
Lists
=====

.. currentmodule:: flatland.schema.containers

Instances of :class:`List` hold other elements and operate like Python
lists.  Lists are configured with a :attr:`~List.member_schema`, such
as an :class:`~flatland.schema.scalars.Integer`. Each list member will
be an instance of that type.  The :meth:`List.of` schema constructor
will set ``member_schema``:

.. doctest::

  >>> from flatland import List, Integer
  >>> Numbers = List.of(Integer)
  >>> Numbers.member_schema
  <class 'flatland.schema.scalars.Integer'>

Python list methods and operators may be passed instances of
:attr:`~List.member_schema` or plain Python values.  Using plain values
is a shorthand for creating a ``member_schema`` instance and
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
:meth:`~flatland.schema.base.Element.find` and their index in the list
is reflected in their flattened name:

Example:

.. doctest::

  >>> from flatland import List, String
  >>> Names = List.named('names').of(String.named('name'))
  >>> names = Names([u'a', u'b'])
  >>> names.value
  [u'a', u'b']
  >>> names.flatten()
  [(u'names_0_name', u'a'), (u'names_1_name', u'b')]
  >>> names[1].value
  u'b'
  >>> names.find_child('1').value
  u'b'

Validation
----------

If :attr:`~Container.descent_validators` is defined, these validators
will be run first, before member elements are validated.

If :attr:`~flatland.schema.base.Element.validators` is defined, these
validators will be run after member elements are validated.


``List``
--------

.. autoclass:: List

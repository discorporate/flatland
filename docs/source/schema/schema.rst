.. -*- coding: utf-8; fill-column: 78 -*-

========
Elements
========

.. currentmodule:: flatland.schema.base


Elements describe the possible fields of a form; their names, structure,
Python types and rules for validation.  A typical schema consists of at least
one :ref:`container <containers>` type and one or more :ref:`scalar <scalars>`
types:

.. testcode:: fso

  from flatland import Dict, String
  SearchSchema = Dict.named('search').of(String.named(u'keywords'))

FIXME UPDATE:

  FieldSchemas are a bit like Python ``class`` definitions: they need be
  defined only once and don't do much on their own.
  :meth:`FieldSchema.create_element` produces :class:`Elements <Element>`;
  closely related objects that hold and manipulate form data.  Much like a
  Python ``class``, a single ``FieldSchema`` may produce an unlimited number
  of ``Element`` instances.

.. doctest:: fso
  :options: +ELLIPSIS

  >>> form = SearchSchema({u'keywords': u'foo bar baz'})
  >>> form.value
  {u'keywords': u'foo bar baz'}

FIXME UPDATE:

  FieldSchema instances may be freely composed and shared among many
  containers.

.. doctest:: fso

  >>> from flatland import List
  >>> ComposedSchema = Dict.of(SearchSchema,
  ...                          List.named(u'many_searches').of(SearchSchema))
  >>> form = ComposedSchema()
  >>> sorted(form.value.keys())
  [u'many_searches', u'search']

FIXME UPDATE:

    Elements can be supplied to template environments and used to
    great effect there: elements contain all of the information needed
    to display or redisplay a HTML form field, including errors
    specific to a field.

    The :attr:`.u`, :attr:`.x`, :attr:`.xa` and :meth:`el` members are
    especially useful in templates and have shortened names to help
    preserve your sanity when used in markup.


Schema Constructors
-------------------

.. automethod:: Element.named

.. automethod:: Element.using

Factory Methods
---------------

.. automethod:: Element.from_defaults

.. automethod:: Element.from_flat

``Element``
-----------

.. autoclass:: Element
   :members:
   :undoc-members:

   **Instance Attributes**

   .. attribute:: parent

      An owning element, or None if element is topmost or not a member
      of a hierarchy.

   .. attribute:: valid

   .. attribute:: errors = []

      A list of validation error messages.

   .. attribute:: warnings = []

      A list of validation warning messages.

   **Members**

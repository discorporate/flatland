.. -*- coding: utf-8; fill-column: 78 -*-

===================
Schema and Elements
===================

.. currentmodule:: flatland.schema.base

Element classes
---------------

Elements describe the possible fields of a form; their names, structure,
Python types and rules for validation.  A typical schema consists of at least
one :ref:`container <containers>` type and one or more :ref:`scalar <scalars>`
types:

.. testcode:: fso

  from flatland import Dict, String
  SearchSchema = Dict.named('search').of(String.named(u'keywords'))

FieldSchemas are a bit like Python ``class`` definitions: they need be
defined only once and don't do much on their own.
:meth:`FieldSchema.create_element` produces :class:`Elements <Element>`; closely
related objects that hold and manipulate form data.  Much like a
Python ``class``, a single ``FieldSchema`` may produce an unlimited
number of ``Element`` instances.

.. doctest:: fso
  :options: +ELLIPSIS

  >>> form = SearchSchema({u'keywords': u'foo bar baz'})
  >>> form.value
  {u'keywords': u'foo bar baz'}

FieldSchema instances may be freely composed and shared among many
containers.

.. doctest:: fso

  >>> from flatland import List
  >>> ComposedSchema = Dict.of(SearchSchema,
  ...                          List.named(u'many_searches').of(SearchSchema))
  >>> form = ComposedSchema()
  >>> sorted(form.value.keys())
  [u'many_searches', u'search']


--------


.. class:: FieldSchema

   .. attribute:: element_type = Element

     The :class:`Element` subclass that will be used to hold data.

   .. attribute:: validators = []

   .. attribute:: ugettext = None

     Provides ``ugettext`` translation support to validation messages
     if set on a subclass or instance.

   .. attribute:: ungettext = None

     Provides ``ungettext`` translation support to validation messages
     if set on a subclass or instance.

   .. automethod:: create_element

   .. automethod:: from_defaults

   .. automethod:: from_flat

   .. automethod:: from_value

   .. automethod:: validate_element

Element objects
---------------

.. autoclass:: Element
   :members:
   :undoc-members:

   .. automethod:: Element.__init__

   .. attribute:: schema

      The :class:`FieldSchema` that constructed the element.

   .. attribute:: parent

      An owning element, or None if element is topmost or not a member
      of a hierarchy.

   .. attribute:: value

      The element's native Python value.  Only validation routines
      should write this attribute directly: use :meth:`set` to update
      the element's value.

   .. attribute:: u

      A Unicode representation of the element's value.  As in
      :attr:`value`, writing directly to this attribute should be
      restricted to validation routines.

   .. attribute:: errors = []

      A list of validation error messages.

   .. attribute:: warnings = []

      A list of validation warning messages.


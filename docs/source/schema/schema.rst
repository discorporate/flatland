==========================
Field Schemas and Elements
==========================

.. currentmodule:: flatland.schema.base

FieldSchema objects
-------------------

FieldSchema describe the possible fields of a form; their names,
structure, Python types and rules for validation.  A typical schema
consists of at least one :ref:`container <containers>` type and one or
more :ref:`scalar <scalars>` types:

.. testcode:: fso

  import flatland
  search_schema = flatland.Dict(u'search_form',
                                flatland.String(u'keywords'))

FieldSchemas are a bit like Python ``class`` definitions: they need be
defined only once and don't do much on their own.
:meth:`FieldSchema.create_element` produces :class:`Elements <Element>`; closely
related objects that hold and manipulate form data.  Much like a
Python ``class``, a single ``FieldSchema`` may produce an unlimited
number of ``Element`` instances.

.. doctest:: fso
  :options: +ELLIPSIS

  >>> form = search_schema.create_element()
  >>> form.set({u'keywords': u'foo bar baz'})
  >>> form.value
  {u'keywords': u'foo bar baz'}
  >>> form.schema
  <flatland.schema.containers.Dict object at 0x...>

FieldSchema instances may be freely composed and shared among many
containers.

.. doctest:: fso

  >>> form_schema = flatland.Dict(u'composed_form',
  ...                            search_schema,
  ...                            flatland.List(u'many_searches',
  ...                                          search_schema))
  >>> form = form_schema.create_element()
  >>> sorted(form.value.keys())
  [u'many_searches', u'search_form']


--------


.. autoclass:: FieldSchema

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


======================
Arrays and MultiValues
======================

.. currentmodule:: flatland.schema.containers

Schema Constructors
-------------------

.. automethod:: Array.named

.. automethod:: Array.of

.. automethod:: Array.using

Factory Methods
---------------

.. automethod:: Array.from_defaults

.. automethod:: Array.from_flat

.. automethod:: Array.from_value

Configurable Attributes
-----------------------

.. autoattribute:: Sequence.child_schema
  :noindex:

.. autoattribute:: Sequence.prune_empty
  :noindex:

``Array``
---------

.. autoclass:: Array
  :show-inheritance:
  :members:
  :inherited-members:
  :exclude-members: child_schema, prune_empty,
     from_defaults, from_flat, from_value,
     create_blank

``MultiValue``
--------------

.. autoclass:: MultiValue
  :show-inheritance:

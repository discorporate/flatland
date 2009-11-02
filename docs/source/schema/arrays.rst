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

Configurable Attributes
-----------------------

.. autoattribute:: Sequence.member_schema
  :noindex:

.. autoattribute:: Sequence.prune_empty
  :noindex:

``Array``
---------

.. autoclass:: Array
  :show-inheritance:
  :members:
  :inherited-members:
  :exclude-members: member_schema, prune_empty,
     from_defaults, from_flat

``MultiValue``
--------------

.. autoclass:: MultiValue
  :show-inheritance:

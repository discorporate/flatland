.. _enums:

============
Enumerations
============

.. currentmodule:: flatland.schema.scalars

Constrained Types
-----------------

.. autoclass:: Constrained
   :show-inheritance:
   :members:

Enumerations
------------

Schema Constructors
-------------------

.. automethod:: Enum.named

.. automethod:: Enum.valued

.. automethod:: Element.using


Factory Methods
---------------

.. automethod:: Element.from_defaults
   :noindex:

.. automethod:: Element.from_flat
   :noindex:

.. automethod:: Element.from_value
   :noindex:

Configurable Attributes
-----------------------

.. autoattribute:: Constrained.child_type
   :noindex:

.. autoattribute:: Enum.valid_values

``Enum``
--------

.. autoclass:: Enum
  :show-inheritance:
  :members:
  :inherited-members:
  :exclude-members: child_type,
     named, using,
     from_defaults, from_flat, from_value

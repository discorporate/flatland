=====
Dicts
=====

.. currentmodule:: flatland.schema.containers

TODO intro

.. _set_policy:

``set()`` Policy
----------------

TODO strict, duck, etc.

Validation
----------

If :attr:`~Container.descent_validators` is defined, these validators
will be run first, before member elements are validated.

If :attr:`~flatland.schema.base.Element.validators` is defined, these
validators will be run after member elements are validated.

Schema Constructors
-------------------

.. automethod:: Dict.named

.. automethod:: Dict.of

.. automethod:: Dict.using

Factory Methods
---------------

.. automethod:: Dict.from_object

Configurable Attributes
-----------------------

.. autoattribute:: Mapping.field_schema

.. autoattribute:: Dict.policy

``Dict``
--------

.. autoclass:: Dict
  :show-inheritance:
  :members:
  :inherited-members:
  :exclude-members: fromkeys, field_schema, policy, from_object,
     named, of, using,
     from_defaults, from_flat


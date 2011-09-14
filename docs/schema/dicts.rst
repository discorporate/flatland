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


``Dict``
--------

.. autoclass:: Dict


``SparseDict``
--------------

.. autoclass:: SparseDict

Validation
==========

TODO: write these docs!

Overview
--------

Event Model
~~~~~~~~~~~

Basic Validation API
--------------------

.. function:: validator(element, state) -> bool


Validation Library
------------------

.. _validation_messaging:

Messaging
~~~~~~~~~

Composing and Extending Validators
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

I18N and L10N
~~~~~~~~~~~~~

Writing Custom Validators
~~~~~~~~~~~~~~~~~~~~~~~~~

Included Validators
~~~~~~~~~~~~~~~~~~~

.. autoclass:: flatland.valid.base.Validator


General
+++++++

.. automodule:: flatland.valid.base
   :members:

Scalars
+++++++

.. automodule:: flatland.valid.scalars
   :members:

Containers
++++++++++

.. automodule:: flatland.valid.containers
   :members:

Strings
+++++++

.. automodule:: flatland.valid.string
   :members:

Numbers
+++++++

.. automodule:: flatland.valid.number
   :members:

URLs
++++

.. autoclass:: flatland.valid.urls.URLValidator
   :members: __init__
   :show-inheritance:

   **Methods**


.. autoclass:: flatland.valid.urls.HTTPURLValidator
   :members: __init__, all_parts
   :show-inheritance:

   **Methods**


.. autoclass:: flatland.valid.urls.URLCanonicalizer
   :members: __init__
   :show-inheritance:

   **Methods**


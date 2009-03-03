.. _scalars:

=============================
Strings, Numbers and Booleans
=============================

Simple Fields
-------------

.. autoclass:: flatland.schema.scalars.Scalar
   :show-inheritance:
   :members:

Strings
-------

.. currentmodule:: flatland

.. autoclass:: String
   :show-inheritance:
   :members:


Numbers
-------

.. autoclass:: flatland.schema.scalars.Number
   :show-inheritance:
   :members:

   .. attribute:: type_ = None

   .. attribute:: format = "%s"

.. currentmodule:: flatland

.. autoclass:: Integer
   :show-inheritance:

   .. attribute:: type_ = int

   .. attribute:: format = "%i"

.. autoclass:: Long
   :show-inheritance:

   .. attribute:: type_ = long

   .. attribute:: format = "%i"

.. autoclass:: Float
   :show-inheritance:

   .. attribute:: type_ = float

   .. attribute:: format = "%f"

Booleans
--------

.. currentmodule:: flatland

.. autoclass:: flatland.Boolean
   :show-inheritance:
   :members:

   .. attribute:: true_synonyms

     A sequence of acceptable string equivalents for True, such as
     ``u'on'``, ``u'1'``, etc.

   .. attribute:: false_synonyms

     A sequence of acceptable string equivalents for False, such as
     ``u'off'``, ``u''``, etc.


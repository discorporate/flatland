===============
Dates and Times
===============

.. currentmodule:: flatland.schema.scalars

.. autoclass:: Temporal

   .. attribute:: type_

     Abstract. The native type for element values, will be called with
     positional arguments per :attr:`used` below.

   .. attribute:: regex

     Abstract. A regular expression to parse datetime values from a
     string.  Must supply named groupings.

   .. attribute:: used

     Abstract. A sequence of regex match group names.  These matches
     will be converted to ints and supplied to the :attr:`type_`
     constructor in the order specified.

   .. attribute:: format

     Abstract.  A Python string format for serializing the native
     value.  The format will be supplied a dict containing all
     attributes of the native type.


.. autoclass:: DateTime

.. autoclass:: Date

.. autoclass:: Time

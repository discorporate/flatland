.. -* coding: utf-8; fill-column: 78 -*-
.. _containers:

===================
Abstract Containers
===================

.. currentmodule:: flatland.schema.containers

Containers
----------

.. autoclass:: Container
   :show-inheritance:
   :members:


Sequences
---------

::
  >>> from flatland import List, String
  >>> Names = List.named('names').of(String.named('name'))

  >>> pruned = Names()
  >>> pruned.set_flat([('names_0_name', 'first'),
  ...                  ('names_99_name', 'last')])
  >>> pruned.value
  [u'first', u'last']

  >>> unpruned = Names(prune_empty=False)
  >>> unpruned.set_flat([('names_0_name', 'first'),
  ...                    ('names_99_name', 'last')])
  >>> len(unpruned.value)
  100
  >>> unpruned.value[0:3]
  [u'first', None, None]

.. autoclass:: Sequence
   :show-inheritance:
   :members: prune_empty


Mappings
--------

.. autoclass:: Mapping

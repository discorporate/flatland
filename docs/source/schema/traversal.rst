=========
Traversal
=========

.. currentmodule:: flatland.schema

Flatland supplies a rich set of tools for working with structured data.  For
this section, we'll use the following schema as an example.  It is simple yet
has a bit of variety in its structure.

.. testcode::

  from flatland import Form, Dict, List, String, Integer

  class Annotation(Form):
      """A spot on a 2D surface."""
      title = String
      flags = List.of(Integer)
      location = Dict.of(Integer.named('x'),
                         Integer.named('y'))

  sample_data = {
    'title': 'Interesting Spot',
    'flags': [1, 3, 5],
    'location': {'x': 10, 'y': 20},
  }

  ann1 = Annotation(sample_data, name=u'ann1')


Going Raw
---------

You may not even need to use any of these traversal strategies in your
application.  An element's :attr:`~base.Element.value` is a full & recursive
"export" of its native Python value.  Many times this is sufficient.

.. doctest::

  >>> ann1['title']  # ann1 is a flatland structure
  <String u'title'; value=u'Interesting Spot'>
  >>> type(ann1.value)  # but its .value is not
  <type 'dict'>
  >>> ann1.value == sample_data
  True


Python Syntax
-------------

Containers elements such as :class:`~forms.Form`, :class:`~containers.Dict`,
and :class:`~containers.List` implement the Python methods you'd expect for
their type.  In most cases you may use them as if they were ``dict`` and
``list`` instances- the difference being that they always contain
:class:`~base.Element` instances.

For example, ``Form`` and ``Dict`` can be indexed and used like ``dict``:

.. doctest::

  >>> ann1['title'].value
  u'Interesting Spot'
  >>> ann1['location']['x'].value
  10
  >>> sorted(ann1['location'].items())
  [(u'x', <Integer u'x'; value=10>), (u'y', <Integer u'y'; value=20>)]
  >>> u'title' in ann1
  True

And ``List`` and similar types can be used like lists:

.. doctest::

  >>> ann1['flags']
  [<Integer None; value=1>, <Integer None; value=3>, <Integer None; value=5>]
  >>> ann1['flags'][0].value
  1
  >>> ann1['flags'].value
  [1, 3, 5]
  >>> Integer(3) in ann1['flags']
  True
  >>> 3 in ann1['flags']
  True

The final example is of special note: the value in the expression is not an
``Element``.  Most containers will accept native Python values in these types
of expressions and convert them into a temporary ``Element`` for the
operation.  The example below is equivalent to the example above.

.. doctest::

  >>> ann1['flags'].member_schema(3) in ann1['flags']
  True


Traversal Properties
--------------------

Elements of all types support a core set of properties that allow navigation
to related elements: :attr:`~base.Element.root`,
:attr:`~base.Element.parents`, :attr:`~base.Element.children`, and
:attr:`~base.Element.all_children`.

.. doctest::

  >>> list(ann1['flags'].children)
  [<Integer None; value=1>, <Integer None; value=3>, <Integer None; value=5>]
  >>> list(ann1['title'].children)  # title is a String and has no children
  []
  >>> sorted(el.name for el in ann1.all_children if el.name)
  [u'flags', u'location', u'title', u'x', u'y']
  >>> [el.name for el in ann1['location']['x'].parents]
  [u'location', u'ann1']

Each of these properties (excepting ``root``) returns an iterator of
elements.

.. _path_lookups:

Path Lookups
------------

Another option for operating on elements is the :meth:`~base.Element.find`
method.  ``find`` selects elements by *path*, a string that represents one or
more related elements.  Looking up elements by path is a powerful technique to
use when authoring flexible & reusable validators.

.. doctest::

   >>> ann1.find('title')   # find 'ann1's child named 'title'
   [<String u'title'; value=u'Interesting Spot'>]

Paths are evaluated relative to the element:

.. doctest::

   >>> ann1['location'].find('x')
   [<Integer u'x'; value=10>]

Referencing parents is possible with ``..``:

.. doctest::

   >>> ann1['location']['x'].find('../../title')
   [<String u'title'; value=u'Interesting Spot'>]

Absolute paths begin with a ``/``.

   >>> ann1['location']['x'].find('/title')
   [<String u'title'; value=u'Interesting Spot'>]

Members of sequences can be selected like any other child (their index number
is their name), or you can use Python-like slicing:

   >>> ann1.find('/flags/0')
   [<Integer None; value=1>]
   >>> ann1.find('/flags[0]')
   [<Integer None; value=1>]

Full Python slice notation is supported as well.  With slices, paths can
select more than one element.

   >>> ann1.find('/flags[:]')
   [<Integer None; value=1>, <Integer None; value=3>, <Integer None; value=5>]
   >>> ann1.find('/flags[1:]')
   [<Integer None; value=3>, <Integer None; value=5>]

Further path operations are permissible after slices.  A richer schema is
needed to illustrate this:

  >>> Points = List.of(List.of(Dict.of(Integer.named('x'),
  ...                                  Integer.named('y'))))
  >>> p = Points([[dict(x=1, y=1), dict(x=2, y=2)],
  ...             [dict(x=3, y=3)]])
  >>> p.find('[:][:]/x')
  [<Integer u'x'; value=1>, <Integer u'x'; value=2>, <Integer u'x'; value=3>]

The equivalent straight Python to select the same set of elements is quite a
bit more wordy.


Path Syntax
~~~~~~~~~~~

``/`` (leading slash)
    Selects the root of the element tree

``element``
    The name of a child element

``element/child``
    ``/`` separates path segments

``..``
    Traverse to the parent element

``element[0]``
    For a sequence container element, select the 0th child

``element[:]``
    Select all children of a container element (need not be a sequence)

``element[1:5]``
    Select a slice of a sequence container's children

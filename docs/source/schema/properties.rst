========================
Annotations & Properties
========================

.. currentmodule:: flatland.schema.base

Flatland provides two options for annotating schemas and data.


Standard Python
---------------

Element schemas are normal Python classes and can be extended in all
of the usual ways.  For example, you can add an attribute when
subclassing:

.. testcode:: pyann

  from flatland import String

  class Textbox(String):
      tooltip = 'Undefined'


Once an attribute has been added to an element class, its value can be
overridden by further subclassing or, more compactly, with the
:meth:`~Element.using` schema constructor:

.. testcode:: pyann

  class Password(Textbox):
      tooltip = 'Enter your password'


  Password = Textbox.using(tooltip='Enter your password')
  assert Password.tooltip == 'Enter your password'

Both are equivalent, and the custom ``tooltip`` will be inherited by
any subclasses of ``Password``.  Likewise, instances of ``Password``
will have the attribute as well.

.. testcode:: pyann

  el = Password()
  assert el.tooltip = 'Enter your password'

And because the :meth:`Element` constructor allows overriding any
schema attribute by keyword argument, individual element instances can
be constructed with own values, masking the value provided by their
class.

.. testcode:: pyann

  password_match = Textbox(tooltip='Enter your password again')

  assert password_match.tooltip == 'Enter your password again'


Properties
----------

Another option for annotation is the :attr:`~Element.properties`
mapping of element classes and instances.  Unlike class attributes,
almost any object you like can be used as the key in the mapping.

The unique feature of :attr:`~Element.properties` is data inheritance:

.. testcode:: props

  from flatland import String

  # Textboxes are Strings with tooltips
  Textbox = String.with_properties(tooltip='Undefined')

  # A Password is a Textbox with a custom tooltip message
  Password = Textbox.with_properties(tooltip='Enter your password')

  assert Textbox.properties['tooltip'] == 'Undefined'
  assert Password.properties['tooltip'] == 'Enter your password'

Annotations made on a schema are visible to itself and any subclasses,
but not to its parents.

.. testcode:: props

  # Add disabled to all Textboxes
  Textbox.properties['disabled'] = False

  # disabled is inherited from Textbox
  assert Password.properties['disabled'] is False

  # changes in a subclass do not affect the parent
  del Password.properties['disabled']
  assert 'disabled' in Textbox.properties


Annotating With Properties
--------------------------

To create a new schema that includes additional properties, construct
it with :meth:`~Element.with_properties`:

.. testcode:: props

  Textbox = String.with_properties(tooltip='Undefined')

Or if the schema has already been created, manipulate its
:attr:`~Element.properties` mapping:

.. testcode:: props

  class Textbox(String):
     pass

  Textbox.properties['tooltip'] = 'Undefined'

The :attr:`~Element.properties` mapping is implemented as a view over
the Element schema inheritance hierarchy.  If annotations are added to
a superclass such as :class:`~flatland.schema.scalars.String`, they
are visible immediately to all Strings and subclasses.

Private Annotations
-------------------

To create a schema with completely unrelated properties, not
inheriting from its superclass at all, declare it with
:meth:`~Element.using`:

.. testcode:: props

  Alone = Textbox.using(properties={'something': 'else'})
  assert 'tooltip' not in Alone.properties

Or when subclassing longhand, construct a
:class:`~flatland.schema.properties.Properties` collection explicitly.

.. testcode:: props

  from flatland import Properties

  class Alone(Textbox):
     properties = Properties(something='else')

  assert 'tooltip' not in Alone.properties

An instance may also have a private collection of properties.  This
can be done either at or after construction:

.. testcode:: props

  solo1 = Textbox(properties={'something': 'else'})

  solo2 = Textbox()
  solo2.properties = {'something': 'else'}

  Textbox.properties['background_color'] = 'red'

  assert 'background_color' not in solo1.properties
  assert 'background_color' not in solo2.properties


..  LocalWords:  pyann tooltip Textbox

.. -*- coding: utf-8; fill-column: 78 -*-

.. _Validation:

==========
Validation
==========

Basic Validation
----------------

All elements support validation.  The default, built-in validation logic is
simple: if the element is empty, it is invalid.  Otherwise it is valid.

If that sounds too simple don't worry- you can customize validation to suit
your needs.

Validating an Element
~~~~~~~~~~~~~~~~~~~~~

.. doctest::

  >>> from flatland import String
  >>> form = String()
  >>> form.is_empty
  True
  >>> form.valid
  Unevaluated
  >>> form.validate()
  False
  >>> form.valid
  False

Validation sets the :attr:`~flatland.Element.valid` attribute of each element
it inspects.  :meth:`~flatland.Element.validate` may be invoked more than
once.

.. doctest::

  >>> form.set('Squiznart')
  True
  >>> form.is_empty
  False
  >>> form.validate()
  True
  >>> form.valid
  True

Note that default validation does not set any error messages that might be
displayed to an interactive user.  Messages are easily added through custom
validation.

Validating Entire Forms At Once
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:meth:`~flatland.Element.validate` is recursive by default.  Called on a
parent node, it will decend through all of its children, validating each.  If
the parent or any one of its children are invalid, ``validate`` returns false.
Note that recursion does **not** stop if it finds an invalid child: all
children are evaluated, and each will have its :attr:`~flatland.Element.valid`
attribute updated.

Optional Fields
~~~~~~~~~~~~~~~

If a field is marked as :attr:`~flatland.FieldSchema.optional`, its elements
are exempt from validation when empty.  With the default validation strategy,
this effectively means that element can never be invalid.  With custom
validation, optional fields become more useful.

.. doctest::

  >>> from flatland import Dict, Integer
  >>> schema = Dict.of(Integer.named('x'),
  ...                  Integer.named('y'),
  ...                  Integer.named('z').using(optional=True))
  >>> form = schema(dict(x=1))
  >>> form.validate()
  False
  >>> form.valid
  True
  >>> form['x'].valid
  True
  >>> form['y'].valid
  False
  >>> form['z'].valid
  True


Validation Signals
~~~~~~~~~~~~~~~~~~

The :obj:`flatland.signals.validator_validated` signal is emitted each time a
validator evaluates an element.  The signal's sender is the validator (or the
symbol :obj:`flatland.validation.NotEmpty` for the default validation
strategy).  The signal also sends the ``element``, the ``state``, and the
``result`` of the validation function.

During development, it can be convenient to connect the
:obj:`~flatland.signals.validator_validated` signal to a logging function to
aid in debugging.

.. testcode:: signals

  from flatland.signals import validator_validated

  @validator_validated.connect
  def monitor_validation(sender, element, state, result):
      # print or logging.debug validations as they happen:
      print "validation: %s(%s) valid == %r" % (
        sender, element.flattened_name(), result)

.. doctest:: signals

  >>> from flatland import String
  >>> form = String(name='surname')
  >>> form.validate()
  validation: NotEmpty(surname) valid == False
  False

.. testcode:: signals
  :hide:

  from flatland.signals import validator_validated
  validator_validated._clear_state()


Custom Validation
-----------------

The default validation support is useful for some tasks, however in many cases
you will want to provide your own validation rules tailored to your schema.

Flatland provides a low level interface for custom validation logic, based on
a simple callable.  Also provided is a higher level, class-based interface
that provides conveniences for messaging, i18n and validator reuse.  A library
of commonly needed validators is included.

Custom Validation Basics
~~~~~~~~~~~~~~~~~~~~~~~~

To use custom validation, assign a list of one or more validators to a field's
:attr:`~flatland.FieldSchema.validators` attribute.  Each validator will be
evaluated in sequence until a validator returns false or the list of
validators is exhausted.  If the list is exhausted and all have returned true,
the element is considered valid.

A validator is a callable of the form:

.. function:: validator(element, state) -> bool

``element`` is the element being validated, and ``state`` is the value passed
into :meth:`~flatland.Element.validate`, which defaults to ``None``.

A typical validator will examine the :attr:`~flatland.Element.value` of the
element:

.. testcode::

  def no_shouting(element, state):
      """Disallow ALL CAPS TEXT."""
      if element.value.isupper():
          return False
      else:
          return True

  # Try out the validator
  from flatland import String
  form = String(validators=[no_shouting])
  form.set('OH HAI')
  assert not form.validate()
  assert not form.valid


Validation Phases
~~~~~~~~~~~~~~~~~

There are two phases when validating an element or container of elements.
First, each element is visited once descending down the container,
breadth-first.  Then each is visited again ascending back up the container.

The simple, scalar types such as :class:`~flatland.String` and
:class:`~flatland.Integer` process their
:attr:`~flatland.FieldSchema.validators` on the **descent** phase.  The
containers, such as :class:`~flatland.Form` and :class:`~flatland.List` process
:attr:`~flatland.FieldSchema.validators` on the **ascent** phase.

The upshot of the phased evaluation is that container validators fire after
their children, allowing container validation logic that considers the
validity and status of child elements.

.. doctest::

  >>> from flatland import Dict, String
  >>> def tattle(element, state):
  ...     print element.name
  ...     return True
  ...
  >>> schema = (Dict.named('outer').
  ...                of(String.named('inner').
  ...                          using(validators=[tattle])).
  ...                using(validators=[tattle]))
  >>> form = schema()
  >>> form.validate()
  inner
  outer
  True


Short-Circuiting Descent Validation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Descent validation can be aborted early by returning :obj:`~flatland.SkipAll`
or :obj:`~flatland.SkipAllFalse` from a validator.  Children will not be
validated or have their :attr:`~flatland.Element.valid` attribute assigned.
This capability comes in handy in a web environment when designing rich UIs.

Containers will run any validators in their
:attr:`~flatland.Container.descent_validators` list during the decent phase.
Decent validation is the only phase that may be short-circuited.

.. doctest::

  >>> from flatland import Dict, SkipAll, String
  >>> def skip_children(element, state):
  ...     return SkipAll
  ...
  >>> def always_fail(element, state):
  ...     return False
  ...
  >>> schema = Dict.of(String.named('child').using(validators=[always_fail])).\
  ...               using(descent_validators=[skip_children])
  >>> form = schema()
  >>> form.validate()
  True
  >>> form['child'].valid
  Unevaluated


Messaging
~~~~~~~~~

A form that fails to submit without a clear reason is frustrating.  Messages
may be stashed in the :attr:`~flatland.Element.errors` and
:attr:`~flatland.Element.warnings` lists on elements.  In your UI or template
code, these can be used to flag individual form elements that failed
validation and the reason(s) why.

.. _no_shouting:
.. testcode::

  def no_shouting(element, state):
      """Disallow ALL CAPS TEXT."""
      if element.value.isupper():
          element.errors.append("NO SHOUTING!")
          return False
      else:
          return True

See also :meth:`~flatland.Element.add_error`, a wrapper around
``errors.append`` that ensures that identical messages aren't added to an
element more than once.

A powerful and i18n-capable interface to validation and messaging is available
in the higher level :ref:`Validation` API.

Normalization
~~~~~~~~~~~~~

If you want to tweak the element's :attr:`~flatland.Element.value` or
:attr:`~flatland.Element.u` string representation, validators are free to
assign directly to those attributes.  There is no special enforcement of
assignment to these attributes, however the convention is to consider them
immutable outside of normalizing validators.

Validation ``state``
~~~~~~~~~~~~~~~~~~~~

:meth:`~flatland.Element.validate` accepts an optional ``state`` argument.
``state`` can be anything you like, such as a dictionary, an object, or a
string.  Whatever you choose, it will be supplied to each and every validator
that's called.

``state`` can be a convenient way of passing transient information to
validators that require additional information to make their decision.  For
example, in a web environment, one may need to supply the client's IP address
or the logged-in user for some validators to function.

A dictionary is a good place to start if you're considering passing
information in ``state``.  None of the validators that ship with flatland
access ``state``, so no worries about type conflicts there.

.. testcode::

  class User(object):
      """A mock website user class."""

      def check_password(self, plaintext):
          """Mock comparing a password to one stored in a database."""
          return plaintext == 'secret'

  def password_validator(element, state):
      """Check that a field matches the user's current password."""
      user = state['user']
      return user.check_password(element.value)

  from flatland import String
  form = String(validators=[password_validator])
  form.set('WrongPassword')
  state = dict(user=User())
  assert not form.validate(state)


Examining Other Elements
~~~~~~~~~~~~~~~~~~~~~~~~

:class:`~flatland.Element` provides a rich API for accessing a form's members,
an element's parents, children, etc.  Writing simple validators such as
requiring two fields to match is easy, and complex validations are not much
harder.

.. testcode::

  def passwords_must_match(element, state):
      """Both password fields must match for a password change to succeed."""
      if element.value == element.parent.el('password2').value:
          return True
      element.errors.append("Passwords must match.")
      return False

  from flatland import Form, String
  class ChangePassword(Form):
      password = String.using(validators=[passwords_must_match])
      password2 = String
      new_password = String

  form = ChangePassword()
  form.set({'password': 'foo', 'password2': 'f00', 'new_password': 'bar'})
  assert not form.validate()
  assert form['password'].errors


Short-Circuiting Validation
~~~~~~~~~~~~~~~~~~~~~~~~~~~

To stop validation of an element & skip any remaining members of
:attr:`flatland.FieldSchema.validators`, return :obj:`flatland.Skip` from the
validator:

.. testcode::

  from flatland import Skip

  def succeed_early(element, state):
      return Skip

  def always_fails(element, state):
      return False

  from flatland import String
  form = String(validators=[succeed_early, always_fails])
  assert form.validate()

Above, ``always_fails`` is never invoked.

To stop validation early with a failure, simply return False.


Validator API
-------------

The :class:`~flatland.validation.Validator` class implements the validator
callable interface and adds conveniences for messaging, internationalization,
and customization.

To use it, subclass ``Validator`` and implement
:meth:`~flatland.validation.Validator.validate`.

.. testcode:: NoShouting

  from flatland.validation import Validator

  class NoShouting(Validator):
      """Disallow ALL CAPS TEXT."""

      has_shouting = "NO SHOUTING in %(label)s, please."

      def validate(self, element, state):
          if element.value.isupper():
              self.note_error('has_shouting', element, state)
              return False
          return True

  from flatland import String

  schema = String.using(validators=[NoShouting()])

Above is a ``Validator`` version of the basic :ref:`custom validator
<no_shouting>` example.  In this version, the
:meth:`flatland.validation.Validator.note_error` method allows the messaging
to be separated from the validation logic.  ``note_error`` has some useful
features, including templating and automatic I18N translation.


Customizing Validators
~~~~~~~~~~~~~~~~~~~~~~

The base constructor of the ``Validator`` class has a twist that makes
customizing existing Validators on the fly a breeze.  The constructor can be
passed keyword arguments matching any class attribute, and they will be
overridden on the instance.

.. testcode:: NoShouting

  schema = String.using(validators=[NoShouting(has_shouting='shh.')])

Subclassing achieves the same effect.

.. testcode:: NoShouting

  class QuietPlease(NoShouting):
      has_shouting = 'shh.'

  schema = String.using(validators=[QuietPlease()])

The validators that ship with Flatland place all of their messaging and as
much configurable behavior as possible in class attributes to support easy
customization.


Message Templating
~~~~~~~~~~~~~~~~~~

Messages prepared by :meth:`Validator.note_error` and
:meth:`Validator.note_warning` may be templated using keywords in the
sprintf-style Python string format syntax.

Possible keys are taken from multiple sources.  In order of priority:

- Keyword arguments sent to the ``note_error`` and ``note_warning`` methods.

- Elements of ``state``, if ``state`` is dict-like or supports ``[index]``
  access.

- Attributes of ``state``.

- Attributes of the ``Validator`` instance.

- Attributes of the ``element``.


Message Pluralization
~~~~~~~~~~~~~~~~~~~~~

Flatland supports ``ngettext``-style message pluralization.  For this style,
messages are specified as a 3-tuple of (``singular message``, ``plural
message``, ``n-key``).  ``n_key`` is any :ref:`valid templating keyword
<Message Templating>`, and its value ``n`` will be looked up using the same
resolution rules.  If the value ``n`` equals 1, the singular form will be
used.  Otherwise the plural.

.. testcode::

  from flatland.validation import Validator

  class MinLength(Validator):

      min_length = 2

      too_short = (
        "%(label)s must be at least one character long.",
        "%(label)s must be at least %(min_length)s characters long.",
        "min_length")

      def validate(self, element, state):
          if len(element.value) < self.min_length:
              self.note_error(element, state, "too_short")
              return False
          return True

Conditional pluralizaton functions with or without I18N configured.


Message Internationalization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Messages can be translated using gettext-compatible functions.  Translation
works in conjunction with message templating features: the message itself is
translated, and strings substituted into the message are also translated
individually.

Translation uses ``ugettext`` and optionally ``ungettext`` functions that you
provide.  You may place these functions in the ``state``, place them on the
``element`` or its schema, or place them in Python's builtins.

An element's ancestry will be searched for these functions.  If you like, you
may assign them soley to the top-most element or its schema and they will be
used to translate all of its child elements.

If you opt to supply ``ugettext`` but not ``ungettext``, Flatland's built-in
pluralization will kick in if a pluralized message is found.  Flatland will
choose the correct form internally, and the result will be fed through
``ugettext`` for translation.


Dynamic Messages
~~~~~~~~~~~~~~~~

Dynamic generated messages can also take advantage of the templating and
internationalization features.  There are two options for dynamic messages
through :meth:`Validator.note_error` and :meth:`Validator.note_warning`:

 1.  Supply the message directly to ``note_error`` using ``message="..."``
     instead of a message key.

 2.  Messages looked up by key may also be callables.  The callable will
     be invoked with ``element`` and ``state``, and should return either
     a message string or a 3-tuple as described in :ref:`pluralization
     <Message Pluralization>`.


The Validator Class
~~~~~~~~~~~~~~~~~~~

.. autoclass:: flatland.validation.Validator
   :members:

Included Validators
-------------------


Scalars
~~~~~~~

.. automodule:: flatland.validation.scalars
   :members:

Containers
~~~~~~~~~~

.. automodule:: flatland.validation.containers
   :members:

Strings
~~~~~~~

.. automodule:: flatland.validation.string
   :members:

Numbers
~~~~~~~

.. automodule:: flatland.validation.number
   :members:

Email Addresses
~~~~~~~~~~~~~~~


.. autoclass:: flatland.validation.IsEmail
   :show-inheritance:

URLs
~~~~

.. autoclass:: flatland.validation.URLValidator
   :members: __init__
   :show-inheritance:

   **Methods**


.. autoclass:: flatland.validation.HTTPURLValidator
   :members: __init__, all_parts
   :show-inheritance:

   **Methods**


.. autoclass:: flatland.validation.URLCanonicalizer
   :members: __init__
   :show-inheritance:

   **Methods**


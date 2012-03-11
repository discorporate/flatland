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
:attr:`~flatland.Container.descent_validators` list during the descent phase.
Descent validation is the only phase that may be short-circuited.

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


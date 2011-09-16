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
parent node, it will descend through all of its children, validating each.  If
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


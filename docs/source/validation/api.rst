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
              self.note_error(element, state, 'has_shouting')
              return False
          return True

  from flatland import String

  schema = String.using(validators=[NoShouting()])

Above is a ``Validator`` version of the basic `Customizing Validators
<no_shouting>`_ example.  In this version, the
:meth:`flatland.validation.Validator.note_error` method allows the
messaging to be separated from the validation logic.  ``note_error`` has
some useful features, including templating and automatic I18N translation.


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

Flatland supports ``ngettext``-style message pluralization.  For this
style, messages are specified as a 3-tuple of (``singular message``,
``plural message``, ``n-key``).  ``n_key`` is any `valid templating keyword
<Message Templating>`_, and its value ``n`` will be looked up using the
same resolution rules.  If the value ``n`` equals 1, the singular form will
be used.  Otherwise the plural.

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

Conditional pluralization functions with or without I18N configured.

.. _msg-i18n:

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
may assign them solely to the top-most element or its schema and they will be
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
     a message string or a 3-tuple as described in `pluralization
     <Message Pluralization>`_.


The Validator Class
~~~~~~~~~~~~~~~~~~~

.. autoclass:: flatland.validation.base.Validator
   :no-show-inheritance:


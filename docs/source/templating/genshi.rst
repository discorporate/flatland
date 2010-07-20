Genshi Templates
================

.. highlight:: html

Direct Element Access
---------------------

Examples::

  You entered username: ${form.el('username').u}

  <ul py:with="username=form.el('username')" py:if="username.errors">
    <li py:for="msg in username.errors">Error: ${error}</li>
  </ul>

Binding Elements to Input Controls
----------------------------------

Form controls may be bound to a flatland element::

  <input type="text" form:bind="form.el('username').bind"/>

The missing ``name` and ``value`` attributes will be filled by the
flatland filter::

  <input type="text" name="username" value="jek"/>

The filter understands HTML and will intelligently expand and
manipulate the attributes and value of any tag containing a
`form:bind` attribute.  You can also request expansions on tags
unknown to the filter, for example adding a managed ``tabindex`` onto
an ``<a />`` tag.

.bind and .binds
~~~~~~~~~~~~~~~~

The flatland Genshi filter augments the :class:`Element` class and
adds two properties: :attr:`.bind` and :attr:`.binds`.

:attr:`.bind` returns a value suitable for use in a ``form:bind=``
attribute.  This additional step is made necessary by the combination
of Genshi's filter architecture and the quirkiness of Genshi's
expression evaluation for rich Python types like the :class:`Element`.

The :attr:`.binds` collection is an iterable, indexable tree-like
collection of :attr:`.bind` values.  If you want to refer to nested
form elements in an expression, use either the :attr:`.binds`
collection or the :meth:`.el <Element.el>` method to resolve the
path::

  <input type="text" form:bind="form.binds.login.name" />
  <py:if test="form.el('login.name').errors">...</py:if>
  <input type="password" form:bind="form.el('login.password').bind" />

The Genshi expression engine's blending of ``.attribute`` and
``[index]`` access interferes with reliable access to elements.  In
Python code, ``form['login']['name']`` would return the (presumably
String) "name" element, however the same expression executed in a
Genshi template is equivalent to ``form['login'].name``.

Configuring .bind
~~~~~~~~~~~~~~~~~

:attr:`.bind` returns a string containing the eval-able path to the
element.  These values are written out into the markup during Genshi's
first pass.  On the second pass, the flatland filter consumes the
paths and uses that information to look up the :class:`Element`
instances in the context.

For this two-pass, indirect processing to work, the root element needs
to know where it is located in Genshi's Context.  flatland provides
some default lookup behavior and a customization option.

unnamed :class:`Forms <Form>` and top-level :class:`Elements <Element>`:
  Assumes the element has been added to the context as 'form'::

    myform = MyForm.from_defaults()
    context = {'form': myform}
    stream = flatland_filter(template.generate(**context), **context)
    return stream.generate()

named :class:`Forms <Form>` and top-level :class:`Elements <Element>`:
  Assumes the context contains a dictionary named 'forms', with a key
  of the element's name and the element as the value::

    form_a = MyForm.from_defaults(name='form_a')
    form_b = MyForm.from_defaults(name='form_b')
    context = {'forms': dict(form_a=form_a, form_b=form_b)}
    stream = flatland_filter(template.generate(**context), **context)
    return stream.generate()

other locations:
  Use :meth:`set_prefix` on the root element to assign a
  Genshi-evalable prefix for the form.  The prefix will have
  ``.el(...)`` appended to complete the lookup.


Scope
-----

Tag transformations can be selectively enabled, disabled and
configured at the individual tag level or applied to multiple tags
using the <form:with> and <form:set> tags.

Boolean settings may be "on" or "off", or set to "auto" to revert to
the transformation's built-in default setting.

<form:with></form:with>
~~~~~~~~~~~~~~~~~~~~~~~

Configures transformations for enclosed tags.

:`auto-name`_: Boolean or "auto".
:`auto-value`_: Boolean or "auto".
:`auto-domid`_: Boolean or "auto".
:`domid-format <auto-domid>`_: A string.
:`auto-for`_: Boolean or "auto".
:`auto-tabindex`_: Boolean or "auto".
:`tabindex <auto-tabindex>`_: An integer.

Example::

  <form:with auto-value="off">
    <!-- blank form -->
    <input type="text" form:bind="form.x.bind" />
    <input type="text" form:bind="form.y.bind" />
  </form:with>

<form:with> can nest as deeply as needed::

  <form:with auto-tabindex="on" tabindex="100">
    <input type="text" form:bind="form.x.bind" />
    <form:with tabindex="200">
      <input type="text" form:bind="form.y.bind" />
    </form:with>
    <input type="text" form:bind="form.z.bind" />
  </form:with>

This would emit fields with tabindexes 100, 200, 101.

<form:set />
~~~~~~~~~~~~

Configures transformations for all subsequent tags.

:`auto-name`_: Boolean or "auto".
:`auto-value`_: Boolean or "auto".
:`auto-domid`_: Boolean or "auto".
:`domid-format <auto-domid>`_: A string.
:`auto-for`_: Boolean or "auto".
:`auto-tabindex`_: Boolean or "auto".
:`tabindex <auto-tabindex>`_: An integer.

Example::

  <input type="text" form:bind="form.x.bind" />
  <form:set auto-value="off" />
  <!-- the following tag will not receive an auto-value. --->
  <input type="text" form:bind="form.y.bind" />

Configuration changes made by ``set`` take effect immediately and will
remain in effect until the end of the document or enclosing ``with``
scope, if any::

  <form:with auto-tabindex="on" tabindex="100">
    <input type="text" form:bind="form.a.bind" />
    <form:with tabindex="200">
      <input type="text" form:bind="form.b.bind" />
      <form:set tabindex="210">
      <input type="text" form:bind="form.c.bind" />
    </form:with>
    <input type="text" form:bind="form.d.bind" />
  </form:with>

This would emit fields with tabindexes 100, 200, 210, 101.

Transformations
---------------

Bound markup tags can be transformed by the flatland filter.
Attributes and values can be added, removed or corrected to match the
element's state.  Transforms can be turned on an off at the scope
level, or controlled at the individual tag level.  Any of the
transforms can be specified as an attribute::

  <tag form:auto-name="on" />
  <tag form:auto-name="off" />

Setting a transform to "on" on the tag itself will force application
of the transform to the tag, allowing the transform to be used on tags
and in situations outside of its default.  Most transforms will still
require a ``form:bind`` for context, however ``form:auto-tabindex``
can be used on any markup element without a bind.

auto-name
~~~~~~~~~

:Default: on
:Tags: button, form, input, select, textarea

Sets the tag ``name=`` to the bound element's :attr:`.name
<Element.name>`.  Takes no action if the markup already contains a
``name=`` unless forced by setting ``form:auto-name="on"``.

  .. code-block:: html

    <!-- receives a name attribute -->
    <input type="text" form:bind="${form.field.bind}" />

    <!-- leaves name="existing" -->
    <input type="text" name="existing" form:bind="${form.field.bind}" />

    <!-- replaces name="existing" with the element's name -->
    <input type="text" name="existing" form:bind="${form.field.bind}" form:auto-name="on" />


auto-value
~~~~~~~~~~

:Default: on
:Tags: button, input, select, textarea

Uses the bound element's :attr:`Element.u` as the value for the tag.
The exact semantics of "value" vary by tag.

<input type=[text, password, hidden, button, submit, reset]>:

  Sets the ``value=""`` attribute of the tag, or omits the attribute
  if :attr:`.u <Element.u>` is an empty string.

  If the tag has a literal ``value=`` attribute in the markup already,
  it will be used preferentially unless ``form:auto-value="on"`` is
  applied to the tag.

  .. code-block:: html

    <!-- receives a value attribute -->
    <input type="text" form:bind="${form.field.bind}" />

    <!-- will not have value added -->
    <input type="text" form:bind="${form.field.bind}" form:auto-value="off" />

    <!-- the literal value will be used, not bind.u -->
    <input type="text" form:bind="${form.field.bind}" value="foo" />

<input type=[image, file]>:

  No value is added unless forced by setting ``form:auto-value="on"``
  on the tag.

  .. code-block:: html

    <!-- will not have value added -->
    <input type="image" form:bind="${form.field.bind}" />

    <!-- forced, receives a value attribute -->
    <input type="image" form:bind="${form.field.bind}" form:auto-value="on" />

<input type=radio>:

  Radio buttons will add a ``checked="checked"`` attribute if the
  literal ``value=`` matches the :attr:`Element.u` or, if the bind is
  a :class:`Container`, the :attr:`.u <Element.u>` of one of its
  children.

  If the tag lacks a ``value=`` attribute, no action is taken.

  .. code-block:: html

    <input type="radio" form:bind="${form.field.bind}" value="choice_a"/>
    <input type="radio" form:bind="${form.field.bind}" value="choice_b"/>
    <input type="radio" form:bind="${form.field.bind}" value="choice_c"/>

<input type=checkbox>:

  Radio buttons will add a ``checked="checked"`` attribute if the
  literal ``value=`` matches the :attr:`Element.u` or, if the bind is
  a :class:`Container`, the :attr:`.u <Element.u>` of one of its
  children.

  .. code-block:: html

    <input type="radio" form:bind="${form.field.bind}" value="choice_a"/>
    <input type="radio" form:bind="${form.field.bind}" value="choice_b"/>
    <input type="radio" form:bind="${form.field.bind}" value="choice_c"/>

  If no ``value=`` is present in the markup and the bound element's
  schema is a :class:`Boolean`, a ``value=`` will be added using the
  schema's :attr:`Boolean.true`.

  If the tag otherwise lacks a ``value=`` attribute, no action is
  taken.

<input type=???>:

  For types unknown to flatland, no value is set unless forced by
  setting ``form:auto-value="on"`` on the tag.

<textarea/>:

  Textareas will insert the :attr:`Element.u` inside the tag pair.
  Existing content between the tags will be left in place unless value
  application is forced with ``form:auto-value="on"``.

  .. code-block:: html

    <!-- these: -->
    <textarea form:bind="${form.field.bind}" />
    <textarea form:bind="${form.field.bind}"></textarea>

    <!-- will both render as -->
    <textarea name="field">value</textarea>

<select/>:

  Select tags apply a ``selected="selected"`` attribute to their
  `<option>` tags that match the :attr:`Element.u` or, if the bind is
  a :class:`Container`, the :attr:`.u <Element.u>` of one of its
  children.

  For this matching to work, the ``<option>`` tags must have a literal
  value set in the markup.  The value may an explicit ``value=``
  attribute, or it may be the text of the tag.  Leading and trailing
  whitespace will be stripped when considering the text of the tag as
  the value.

  The below will emit ``selected="selected"`` if form.field is equal
  to any of "a", "b", "c", and "d".

  .. code-block:: html

    <select form:bind="${form.field.bind}">
       <option>a</option>
       <option value="b"/>
       <option value="c">label</option>
       <option>
         d
       </option>
    </select>

<button/> and <button value=""/>:

  Regular ``<button />`` tags will insert the :attr:`Element.u` inside
  the ``<button></button>`` tag pair.  The output will **not** be
  XML-escaped, allowing any markup in the :attr:`.u <Element.u>` to
  render properly.

  If the tag contains a literal ``value=`` attribute and a value
  override is forced by setting ``form:auto-value="on"``, the
  :attr:`.u <Element.u>` will be placed in the ``value=`` attribute,
  replacing the existing content.  The value is escaped in this case.

  .. code-block:: html

    <!-- set or replace the inner *markup* -->
    <button form:bind="${form.field.bind}"/>
    <button form:bind="${form.field.bind}" form:auto-value="on">xyz</button>

    <!-- set the value, retaining the value= style used in the original -->
    <button form:bind="${form.field.bind}" value="xyz" form:auto-value="on"/>



auto-domid
~~~~~~~~~~

:Default: off
:Tags: button, input, select, textarea

Sets the ``id=`` attribute of the tag.  Takes no action if the markup
already contains a ``id=`` unless forced by setting
``form:auto-domid="on"``.

The id is generated by combining the bound element's
:meth:`flattened_name <Element.flattened_name>` with the
``domid-format`` in the current Scope_.  The default format is
**f_%s**.


auto-for
~~~~~~~~

:Default: on
:Tags: label

Sets the ``for=`` attribute of the tag to the id of the bound element.
The id is generated using the same process as auto-domid_.  No
consistency checks are performed on the generated id value.

Defaults to "on", and will only apply if auto-domid_ is also "on".
Takes no action if the markup already contains a ``id=`` unless forced
by setting ``form:auto-for="on"``.

.. code-block:: html

  <form:with auto-domid="on">
    <fieldset py:with="field=form.field">
      <label form:bind="${field.bind}">${field.label.x}</label>
      <input type="text" form:bind="${field}" />
    </fieldset>
  </form:with>


auto-tabindex
~~~~~~~~~~~~~

:Default: off
:Tags: button, input, select, textarea

Sets the ``tabindex`` attribute of tags with an incrementing integer.

Numbering starts at the scope's ``tabindex``, which has no default.
Assigning a value for ``tabindex`` will set the value for the next
tabindex assignment, and subsequent assignments will increment by one.

A ``tabindex`` value of 0 will block the assignment of a tabindex and
will not be incremented.

Takes no action if the markup already contains a ``tabindex=`` unless
forced by setting ``form:auto-tabindex="on"``.

.. code-block:: html

  <form:with auto-tabindex="on" tabindex="1">
    <!-- assigns tabindex="1" -->
    <input type="text" form:bind="${form.field.bind}"/>

    <!-- leaves existing tabindex in place -->
    <input type="text" tabindex="-1" form:bind="${form.field.bind}"/>

    <!-- assigns tabindex="2" -->
    <a href="#" form:auto-tabindex="on" />
  </form:with>

Integration With Python
-----------------------

TODO: doc!

.. testsetup::

  from genshi.template import MarkupTemplate, Context

  template = MarkupTemplate('<hello-world/>')
  context = Context()

.. testcode::

  from flatland.out.genshi import flatland_filter

  stream = flatland_filter(template.generate(context), context)
  content = stream.render()

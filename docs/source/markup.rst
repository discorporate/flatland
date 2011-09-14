HTML Forms and Markup
=====================

Flatland is not explicitly a form library, although it handles that task
handily with powerful type conversion and validation error reporting.
Dedicated form libraries often provide sophisticated "widget" or "control"
features to render data fields as complex HTML markup with CSS and JavaScript
support.  The full expression of these features is outside Flatland's scope.

However!  Properly generating HTML form tags and filling them with processed
data is tedious and a common need, so Flatland ships with a minimalistic yet
powerful toolset for tag generation.  These tools are both highly usable as-is
and also a solid base for constructing higher-level widgeting systems.


Markup Generation
-----------------

The generation formula is simple: a desired tag (such as ``input``) plus a
flatland Element equals a complete HTML tag with attributes like ``name`` and
``value`` filled in using the element's state.

Operating on :class:`~flatland.Element` rather than the raw HTTP input or the
polished final value provides a huge amount of expressive power.  For example,

- Elements carry their validation errors- place these directly next to the
  form fields, or roll them up- your choice.  Highlight failing fields with a
  ``class="error"`` CSS attribute right on the input element.

- (Re)populate form fields with exactly what the user typed, or the normalized
  version.

- Leverage the structure of the schema in template markup- if a form contains
  a list of 1 or more email addresses, loop over that list using your template
  language and render fields.

- Directly access Element properties and metadata, translation functions, and
  cross-element relations to implement complex view problems simply.

Flatland ships with two generator front-ends, both supporting the same
features via a shared backend.  The first,
:class:`~flatland.out.markup.Generator`, is for use in straight Python code,
Jinja2, Mako, Genshi, or any other templating system.  The second is a plugin
for the Genshi templating library that integrates Flatland element binding
directly and naturally into your existing <input/> tags.


Basic DWIM Binding
~~~~~~~~~~~~~~~~~~

.. doctest:: generatorintro

   >>> from flatland.out.markup import Generator
   >>> from flatland import Form, String
   >>> html = Generator()
   >>> class Login(Form):
   ...     username = String
   ...     password = String
   ...
   >>> form = Login({'username': 'jek'})

Basic "Do What I Mean" form binding:

.. doctest:: generatorintro

   >>> print html.input(form['username'])
   <input name="username" value="jek" />

Likewise with Genshi.

.. code-block:: html

   <input form:bind="form.username" />

and Genshi generates:

.. code-block:: html

   <input name="username" value="jek" />


Attributes Too
~~~~~~~~~~~~~~

Any HTML attribute can be included.  Generated attributes can be overriden,
too.

This time, the Generator is used in a Jinja2 template.

.. doctest:: generatorintro

    >>> from jinja2 import Template
    >>> template = Template("""\
    ... {{ html.input(form.username, name="other", class_="custom") }}
    ... """)
    >>> print template.render(html=html, form=form)
    <input name="other" value="jek" class="custom" />

These features are very similar in Genshi, too.

.. code-block:: html

   <input form:bind="form.username" name="other" class="custom" />

Which generates the same output:

.. code-block:: html

   <input name="other" value="jek" class="custom" />

Many Python templating systems allow you to replace the indexing operator
(``form['username']``) with the attribute operator (``form.username``) to
improve readability in templates.  As shown above, this kind of rewriting
trickery is generally not a problem for Flatland.  Just keep name collisions
in mind- if your form has a String field called ``name``, is ``form.name`` the
value of your form's name attribute or is it the String field?  When writing
macros or reusable functions, using the explicit ``form[...]`` index syntax is
a good choice to protect against unexpected mangling by the template system no
matter what the fields are named.


And More
~~~~~~~~

The tag and attribute generation behavior can be configured and even
post-processed just as you like it, affecting all of your tags, just one
template, a block, or even individual tags.


Controlling Attribute Transformations
-------------------------------------

Out of the box, generation will do everything required for form element
rendering and repopulation: filling ``<textarea>s``, checking checkboxes, etc.
Flatland can also generate some useful *optional* attributes, such as ``id=``
and ``for=`` linking for ``<label>s``.  Generation of attributes is controlled
with markup options at several levels:

Global:
   Everything generated with a Generator instance or within a Genshi
   rendering operation.

Block:
   Options can be overridden within the scope of a block, reverting to their
   previous value at the end of the block.

Tag:
   Options can overriden on a per-tag basis.

Default:
   Finally, each tag has a set of sane default behaviors.

Boolean options may be True, or False, "on" or "off", or set to "auto" to
revert to the transformation's built-in default setting.


Transformations
---------------

Most transforms require a Flatland element for context, such as setting an
``input`` tag's ``value=`` to the element's Unicode value.  These tags can be
said to be "bound" to the element.

Tags need not be bound, however.  Here an unbound ``textarea`` can still
participate in ``tabindex=`` generation.

.. testsetup:: transforms1

   from flatland.out.markup import Generator

.. doctest:: transforms1

   >>> html = Generator(tabindex=100)
   >>> print html.textarea()
   <textarea></textarea>
   >>> print html.textarea(auto_tabindex=True)
   <textarea tabindex="100"></textarea>
   >>> html.set(auto_tabindex=True)
   u''
   >>> print html.textarea()
   <textarea tabindex="101"></textarea>


Setting a boolean option to "on" or True on the tag itself will always attempt
to apply the transform, allowing the transform to be applied to arbitrary tags
that normally would not be transformed.

.. doctest:: transforms1

   >>> print html.tag('squiznart', auto_tabindex=True)
   <squiznart tabindex="102" />

The Python APIs and the Generator tags use "_"-separated transform names
(valid Python identifiers) as shown below, however please note that Genshi
uses XML-friendly "-"-separated attribute names in markup.

.. testsetup:: transforms2

   from flatland.out.markup import Generator
   from flatland import Form, String
   html = Generator()
   class Login(Form):
       username = String
       password = String
   form = Login({'username': 'jek', 'password': 'secret'})


auto_name
~~~~~~~~~

:Default: on
:Tags: button, form, input, select, textarea

Sets the tag ``name=`` to the bound element's :attr:`.name <Element.name>`.
Takes no action if the tag already contains a ``name=`` attribute, unless
forced.

Receives a ``name=`` attribute:

.. doctest:: transforms2

  >>> print html.input(form['username'], type="text")
  <input type="text" name="username" value="jek" />

Uses the explicitly provided ``name="foo"``:

.. doctest:: transforms2

  >>> print html.input(form['username'], type="text", name='foo')
  <input type="text" name="foo" value="jek" />

Replaces ``name="foo"`` with the element's name:

.. doctest:: transforms2

  >>> print html.input(form['username'], type="text", name='foo', auto_name=True)
  <input type="text" name="username" value="jek" />



auto_value
~~~~~~~~~~

:Default: on
:Tags: button, input, select, textarea

Uses the bound element's :attr:`.u <Element.u>` Unicode value for the tag's
value.  The semantics of "value" vary by tag.

``<input>`` types **text**, **hidden**, **button**, **submit** and **reset**:

  Sets the ``value=""`` attribute of the tag, or omits the attribute if
  :attr:`.u <Element.u>` is the empty string.

  Receives a ``value=`` attribute:

  .. doctest:: transforms2

    >>> print html.input(form['username'], type="text")
    <input type="text" name="username" value="jek" />

  Uses the explicitly provided ``value="quux"``:

  .. doctest:: transforms2

    >>> print html.input(form['username'], type="text", value='quux')
    <input type="text" name="username" value="quux" />

``<input>`` types **password**, **image** and **file**:

  No value is added unless forced by setting auto_value on the tag.

  .. doctest:: transforms2

    >>> print html.input(form['password'], type="password")
    <input type="password" name="password" />

  But this behavior can be forced:

  .. doctest:: transforms2

    >>> print html.input(form['password'], type="password", auto_value=True)
    <input type="password" name="password" value="secret" />

``<input>`` type **radio**:

  Radio buttons will add a ``checked="checked"`` attribute if the literal
  ``value=`` matches the element's value.  Or, if the bind is a
  :class:`~flatland.Container`, ``value=`` will be compared against the
  :attr:`.u <Element.u>` of each of the container's children until a match is
  found.

  If the tag lacks a ``value=`` attribute, no action is taken.

  .. doctest:: transforms2

    >>> print form['username'].u
    jek
    >>> print html.input(form['username'], type="radio", value="quux")
    <input type="radio" name="username" value="quux" />
    >>> print html.input(form['username'], type="radio", value="jek")
    <input type="radio" name="username" value="jek" checked="checked" />

``<input>`` type **checkbox**:

  Check boxes will add a ``checked="checked"`` attribute if the literal
  ``value=`` matches the element's value.

  .. doctest:: transforms2

    >>> print form['username'].u
    jek
    >>> print html.input(form['username'], type="checkbox", value="quux")
    <input type="checkbox" name="username" value="quux" />
    >>> print html.input(form['username'], type="checkbox", value="jek")
    <input type="checkbox" name="username" value="jek" checked="checked" />

  Or, if the bind is a :class:`~flatland.Container`, ``value=`` will be
  compared against the :attr:`.u <Element.u>` of each of the container's
  children until a match is found.

  .. doctest:: transforms2

    >>> from flatland import Array
    >>> Bag = Array.named('bag').of(String)
    >>> bag = Bag(['a', 'c'])
    >>> for value in 'a', 'b', 'c':
    ...     print html.input(bag, type="checkbox", value=value)
    ...
    <input type="checkbox" name="bag" value="a" checked="checked" />
    <input type="checkbox" name="bag" value="b" />
    <input type="checkbox" name="bag" value="c" checked="checked" />

  If the tag lacks a ``value=`` attribute, no action is taken, unless the bind
  is a Boolean.  The missing ``value=`` will be added using the schema's
  :attr:`Boolean.true` value.

  .. doctest:: transforms2

    >>> print html.input(form['username'], type="checkbox")
    <input type="checkbox" name="username" />
    >>> from flatland import Boolean
    >>> toggle = Boolean.named('toggle')()
    >>> print html.input(toggle, type="checkbox")
    <input type="checkbox" name="toggle" value="1" />
    >>> toggle.set(True)
    True
    >>> print html.input(toggle, type="checkbox")
    <input type="checkbox" name="toggle" value="1" checked="checked" />
    >>> toggle.true = "yes"

``<input>`` types unknown:

  For types unknown to flatland, no value is set unless forced by setting
  ``form:auto-value="on"`` on the tag.

``<textarea>``:

  Textareas will insert the :attr:`Element.u` inside the tag pair.  Content
  supplied with ``contents=`` for Generators or between Genshi tags will be
  preferred unless forced.

  .. doctest:: transforms2

    >>> print html.textarea(form['username'])
    <textarea name="username">jek</textarea>
    >>> print html.textarea(form['username'], contents="quux")
    <textarea name="username">quux</textarea>

  Note that in Genshi, these two forms are equivalent.

  .. code-block:: html

    <!-- these: -->
    <textarea form:bind="form.username" />
    <textarea form:bind="form.username"></textarea>

    <!-- will both render as -->
    <textarea name="username">jek</textarea>

``<select>``:

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

    <select form:bind="${form.field}">
       <option>a</option>
       <option value="b"/>
       <option value="c">label</option>
       <option>
         d
       </option>
    </select>

``<button/>`` and ``<button value=""/>``:

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
    <button form:bind="${form.field}"/>
    <button form:bind="${form.field}" form:auto-value="on">xyz</button>

    <!-- set the value, retaining the value= style used in the original -->
    <button form:bind="${form.field}" value="xyz" form:auto-value="on"/>



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
      <label form:bind="${field}">${field.label.x}</label>
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
    <input type="text" form:bind="${form.field}"/>

    <!-- leaves existing tabindex in place -->
    <input type="text" tabindex="-1" form:bind="${form.field}"/>

    <!-- assigns tabindex="2" -->
    <a href="#" form:auto-tabindex="on" />
  </form:with>


Generator
---------


Genshi Directives
-----------------

::

  http://ns.discorporate.us/flatland/genshi

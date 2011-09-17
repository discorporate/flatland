Widgets using Templates and Schema Properties
=============================================

Unlike utilities more directly focused on processing Web forms, Flatland
does not include any concept of "widgets" that render a field.  It is
however easy enough to employ Flatland's "properties" and markup generation
support to build our own widget system.  This also gives us complete
control over the rendering.

::

  from flatland import Form, String

  Input = String.with_properties(template='input.html', type='text')
  Password = Input.with_properties(type='password')

  class SignInForm(Form):
      username = Input.using(label='Username')
      password = Password.using(label='Password')


Rendering Widgets with Genshi
-----------------------------

To render a field, we simply inspect its properties to locate a template
that we include, passing it the field instance.  With Genshi, it might look
something like this:

.. sourcecode:: html+genshi

  <html
      xmlns:py="http://genshi.edgewall.org/"
      xmlns:xi="http://www.w3.org/2001/XInclude"
    >
    <body>
      <form>

        <xi:include
            py:for="field in form.children"
            href="widgets/${field.properties.template}"
          />

      </form>
    </body>
  </html>


The widget template in turn might look something like this:

.. sourcecode:: html+genshi

  <fieldset
      xmlns:form="http://ns.discorporate.us/flatland/genshi"
      xmlns:py="http://genshi.edgewall.org/"
      form:auto-domid="on"
    >

    <label
        form:bind="field"
        py:content="field.label"
      />

    <input
        form:bind="field"
        type="${field.properties.type}"
      />

  </fieldset>


Rendering with Jinja
--------------------

If you prefer to use Jinja you can use Flatland's markup generator
directly.  Our form template might look something like this:

.. sourcecode:: html+jinja

  <form>
    {% for field in form.children %}
      {% include 'widgets/' + field.properties.template %}
    {% endfor %}
  </form>


And the widget template:

.. sourcecode:: html+jinja

  {% do forms.begin(auto_domid=True) %}
    <fieldset>
      {{ forms.label(field, contents=field.label) }}
      {{ forms.input(field, type=field.properties.type) }}
    </fieldset>
  {% do forms.end() %}


Make sure to add a markup generator to the globals of your Jinja
environment::

  from flatland.out.markup import Generator
  jinja_env.globals['forms'] = Generator('html')

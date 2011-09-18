Widgets using Templates and Schema Properties
=============================================

Unlike utilities more directly focused on processing Web forms, Flatland
does not include any concept of "widgets" that render a field.  It is
however easy enough to employ Flatland's "properties" and markup generation
support to build our own widget system.  This also gives us complete
control over the rendering.

::

  from flatland import Form, String

  Input = String.with_properties(widget='input', type='text')
  Password = Input.with_properties(type='password')

  class SignInForm(Form):
      username = Input.using(label='Username')
      password = Password.using(label='Password')

.. testsetup:: *

  from flatland import Form, String

  Input = String.with_properties(widget='input', type='text')
  Password = Input.with_properties(type='password')

  class SignInForm(Form):
      username = Input.using(label='Username')
      password = Password.using(label='Password')


Rendering Widgets with Genshi
-----------------------------

Macros via Genshi's ``py:def`` directive would be a good way to implement
the actual widgets.  For example:

.. literalinclude:: /_fixtures/genshi/widgets.html
  :language: html+genshi


Typically we would call the ``widget`` macro manually for each field we
want rendered, and in the desired order, but for demonstrative purposes
we stub out widgets for each field in arbitrary order:

.. literalinclude:: /_fixtures/genshi/form.html
  :language: html+genshi


.. testcode:: genshi
  :hide:

  from genshi.template import TemplateLoader
  from flatland.out.genshi import setup
  loader = TemplateLoader(['docs/_fixtures/genshi'], callback=setup)
  template = loader.load('form.html')
  form = SignInForm({'username': 'admin', 'password': 'secret'})
  print template.generate(form=form).render()


.. testoutput:: genshi
  :hide:

  <html>
    <body>
      <form>
        <fieldset>
        <label for="f_username">Username</label>
        <input type="text" name="username" value="admin" id="f_username"/>
    </fieldset><fieldset>
        <label for="f_password">Password</label>
        <input type="password" name="password" id="f_password"/>
    </fieldset>
      </form>
    </body>
  </html>


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

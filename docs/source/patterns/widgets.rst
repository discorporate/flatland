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

  form = SignInForm({'username': 'admin', 'password': 'secret'})


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

If you're not using Genshi you can still benefit from Flatland's
schema-aware markup generating support.  With Jinja we might implement the
macros as something resembling this:

.. literalinclude:: /_fixtures/jinja/widgets.html
  :language: html+jinja


Then we can simply import the ``widget`` macro to form templates:

.. literalinclude:: /_fixtures/jinja/form.html
  :language: html+jinja


Make sure to add a markup generator to the globals of your Jinja
environment::

  from flatland.out.markup import Generator
  jinja_env.globals['form_generator'] = Generator('html')


.. testcode:: jinja
  :hide:

  from jinja2 import Environment, FileSystemLoader
  from flatland.out.markup import Generator
  loader = FileSystemLoader('docs/_fixtures/jinja')
  env = Environment(loader=loader, extensions=['jinja2.ext.do'])
  env.globals['form_generator'] = Generator('html')
  template = env.get_template('form.html')
  print template.render(form=form)


.. testoutput:: jinja
  :hide:

  <html>
    <body>
      <form>
  <fieldset>
    <label for="f_username">Username</label>
    <input type="text" name="username" value="admin" id="f_username">
  </fieldset>

  <fieldset>
    <label for="f_password">Password</label>
    <input type="password" name="password" id="f_password">
  </fieldset>

      </form>
    </body>
  </html>

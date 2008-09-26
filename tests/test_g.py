import flatland

template_text = """
<div xmlns="http://www.w3.org/1999/xhtml"
  xmlns:form="http://code.discorporate.us/springy-form"
  xmlns:py="http://genshi.edgewall.org/">

  <h1>$title</h1>

  <py:with vars="form=forms.one">
    <form action="post">
      <input type="text" form:bind="${form.name}"/>
      <input type="text" form:bind="${form.calories}"/>
      <input type="text" form:bind="${form.released_on}"/>
      <py:for each="ingredient in form.ingredients">
        <input type="text" form:bind="${ingredient}"/>
      </py:for>
    </form>
  </py:with>
  <hr/>
  Default form:
  <form action="post">
    <input type="text" form:bind="${form.name}"/>
    <input type="text" form:bind="${form.calories}"/>
    <input type="text" form:bind="${form.released_on}"/>
    <py:for each="ingredient in form.ingredients">
      <input type="text" form:bind="${ingredient}"/>
    </py:for>
  </form>
</div>
"""

def test_sane():
    class Form(flatland.Form):
        schema = [flatland.String('name'),
                  flatland.Integer('calories', 100),
                  flatland.DateTime('released_on', '1999-05-20'),
                  flatland.List('ingredients',
                                flatland.String('ingredient'))]

    req = { 'one_name': 'snack',
            'one_released_on': '2003-12-03',
            'one_calories': 'oink',
            'one_ingredients_1_ingredient': 'grease',
            'one_ingredients_1_ingredient': 'salt',
            'name': 'bare snack',
            'calories': 'bare oink',
            'released_on': '2003-10-03',
            'ingredients_1_ingredient': 'bare grease',
            'ingredients_1_ingredient': 'bare salt',
        }

    snack = Form.from_flat(req)
    snack_one = Form.from_flat(req, name='one')

    context = {'title': 'a test',
               'forms': {}}

    from flatland.out.genshi import genshi_add_to_context, genshi_springy_filter
    import genshi

    genshi_add_to_context(snack, context)
    genshi_add_to_context(snack_one, context)

    o = context['forms']['one']

    template = genshi.template.MarkupTemplate(template_text)
    context = genshi.template.Context(**context)

    stream = template.generate(context)
    print stream.render('xhtml')

    stream = genshi_springy_filter(template.generate(context), context)
    print stream.render('xhtml')

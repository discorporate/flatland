from tests.markup._util import alternate_expectation, desired_output


def simple_schema():
    from flatland import Schema, String

    class SmallForm(Schema):
        name = u'test'

        valued = String
        empty = String

    return SmallForm({u'valued': u'val'})

### value


@desired_output(u'xhtml', simple_schema)
def value_default():
    """<input name="test_valued" value="val" />"""


@value_default.genshi
def test_value_default_genshi():
    """<input form:bind="form.valued"/>"""


@value_default.markup
def test_value_default_markup(gen, el):
    return gen.input(el[u'valued'])


@desired_output(u'xhtml', simple_schema)
def value_disabled():
    """<input name="test_valued" />"""


@value_disabled.genshi
def test_with_value_disabled_genshi():
    """
    <form:with auto-value="off">
      <input form:bind="form.valued"/>
    </form:with>
    """


@value_disabled.markup
def test_with_value_disabled_markup(gen, el):
    gen.begin(auto_value=False)
    output = gen.input(el[u'valued'])
    gen.end()
    return output


@value_disabled.genshi
def test_set_value_disabled_genshi():
    """
    <form:set auto-value="off"/>
    <input form:bind="form.valued"/>
    """


@value_disabled.markup
def test_set_value_disabled_markup(gen, el):
    gen.set(auto_value=False)
    output = gen.input(el[u'valued'])
    return output


@value_disabled.genshi
def test_element_value_disabled_genshi():
    """<input form:bind="form.valued" form:auto-value="off"/>"""


@value_disabled.markup
def test_element_value_disabled_markup(gen, el):
    return gen.input(el[u'valued'], auto_value=False)


@value_disabled.genshi
def test_element_value_auto_genshi():
    """
    <form:with auto-value="no">
      <input form:bind="form.valued" form:auto-value="auto"/>
    </form:with>
    """


@value_disabled.markup
def test_element_value_auto_markup(gen, el):
    gen.begin(auto_value=False)
    output = gen.input(el[u'valued'], auto_value="auto")
    gen.end()
    return output

### name

@desired_output(u'xhtml', simple_schema)
def name_default():
    """<form name="test"></form>"""


@name_default.genshi
def test_name_default_genshi():
    """<form form:bind="form"/>"""


@name_default.markup
def test_name_default_markup(gen, el):
    return gen.form(el)


@desired_output(u'xhtml', simple_schema)
def name_disabled():
    """<form></form>"""


@name_disabled.genshi
def test_with_name_disabled_genshi():
    """
    <form:with auto-name="off">
      <form form:bind="form"/>
    </form:with>
    """


@name_disabled.markup
def test_with_name_disabled_markup(gen, el):
    gen.begin(auto_name=False)
    output = gen.form(el)
    gen.end()
    return output


@name_disabled.genshi
def test_set_name_disabled_genshi():
    """
    <form:set auto-name="off"/>
    <form form:bind="form"/>
    """


@name_disabled.markup
def test_set_name_disabled_markup(gen, el):
    gen.set(auto_name=False)
    output = gen.form(el)
    return output


@name_disabled.genshi
def test_element_name_disabled_genshi():
    """<form form:bind="form" form:auto-name="off"/>"""


@name_disabled.markup
def test_element_name_disabled_markup(gen, el):
    return gen.form(el, auto_name=False)


@name_disabled.genshi
def test_element_name_auto_genshi():
    """
    <form:with auto-name="no">
      <form form:bind="form" form:auto-name="auto"/>
    </form:with>
    """


@name_disabled.markup
def test_element_name_auto_markup(gen, el):
    gen.begin(auto_name=False)
    output = gen.form(el, auto_name="auto")
    gen.end()
    return output

### domid


@desired_output(u'xhtml', simple_schema)
def domid_default():
    """<select name="test_valued"></select>"""


@domid_default.genshi
def test_domid_default_genshi():
    """<select form:bind="form.valued"/>"""


@domid_default.markup
def test_domid_default_markup(gen, el):
    return gen.select(el[u'valued'])


@desired_output(u'xhtml', simple_schema)
def domid_enabled():
    """<select name="test_valued" id="-test_valued-"></select>"""


@domid_enabled.genshi
def test_with_domid_enabled_genshi():
    """
    <form:with auto-domid="on" domid-format="-%s-">
      <select form:bind="form.valued"/>
    </form:with>
    """


@domid_enabled.markup
def test_with_domid_enabled_markup(gen, el):
    gen.begin(auto_domid=True, domid_format=u'-%s-')
    output = gen.select(el[u'valued'])
    gen.end()
    return output


@domid_enabled.genshi
def test_set_domid_enabled_genshi():
    """
    <form:set auto-domid="on" domid-format="-%s-" />
    <select form:bind="form.valued"/>
    """


@domid_enabled.markup
def test_set_domid_enabled_markup(gen, el):
    gen.set(auto_domid=True, domid_format=u'-%s-')
    return gen.select(el[u'valued'])


@domid_enabled.genshi
def test_element_domid_enabled_genshi():
    """
    <form:set domid-format="-%s-" />
    <select form:bind="form.valued" form:auto-domid="on"/>
    """


@domid_enabled.markup
def test_element_domid_enabled_markup(gen, el):
    gen.set(domid_format=u'-%s-')
    return gen.select(el[u'valued'], auto_domid=True)


@domid_enabled.genshi
def test_element_domid_auto_genshi():
    """
    <form:with auto-domid="on" domid-format="-%s-">
      <select form:bind="form.valued" form:auto-domid="auto"/>
    </form:with>
    """


@domid_enabled.markup
def test_element_domid_auto_markup(gen, el):
    gen.begin(auto_domid=True, domid_format=u'-%s-')
    output = gen.select(el[u'valued'], auto_domid=u'auto')
    gen.end()
    return output

### for


### tabindex

### filter


def filter1(tagname, attributes, contents, context, bind):
    attributes[u'class'] = u'required'
    contents += u' *'

    return contents


@desired_output(u'xhtml', simple_schema, funky_filter=filter1)
def filter_enabled():
    """
    <label class="required">field2 *</label>
    """


@filter_enabled.genshi
def test_with_filter_enabled_genshi():
    """
    <form:with auto-filter="on" filters="[funky_filter]">
      <label form:bind="form.valued">field2</label>
    </form:with>
    """


@filter_enabled.markup
def test_with_filter_enabled_markup(gen, el, funky_filter):
    gen.begin(auto_filter=True, filters=[funky_filter])
    output = gen.label(el[u'valued'], contents=u'field2')
    gen.end()
    return output

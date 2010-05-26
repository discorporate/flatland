from tests.markup._util import alternate_expectation, desired_output


def simple_schema():
    from flatland import Form, String

    class SmallForm(Form):
        name = "test"

        valued = String
        empty = String

    return SmallForm({u'valued': u'val'})

### value


@desired_output('xhtml', simple_schema)
def value_default():
    """<input name="test_valued" value="val" />"""


@value_default.genshi_06
def test_value_default_genshi_06():
    """<input form:bind="form.valued"/>"""


@value_default.genshi_05
def test_value_default_genshi_05():
    """<input form:bind="${form.valued.bind}"/>"""


@value_default.markup
def test_value_default_markup(gen, el):
    return gen.input(el['valued'])


@desired_output('xhtml', simple_schema)
def value_disabled():
    """<input name="test_valued" />"""


@value_disabled.genshi_06
def test_with_value_disabled_genshi_06():
    """
    <form:with auto-value="off">
      <input form:bind="form.valued"/>
    </form:with>
    """


@value_disabled.genshi_05
def test_with_value_disabled_genshi_05():
    """
    <form:with auto-value="off">
      <input form:bind="${form.valued.bind}"/>
    </form:with>
    """


@value_disabled.markup
def test_with_value_disabled_markup(gen, el):
    gen.begin(auto_value=False)
    output = gen.input(el['valued'])
    gen.end()
    return output


@value_disabled.genshi_06
def test_set_value_disabled_genshi_06():
    """
    <form:set auto-value="off"/>
    <input form:bind="form.valued"/>
    """


@value_disabled.genshi_05
def test_set_value_disabled_genshi_05():
    """
    <form:set auto-value="off" />
    <input form:bind="${form.valued.bind}"/>
    """


@value_disabled.markup
def test_set_value_disabled_markup(gen, el):
    gen.set(auto_value=False)
    output = gen.input(el['valued'])
    return output


@value_disabled.genshi_06
def test_element_value_disabled_genshi_06():
    """<input form:bind="form.valued" form:auto-value="off"/>"""


@value_disabled.genshi_05
def test_element_value_disabled_genshi_05():
    """<input form:bind="${form.valued.bind}" form:auto-value="off"/>"""


@value_disabled.markup
def test_element_value_disabled_markup(gen, el):
    return gen.input(el['valued'], auto_value=False)


@value_disabled.genshi_06
def test_element_value_auto_genshi_06():
    """
    <form:with auto-value="no">
      <input form:bind="form.valued" form:auto-value="auto"/>
    </form:with>
    """


@value_disabled.genshi_05
def test_element_value_auto_genshi_05():
    """
    <form:with auto-value="no">
      <input form:bind="${form.valued.bind}" form:auto-value="off"/>
    </form:with>
    """


@value_disabled.markup
def test_element_value_auto_markup(gen, el):
    gen.begin(auto_value=False)
    output = gen.input(el['valued'], auto_value="auto")
    gen.end()
    return output

### name

@desired_output('xhtml', simple_schema)
def name_default():
    """<form name="test"></form>"""


@name_default.genshi_06
def test_name_default_genshi_06():
    """<form form:bind="form"/>"""


@name_default.genshi_05
def test_name_default_genshi_05():
    """<form form:bind="${form.bind}"/>"""


@name_default.markup
def test_name_default_markup(gen, el):
    return gen.form(el)


@desired_output('xhtml', simple_schema)
def name_disabled():
    """<form></form>"""


@name_disabled.genshi_06
def test_with_name_disabled_genshi_06():
    """
    <form:with auto-name="off">
      <form form:bind="form"/>
    </form:with>
    """


@name_disabled.genshi_05
def test_with_name_disabled_genshi_05():
    """
    <form:with auto-name="off">
      <form form:bind="${form.bind}"/>
    </form:with>
    """


@name_disabled.markup
def test_with_name_disabled_markup(gen, el):
    gen.begin(auto_name=False)
    output = gen.form(el)
    gen.end()
    return output


@name_disabled.genshi_06
def test_set_name_disabled_genshi_06():
    """
    <form:set auto-name="off"/>
    <form form:bind="form"/>
    """


@name_disabled.genshi_05
def test_set_name_disabled_genshi_05():
    """
    <form:set auto-name="off" />
    <form form:bind="${form.bind}"/>
    """


@name_disabled.markup
def test_set_name_disabled_markup(gen, el):
    gen.set(auto_name=False)
    output = gen.form(el)
    return output


@name_disabled.genshi_06
def test_element_name_disabled_genshi_06():
    """<form form:bind="form" form:auto-name="off"/>"""


@name_disabled.genshi_05
def test_element_name_disabled_genshi_05():
    """<form form:bind="${form.bind}" form:auto-name="off"/>"""


@name_disabled.markup
def test_element_name_disabled_markup(gen, el):
    return gen.form(el, auto_name=False)


@name_disabled.genshi_06
def test_element_name_auto_genshi_06():
    """
    <form:with auto-name="no">
      <form form:bind="form" form:auto-name="auto"/>
    </form:with>
    """


@name_disabled.genshi_05
def test_element_name_auto_genshi_05():
    """
    <form:with auto-name="no">
      <form form:bind="${form.bind}" form:auto-name="off"/>
    </form:with>
    """


@name_disabled.markup
def test_element_name_auto_markup(gen, el):
    gen.begin(auto_name=False)
    output = gen.form(el, auto_name="auto")
    gen.end()
    return output

### domid


@desired_output('xhtml', simple_schema)
def domid_default():
    """<select name="test_valued"></select>"""


@domid_default.genshi_06
def test_domid_default_genshi_06():
    """<select form:bind="form.valued"/>"""


@domid_default.genshi_05
def test_domid_default_genshi_05():
    """<select form:bind="${form.valued.bind}"/>"""


@domid_default.markup
def test_domid_default_markup(gen, el):
    return gen.select(el['valued'])


@desired_output('xhtml', simple_schema)
@alternate_expectation(
    'genshi_05',
    '<select id="-test_valued-" name="test_valued"></select>')
def domid_enabled():
    """<select name="test_valued" id="-test_valued-"></select>"""


@domid_enabled.genshi_06
def test_with_domid_enabled_genshi_06():
    """
    <form:with auto-domid="on" domid-format="-%s-">
      <select form:bind="form.valued"/>
    </form:with>
    """


@domid_enabled.genshi_05
def test_with_domid_enabled_genshi_05():
    """
    <form:with auto-domid="on" domid-format="-%s-">
      <select form:bind="${form.valued.bind}"/>
    </form:with>
    """


@domid_enabled.markup
def test_with_domid_enabled_markup(gen, el):
    gen.begin(auto_domid=True, domid_format="-%s-")
    output = gen.select(el['valued'])
    gen.end()
    return output


@domid_enabled.genshi_06
def test_set_domid_enabled_genshi_06():
    """
    <form:set auto-domid="on" domid-format="-%s-" />
    <select form:bind="form.valued"/>
    """


@domid_enabled.genshi_05
def test_set_domid_enabled_genshi_05():
    """
    <form:set auto-domid="on" domid-format="-%s-" />
    <select form:bind="${form.valued.bind}"/>
    """


@domid_enabled.markup
def test_set_domid_enabled_markup(gen, el):
    gen.set(auto_domid=True, domid_format="-%s-")
    return gen.select(el['valued'])


@domid_enabled.genshi_06
def test_element_domid_enabled_genshi_06():
    """
    <form:set domid-format="-%s-" />
    <select form:bind="form.valued" form:auto-domid="on"/>
    """


@domid_enabled.genshi_05
def test_element_domid_enabled_genshi_05():
    """
    <form:set domid-format="-%s-" />
    <select form:bind="${form.valued.bind}" form:auto-domid="on"/>
    """


@domid_enabled.markup
def test_element_domid_enabled_markup(gen, el):
    gen.set(domid_format="-%s-")
    return gen.select(el['valued'], auto_domid=True)


@domid_enabled.genshi_06
def test_element_domid_auto_genshi_06():
    """
    <form:with auto-domid="on" domid-format="-%s-">
      <select form:bind="form.valued" form:auto-domid="auto"/>
    </form:with>
    """


@domid_enabled.genshi_05
def test_element_domid_auto_genshi_05():
    """
    <form:with auto-domid="on" domid-format="-%s-">
      <select form:bind="${form.valued.bind}" form:auto-domid="auto"/>
    </form:with>
    """


@domid_enabled.markup
def test_element_domid_auto_markup(gen, el):
    gen.begin(auto_domid=True, domid_format="-%s-")
    output = gen.select(el['valued'], auto_domid="auto")
    gen.end()
    return output

### for


### tabindex

### filter


def filter1(tagname, attributes, contents, context, bind):
    attributes['class'] = 'required'
    contents += ' *'

    return contents


@desired_output('xhtml', simple_schema, funky_filter=filter1)
def filter_enabled():
    """
    <label class="required">field2 *</label>
    """


@filter_enabled.genshi_06
def test_with_filter_enabled_genshi_06():
    """
    <form:with auto-filter="on" filters="[funky_filter]">
      <label form:bind="form.valued">field2</label>
    </form:with>
    """


@filter_enabled.markup
def test_with_filter_enabled_markup(gen, el, funky_filter):
    gen.begin(auto_filter=True, filters=[funky_filter])
    output = gen.label(el['valued'], contents='field2')
    gen.end()
    return output

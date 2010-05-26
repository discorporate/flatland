from tests.markup._util import desired_output


def simple_schema():
    from flatland import Form, String

    class SmallForm(Form):
        valued = String
        empty = String

    return SmallForm({u'valued': u'val'})

###


@desired_output('html', simple_schema)
def input_value_html():
    """<input name="valued" value="val">"""


@input_value_html.genshi_06
def test_input_value_html_genshi_06():
    """<input form:bind="form.valued"/>"""


@input_value_html.genshi_05
def test_input_value_html_genshi_05():
    """<input form:bind="${form.valued.bind}"/>"""


@input_value_html.markup
def test_input_value_html_markup(gen, el):
    return gen.input(el['valued'])

###


@desired_output('xhtml', simple_schema)
def input_value_xhtml():
    """<input name="valued" value="val" />"""


@input_value_xhtml.genshi_06
def test_input_value_xhtml_genshi_06():
    """<input form:bind="form.valued"/>"""


@input_value_xhtml.genshi_05
def test_input_value_xhtml_genshi_05():
    """<input form:bind="${form.valued.bind}"/>"""


@input_value_xhtml.markup
def test_input_value_xhtml_markup(gen, el):
    return gen.input(el['valued'])

###


@desired_output('xhtml', simple_schema)
def textarea_value():
    """<textarea name="valued">val</textarea>"""


@textarea_value.genshi_06
def test_textarea_value_genshi_06():
    """<textarea form:bind="form.valued"/>"""


@textarea_value.genshi_05
def test_textarea_value_genshi_05():
    """<textarea form:bind="${form.valued.bind}"/>"""


@textarea_value.markup
def test_textarea_value_markup(gen, el):
    return gen.textarea(el['valued'])

###


@desired_output('xhtml', simple_schema)
def textarea_empty_value():
    """<textarea name="empty"></textarea>"""


@textarea_empty_value.genshi_06
def test_textarea_empty_value_genshi_06():
    """<textarea form:bind="form.empty"/>"""


@textarea_empty_value.genshi_05
def test_textarea_empty_value_genshi_05():
    """<textarea form:bind="${form.empty.bind}"/>"""


@textarea_empty_value.markup
def test_textarea_empty_value_markup(gen, el):
    return gen.textarea(el['empty'])

###


@desired_output('xhtml', simple_schema)
def textarea_explicit_value():
    """<textarea name="valued">override</textarea>"""


@textarea_explicit_value.genshi_06
def test_textarea_explicit_value_genshi_06():
    """<textarea form:bind="form.valued">override</textarea>"""


@textarea_explicit_value.genshi_05
def test_textarea_explicit_value_genshi_05():
    """<textarea form:bind="${form.valued.bind}">override</textarea>"""


@textarea_explicit_value.markup
def test_textarea_explicit_value_markup(gen, el):
    return gen.textarea(el['valued'], contents='override')

###


@desired_output('html', simple_schema)
def label_empty_html():
    """<label></label>"""


@label_empty_html.genshi_06
def test_label_empty_html_genshi_06():
    """<label form:bind="form.valued"/>"""


@label_empty_html.genshi_05
def test_label_empty_html_genshi_05():
    """<label form:bind="${form.valued.bind}"/>"""


@label_empty_html.markup
def test_label_empty_html_markup(gen, el):
    return gen.label(el['valued'])

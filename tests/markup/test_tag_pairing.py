from tests.markup._util import desired_output


def simple_schema():
    from flatland import Schema, String

    class SmallForm(Schema):
        valued = String
        empty = String

    return SmallForm({u'valued': u'val'})

###


@desired_output('html', simple_schema)
def input_value_html():
    """<input name="valued" value="val">"""


@input_value_html.genshi
def test_input_value_html_genshi():
    """<input form:bind="form.valued"/>"""


@input_value_html.markup
def test_input_value_html_markup(gen, el):
    return gen.input(el['valued'])

###


@desired_output('xhtml', simple_schema)
def input_value_xhtml():
    """<input name="valued" value="val" />"""


@input_value_xhtml.genshi
def test_input_value_xhtml_genshi():
    """<input form:bind="form.valued"/>"""


@input_value_xhtml.markup
def test_input_value_xhtml_markup(gen, el):
    return gen.input(el['valued'])

###


@desired_output('xhtml', simple_schema)
def textarea_value():
    """<textarea name="valued">val</textarea>"""


@textarea_value.genshi
def test_textarea_value_genshi():
    """<textarea form:bind="form.valued"/>"""


@textarea_value.markup
def test_textarea_value_markup(gen, el):
    return gen.textarea(el['valued'])

###


@desired_output('xhtml', simple_schema)
def textarea_empty_value():
    """<textarea name="empty"></textarea>"""


@textarea_empty_value.genshi
def test_textarea_empty_value_genshi():
    """<textarea form:bind="form.empty"/>"""


@textarea_empty_value.markup
def test_textarea_empty_value_markup(gen, el):
    return gen.textarea(el['empty'])

###


@desired_output('xhtml', simple_schema)
def textarea_explicit_value():
    """<textarea name="valued">override</textarea>"""


@textarea_explicit_value.genshi
def test_textarea_explicit_value_genshi():
    """<textarea form:bind="form.valued">override</textarea>"""


@textarea_explicit_value.markup
def test_textarea_explicit_value_markup(gen, el):
    return gen.textarea(el['valued'], contents='override')

###


@desired_output('html', simple_schema)
def label_empty_html():
    """<label></label>"""


@label_empty_html.genshi
def test_label_empty_html_genshi():
    """<label form:bind="form.valued"/>"""


@label_empty_html.markup
def test_label_empty_html_markup(gen, el):
    return gen.label(el['valued'])

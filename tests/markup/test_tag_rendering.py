from flatland import Array, String

from tests.markup._util import desired_output


def scalar_schema():
    schema = String.named('scalar')
    return schema('abc')


def multivalue_schema():
    schema = Array.named('multi').of(String)
    return schema(['abc', 'xyz'])


@desired_output('xhtml', scalar_schema)
def select():
    """
<select name="scalar">
<option value="abc" selected="selected"></option>
<option value="def">DEF</option>
<option selected="selected">abc</option>
<option value="abc" selected="selected">abc</option>
</select>
"""


@select.genshi
def test_select_genshi():
    """
<select form:bind="form">
<option value="abc" form:bind="form"></option>
<option value="def">DEF</option>
<option>abc</option>
<option value="abc">abc</option>
</select>
    """


@select.markup
def test_select_markup(gen, el):
    output = []
    output += [gen.select.open(el)]
    output += [gen.option(el, value='abc')]
    output += [gen.option(el, value='def', contents='DEF')]
    output += [gen.option(el, contents='abc')]
    output += [gen.option(el, value='abc', contents='abc')]
    output += [gen.select.close()]
    return '\n'.join(output)


@desired_output('xhtml', multivalue_schema)
def multiselect():
    """
<select name="multi" multiple="multiple">
<option value="abc" selected="selected"></option>
<option value="def">DEF</option>
<option selected="selected">xyz</option>
</select>
"""


@multiselect.genshi
def test_multiselect_genshi():
    """
<select name="multi" form:bind="form" multiple="multiple">
<option value="abc"></option>
<option value="def">DEF</option>
<option>xyz</option>
</select>
    """


@multiselect.markup
def test_multiselect_markup(gen, el):
    output = []
    output += [gen.select.open(el, multiple='multiple')]
    output += [gen.option(el, value='abc')]
    output += [gen.option(el, value='def', contents='DEF')]
    output += [gen.option(el, contents='xyz')]
    output += [gen.select.close()]
    return '\n'.join(output)

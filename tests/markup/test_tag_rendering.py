from flatland import Array, String

from tests._util import fails
from tests.markup._util import desired_output


def scalar_schema():
    schema = String.named(u'scalar')
    return schema(u'abc')


def multivalue_schema():
    schema = Array.named(u'multi').of(String)
    return schema([u'abc', u'xyz'])


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


@select.genshi_06
def test_select_genshi_06():
    """
<select form:bind="form">
<option value="abc" form:bind="form"></option>
<option value="def">DEF</option>
<option>abc</option>
<option value="abc">abc</option>
</select>
    """


@select.genshi_05
def test_select_genshi_05():
    """
<select form:bind="form">
<option value="abc"></option>
<option value="def">DEF</option>
<option>abc</option>
<option value="abc">abc</option>
</select>
    """


@select.markup
def test_select_markup(gen, el):
    output = []
    output += [gen.select.open(el)]
    output += [gen.option(el, value=u'abc')]
    output += [gen.option(el, value=u'def', contents=u'DEF')]
    output += [gen.option(el, contents=u'abc')]
    output += [gen.option(el, value=u'abc', contents=u'abc')]
    output += [gen.select.close()]
    return u'\n'.join(output)


@desired_output('xhtml', multivalue_schema)
def multiselect():
    """
<select name="multi" multiple="multiple">
<option value="abc" selected="selected"></option>
<option value="def">DEF</option>
<option selected="selected">xyz</option>
</select>
"""

@multiselect.genshi_06
def test_multiselect_genshi_06():
    """
<select name="multi" form:bind="form" multiple="multiple">
<option value="abc"></option>
<option value="def">DEF</option>
<option>xyz</option>
</select>
    """

@fails("No multiselect on genshi 05")
@multiselect.genshi_05
def test_multiselect_genshi_05():
    """
<select form:bind="${form.bind}" multiple="multiple">
<option value="abc"></option>
<option value="def">DEF</option>
<option>xyz</option>
</select>
    """

@multiselect.markup
def test_multiselect_markup(gen, el):
    output = []
    output += [gen.select.open(el, multiple=u'multiple')]
    output += [gen.option(el, value=u'abc')]
    output += [gen.option(el, value=u'def', contents=u'DEF')]
    output += [gen.option(el, contents=u'xyz')]
    output += [gen.select.close()]
    return u'\n'.join(output)

from flatland import String

from tests._util import fails
from tests.markup._util import desired_output


schema = String.named(u'element').using(default=u'val').from_defaults

### value


@desired_output('html', schema)
def value_bound():
    """<div value="val"></div>"""


@value_bound.genshi_06
def test_value_bound_genshi_06():
    """<div form:bind="form" form:auto-value="on" />"""


@value_bound.genshi_05
def test_value_bound_genshi_05():
    """<div form:bind="form" form:auto-value="on" />"""


@value_bound.markup
def test_value_bound_markup(gen, el):
    return gen.tag('div', el, auto_value=True)


@desired_output('html', None)
def value_unbound():
    """<div></div>"""


@value_unbound.genshi_06
def test_value_unbound_genshi_06():
    """<div form:auto-value="on" />"""


@value_unbound.genshi_05
def test_value_unbound_genshi_05():
    """<div form:auto-value="on" />"""


@value_unbound.markup
def test_value_unbound_markup(gen, el):
    return gen.tag('div', auto_value=True)


### name


@desired_output('html', schema)
def name_bound():
    """<div name="element"></div>"""


@name_bound.genshi_06
def test_name_bound_genshi_06():
    """<div form:bind="form" form:auto-name="on" />"""


@name_bound.genshi_05
def test_name_bound_genshi_05():
    """<div form:bind="form" form:auto-name="on" />"""


@name_bound.markup
def test_name_bound_markup(gen, el):
    return gen.tag('div', el, auto_name=True)


@desired_output('html', None)
def name_unbound():
    """<div></div>"""


@name_unbound.genshi_06
def test_name_unbound_genshi_06():
    """<div form:auto-name="on" />"""


@name_unbound.genshi_05
def test_name_unbound_genshi_05():
    """<div form:auto-name="on" />"""


@name_unbound.markup
def test_name_unbound_markup(gen, el):
    return gen.tag('div', auto_name=True)


### domid


@desired_output('html', schema)
def domid_bound():
    """<div id="f_element"></div>"""


@domid_bound.genshi_06
def test_domid_bound_genshi_06():
    """<div form:bind="form" form:auto-domid="on" />"""


@domid_bound.genshi_05
def test_domid_bound_genshi_05():
    """<div form:bind="form" form:auto-domid="on" />"""


@domid_bound.markup
def test_domid_bound_markup(gen, el):
    return gen.tag('div', el, auto_domid=True)


@desired_output('html', None)
def domid_unbound():
    """<div></div>"""


@domid_unbound.genshi_06
def test_domid_unbound_genshi_06():
    """<div form:auto-domid="on" />"""


@fails('<div id="None"></div>')
@domid_unbound.genshi_05
def test_domid_unbound_genshi_05():
    """<div form:auto-domid="on" />"""


@domid_unbound.markup
def test_domid_unbound_markup(gen, el):
    return gen.tag('div', auto_domid=True)


### for


@desired_output('html', schema)
def for_bound():
    """<div for="f_element"></div>"""


@for_bound.genshi_06
def test_for_bound_genshi_06():
    """<div form:bind="form" form:auto-for="on" />"""


@for_bound.genshi_05
def test_for_bound_genshi_05():
    """<div form:bind="form" form:auto-for="on" />"""


@for_bound.markup
def test_for_bound_markup(gen, el):
    return gen.tag('div', el, auto_for=True)


@desired_output('html', None)
def for_unbound():
    """<div></div>"""


@for_unbound.genshi_06
def test_for_unbound_genshi_06():
    """<div form:auto-for="on" />"""


@for_unbound.genshi_05
def test_for_unbound_genshi_05():
    """<div form:auto-for="on" />"""


@for_unbound.markup
def test_for_unbound_markup(gen, el):
    return gen.tag('div', auto_for=True)


### tabindex


@desired_output('html', schema)
def tabindex_bound():
    """<div tabindex="1"></div>"""


@tabindex_bound.genshi_06
def test_tabindex_bound_genshi_06():
    """
    <form:set tabindex="1"/>
    <div form:bind="form" form:auto-tabindex="on" />
    """


@tabindex_bound.genshi_05
def test_tabindex_bound_genshi_05():
    """
    <form:set tabindex="1"/>
    <div form:bind="form" form:auto-tabindex="on" />
    """


@tabindex_bound.markup
def test_tabindex_bound_markup(gen, el):
    gen.set(tabindex=1)
    return gen.tag('div', el, auto_tabindex=True)


@desired_output('html', None)
def tabindex_unbound():
    """<div tabindex="1"></div>"""


@tabindex_unbound.genshi_06
def test_tabindex_unbound_genshi_06():
    """
    <form:set tabindex="1"/>
    <div form:auto-tabindex="on" />
    """


@tabindex_unbound.genshi_05
def test_tabindex_unbound_genshi_05():
    """
    <form:set tabindex="1"/>
    <div form:auto-tabindex="on" />
    """


@tabindex_unbound.markup
def test_tabindex_unbound_markup(gen, el):
    gen.set(tabindex=1)
    return gen.tag('div', auto_tabindex=True)


### combo

@desired_output('html', schema)
def combo_unbound():
    """<div tabindex="1"></div>"""


@combo_unbound.genshi_06
def test_combo_unbound_genshi_06():
    """
    <form:set tabindex="1"/>
    <div form:auto-tabindex="on" form:auto-domid="on" />
    """


@fails('<div tabindex="1" id="None"></div>')
@combo_unbound.genshi_05
def test_combo_unbound_genshi_05():
    """
    <form:set tabindex="1"/>
    <div form:auto-tabindex="on" form:auto-domid="on" />
    """


@combo_unbound.markup
def test_combo_unbound_markup(gen, el):
    gen.set(tabindex=1)
    return gen.tag('div', auto_tabindex=True, auto_domid=True)

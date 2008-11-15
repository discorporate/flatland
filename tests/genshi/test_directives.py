from tests.genshi._util import (
    FilteredRenderTest, from_text_files, from_docstring)
import flatland


def simple_context():
    schema = flatland.String('field1')
    el = schema.create_element()
    el.set_prefix('field1')
    return {'field1': el}

class TestWith(FilteredRenderTest):
    @from_docstring(context_factory=simple_context)
    def test_tag_options(self):
        """
:: test nothing in context
${value_of('auto-domid')}
${value_of('auto-for')}
${value_of('auto-name')}
${value_of('auto-tabindex')}
${value_of('auto-value')}
:: eq
:: endtest

:: test auto-domid
<form:with auto-domid="auto">
${value_of('auto-domid')}
</form:with>
:: eq
Maybe
:: endtest

:: test auto-for
<form:with auto-for="auto">
${value_of('auto-for')}
</form:with>
:: eq
Maybe
:: endtest

:: test auto-name
<form:with auto-name="auto">
${value_of('auto-name')}
</form:with>
:: eq
Maybe
:: endtest

:: test auto-tabindex
<form:with auto-tabindex="auto">
${value_of('auto-tabindex')}
</form:with>
:: eq
Maybe
:: endtest

:: test auto-value
<form:with auto-value="auto">
${value_of('auto-value')}
</form:with>
:: eq
Maybe
:: endtest

:: test tabindex
<div form:auto-tabindex="on"/>
<form:with tabindex="1000">
<div form:auto-tabindex="on"/>
</form:with>
<div form:auto-tabindex="on"/>
:: eq
<div />
<div tabindex="1000" />
<div />
:: endtest

:: test domid format
<div form:bind="${field1.bind}" form:auto-domid="on" />

<form:with domid-format="id_%s_di">
<div form:bind="${field1.bind}" form:auto-domid="on" />
</form:with>

<div form:bind="${field1.bind}" form:auto-domid="on" />
:: eq
<div id="f_field1" />

<div id="id_field1_di" />

<div id="f_field1" />
:: endtest

        """


class TestSet(FilteredRenderTest):
    @from_docstring(context_factory=simple_context)
    def test_tag_options(self):
        """
:: test nothing in context
${value_of('auto-domid')}
${value_of('auto-for')}
${value_of('auto-name')}
${value_of('auto-tabindex')}
${value_of('auto-value')}
:: eq
:: endtest


:: test auto-domid
<form:set auto-domid="auto" />
${value_of('auto-domid')}
:: eq
Maybe
:: endtest

:: test auto-for
<form:set auto-for="auto" />
${value_of('auto-for')}
:: eq
Maybe
:: endtest

:: test auto-name
<form:set auto-name="auto" />
${value_of('auto-name')}
:: eq
Maybe
:: endtest

:: test auto-tabindex
<form:set auto-tabindex="auto" />
${value_of('auto-tabindex')}
:: eq
Maybe
:: endtest

:: test auto-value
<form:set auto-value="auto" />
${value_of('auto-value')}
:: eq
Maybe
:: endtest


:: test tabindex
<div form:auto-tabindex="on"/>
<form:set tabindex="1000" />
<div form:auto-tabindex="on"/>
<div form:auto-tabindex="on"/>
:: eq
<div />
<div tabindex="1000" />
<div tabindex="1001" />
:: endtest


:: test domid format
<div form:bind="${field1.bind}" form:auto-domid="on" />

<form:set domid-format="id_%s_di" />
<div form:bind="${field1.bind}" form:auto-domid="on" />

<div form:bind="${field1.bind}" form:auto-domid="on" />
:: eq
<div id="f_field1" />

<div id="id_field1_di" />

<div id="id_field1_di" />
:: endtest
        """

from tests.genshi._util import (
    RenderTest, FilteredRenderTest, from_text_files, from_docstring)
import flatland


def small_form():
    schema = flatland.Dict(None, flatland.String('field'))
    el = schema.create_element(value={'field': 'val'})
    el.set_prefix('form')
    return {'form': el}

class TestUnfilteredTags(RenderTest):
    @from_docstring(context_factory=small_form)
    def test_any(self):
        """
:: test
${form.field.bind}
:: eq
form.el(u'.field')
:: endtest

:: test
<div id="${type(form.field.bind).__name__}">x</div>
:: eq
<div id="WrappedElement">x</div>
:: endtest

:: test
<div id="${unicode(form.field.bind)}">x</div>
:: eq
<div id="form.el(u'.field')">x</div>
:: endtest

:: test
<div id="${form.field.bind}">x</div>
:: eq
<div id="form.el(u'.field')">x</div>
:: endtest

:: test
<input type="text" form:bind="${form.field.bind}" />
:: eq
<input type="text" form:bind="form.el(u'.field')" />
:: endtest

:: test
<input type="text" form:bind="${form.field.bind}" name="x"/>
:: eq
<input type="text" form:bind="form.el(u'.field')" name="x"/>
:: endtest
        """


class TestTags(FilteredRenderTest):
    def setup(self):
        from flatland import Dict, String
        self.schema = Dict(None, String('field'))

    @from_docstring(context_factory=small_form)
    def test_empty(self):
        """
:: test
<input type="text" form:bind="${form.field.bind}" />
:: eq  # sneaky
<input type="text" form:bind="form.el(u'.field')" />
:: endtest

:: test
<input type="text" form:bind="${form.field.bind}" />
:: eq
<input type="text" name="field" value="val" />
:: endtest
        """

    @from_docstring(context_factory=small_form)
    def test_auto_name(self):
        """
:: test
<input type="text" form:bind="${form.field.bind}" />
:: eq
<input type="text" name="field" value="val" />
:: endtest

:: test
<form:with auto-name="off">
<input type="text" form:bind="${form.field.bind}" />
</form:with>
:: eq
<input type="text" value="val" />
:: endtest

:: test default fallback
<form:with auto-name="auto">
<input type="text" form:bind="${form.field.bind}" />
</form:with>
:: eq
<input type="text" name="field" value="val" />
:: endtest

:: test full explicit default fallback
<form:with auto-name="auto">
<input type="text" form:bind="${form.field.bind}" form:auto-name="auto" />
</form:with>
:: eq
<input type="text" name="field" value="val" />
:: endtest

:: test local on
<input type="text" form:bind="${form.field.bind}" form:auto-name="on"/>
:: eq
<input type="text" name="field" value="val" />
:: endtest

:: test local off
<input type="text" form:bind="${form.field.bind}" form:auto-name="off"/>
:: eq
<input type="text" value="val" />
:: endtest

:: test existing attribute wins over context on
<input type="text" name="foo" form:bind="${form.field.bind}" />
:: eq
<input type="text" name="foo" value="val" />
:: endtest

:: test local on squeezes out existing attribute
<input type="text" name="foo" form:bind="${form.field.bind}"
  form:auto-name="on"/>
:: eq
<input type="text" name="field" value="val" />
:: endtest

:: test context on
<form:with auto-domid="on">
<input type="text" form:bind="${form.field.bind}" />
</form:with>
:: eq
<input type="text" id="f_field" name="field" value="val" />
:: endtest
        """

    @from_docstring(context_factory=small_form)
    def test_auto_domid(self):
        """
:: test
<input type="text" form:bind="${form.field.bind}" />
:: eq
<input type="text" name="field" value="val" />
:: endtest

:: test
<form:with auto-domid="off">
<input type="text" form:bind="${form.field.bind}" />
</form:with>
:: eq
<input type="text" name="field" value="val" />
:: endtest

:: test default fallback
<form:with auto-domid="auto">
<input type="text" form:bind="${form.field.bind}" />
</form:with>
:: eq
<input type="text" name="field" value="val" />
:: endtest

:: test full explicit default fallback
<form:with auto-domid="auto">
<input type="text" form:bind="${form.field.bind}" form:auto-domid="auto" />
</form:with>
:: eq
<input type="text" name="field" value="val" />
:: endtest

:: test local on
<input type="text" form:bind="${form.field.bind}" form:auto-domid="on"/>
:: eq
<input type="text" id="f_field" name="field" value="val" />
:: endtest

:: test context on
<form:with auto-domid="on">
<input type="text" form:bind="${form.field.bind}" />
</form:with>
:: eq
<input type="text" id="f_field" name="field" value="val" />
:: endtest
</div>
        """

    @from_docstring(context_factory=small_form)
    def test_auto_for(self):
        """
:: test
<label form:bind="${form.field.bind}" />
:: eq
<label />
:: endtest

:: test
<form:with auto-domid="off">
<label form:bind="${form.field.bind}" />
</form:with>
:: eq
<label />
:: endtest

:: test default fallback
<form:with auto-domid="auto">
<label form:bind="${form.field.bind}" />
</form:with>
:: eq
<label />
:: endtest

:: test full explicit default fallback
<form:with auto-domid="auto">
<label form:bind="${form.field.bind}" form:auto-domid="auto" />
</form:with>
:: eq
<label />
:: endtest

:: test local on
<label form:bind="${form.field.bind}" form:auto-for="on"/>
:: eq
<label for="f_field" />
:: endtest

:: test context on
<form:with auto-domid="on">
<label form:bind="${form.field.bind}" />
</form:with>
:: eq
<label for="f_field" />
:: endtest
</div>
        """

    # def test_auto_tabindex
    # def test_auto_value


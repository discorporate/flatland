from tests.genshi._util import (
    rendered_markup_eq_, RenderTest, FilteredRenderTest)
import flatland


class TestUnfilteredTags(RenderTest):
    def setup(self):
        from flatland import Dict, String
        self.schema = Dict(None, String('field'))

    def test_any(self):
        el = self.schema.create_element(value={'field':'val'})
        el.set_prefix('form')
        self.compare_(el, dict(form=el), """
<div xmlns="http://www.w3.org/1999/xhtml"
  xmlns:form="http://code.discorporate.us/springy-form"
  xmlns:py="http://genshi.edgewall.org/">
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

</div>
                   """)


class TestTags(FilteredRenderTest):
    def setup(self):
        from flatland import Dict, String
        self.schema = Dict(None, String('field'))

    def test_empty(self):
        el = self.schema.create_element(value={'field':'val'})
        el.set_prefix('form')
        self.compare_(el, dict(form=el), """
<div xmlns="http://www.w3.org/1999/xhtml"
  xmlns:form="http://code.discorporate.us/springy-form"
  xmlns:py="http://genshi.edgewall.org/">

:: test
<input type="text" form:bind="${form.field.bind}" />
:: eq  # sneaky
<input type="text" form:bind="form.el(u'.field')" />
:: endtest

:: test
<input type="text" form:bind="${form.field.bind}" />
:: eq  # sneaky
<input type="text" name="field" value="val" />
:: endtest
</div>
        """)

    def test_auto_name(self):
        el = self.schema.create_element()
        el.set_prefix('form')
        self.compare_(el, {'form': el}, """
<div xmlns="http://www.w3.org/1999/xhtml"
  xmlns:form="http://code.discorporate.us/springy-form"
  xmlns:py="http://genshi.edgewall.org/">

:: test
<input type="text" form:bind="${form.field.bind}" />
:: eq
<input type="text" name="field" value="" />
:: endtest

:: test
<form:with auto-name="off">
<input type="text" form:bind="${form.field.bind}" />
</form:with>
:: eq
<input type="text" value="" />
:: endtest

:: test default fallback
<form:with auto-name="auto">
<input type="text" form:bind="${form.field.bind}" />
</form:with>
:: eq
<input type="text" name="field" value="" />
:: endtest

:: test full explicit default fallback
<form:with auto-name="auto">
<input type="text" form:bind="${form.field.bind}" form:auto-name="auto" />
</form:with>
:: eq
<input type="text" name="field" value="" />
:: endtest

:: test local on
<input type="text" form:bind="${form.field.bind}" form:auto-name="on"/>
:: eq
<input type="text" name="field" value="" />
:: endtest

:: test local off
<input type="text" form:bind="${form.field.bind}" form:auto-name="off"/>
:: eq
<input type="text" value="" />
:: endtest

:: test existing attribute wins over context on
<input type="text" name="foo" form:bind="${form.field.bind}" />
:: eq
<input type="text" name="foo" value="" />
:: endtest

:: test local on squeezes out existing attribute
<input type="text" name="foo" form:bind="${form.field.bind}"
  form:auto-name="on"/>
:: eq
<input type="text" name="field" value="" />
:: endtest

:: test context on
<form:with auto-domid="on">
<input type="text" form:bind="${form.field.bind}" />
</form:with>
:: eq
<input type="text" id="f_field" name="field" value="" />
:: endtest
</div>
        """)
        self.compare_(el, {'form': el, 'auto-domid': 'on'}, """
<div xmlns="http://www.w3.org/1999/xhtml"
  xmlns:form="http://code.discorporate.us/springy-form"
  xmlns:py="http://genshi.edgewall.org/">

:: test
<input type="text" form:bind="${form.field.bind}" />
:: eq
<input type="text" id="f_field" name="field" value="" />
:: endtest

:: test
<input type="text" form:bind="${form.field.bind}" form:auto-domid="auto" />
:: eq
<input type="text" id="f_field" name="field" value="" />
:: endtest

:: test
<input type="text" form:bind="${form.field.bind}" form:auto-domid="off"/>
:: eq
<input type="text" name="field" value="" />
:: endtest
</div>
    """)

    def test_auto_domid(self):
        el = self.schema.create_element()
        el.set_prefix('form')
        self.compare_(el, {'form': el}, """
<div xmlns="http://www.w3.org/1999/xhtml"
  xmlns:form="http://code.discorporate.us/springy-form"
  xmlns:py="http://genshi.edgewall.org/">

:: test
<input type="text" form:bind="${form.field.bind}" />
:: eq
<input type="text" name="field" value="" />
:: endtest

:: test
<form:with auto-domid="off">
<input type="text" form:bind="${form.field.bind}" />
</form:with>
:: eq
<input type="text" name="field" value="" />
:: endtest

:: test default fallback
<form:with auto-domid="auto">
<input type="text" form:bind="${form.field.bind}" />
</form:with>
:: eq
<input type="text" name="field" value="" />
:: endtest

:: test full explicit default fallback
<form:with auto-domid="auto">
<input type="text" form:bind="${form.field.bind}" form:auto-domid="auto" />
</form:with>
:: eq
<input type="text" name="field" value="" />
:: endtest

:: test local on
<input type="text" form:bind="${form.field.bind}" form:auto-domid="on"/>
:: eq
<input type="text" id="f_field" name="field" value="" />
:: endtest

:: test context on
<form:with auto-domid="on">
<input type="text" form:bind="${form.field.bind}" />
</form:with>
:: eq
<input type="text" id="f_field" name="field" value="" />
:: endtest
</div>
        """)
        self.compare_(el, {'form': el, 'auto-domid': 'on'}, """
<div xmlns="http://www.w3.org/1999/xhtml"
  xmlns:form="http://code.discorporate.us/springy-form"
  xmlns:py="http://genshi.edgewall.org/">

:: test
<input type="text" form:bind="${form.field.bind}" />
:: eq
<input type="text" id="f_field" name="field" value="" />
:: endtest

:: test
<input type="text" form:bind="${form.field.bind}" form:auto-domid="auto" />
:: eq
<input type="text" id="f_field" name="field" value="" />
:: endtest

:: test
<input type="text" form:bind="${form.field.bind}" form:auto-domid="off"/>
:: eq
<input type="text" name="field" value="" />
:: endtest
</div>
        """)

    def test_auto_for(self):
        el = self.schema.create_element()
        el.set_prefix('form')
        self.compare_(el, {'form': el}, """
<div xmlns="http://www.w3.org/1999/xhtml"
  xmlns:form="http://code.discorporate.us/springy-form"
  xmlns:py="http://genshi.edgewall.org/">

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
        """)
        self.compare_(el, {'form': el, 'auto-domid': 'on'}, """
<div xmlns="http://www.w3.org/1999/xhtml"
  xmlns:form="http://code.discorporate.us/springy-form"
  xmlns:py="http://genshi.edgewall.org/">

:: test Context on
<label form:bind="${form.field.bind}" />
:: eq
<label for="f_field" />
:: endtest

:: test local fallback to Context
<label form:bind="${form.field.bind}" form:auto-domid="auto" />
:: eq
<label for="f_field" />
:: endtest

:: test local override Context
<label form:bind="${form.field.bind}" form:auto-for="off"/>
:: eq
<label />
:: endtest
</div>
        """)

    # def test_auto_tabindex
    # def test_auto_value

    def test_others(self):
        el = self.schema.create_element(value={'field':'val'})
        el.set_prefix('form')
        self.compare_(el, dict(form=el), """
<div xmlns="http://www.w3.org/1999/xhtml"
  xmlns:form="http://code.discorporate.us/springy-form"
  xmlns:py="http://genshi.edgewall.org/">

:: test
<input type="text" form:bind="${form.field.bind}" form:auto-domid="off" />
:: eq  # sneaky
<input type="text" name="field" value="val" />
:: endtest

:: test
<input type="text" form:bind="${form.field.bind}" form:auto-value="off" />
:: eq  # sneaky
<input type="text" name="field"  />
:: endtest
</div>
        """)

    


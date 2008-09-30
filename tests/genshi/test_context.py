from tests.genshi._util import (
    RenderTest, FilteredRenderTest, from_text_files, from_docstring)
import flatland


class TestPrefilterTags(RenderTest):
    @from_docstring()
    def test_with(self):
        """
:: test
<form:with />
:: eq
<form:with />
:: endtest

:: test
<form:with>stuff</form:with>
:: eq
<form:with>stuff</form:with>
:: endtest

:: test
<form:with auto-domid="on">
${value_of('auto-domid')}
<div id="${value_of('auto-domid')}" />
</form:with>
:: eq
<form:with auto-domid="on">

<div />
</form:with>
:: endtest

:: test
<form:with auto-domid="true">
  <py:if test="value_of('auto-domid')">
  defined
  </py:if>
  <py:if test="not value_of('auto-domid')">
  not defined
  </py:if>
</form:with>
:: eq
<form:with auto-domid="true">
  not defined
</form:with>
:: endtest

:: test
<form:set />
:: eq
<form:set />
:: endtest

:: test
<form:set>stuff</form:set>
:: eq
<form:set>stuff</form:set>
:: endtest
        """


class TestContext(FilteredRenderTest):
    @from_docstring()
    def test_with_scope(self):
        """
:: test with leaves no trace
<form:with />
:: eq

:: endtest


:: test with passes through inner
<form:with>stuff</form:with>
:: eq
stuff
:: endtest


:: test nothing in context
${value_of('auto-name')}
:: eq
:: endtest


:: test with adds Maybe context
<form:with auto-name="auto">
${value_of('auto-name')}
</form:with>
:: eq
Maybe
:: endtest


:: test with adds True to context
<form:with auto-name="on">
${value_of('auto-name')}
</form:with>
:: eq
True
:: endtest


:: test with adds False to context
<form:with auto-name="off">
${value_of('auto-name')}
</form:with>
:: eq
False
:: endtest


:: test with scopes nest
<form:with auto-name="off">
${value_of('auto-name')}
<form:with auto-name="on">${value_of('auto-name')}</form:with>
<form:with auto-name="auto">${value_of('auto-name')}</form:with>
${value_of('auto-name')}
</form:with>
:: eq
False
True
Maybe
False
::endtest

:: test
<form:with auto-domid="on">
${value_of('auto-domid')}
<div id="${value_of('auto-domid')}" />
</form:with>
:: eq
True
<div id="True" />
:: endtest

:: test
<form:with auto-domid="true">
  <py:if test="value_of('auto-domid')">
  defined
  </py:if>
  <py:if test="not value_of('auto-domid')">
  not defined
  </py:if>
</form:with>
:: eq
  defined
:: endtest
    """

    @from_docstring()
    def test_set_scope(self):
        """
:: test set leaves no trace
<form:set />
:: eq
:: endtest


:: test set pases through inner
<form:set>stuff</form:set>
:: eq
stuff
:: endtest


:: test set does not nest
${value_of('auto-name')}
<form:set auto-name="auto">
${value_of('auto-name')}
</form:set>
${value_of('auto-name')}
:: eq
Maybe
Maybe
:: endtest


:: test set can set any trool
${value_of('auto-name')}
<form:set auto-name="on"/>
${value_of('auto-name')}
<form:set auto-name="off"/>
${value_of('auto-name')}
:: eq
True
False
:: endtest


:: test set really doesn't nest
<form:set auto-name="off">
${value_of('auto-name')}
<form:set auto-name="on">${value_of('auto-name')}</form:set>
<form:set auto-name="off"/>
${value_of('auto-name')}
<form:set auto-name="auto">${value_of('auto-name')}</form:set>
${value_of('auto-name')}
</form:set>
${value_of('auto-name')}
:: eq
False
True
False
Maybe
Maybe
Maybe
:: endtest
        """

    def test_eval_order(self):
        template = """
:: test filter interleaves with py:
<py:if test="is_none(value_of('auto-domid'))">
  <form:with auto-domid="true">
    <py:choose test="is_none(value_of('auto-domid'))">
      <py:when test="1">true</py:when>
      <py:when test="0">false</py:when>
    </py:choose>
  </form:with>
</py:if>
:: eq
      false
:: endtest
"""
        template = self.wrap_with_xmlns(template)
        calls = []
        def is_none(val):
            calls.append(True)
            return val is None
        self.compare_({'is_none': is_none}, template)
        assert len(calls) == 2, len(calls)

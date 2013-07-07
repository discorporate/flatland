from flatland import String
from flatland.out.generic import Markup

from tests._util import assert_raises
from tests.markup._util import render_genshi as render, need


TemplateSyntaxError = None
schema = String.named(u'element').using(default=u'val')


@need('genshi')
def setup():
    global TemplateSyntaxError
    from genshi.template.base import TemplateSyntaxError


def test_version_sensor():
    from flatland.out import genshi
    template = u'not a Genshi 0.6+ template'
    assert_raises(RuntimeError, genshi.setup, template)


def test_bogus_tags():
    for snippet in [
        u'<form:auto-name/>',
        u'<form:auto-value/>',
        u'<form:auto-domid/>',
        u'<form:auto-for/>',
        u'<form:auto-tabindex/>',
        ]:
        assert_raises(TemplateSyntaxError, render, snippet, u'xml', schema)


def test_bogus_elements():
    for snippet in [
        u'<div form:with="snacks" />',
        u'<div form:set="snacks" />',
        ]:
        assert_raises(TemplateSyntaxError, render, snippet, u'xml', schema)


def test_directive_ordering():
    markup = u"""\
<form form:bind="form" py:if="True">
  <input form:bind="form" py:if="False"/>
  <input py:with="foo=form" form:bind="foo" />
</form>
"""
    expected = u"""\
<form name="element">
  <input name="element" value="" />
</form>"""

    rendered = render(markup, u'xhtml', schema)
    assert rendered == expected


def test_attribute_interpolation():
    markup = u"""\
<input form:bind="form" form:auto-domid="${ON}" />
<input form:bind="form" form:auto-domid="o${N}" />
<input type="checkbox" value="${VAL}" form:bind="form" />
<input type="checkbox" value="v${A}l" form:bind="form" />
<input type="checkbox" value="${V}a${L}" form:bind="form" />
"""
    expected = u"""\
<input name="element" value="val" id="f_element" />
<input name="element" value="val" id="f_element" />
<input type="checkbox" value="val" name="element" checked="checked" />
<input type="checkbox" value="val" name="element" checked="checked" />
<input type="checkbox" value="val" name="element" checked="checked" />"""

    rendered = render(markup, u'xhtml', schema.from_defaults,
                      ON=u'on',
                      N=u'n',
                      VAL=Markup(u'val'),
                      V=u'v',
                      A=u'a',
                      L=u'l',
                      )
    assert rendered == expected


def test_pruned_tag():
    markup = u"""\
<form:with auto-name="off" py:if="False">xxx</form:with>
"""
    expected = ""

    rendered = render(markup, u'xhtml', schema)
    assert rendered == expected


def test_attributes_preserved():
    markup = u"""\
<div xmlns:xyzzy="yo">
  <input xyzzy:blat="pow" class="abc" form:bind="form" />
</div>
"""
    expected = u"""\
<div xmlns:xyzzy="yo">
  <input xyzzy:blat="pow" class="abc" name="element" value="" />
</div>"""

    rendered = render(markup, u'xhtml', schema)
    assert rendered == expected


def test_attribute_removal():
    markup = u"""\
<input type="checkbox" form:bind="form" value="xyzzy" checked="checked" />
"""
    expected = u"""\
<input type="checkbox" value="xyzzy" name="element" />"""

    rendered = render(markup, u'xhtml', schema)
    assert rendered == expected


def test_stream_preserved():
    markup = u"""\
<py:def function="stream_fn()"><b py:if="1">lumpy.</b></py:def>
<py:def function="flattenable_fn()"><py:if test="1">flat.</py:if></py:def>
<button form:bind="form">
  <em>wow!</em> ${1 + 1}
</button>
<button form:bind="form">${stream_fn()}</button>
<button form:bind="form">${flattenable_fn()}</button>
"""
    expected = u"""\
<button name="element" value="">
  <em>wow!</em> 2
</button>
<button name="element" value=""><b>lumpy.</b></button>
<button name="element" value="">flat.</button>"""

    rendered = render(markup, u'xhtml', schema)
    assert rendered == expected


def test_tortured_select():
    markup = u"""\
<select form:bind="form">
  <option value="hit"/>
  <option value="miss"/>
  <option value="hit" form:bind=""/>
  <optgroup label="nested">
    <option>
      h${"i"}t
    </option>
    <option value="miss"/>
  </optgroup>
  <optgroup label="nested">
    <option value="hit" form:bind=""/>
  </optgroup>
  <option value="hit" py:if="True">
    <option value="hit">
      <option value="hit" form:bind="form" py:if="True"/>
    </option>
  </option>
</select>
    """

    expected = u"""\
<select name="element">
  <option value="hit" selected="selected"></option>
  <option value="miss"></option>
  <option value="hit"></option>
  <optgroup label="nested">
    <option selected="selected">
      hit
    </option>
    <option value="miss"></option>
  </optgroup>
  <optgroup label="nested">
    <option value="hit"></option>
  </optgroup>
  <option value="hit" selected="selected">
    <option value="hit" selected="selected">
      <option value="hit" selected="selected"></option>
    </option>
  </option>
</select>"""

    factory = schema.using(default=u'hit').from_defaults
    rendered = render(markup, u'xhtml', factory)
    if rendered != expected:
        print("\n" + __name__)
        print("Expected:\n" + expected)
        print("Got:\n" + rendered)
    assert rendered == expected

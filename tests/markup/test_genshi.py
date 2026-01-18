from flatland import String
from flatland.out.generic import Markup

import pytest
from tests.markup._util import render_genshi as render, need

TemplateSyntaxError = None
schema = String.named("element").using(default="val")


@need("genshi")
def setup_module():
    global TemplateSyntaxError
    from genshi.template.base import TemplateSyntaxError


def test_version_sensor():
    from flatland.out import genshi

    template = "not a Genshi 0.6+ template"
    with pytest.raises(RuntimeError):
        genshi.setup(template)


def test_bogus_tags():
    for snippet in [
        "<form:auto-name/>",
        "<form:auto-value/>",
        "<form:auto-domid/>",
        "<form:auto-for/>",
        "<form:auto-tabindex/>",
    ]:
        with pytest.raises(TemplateSyntaxError):
            render(snippet, "xml", schema)


def test_bogus_elements():
    for snippet in [
        '<div form:with="snacks" />',
        '<div form:set="snacks" />',
    ]:
        with pytest.raises(TemplateSyntaxError):
            render(snippet, "xml", schema)


def test_directive_ordering():
    markup = """\
<form form:bind="form" py:if="True">
  <input form:bind="form" py:if="False"/>
  <input py:with="foo=form" form:bind="foo" />
</form>
"""
    expected = """\
<form name="element">
  <input name="element" value="" />
</form>"""

    rendered = render(markup, "xhtml", schema)
    assert rendered == expected


def test_attribute_interpolation():
    markup = """\
<input form:bind="form" form:auto-domid="${ON}" />
<input form:bind="form" form:auto-domid="o${N}" />
<input type="checkbox" value="${VAL}" form:bind="form" />
<input type="checkbox" value="v${A}l" form:bind="form" />
<input type="checkbox" value="${V}a${L}" form:bind="form" />
"""
    expected = """\
<input name="element" value="val" id="f_element" />
<input name="element" value="val" id="f_element" />
<input type="checkbox" value="val" name="element" checked="checked" />
<input type="checkbox" value="val" name="element" checked="checked" />
<input type="checkbox" value="val" name="element" checked="checked" />"""

    rendered = render(
        markup,
        "xhtml",
        schema.from_defaults,
        ON="on",
        N="n",
        VAL=Markup("val"),
        V="v",
        A="a",
        L="l",
    )
    assert rendered == expected


def test_pruned_tag():
    markup = """\
<form:with auto-name="off" py:if="False">xxx</form:with>
"""
    expected = ""

    rendered = render(markup, "xhtml", schema)
    assert rendered == expected


def test_attributes_preserved():
    markup = """\
<div xmlns:xyzzy="yo">
  <input xyzzy:blat="pow" class="abc" form:bind="form" />
</div>
"""
    expected = """\
<div xmlns:xyzzy="yo">
  <input xyzzy:blat="pow" class="abc" name="element" value="" />
</div>"""

    rendered = render(markup, "xhtml", schema)
    assert rendered == expected


def test_attribute_removal():
    markup = """\
<input type="checkbox" form:bind="form" value="xyzzy" checked="checked" />
"""
    expected = """\
<input type="checkbox" value="xyzzy" name="element" />"""

    rendered = render(markup, "xhtml", schema)
    assert rendered == expected


def test_stream_preserved():
    markup = """\
<py:def function="stream_fn()"><b py:if="1">lumpy.</b></py:def>
<py:def function="flattenable_fn()"><py:if test="1">flat.</py:if></py:def>
<button form:bind="form">
  <em>wow!</em> ${1 + 1}
</button>
<button form:bind="form">${stream_fn()}</button>
<button form:bind="form">${flattenable_fn()}</button>
"""
    expected = """\
<button name="element" value="">
  <em>wow!</em> 2
</button>
<button name="element" value=""><b>lumpy.</b></button>
<button name="element" value="">flat.</button>"""

    rendered = render(markup, "xhtml", schema)
    assert rendered == expected


def test_tortured_select():
    markup = """\
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

    expected = """\
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

    factory = schema.using(default="hit").from_defaults
    rendered = render(markup, "xhtml", factory)
    if rendered != expected:
        print("\n" + __name__)
        print("Expected:\n" + expected)
        print("Got:\n" + rendered)
    assert rendered == expected

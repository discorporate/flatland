from flatland import String
from flatland.out.markup import Generator

import pytest


@pytest.fixture
def schema():
    return String.named("field1").using(default="val").from_defaults


@pytest.fixture
def el(schema):
    if schema is not None:
        return schema()


@pytest.fixture
def xmlgen():
    return Generator(markup="xml")


@pytest.fixture(params=["markupsafe", "flatland.out.generic"])
def markup_impl(request):
    mod = pytest.importorskip(request.param)
    return mod.Markup


@pytest.mark.parametrize(
    "markup,expected",
    [
        ("html", """<input type="text" name="field1" value="val">"""),
        ("xml", """<input type="text" name="field1" value="val" />"""),
    ],
)
def test_input_html(markup, expected, schema, el):
    generator = Generator(markup=markup)
    got = generator.input(type="text", bind=el)

    assert hasattr(got, "__html__")
    got = got.strip()

    assert expected == got


def test_detached_reuse(el):
    gen = Generator("xml")

    tag = gen.textarea
    output_a = tag.open(el)
    contents = tag.contents
    output_b = tag.open(el)

    assert contents == tag.contents
    assert output_a == output_b

    assert gen.textarea is tag
    assert gen.textarea.contents == contents
    tag.close()
    assert gen.textarea is not tag
    assert gen.textarea.contents != contents
    tag.close()
    tag.close()


def test_input_close(el, xmlgen):
    """</input>"""
    xmlgen.input(type="text", bind=el)
    assert xmlgen.input.close() == """</input>"""


def test_textarea_escaped(xmlgen, el):
    el.set('"<quoted & escaped>"')
    xmlgen.input(type="text", bind=el)
    assert (
        xmlgen.textarea(el) == """<textarea name="field1">"&lt;"""
        """quoted &amp; escaped&gt;"</textarea>"""
    )


def test_textarea_contents(xmlgen, el):
    xmlgen.textarea.open(el)
    assert xmlgen.textarea.contents == """val"""


def test_textarea_escaped_contents(xmlgen, el):
    bind = el
    bind.set('"<quoted & escaped>"')
    xmlgen.textarea.open(bind)
    assert xmlgen.textarea.contents == '''"&lt;quoted &amp; escaped&gt;"'''


def test_textarea_explicit_contents(xmlgen, el):
    xmlgen.textarea.open(el, contents="xyzzy")
    assert xmlgen.textarea.contents == """xyzzy"""


def test(xmlgen, el, markup_impl):
    xmlgen["markup_wrapper"] = markup_impl
    expected = """<label><x></label>"""
    assert xmlgen.label(contents=markup_impl("<x>")) == expected

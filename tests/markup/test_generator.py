# -*- coding: utf-8 -*-
from flatland import String
from flatland.out.markup import Generator

from tests.markup._util import markup_test


schema = String.named(u'field1').using(default=u'val').from_defaults


@markup_test('html', schema)
def test_input_html(gen, el):
    """<input type="text" name="field1" value="val">"""
    return gen.input(type=u'text', bind=el)


@markup_test('xml', schema)
def test_input_xml(gen, el):
    """<input type="text" name="field1" value="val" />"""
    return gen.input(type=u'text', bind=el)


@markup_test('xml', schema)
def test_input_open(gen, el):
    """<input type="text" name="field1" value="val">"""
    return gen.input.open(type=u'text', bind=el)


def test_detached_reuse():
    gen = Generator('xml')
    el = schema()

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


@markup_test('xml', schema)
def test_input_close(gen, el):
    """</input>"""
    return gen.input.close()


@markup_test('xml', schema)
def test_textarea_escaped(gen, el):
    '''<textarea name="field1">"&lt;quoted &amp; escaped&gt;"</textarea>'''
    bind = el
    bind.set(u'"<quoted & escaped>"')
    return gen.textarea(bind)


@markup_test('xml', schema)
def test_textarea_contents(gen, el):
    """val"""
    gen.textarea.open(el)
    return gen.textarea.contents


@markup_test('xml', schema)
def test_textarea_escaped_contents(gen, el):
    '''"&lt;quoted &amp; escaped&gt;"'''
    bind = el
    bind.set(u'"<quoted & escaped>"')
    gen.textarea.open(bind)
    return gen.textarea.contents


@markup_test('xml', schema)
def test_textarea_explicit_contents(gen, el):
    """xyzzy"""
    gen.textarea.open(el, contents=u'xyzzy')
    return gen.textarea.contents

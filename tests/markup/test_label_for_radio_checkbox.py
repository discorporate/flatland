"""Tests for label 'for' attribute generation with radio/checkbox inputs."""
from flatland import String
from flatland.out.markup import Generator

import pytest


@pytest.fixture
def schema():
    return String.named("choice")


@pytest.fixture
def html():
    return Generator(markup="html", auto_domid=True, auto_for=True)


@pytest.fixture
def xml():
    return Generator(markup="xml", auto_domid=True, auto_for=True)


def test_complete_radio_form_example(schema, html):
    """Test a complete example form."""
    el = schema("b")

    # Generate label for option 'a'
    label_a = html.label(el, value="a", contents="Option A")
    assert 'for="f_choice_a"' in label_a
    assert 'Option A' in label_a
    assert 'value="a"' not in label_a

    # Generate radio input for option 'a'
    input_a = html.input(el, type="radio", value="a")
    assert 'id="f_choice_a"' in input_a
    assert 'name="choice"' in input_a
    assert 'type="radio"' in input_a
    assert 'checked' not in input_a
    assert 'value="a"' in input_a

    # Generate label for option 'b'
    label_b = html.label(el, value="b", contents="Option B")
    assert 'for="f_choice_b"' in label_b
    assert 'Option B' in label_b
    assert 'value="b"' not in label_b

    # Generate radio input for option 'b' (should be checked)
    input_b = html.input(el, type="radio", value="b")
    assert 'id="f_choice_b"' in input_b
    assert 'name="choice"' in input_b
    assert 'type="radio"' in input_b
    assert 'checked="checked"' in input_b
    assert 'value="b"' in input_b


def test_label_without_value_backward_compatibility(schema, html):
    """Test that labels without a value attribute still work as before."""
    el = schema("b")
    
    # Label without value should generate for="f_choice" (no suffix)
    label = html.label(el)
    assert 'for="f_choice"' in label
    assert 'value=' not in label


def test_label_with_empty_value(schema, html):
    """Test that label with empty value doesn't add suffix."""
    el = schema("test")
    
    # Label with empty value should not add suffix
    label = html.label(el, value="")
    assert 'for="f_choice"' in label
    assert 'value=' not in label


def test_label_value_sanitization(schema, html):
    """Test that label value is sanitized like input values."""
    el = schema("test")
    
    # Value with special characters should be sanitized
    label = html.label(el, value="option-1")
    assert 'for="f_choice_option-1"' in label
    
    # Value with invalid characters should be sanitized
    label2 = html.label(el, value="option@#$1")
    # Invalid characters should be removed, leaving "option1"
    assert 'for="f_choice_option1"' in label2


def test_label_xml_format(schema, xml):
    """Test that the label value attribute works with XML format."""
    el = schema("b")
    
    label = xml.label(el, value="a")
    assert 'for="f_choice_a"' in label
    assert 'value=' not in label
    
    # Label is not a void element, so it has a closing tag
    assert '</label>' in label


def test_label_explicit_for_not_overridden(schema, html):
    """Test that explicitly provided 'for' attribute is not overridden."""
    el = schema("b")
    
    # Explicit 'for' should take precedence
    label = html.label(el, value="a", **{"for": "custom_id"})
    assert 'for="custom_id"' in label
    # Value should still be removed from attributes
    assert 'value=' not in label


def test_label_auto_for_disabled(schema):
    """Test that the value attribute has no effect when auto_for is disabled."""
    html = Generator(markup="html", auto_domid=True, auto_for=False)
    el = schema("b")
    
    # With auto_for=False, no 'for' attribute should be generated
    label = html.label(el, value="a")
    assert 'for=' not in label
    # Value should still be removed
    assert 'value=' not in label


def test_label_with_contents_and_value(schema, html):
    """Test that the label can have both contents and value attribute."""
    el = schema("b")
    
    label = html.label(el, value="a", contents="Option A")
    assert 'for="f_choice_a"' in label
    assert 'Option A' in label
    assert 'value=' not in label


def test_label_value_with_numbers(schema, html):
    """Test that numeric values work correctly."""
    el = schema("1")
    
    label = html.label(el, value="1")
    assert 'for="f_choice_1"' in label
    
    label2 = html.label(el, value="123")
    assert 'for="f_choice_123"' in label2


def test_label_forced_auto_for_with_value(schema):
    """Test that forced auto_for works with a value attribute."""
    html = Generator(markup="html", auto_domid=True, auto_for=False)
    el = schema("b")
    
    # Force auto_for with auto_for="on"
    label = html.label(el, value="a", auto_for="on")
    assert 'for="f_choice_a"' in label
    assert 'value=' not in label
    assert 'auto_for=' not in label

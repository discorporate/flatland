from flatland import (
    Dict,
    String,
    )

from tests._util import eq_


def test_dict():
    s = Dict.named('dict').of(String.named('k1'),
                              String.named('k2'))
    el = s()
    assert s
    assert el


def test_string_element():
    el1 = String()
    el1.set_default()
    el2 = String(default=None)
    el2.set_default()
    el3 = String(default=u'')
    el3.set_default()

    assert el1.value == None
    assert el1.u == u''
    assert not el1

    assert el2.value == None
    assert el2.u == u''
    assert not el2

    assert el3.value == u''
    assert el3.u == u''
    assert not el3

    assert el1 == el2
    assert el1 != el3
    assert el2 != el3

    el4 = String(default=u'  ', strip=True)
    el4.set_default()
    el5 = String(default=u'  ', strip=False)
    el5.set_default()

    assert el4 != el5

    assert el4.u == u''
    assert el4.value == u''
    el4.set(u'  ')
    assert el4.u == u''
    assert el4.value == u''

    assert el5.u == u'  '
    assert el5.value == u'  '
    el5.set(u'  ')
    assert el5.u == u'  '
    assert el5.value == u'  '


def test_path():
    schema = Dict.named('root').of(
        String.named('element'),
        Dict.named('dict').of(String.named('dict_element')))
    element = schema()

    eq_(list(element.el(['dict', 'dict_element']).path),
        [element, element['dict'], element['dict']['dict_element']])

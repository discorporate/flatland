from tests._util import eq_
import flatland.schema as schema


def test_dict():
    s = schema.Dict('dict', schema.String('k1'), schema.String('k2'))
    el = s.create_element()
    assert s
    assert el

def test_string_element():
    el1 = schema.String('item').create_element()
    el1.set_default()
    el2 = schema.String('item', default=None).create_element()
    el2.set_default()
    el3 = schema.String('item', default=u'').create_element()
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

    el4 = schema.String('item', default=u'  ', strip=True).create_element()
    el4.set_default()
    el5 = schema.String('item', default=u'  ', strip=False).create_element()
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
    s = schema.Dict('root',
                    schema.String('element'),
                    schema.Dict('dict', schema.String('dict_element')))
    el = s.create_element()

    eq_(list(el.el(['dict', 'dict_element']).path),
        [el, el['dict'], el['dict']['dict_element']])

from nose.tools import eq_
import flatland.schema as schema

def test_dict():
    s = schema.Dict('dict', schema.String('k1'), schema.String('k2'))
    sn = s.new()

    assert s
    assert sn


def test_string_element():
    n1 = schema.String('item').new()
    n1.set_default()
    n2 = schema.String('item', default=None).new()
    n2.set_default()
    n3 = schema.String('item', default=u'').new()
    n3.set_default()

    assert n1.value == None
    assert n1.u == u''
    assert n1 == None
    assert not n1

    assert n2.value == None
    assert n2.u == u''
    assert n2 == None
    assert not n2

    assert n3.value == u''
    assert n3.u == u''
    assert n3 == u''
    assert not n3

    assert n1 == n2
    assert n1 != n3
    assert n2 != n3

    n4 = schema.String('item', default=u'  ', strip=True).new()
    n4.set_default()
    n5 = schema.String('item', default=u'  ', strip=False).new()
    n5.set_default()

    assert n4 != n5

    assert n4.u == u''
    assert n4.value == u''
    n4.set(u'  ')
    assert n4.u == u''
    assert n4.value == u''

    assert n5.u == u'  '
    assert n5.value == u'  '
    n5.set(u'  ')
    assert n5.u == u'  '
    assert n5.value == u'  '


def test_path():
    s = schema.Dict('root',
                    schema.String('element'),
                    schema.Dict('dict', schema.String('dict_element')))
    n = s.create_element()

    eq_(list(n.el(['dict', 'dict_element']).path),
        [n, n['dict'], n['dict']['dict_element']])

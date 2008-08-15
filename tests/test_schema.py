import flatland.schema as schema

def test_dict():
    s = schema.Dict('dict', schema.String('k1'), schema.String('k2'))
    sn = s.node()

    assert s
    assert sn
    
    
def test_string_node():
    n1 = schema.String('item').node()
    n2 = schema.String('item', default=None).node()
    n3 = schema.String('item', default=u'').node()

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
    assert n1 <> n3
    assert n2 <> n3

    n4 = schema.String('item', default=u'  ', strip=True).node()
    n5 = schema.String('item', default=u'  ', strip=False).node()

    assert n4 <> n5

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
    n = schema.Form('root',
                    schema.String('node'),
                    schema.Dict('dict', schema.String('dict_node')))

    assert n.el(['dict', 'dict_node']).path == ('root', 'dict', 'dict_node')

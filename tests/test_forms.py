import flatland as fl


REQUEST_DATA = ((u'abc', u'123'),
                (u'surname', u'SN'),
                (u'xjioj', u'1232'),
                (u'age', u'99'),
                (u'fname', u'FN'),
                (u'ns_fname', u'ns_FN'),
                (u'ns_surname', u'ns_SN'),
                (u'ns_age', u'23'))

class SimpleForm1(fl.Form):
    schema = [fl.String('fname'),
              fl.String('surname'),
              fl.Integer('age')]

def fakey_to_py(node):
    # Doesn't look like export to full Python native is in from springy yet.
    pairs = []
    def extract(node, data):
        if node.flattenable:
            data.append((node.name, node.value))
    node.apply(extract, pairs)
    return pairs

def test_straight_parse():
    f = SimpleForm1()
    f.set_flat(REQUEST_DATA)
    assert set(f.flatten()) == set(((u'fname', u'FN'),
                                    (u'surname', u'SN'),
                                    (u'age', u'99')))

def test_namespaced_parse():
    f = SimpleForm1('ns')
    f.set_flat(REQUEST_DATA)

    assert set(f.flatten()) == set(((u'ns_fname', u'ns_FN'),
                                    (u'ns_surname', u'ns_SN'),
                                    (u'ns_age', u'23')))
    assert set(fakey_to_py(f)) == set(((u'fname', u'ns_FN'),
                                      (u'surname', u'ns_SN'),
                                      (u'age', 23)))

    assert dict(fakey_to_py(f)) == dict(fname=u'ns_FN',
                                        surname=u'ns_SN',
                                        age=23)

    assert f['age'].value == 23
    assert f['age'].u == u'23'



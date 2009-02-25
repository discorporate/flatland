import datetime
import flatland
from flatland import schema
from tests._util import eq_, assert_raises


def test_ref_binops():
    s = schema.Dict('d',
                    schema.Integer('main'),
                    schema.Ref('aux', 'main'),
                    schema.Integer('other'))
    n = s.new()
    n['main'].set(5)

    assert n['aux'] == u'5'
    assert n['aux'].value == 5
    assert n['aux'].u == u'5'
    assert u'5' == n['aux']
    assert 5 == n['aux'].value
    assert u'5' == n['aux'].u

    assert n['aux'] != u'6'
    assert n['aux'].value != 6
    assert n['aux'].u != u'6'
    assert u'6' != n['aux']
    assert 6 != n['aux']
    assert u'6' != n['aux']

    assert n['aux'] == n['main']
    assert n['main'] == n['aux']
    assert n['aux'] != n['other']
    assert n['other'] != n['aux']

def test_ref_writable_ignore():
    s = schema.Dict('d',
                    schema.Integer('main'),
                    schema.Ref('aux', 'main'))

    n = s.new()
    n['aux'] = 6
    assert n['main'] == None

def test_ref_writable():
    s = schema.Dict('d',
                    schema.Integer('main'),
                    schema.Ref('aux', 'main', writable=True))

    n = s.new()
    n['aux'] = 6
    assert n['main'] == 6

def test_ref_not_writable():
    s = schema.Dict('d',
                    schema.Integer('main'),
                    schema.Ref('aux', 'main', writable=False))

    n = s.new()
    assert_raises(TypeError, n['aux'].set, 6)

def test_dereference_twice():
    class RefForm(flatland.Form):
        schema = [
            schema.Integer('main', default=1),
            schema.Ref('aux', 'main', writable=True),
        ]

    f = RefForm.from_defaults()
    assert f.el('aux').value == 1

    f.el('aux').set(10)
    assert f.el('main').value == 10

    f.set_flat({'aux': 15})
    assert f.el('main').value == 15

    # Previous versions would fail after two dereferences
    f.el(f.el('aux').schema.path)
    f.el(f.el('aux').schema.path)

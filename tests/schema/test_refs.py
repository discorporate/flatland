import datetime
from nose.tools import eq_, assert_raises

from flatland import schema


def test_ref_simple():
    s = schema.Dict('d',
                    schema.Integer('main'),
                    schema.Ref('aux', 'main'))
    n = s.node()
    n['main'].set(5)
    eq_(n['aux'], u'5')
    eq_(n['aux'].value, 5)
    eq_(n['aux'].u, u'5')

def test_ref_writable_ignore():
    s = schema.Dict('d',
                    schema.Integer('main'),
                    schema.Ref('aux', 'main'))

    n = s.node()
    n['aux'] = 6
    assert n['main'] == None

def test_ref_writable():
    s = schema.Dict('d',
                    schema.Integer('main'),
                    schema.Ref('aux', 'main', writable=True))

    n = s.node()
    n['aux'] = 6
    assert n['main'] == 6

def test_ref_not_writable():
    s = schema.Dict('d',
                    schema.Integer('main'),
                    schema.Ref('aux', 'main', writable=False))

    n = s.node()
    assert_raises(TypeError, n['aux'].set, 6)







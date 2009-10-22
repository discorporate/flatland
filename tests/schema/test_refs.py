from flatland import (
    Dict,
    Integer,
    Ref,
    )

from tests._util import assert_raises


def test_binops():
    schema = Dict.of(Integer.named('main'),
                     Ref.named('aux').to('main'),
                     Integer.named('other'))
    el = schema({'main': 5})

    assert el['aux'] == Integer(5)
    assert el['aux'].value == 5
    assert el['aux'].u == u'5'
    assert Integer(5) == el['aux']
    assert 5 == el['aux'].value
    assert u'5' == el['aux'].u

    assert el['aux'] != Integer(6)
    assert el['aux'].value != 6
    assert el['aux'].u != u'6'
    assert Integer(6) != el['aux']
    assert 6 != el['aux']
    assert u'6' != el['aux']

    assert el['aux'] == el['main']
    assert el['main'] == el['aux']
    assert el['aux'] != el['other']
    assert el['other'] != el['aux']


def test_writable_ignore():

    def element(writable):
        ref = Ref.named('aux').to('main')
        if writable:
            ref = ref.using(writable=writable)
        return Dict.of(Integer.named('main'), ref)()

    # class default and explicit writable=ignore
    for el in element(None), element('ignore'):
        el['aux'] = 6
        assert el['main'].value is None
        assert el['aux'].value is None


def test_writable():
    schema = Dict.of(Integer.named('main'),
                     Ref.named('aux').to('main').using(writable=True))

    el = schema()
    el['aux'] = 6
    assert el['main'].value == 6
    assert el['aux'].value == 6


def test_not_writable():
    schema = Dict.of(Integer.named('main'),
                     Ref.named('aux').to('main').using(writable=False))

    el = schema()
    assert_raises(TypeError, el['aux'].set, 6)


def test_dereference_twice():
    schema = Dict.of(Integer.named('main'),
                     Ref.named('aux').to('main').using(writable=True))

    # Previous revisions would fail after two dereferences
    element = schema()

    element['aux'] = 1
    assert element['aux'].value == 1

    element['aux'].set(1)
    assert element['aux'].value == 1

    assert element.el(element['aux'].target_path) is element['main']
    assert element.el(element['aux'].target_path) is element['main']

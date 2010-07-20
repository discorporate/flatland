from flatland import (
    Dict,
    Integer,
    Ref,
    )

from tests._util import assert_raises


def test_binops():
    schema = Dict.of(Integer.named(u'main'),
                     Ref.named(u'aux').to(u'main'),
                     Integer.named(u'other'))
    el = schema({u'main': 5})

    assert el[u'aux'] == Integer(5)
    assert el[u'aux'].value == 5
    assert el[u'aux'].u == u'5'
    assert Integer(5) == el[u'aux']
    assert 5 == el[u'aux'].value
    assert u'5' == el[u'aux'].u

    assert el[u'aux'] != Integer(6)
    assert el[u'aux'].value != 6
    assert el[u'aux'].u != u'6'
    assert Integer(6) != el[u'aux']
    assert 6 != el[u'aux']
    assert u'6' != el[u'aux']

    assert el[u'aux'] == el[u'main']
    assert el[u'main'] == el[u'aux']
    assert el[u'aux'] != el[u'other']
    assert el[u'other'] != el[u'aux']


def test_writable_ignore():

    def element(writable):
        ref = Ref.named(u'aux').to(u'main')
        if writable:
            ref = ref.using(writable=writable)
        return Dict.of(Integer.named(u'main'), ref)()

    # class default and explicit writable=ignore
    for el in element(None), element('ignore'):
        el[u'aux'] = 6
        assert el[u'main'].value is None
        assert el[u'aux'].value is None


def test_writable():
    schema = Dict.of(Integer.named(u'main'),
                     Ref.named(u'aux').to(u'main').using(writable=True))

    el = schema()
    el[u'aux'] = 6
    assert el[u'main'].value == 6
    assert el[u'aux'].value == 6


def test_not_writable():
    schema = Dict.of(Integer.named(u'main'),
                     Ref.named(u'aux').to(u'main').using(writable=False))

    el = schema()
    assert_raises(TypeError, el[u'aux'].set, 6)


def test_dereference_twice():
    schema = Dict.of(Integer.named(u'main'),
                     Ref.named(u'aux').to(u'main').using(writable=True))

    # Previous revisions would fail after two dereferences
    element = schema()

    element[u'aux'] = 1
    assert element[u'aux'].value == 1

    element[u'aux'].set(1)
    assert element[u'aux'].value == 1

    assert element.el(element[u'aux'].target_path) is element[u'main']
    assert element.el(element[u'aux'].target_path) is element[u'main']

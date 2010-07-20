from datetime import date
from flatland import (
    Array,
    DateYYYYMMDD,
    Dict,
    Integer,
    Form,
    List,
    )
from flatland.schema.paths import (
    NAME,
    SLICE,
    TOP,
    UP,
    pathexpr,
    tokenize,
    )
from tests._util import assert_raises


def _tokenizes_as(path, expected):
    tokenized = tokenize(path)
    assert tokenized == expected


top = (TOP, None)
up = (UP, None)
name = lambda x: (NAME, x)
sl = lambda x: (SLICE, x)


def test_tokenize():
    _tokencases = [
        ('/', [top]),
        ('..', [up]),
        ('/..', [top]),
        ('../..', [up, up]),
        ('//', [top, name(None)]),
        ('foo', [name('foo')]),
        ('/foo', [top, name('foo')]),
        ('foo/', [name('foo')]),
        ('foo/bar', [name('foo'), name('bar')]),
        ('foo/../bar', [name('bar')]),
        ('foo/bar[bogus]', [name('foo'), name('bar[bogus]')]),
        ('a[b][c:d][0]', [name('a[b][c:d]'), name('0')]),
        ('foo[1]', [name('foo'), name('1')]),
        ('foo[1]/', [name('foo'), name('1')]),
        ('foo[1][2][3]', [name('foo'), name('1'), name('2'), name('3')]),
        ('[1][2][3]', [name('1'), name('2'), name('3')]),
        ('[1]/foo/[2]', [name('1'), name('foo'), name('2')]),
        ('[:]', [sl(slice(None))]),
        ('[1:]', [sl(slice(1, None))]),
        ('[1:2]', [sl(slice(1, 2))]),
        ('[:5]', [sl(slice(0, 5))]),
        ('[-5:]', [sl(slice(-5, None))]),
        ('[1:8:2]', [sl(slice(1, 8, 2))]),
        ]
    for path, expected in _tokencases:
        yield _tokenizes_as, path, expected


def test_tokenize_escapes():
    _tokencases = [
        (r'\/', [name('/')]),
        (r'\.\.', [name('..')]),
        (r'/\.\.', [top, name('..')]),
        (r'\/..', [name('/..')]),
        (r'..\/..', [name('../..')]),
        (r'foo\[1]', [name('foo[1]')]),
        (r'foo\/bar', [name(r'foo/bar')]),
        (r'\/foo', [name(r'/foo')]),
        (r'foo\/', [name(r'foo/')]),
        ]
    for path, expected in _tokencases:
        yield _tokenizes_as, path, expected


class Schema(Form):
    i1 = Integer.using(default=0)

    d1 = Dict.of(Integer.named('d1i1').using(default=1),
                 Integer.named('d1i2').using(default=2))

    l1 = List.using(default=2).of(Integer.named('l1i1').using(default=3))

    l2 = List.using(default=3).of(Integer.named('l2i1').using(default=4),
                                  Integer.named('l2i2').using(default=5))

    l3 = List.using(default=2).of(
        List.named('l3l1').using(default=2).of(Integer.using(default=6)))

    a1 = Array.using(default=[10, 11, 12, 13, 14, 15]).of(Integer)

    dt1 = DateYYYYMMDD.using(default=date.today())


def _finds(el, path, expected):
    finder = pathexpr(path)
    elements = finder(el)
    found = [e.value for e in elements]

    if isinstance(expected, set):
        found = set(found)
    assert found == expected


def test_evaluation():
    el = Schema.from_defaults()
    today = date.today()

    _finders = [
        (el, 'i1', [0]),
        (el, '/i1', [0]),
        (el, '../i1', [0]),
        (el['i1'], '../i1', [0]),
        (el, 'd1/d1i1', [1]),
        (el, '/d1/d1i2', [2]),
        (el['d1']['d1i1'], '..', [{'d1i1': 1, 'd1i2': 2}]),
        (el, '/l1', [[3, 3]]),
        (el, '/l1[:]', [3, 3]),
        (el, '/l1[2:]', []),
        (el, '/l1[0]', [3]),
        (el, '/l2[:]/l2i1', [4, 4, 4]),
        (el, '/l3[:]', [[6, 6], [6, 6]]),
        (el, '/l3[:][:]', [6, 6, 6, 6]),
        (el, 'l3[1:][1:]', [6]),
        (el, 'a1[1:]', [11, 12, 13, 14, 15]),
        (el, 'a1[:-1]', [10, 11, 12, 13, 14]),
        (el, 'a1[3]', [13]),
        (el, 'a1[2]', [12]),
        (el, 'a1[1]', [11]),
        (el, 'a1[0]', [10]),
        (el, 'a1[-1]', [15]),
        (el, 'a1[-2]', [14]),
        (el, 'a1[-3]', [13]),
        (el, 'a1[10]', []),
        (el, 'a1[-10]', []),
        (el, 'a1[-3:-1]', [13, 14]),
        (el, 'a1[1:3]', [11, 12]),
        (el, 'a1[:3]', [10, 11, 12]),
        (el, 'a1[::2]', [10, 12, 14]),
        (el, 'a1[2::2]', [12, 14]),
        (el, 'a1[2:4:2]', [12]),
        (el, 'a1[::-1]', [15, 14, 13, 12, 11, 10]),
        (el, 'a1[::-2]', [15, 13, 11]),
        (el, 'dt1', [today]),
        (el, 'dt1/year', [today.year]),
        ]
    for element, path, expected in _finders:
        yield _finds, element, path, expected


def test_find_strict_loose():
    el = Schema.from_defaults()
    _cases = [
        (el, 'bogus'),
        (el, '/d1/d1i3'),
        (el, 'l1[5]'),
        (el, 'l3[:]/missing'),
        ]

    for element, path in _cases:
        assert_raises(LookupError, element.find, path)

        found = element.find(path, strict=False)
        assert not found


def _find_message(el, path, **find_kw):
    try:
        el.find(path, **find_kw)
    except LookupError, exc:
        return str(exc)
    assert False


def test_find_strict_messaging():
    el = Schema.from_defaults()

    message = _find_message(el, 'bogus')
    expected = ("Unnamed element Schema has no child u'bogus' "
                "in expression u'bogus'")
    assert expected in message

    message = _find_message(el, 'd1/bogus')
    expected = ("Dict element u'd1' has no child u'bogus' "
                "in expression u'd1/bogus'")
    assert expected in message

    message = _find_message(el, 'l1[5]')
    expected = ("List element u'l1' has no child u'5' "
                "in expression u'l1[5]'")
    assert expected in message


def test_find_default():
    el = Schema.from_defaults()
    _cases = [
        (el, 'i1', [0]),
        (el, 'a1[:]', [10, 11, 12, 13, 14, 15]),
        (el, 'a1[0]', [10]),
        ]

    for element, path, expected in _cases:
        elements = element.find(path)
        found = [e.value for e in elements]
        assert found == expected


def test_find_single():
    el = Schema.from_defaults()
    _cases = [
        (el, 'i1', 0),
        (el, 'bogus', None),
        (el, 'a1[0]', 10),
        (el, 'a1[10]', None),
        (el, 'l3[1:][1:]', 6),
        ]

    for element, path, expected in _cases:
        element = element.find(path, single=True, strict=False)
        if element is None:
            found = None
        else:
            found = element.value
        assert found == expected


def test_find_single_loose():
    el = Schema.from_defaults()

    element = el.find('l3[:][:]', single=True, strict=False)
    found = element.value
    assert found == 6


def test_find_single_messaging():
    el = Schema.from_defaults()

    message = _find_message(el, 'a1[:]', single=True)
    expected = "Path 'a1[:]' matched multiple elements"
    assert expected in message

from flatland.schema.scalars import String
from flatland.valid import urls
from tests._util import eq_


def scalar(value):
    return String('test').create_element(value=value)

def test_url_validator_default():
    v = urls.URLValidator()
    el = scalar('http://me:you@there/path#fragment')
    assert v.validate(el, None)
    assert not el.errors

def test_url_validator_schemes():
    v = urls.URLValidator(allowed_schemes=(), blocked_scheme='X')
    el = scalar('http://me:you@there/path#fragment')
    assert not v.validate(el, None)
    eq_(el.errors, ['X'])

    v = urls.URLValidator(allowed_schemes=('https',), blocked_scheme='X')
    el = scalar('http://me:you@there/path#fragment')
    assert not v.validate(el, None)
    eq_(el.errors, ['X'])

def test_url_validator_parts():
    v = urls.URLValidator(allowed_parts=(), blocked_part='X')
    el = scalar('http://me:you@there/path#fragment')
    assert not v.validate(el, None)
    eq_(el.errors, ['X'])

    v = urls.URLValidator(allowed_parts=urls._url_parts)
    el = scalar('http://me:you@there/path#fragment')
    assert v.validate(el, None)
    assert not el.errors

    v = urls.URLValidator(allowed_parts=('scheme', 'netloc'))
    el = scalar('http://blarg')
    assert v.validate(el, None)
    assert not el.errors

    v = urls.URLValidator(allowed_parts=('scheme', 'netloc'), blocked_part='X')
    el = scalar('http://blarg/')
    assert not v.validate(el, None)
    eq_(el.errors, ['X'])

def test_http_validator_default():
    v = urls.HTTPURLValidator(forbidden_part='X')
    el = scalar('http://there/path#fragment')
    assert v.validate(el, None)
    assert not el.errors

    el = scalar('http://phis:ing@there/path#fragment')
    not v.validate(el, None)
    eq_(el.errors, ['X'])

def test_url_canonicalizer_default():
    v = urls.URLCanonicalizer()
    el = scalar('http://localhost/#foo')
    eq_(el.value, 'http://localhost/#foo')

    assert v.validate(el, None)
    eq_(el.value, 'http://localhost/')
    assert not el.errors

def test_url_canonicalizer_want_none():
    v = urls.URLCanonicalizer(discard_parts=urls._url_parts)
    el = scalar('http://me:you@there/path#fragment')
    eq_(el.value, 'http://me:you@there/path#fragment')

    assert v.validate(el, None)
    eq_(el.value, '')
    assert not el.errors

def test_url_canonicalizer_want_one():
    v = urls.URLCanonicalizer(discard_parts=urls._url_parts[1:])
    el = scalar('http://me:you@there/path#fragment')
    eq_(el.value, 'http://me:you@there/path#fragment')

    assert v.validate(el, None)
    eq_(el.value, 'http://')
    assert not el.errors

def test_url_canonicalizer_want_all():
    v = urls.URLCanonicalizer(discard_parts=())
    el = scalar('http://me:you@there/path#fragment')
    eq_(el.value, 'http://me:you@there/path#fragment')

    assert v.validate(el, None)
    eq_(el.value, 'http://me:you@there/path#fragment')
    assert not el.errors


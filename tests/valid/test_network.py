import re

from flatland import String
from flatland.valid import IsEmail

from tests._util import eq_


def email(value):
    return String('email').create_element(value=value)

def assert_email_not_valid(value, kw={}):
    validator = IsEmail(**kw)
    el = email(value)
    assert not validator.validate(el, None)
    assert el.errors

def assert_email_valid(value, kw={}):
    validator = IsEmail(**kw)
    el = email(value)
    assert validator.validate(el, None)
    assert not el.errors

def test_email():
    for addr in (u'bob@noob.com', u'bob@noob.frizbit', u'#"$!+,,@noob.c',
                 u'bob@bob-bob.bob'):
        yield assert_email_valid, addr

def test_email_idna():
    assert_email_valid(u'bob@snow\u2603man.com')

def test_email_nonlocal():
    assert_email_not_valid(u'root@localhost')

def test_email_nonlocal_ok():
    assert_email_valid(u'root@localhost', {'nonlocal': False})

def test_email_altlocal():
    override = dict(local_part_pattern=re.compile(r'^bob$'))
    assert_email_valid('bob@bob.com', override)
    assert_email_not_valid('foo@bar.com', override)

def test_email_bogus():
    c64 = u'x' * 64
    c63 = u'x' * 63
    for addr in (u'bob@zig..', u'bob@', u'@bob.com', u'@', u'snork',
                 u'bob@zig:zag.com', u'bob@zig zag.com', u'bob@zig/zag.com',
                 u'bob@%s.com' % c64,
                 u'bob@%s.%s.%s.%s.com' % (c63, c63, c63, c63),
                 u'foo.com', u'bob@bob_bob.com', u''):
        yield assert_email_not_valid, addr



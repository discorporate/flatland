from flatland.schema.scalars import String
from flatland.valid import email
from tests._util import eq_

def scalar(value):
    return String('email').create_element(value=value)

def test_email_validator_default():
    v = email.IsEmail()
    el = scalar('bob@noob.cob')
    assert v.validate(el, None)
    assert not el.errors

def test_email_bogus_email():
    v = email.IsEmail()
    for bog in ['bob@cob', 'bob@zig..', 'bob@zig.x']:
        el = scalar(bog)
        assert not v.validate(el, None)
        assert el.errors


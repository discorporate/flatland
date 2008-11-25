import re
from flatland import *
from flatland.ext import creditcard


class SimpleSchema(Form):
    schema = [creditcard.CreditCardNumber('num')]

class MyCreditCard(creditcard.CreditCardNumber):
    class Present(creditcard.CreditCardNumber.Present):
        missing = u'Yo! You need a %(label)s!'

class SimpleSchema2(Form):
    schema = [MyCreditCard('num',
                           label='Visa/MC Number',
                           types=(creditcard.VISA,
                                  creditcard.MASTERCARD)),
              String('name', optional=True)]


def test_simple():
    data = SimpleSchema.from_flat({})
    assert not data.validate()
    assert data.el('num').errors
    e1 = list(data.el('num').errors)

    data = SimpleSchema.from_flat({'num': 'asdf'})
    assert not data.validate()
    assert data['num'].errors
    assert data['num'].errors != e1
    e2 = list(data['num'].errors)

    data = SimpleSchema.from_flat({'num': '1234'})
    assert not data.validate()
    assert data['num'].errors
    assert data['num'].errors == e2
    e3 = list(data['num'].errors)

    data = SimpleSchema.from_flat({'num': '4100000000000009'})
    assert not data.validate()
    assert data['num'].errors
    assert data['num'].errors != e3
    e4 = list(data['num'].errors)

    data = SimpleSchema.from_flat({'num': '4100000000000001'})
    assert data.validate()
    assert isinstance(data['num'].value, long)
    assert data['num'].u == '4100-0000-0000-0001'


def test_subclass():
    data = SimpleSchema2.from_flat({})
    assert not data.validate()
    assert data['num'].errors
    err = data['num'].errors[0]

    assert err.startswith('Yo!')
    assert 'Visa/MC Number' in err

from flatland import Form, String
from flatland.ext.creditcard import CreditCardNumber, VISA, MASTERCARD


def test_simple():

    class Schema(Form):
        num = CreditCardNumber.named('num')

    data = Schema({})
    assert not data.validate()
    assert data.el('num').errors
    e1 = list(data.el('num').errors)

    data = Schema({'num': 'asdf'})
    assert not data.validate()
    assert data['num'].errors
    assert data['num'].errors != e1
    e2 = list(data['num'].errors)

    data = Schema({'num': '1234'})
    assert not data.validate()
    assert data['num'].errors
    assert data['num'].errors == e2
    e3 = list(data['num'].errors)

    data = Schema({'num': '4100000000000009'})
    assert not data.validate()
    assert data['num'].errors
    assert data['num'].errors != e3
    e4 = list(data['num'].errors)

    data = Schema({'num': '4100000000000001'})
    assert data.validate()
    assert isinstance(data['num'].value, long)
    assert data['num'].u == '4100-0000-0000-0001'


def test_subclass():

    class MyCreditCard(CreditCardNumber):

        class Present(CreditCardNumber.Present):
            missing = u'Yo! You need a %(label)s!'

    class Schema(Form):
        num = MyCreditCard.using(label='Visa/MC Number',
                                 accepted=(VISA, MASTERCARD))
        name = String.using(optional=True)


    data = Schema.from_flat({})
    assert not data.validate()
    assert data['num'].errors
    err = data['num'].errors[0]

    assert err.startswith('Yo!')
    assert 'Visa/MC Number' in err

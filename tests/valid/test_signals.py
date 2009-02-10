from flatland import signals, String, valid
from flatland.schema.base import NotEmpty
from tests._util import eq_


def test_validator_validated():
    s = String('text',
               validators=[valid.Present(),
                           valid.Converted(),
                           valid.NoLongerThan(5)])

    sentinel = []
    def listener(**kw):
        sentinel.append(kw)

    signals.validator_validated.connect(listener)

    el = s.create_element()
    assert not el.validate()
    eq_(sentinel, [dict(sender=s.validators[0],
                        element=el,
                        state=None,
                        result=False)])
    del sentinel[:]
    el = s.create_element(value='abcd')
    assert el.validate()
    assert len(sentinel) == 3
    assert sentinel[-1]['result']

    del sentinel[:]
    el = s.create_element(value='squiznart')
    assert not el.validate()
    assert len(sentinel) == 3
    assert not sentinel[-1]['result']

    s2 = String('text', optional=False)

    del sentinel[:]
    el = s2.create_element()
    assert not el.validate()
    eq_(sentinel, [dict(sender=NotEmpty, element=el, state=None, result=False)])

    del sentinel[:]
    el = s2.create_element(value='squiznart')
    assert el.validate()
    eq_(sentinel, [dict(sender=NotEmpty, element=el, state=None, result=True)])

    del listener
    del sentinel[:]
    el = s.create_element(value='squiznart')
    assert not el.validate()
    assert not sentinel

    signals.validator_validated._clear_state()

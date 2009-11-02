from flatland import String, signals
from flatland.schema.base import NotEmpty
from flatland.validation import (
    Converted,
    NoLongerThan,
    Present,
    )

from tests._util import eq_


def test_validator_validated():
    sentinel = []

    def listener(**kw):
        sentinel.append(kw)

    signals.validator_validated.connect(listener)

    schema = String.using(validators=[Present(),
                                      Converted(),
                                      NoLongerThan(5)])
    el = schema()
    assert not el.validate()
    eq_(sentinel, [dict(sender=schema.validators[0],
                        element=el,
                        state=None,
                        result=False)])
    del sentinel[:]
    el = schema(value='abcd')
    assert el.validate()
    assert len(sentinel) == 3
    assert sentinel[-1]['result']

    del sentinel[:]
    el = schema('squiznart')
    assert not el.validate()
    assert len(sentinel) == 3
    assert not sentinel[-1]['result']

    s2 = String.using(optional=False)

    del sentinel[:]
    el = s2()
    assert not el.validate()
    eq_(sentinel, [dict(sender=NotEmpty, element=el,
                        state=None, result=False)])

    del sentinel[:]
    el = s2('squiznart')
    assert el.validate()
    eq_(sentinel, [dict(sender=NotEmpty, element=el,
                        state=None, result=True)])

    del listener
    del sentinel[:]
    el = schema('squiznart')
    assert not el.validate()
    assert not sentinel

    signals.validator_validated._clear_state()

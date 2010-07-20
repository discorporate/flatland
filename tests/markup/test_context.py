from flatland.out.generic import Context, _default_context
from tests._util import assert_raises

Nothing = object()


def test_read_write_known():
    ctx = Context()

    needle = _default_context.keys()[0]
    assert needle in ctx
    assert ctx[needle] is not Nothing
    ctx[needle] = Nothing
    assert ctx[needle] is Nothing


def test_read_write_unknown():
    ctx = Context()

    needle = 'xyzzy'
    assert needle not in _default_context.keys()
    assert needle not in ctx
    assert_raises(KeyError, lambda: ctx[needle])
    assert_raises(KeyError, ctx.__setitem__, needle, Nothing)


def test_push_known():
    ctx = Context()

    needle = _default_context.keys()[0]
    assert needle in ctx
    assert ctx[needle] is not Nothing

    ctx.push(**{needle.encode('ascii'): Nothing})
    assert ctx[needle] is Nothing

    ctx.pop()
    assert ctx[needle] is not Nothing


def test_push_unknown():
    ctx = Context()

    needle = 'xyzzy'
    assert needle not in _default_context.keys()

    assert_raises(KeyError, ctx.push, **{needle: Nothing})
    assert_raises(RuntimeError, ctx.pop)


def test_update_known():
    ctx = Context()
    known = _default_context.keys()
    sentinels = [object(), object()]

    iterable = [(known[0], sentinels[0])]
    kwargs = {known[1].encode('ascii'): sentinels[1]}

    ctx.update(iterable, **kwargs)

    assert ctx[known[0]] is sentinels[0]
    assert ctx[known[1]] is sentinels[1]

    ctx = Context()
    ctx.update(iterable)
    assert ctx[known[0]] is sentinels[0]

    ctx = Context()
    ctx.update(**kwargs)
    assert ctx[known[1]] is sentinels[1]


def test_update_unknown():
    ctx = Context()
    assert u'xyzzy' not in _default_context.keys()

    assert_raises(KeyError, ctx.update, xyzzy=123)
    assert u'xyzzy' not in ctx


def test_update_bogus():
    ctx = Context()
    assert_raises(TypeError, ctx.update, [], [])


def test_minimum_repr_sanity():
    ctx = Context()
    assert repr(ctx)  # don't blow up
    assert str(ctx)   # string coercion too


def test_default_minimum_stack():
    ctx = Context()
    assert_raises(RuntimeError, ctx.pop)


def test_stack_plain_push_pop():
    ctx = Context()

    needle, initial_value = _default_context.items()[0]
    assert ctx[needle] == initial_value

    ctx.push()
    assert ctx[needle] == initial_value
    ctx[needle] = Nothing
    assert ctx[needle] is Nothing

    ctx.pop()
    assert ctx[needle] is not Nothing
    assert ctx[needle] == initial_value

    assert_raises(RuntimeError, ctx.pop)

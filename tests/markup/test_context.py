from flatland.out.generic import Context, _default_context
import pytest

Nothing = object()


def test_read_write_known():
    ctx = Context()

    needle = list(_default_context.keys())[0]
    assert needle in ctx
    assert ctx[needle] is not Nothing
    ctx[needle] = Nothing
    assert ctx[needle] is Nothing


def test_read_write_unknown():
    ctx = Context()

    needle = 'xyzzy'
    assert needle not in _default_context.keys()
    assert needle not in ctx
    with pytest.raises(KeyError):
        # noinspection PyStatementEffect
        ctx[needle]
    with pytest.raises(KeyError):
        ctx[needle] = Nothing


def test_push_known():
    ctx = Context()

    needle = list(_default_context.keys())[0]
    assert needle in ctx
    assert ctx[needle] is not Nothing

    ctx.push(**{needle: Nothing})
    assert ctx[needle] is Nothing

    ctx.pop()
    assert ctx[needle] is not Nothing


def test_push_unknown():
    ctx = Context()

    needle = 'xyzzy'
    needle_attribute = 'xyzzy'  # native text type
    assert needle not in _default_context.keys()

    with pytest.raises(KeyError):
        ctx.push(**{needle_attribute: Nothing})
    with pytest.raises(RuntimeError):
        ctx.pop()


def test_update_known():
    ctx = Context()
    known = list(_default_context.keys())
    sentinels = [object(), object()]

    iterable = [(known[0], sentinels[0])]
    kwargs = {known[1]: sentinels[1]}

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
    assert 'xyzzy' not in _default_context.keys()

    with pytest.raises(KeyError):
        ctx.update(xyzzy=123)
    assert 'xyzzy' not in ctx


def test_update_bogus():
    ctx = Context()
    with pytest.raises(TypeError):
        ctx.update([], [])


def test_minimum_repr_sanity():
    ctx = Context()
    assert repr(ctx)  # don't blow up
    assert str(ctx)   # string coercion too


def test_default_minimum_stack():
    ctx = Context()
    with pytest.raises(RuntimeError):
        ctx.pop()


def test_stack_plain_push_pop():
    ctx = Context()

    needle, initial_value = list(_default_context.items())[0]
    assert ctx[needle] == initial_value

    ctx.push()
    assert ctx[needle] == initial_value
    ctx[needle] = Nothing
    assert ctx[needle] is Nothing

    ctx.pop()
    assert ctx[needle] is not Nothing
    assert ctx[needle] == initial_value

    with pytest.raises(RuntimeError):
        ctx.pop()

"""Test suite helpers."""

from functools import wraps

__all__ = ["fails"]


def fails(reason):
    """Mark a test case as expected to fail for *reason*."""

    def decorator(fn):
        @wraps(fn)
        def decorated(*args, **kw):
            try:
                fn(*args, **kw)
            except (SystemExit, KeyboardInterrupt):
                raise
            except:
                pass  # ok
            else:
                raise AssertionError("Unexpected success.")

        return decorated

    return decorator


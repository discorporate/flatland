"""Test suite helpers."""

from functools import wraps

__all__ = ["fails", "udict"]


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


def udict(*dictionary, **kwargs):
    "Return a dict with unicode keys. A stand-in for the dict constructor."
    kwargs = {str(k): v for k, v in kwargs.items()}
    if dictionary:
        base = {str(k): v for k, v in dictionary[0].items()}
        base.update(kwargs)
        return base
    else:
        return kwargs

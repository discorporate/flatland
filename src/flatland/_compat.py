__all__ = [
    "builtins",
    "iterkeys",
    "iteritems",
    "itervalues",
    "with_metaclass",
]

import builtins

iterkeys = lambda d: iter(d.keys())
itervalues = lambda d: iter(d.values())
iteritems = lambda d: iter(d.items())


def with_metaclass(meta, *bases):
    # From flask, MIT License
    # https://github.com/mitsuhiko/flask/blob/master/flask/_compat.py
    class metaclass(meta):
        __call__ = type.__call__
        __init__ = type.__init__

        def __new__(cls, name, this_bases, d):
            if this_bases is None:
                return type.__new__(cls, name, (), d)
            return meta(name, bases, d)

    return metaclass("temporary_class", None, {})

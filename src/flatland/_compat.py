__all__ = [
    "builtins",
    "getattr_py2",
    "hasattr_py2",
    "identifier_transform",
    "iterkeys",
    "iteritems",
    "itervalues",
    "long_type",
    "setattr_py2",
    "string_types",
    "with_metaclass",
    "xrange",
]

import builtins

long_type = int
identifier_transform = lambda i: i
text_transform = str
getattr_py2 = getattr
hasattr_py2 = hasattr
setattr_py2 = setattr
iterkeys = lambda d: iter(d.keys())
itervalues = lambda d: iter(d.values())
iteritems = lambda d: iter(d.items())
xrange = range

string_types = (bytes, str)


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

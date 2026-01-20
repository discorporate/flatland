__all__ = [
    "builtins",
    "bytestring_type",
    "getattr_py2",
    "hasattr_py2",
    "identifier_transform",
    "iterkeys",
    "iteritems",
    "itervalues",
    "long_type",
    "setattr_py2",
    "string_types",
    "text_type",
    "with_metaclass",
    "xrange",
]

import builtins

text_type = str
bytestring_type = bytes
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

string_types = (bytestring_type, text_type)


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

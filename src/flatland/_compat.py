__all__ = [
    "builtins",
    "iterkeys",
    "iteritems",
    "itervalues",
]

import builtins

iterkeys = lambda d: iter(d.keys())
itervalues = lambda d: iter(d.values())
iteritems = lambda d: iter(d.items())

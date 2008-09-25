import functools
import inspect
import itertools
import operator
import re

try:
    import threading
except ImportError:                                           # pragma:nocover
    import dummy_threading as threading


# derived from ASPN Cookbook (#36302)
class lazy_property(object):
    def __init__(self, deferred):
        self._deferred = deferred

    def __get__(self, obj, cls):
        if obj is None:
            return self
        value = self._deferred(obj)
        setattr(obj, self._deferred.func_name, value)
        return value


class as_mapping(object):
    """Provide a mapping view of an instance.

    Similar to vars(), but effective on extension types and will
    invoke descriptors on access.

    """

    __slots__ = 'target',

    def __init__(self, target):
        self.target = target

    def __getitem__(self, item):
        try:
            return getattr(self.target, item)
        except AttributeError:
            raise KeyError(item)

    def __contains__(self, item):
        return hasattr(self.target, item)

    def __iter__(self):
        return iter(dir(self.target))


def re_ucompile(pattern, flags=0):
    """Compile a regex with re.UNICODE on by default."""
    return re.compile(pattern, flags | re.UNICODE)

def luhn10(number):
    """Return True if the number passes the Luhn checksum algorithm."""

    sum = 0
    while number:
        r = number % 100
        number //= 100
        z = r % 10
        r = r // 10 * 2
        sum += r // 10 + r % 10 + z

    return 0 == sum % 10

def to_pairs(dictlike):
    """Yield (key, value) pairs from any dict-like object.

    Implements an optimized version of the dict.update() definition of
    "dictlike".

    """
    if hasattr(dictlike, 'iteritems'):
        return dictlike.iteritems()
    elif hasattr(dictlike, 'keys'):
        return ((key, dictlike[key]) for key in dictlike.keys())
    else:
        return ((key, value) for key, value in dictlike)

def keyslice_pairs(pairs, include=None, omit=None, rename=None):
    """Filter (key, value) pairs by key and return a subset.

    :param pairs: an iterable of ``(key, value)`` pairs (2-tuples).

    :param include: optional, a sequence of key values.  If supplied,
        only pairs whose key is a member of this sequence will be
        returned.

    :param omit: optional, a sequence of key values. If supplied, all
        pairs will be returned, save those whose key is a member of
        this sequence.

    :param rename: optional, a mapping or sequence of 2-tuples
        specifying a key-to-key translation.  A pair whose key has
        been renamed by this translation will always be emitted,
        regardless of *include* or *omit* rules.  The mapping will be
        converted to a dict internally, and keys must be hashable.

    :returns: yields ``(key, value)`` pairs.

    """
    if include and omit:
        raise TypeError('received include and omit, specify only one')

    include = set(include) if include else False
    omit = set(omit) if omit else False
    rename = dict(to_pairs(rename)) if rename else False

    for pair in pairs:
        key = pair[0]
        if rename and key in rename:
            yield (rename[key], pair[1])
            continue
        if include:
            if key not in include:
                continue
        elif omit:
            if key in omit:
                continue
        yield pair

# From ASPN Cookbook (#410692)
class switch(object):
    def __init__(self, value):
        self.value = value
        self.fall = False

    def __iter__(self):
        """Return the match method once, then stop"""
        yield self.match

    def match(self, *args):
        """Indicate whether or not to enter a case suite"""
        if self.fall or not args:
            return True
        elif self.value in args: # changed for v1.5, see below
            self.fall = True
            return True
        else:
            return False


class trool(object):
  def __and__(self, other):
    if type(other) is trool: return False
    if type(other) is not bool: return False
    return other
  __or__ = __and__
  __rand__ = __and__
  __ror__ = __and__

  def __nonzero__(self):
    return False

  def __str__(self):
    return 'Maybe'
  __repr__ = __str__

Maybe = trool()

# derived from SQLAlchemy (http://www.sqlalchemy.org/); MIT License
def format_argspec_plus(fn, grouped=True):
    """Returns a dictionary of formatted, introspected function arguments.

    A enhanced variant of inspect.formatargspec to support code generation.

    fn
       An inspectable callable or tuple of inspect getargspec() results.
    grouped
      Defaults to True; include (parens, around, argument) lists

    Returns:

    args
      Full inspect.formatargspec for fn
    self_arg
      The name of the first positional argument, varargs[0], or None
      if the function defines no positional arguments.
    apply_pos
      args, re-written in calling rather than receiving syntax.  Arguments are
      passed positionally.
    apply_kw
      Like apply_pos, except keyword-ish args are passed as keywords.

    Example::

      >>> format_argspec_plus(lambda self, a, b, c=3, **d: 123)
      {'args': '(self, a, b, c=3, **d)',
       'self_arg': 'self',
       'apply_kw': '(self, a, b, c=c, **d)',
       'apply_pos': '(self, a, b, c, **d)'}

    """
    spec = callable(fn) and inspect.getargspec(fn) or fn
    args = inspect.formatargspec(*spec)
    if spec[0]:
        self_arg = spec[0][0]
    elif spec[1]:
        self_arg = '%s[0]' % spec[1]
    else:
        self_arg = None
    apply_pos = inspect.formatargspec(spec[0], spec[1], spec[2])
    defaulted_vals = spec[3] is not None and spec[0][0-len(spec[3]):] or ()
    apply_kw = inspect.formatargspec(spec[0], spec[1], spec[2], defaulted_vals,
                                     formatvalue=lambda x: '=' + x)
    if grouped:
        return dict(args=args, self_arg=self_arg,
                    apply_pos=apply_pos, apply_kw=apply_kw)
    else:
        return dict(args=args[1:-1], self_arg=self_arg,
                    apply_pos=apply_pos[1:-1], apply_kw=apply_kw[1:-1])

# derived from SQLAlchemy (http://www.sqlalchemy.org/); MIT License
def unique_symbols(used, *bases):
    used = set(used)
    for base in bases:
        pool = itertools.chain((base,),
                               itertools.imap(lambda i: base + str(i),
                                              xrange(1000)))
        for sym in pool:
            if sym not in used:
                used.add(sym)
                yield sym
                break
        else:
            raise NameError("exhausted namespace for symbol base %s" % base)

# derived from SQLAlchemy (http://www.sqlalchemy.org/); MIT License
def decorator(target):
    """A signature-matching decorator factory."""

    def decorate(fn):
        spec = inspect.getargspec(fn)
        names = tuple(spec[0]) + spec[1:3] + (fn.func_name,)
        targ_name, fn_name = unique_symbols(names, 'target', 'fn')

        metadata = dict(target=targ_name, fn=fn_name)
        metadata.update(format_argspec_plus(spec, grouped=False))

        code = 'lambda %(args)s: %(target)s(%(fn)s, %(apply_kw)s)' % (
                metadata)
        decorated = eval(code, {targ_name:target, fn_name:fn})
        decorated.func_defaults = getattr(fn, 'im_func', fn).func_defaults
        return functools.update_wrapper(decorated, fn)
    return functools.update_wrapper(decorate, target)


# derived from SQLAlchemy (http://www.sqlalchemy.org/); MIT License
class _symbol(object):
    def __init__(self, name):
        """Construct a new named symbol."""
        assert isinstance(name, str)
        self.name = name
    def __reduce__(self):
        return symbol, (self.name,)
    def __repr__(self):
        return self.name
_symbol.__name__ = 'symbol'

# derived from SQLAlchemy (http://www.sqlalchemy.org/); MIT License
class symbol(object):
    """A constant symbol.

    >>> symbol('foo') is symbol('foo')
    True
    >>> symbol('foo')
    <symbol 'foo>

    A slight refinement of the MAGICCOOKIE=object() pattern.  The primary
    advantage of symbol() is its repr().  They are also singletons.

    Repeated calls of symbol('name') will all return the same instance.

    """
    symbols = {}
    _lock = threading.Lock()

    def __new__(cls, name):
        cls._lock.acquire()
        try:
            sym = cls.symbols.get(name)
            if sym is None:
                cls.symbols[name] = sym = _symbol(name)
            return sym
        finally:
            symbol._lock.release()

Unspecified = symbol('Unspecified')

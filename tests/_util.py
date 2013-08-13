"""Test suite helpers."""
import codecs
from functools import wraps
from inspect import stack
import sys

from nose.tools import eq_, assert_raises, raises


__all__ = ['asciistr', 'assert_raises', 'eq_', 'raises', 'fails',
           'requires_unicode_coercion', 'udict', 'unicode_coercion_available']

# acts like 'str', but safe to use when tests are running with
# sys.getdefaultencoding() == 'nocoercion'.
_ascii_codec = codecs.getencoder('ascii')
asciistr = lambda s: _ascii_codec(s)[0]


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
    kwargs = dict((k.decode('ascii'), v) for k, v in kwargs.items())
    if dictionary:
        base = dict((k.decode('ascii'), v) for k, v in dictionary[0].items())
        base.update(kwargs)
        return base
    else:
        return kwargs


def unicode_coercion_available():
    return sys.getdefaultencoding() != 'nocoercion'


def requires_unicode_coercion(fn):
    @wraps(fn)
    def decorated(*args, **kw):
        if sys.getdefaultencoding() != 'nocoercion':
            return fn(*args, **kw)
        try:
            fn(*args, **kw)
        except UnicodeError:
            # failure is success!
            return
        else:
            raise AssertionError("Test did not trigger expected UnicodeError.")
    return decorated


def _allowed_coercion(input):
    global genshis
    if isinstance(input, (int, float, long, type(None))):
        return True
    calling_file = stack()[2][1]
    if calling_file.endswith('sre_parse.py'):
        return True
    elif 'genshi' in calling_file and 'out/genshi' not in calling_file:
        # OMG slow on genshi 0.5.2
        return True
    return False


class NoCoercionCodec(codecs.Codec):

    def encode(self, input, errors='string'):
        if _allowed_coercion(input):
            return codecs.ascii_encode(input, errors)
        raise UnicodeError("encoding coercion blocked")

    def decode(self, input, errors='strict'):
        if _allowed_coercion(input):
            return codecs.ascii_decode(input, errors)
        raise UnicodeError("encoding coercion blocked")


class _IncrementalEncoder(codecs.IncrementalEncoder):

    def encode(self, input, final=False):
        if _allowed_coercion(input):
            return codecs.ascii_encode(input, self.errors)[0]
        raise UnicodeError("encoding coercion blocked")


class _IncrementalDecoder(codecs.IncrementalDecoder):

    def decode(self, input, final=False):
        if _allowed_coercion(input):
            return codecs.ascii_decode(input, self.errors)[0]
        raise UnicodeError("encoding coercion blocked")


class _StreamWriter(NoCoercionCodec, codecs.StreamWriter):
    pass


class _StreamReader(NoCoercionCodec, codecs.StreamReader):
    pass


def enable_coercion_blocker():
    registration = lambda name: codecs.CodecInfo(
        name='nocoercion',
        encode=NoCoercionCodec().encode,
        decode=NoCoercionCodec().decode,
        incrementalencoder=_IncrementalEncoder,
        incrementaldecoder=_IncrementalDecoder,
        streamwriter=_StreamWriter,
        streamreader=_StreamReader,
        )
    codecs.register(registration)
    reload(sys)
    sys.setdefaultencoding("nocoercion")

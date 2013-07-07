import re

from flatland._compat import PY2, bytestring_type, text_type
from flatland.util import symbol


__all__ = ['pathexpr']

expression_cache = {}
max_cache_size = 1024

TOP = symbol('TOP')
UP = symbol('UP')
HERE = symbol('HERE')
SLICE = symbol('SLICE')
NAME = symbol('NAME')

_tokenize_re = re.compile(r"""
    (
      # name
      (?:\\[/.\[]|[^/\[])+
    | # /
      (?<!\\)/
    | # [1:2:3]
      (?<!\\)\[(-?\d*:?-?\d*\:?-?\d*)(?<!\\)\](?=$|/|\[)
    | # [bogus]
      (?<!\\)\[[^\]]*(?<!\\)\](?=$|/|\[)
    | # . or .. at start
      ^\.\.?
    | # . or .. in expression
      (?<=[^\\]/)\.\.?
    |
      \[
    )
    """, re.VERBOSE)
_unescape_re = re.compile(r"\\(/|\[|\]|\.)")


def pathexpr(expr):
    if isinstance(expr, PathExpression):
        return expr
    elif PY2 and isinstance(expr, bytestring_type):
        expr = text_type(expr)
    elif isinstance(expr, text_type):
        pass
    elif hasattr(expr, '__iter__'):
        expr = u'/'.join(expr)
    try:
        return expression_cache[expr]
    except KeyError:
        compiled = PathExpression(expr)
        if len(expression_cache) < max_cache_size:
            return expression_cache.setdefault(expr, compiled)
        else:
            return compiled


class PathExpression(object):

    def __init__(self, expr):
        self.expr = expr
        self.ops = tokenize(expr)

    def __call__(self, element, strict=False):
        found = []
        contexts = [(self.ops, element)]

        for _ops, el in contexts:
            for idx in xrange(len(_ops)):
                op, data = _ops[idx]
                if op is TOP:
                    el = el.root
                elif op is UP:
                    if el.parent:
                        el = el.parent
                elif op is HERE:
                    pass
                elif op is NAME:
                    try:
                        el = el._index(data)
                    except (LookupError, TypeError):
                        if strict:
                            if el.name:
                                type_ = '%s element %r' % (
                                    el.__class__.__name__, el.name)
                            else:
                                type_ = 'Unnamed element %s' % (
                                    el.__class__.__name__)
                            raise LookupError(
                                "%s has no child %r in expression %r" % (
                                    type_, data, self.expr))
                        break
                elif op is SLICE:
                    children = list(el.children)[data]
                    contexts.extend((_ops[idx + 1:], child)
                                    for child in children)
                    break
            else:
                found.append(el)
        return found

    def __str__(self):
        if PY2:
            return self.expr.encode('utf8')
        return self.expr

    def __unicode__(self):
        return self.expr

    def __repr__(self):
        return 'pathexpr(%r)' % self.__str__()


def tokenize(path):
    """Parse *path* and return a list of (OP, data) pairs."""
    tokens = []
    last, last_type = None, None
    canonical = True

    for token, slice_spec in _tokenize_re.findall(path):
        if token == u'/':
            # '/foo' -> TOP, 'foo'
            if last is None:
                tokens.append((TOP, None))
            # 'foo//' -> 'foo', None
            elif last == u'/':
                tokens.append((NAME, None))

        # . -> here
        elif token == u'.':
            canonical = False
            tokens.append((HERE, None))

        # foo/../bar -> 'foo', up, 'bar'
        elif token == u'..':
            canonical = False
            tokens.append((UP, None))

        # [:] or [123] or [1:] or [5] etc.
        elif slice_spec:
            tokens.append(_parse_slice(slice_spec))

        # /foo/bar[quux]/ -> 'foo', 'bar[quux]'
        elif token.startswith(u'[') and last_type is NAME:
            previous = tokens.pop()
            last = last + _unescape_re.sub(u'\\1', token)
            tokens.append((previous[0], last))
            continue

        # foo/bar/baz[bogus] -> 'foo', 'bar', 'baz[bogus]'
        else:
            name = _unescape_re.sub(u'\\1', token)
            tokens.append((NAME, name))
        last = token
        last_type = tokens[-1][0]

    if canonical:
        return tokens
    # foo/../bar -> bar
    return _canonicalize(tokens)


def _canonicalize(tokens):
    """Collapse redundant steps from token lists containing UP or HERE ops."""
    canonical = []
    for token in tokens:
        if token[0] is HERE and len(tokens) > 1:
            continue
        if token[0] is not UP or not canonical:
            canonical.append(token)
            continue
        last = canonical[-1][0]
        if last is TOP:
            continue
        elif last is not UP:
            canonical.pop()
        else:
            canonical.append(token)
    return canonical


def _parse_slice(pattern):
    """Return a slice() instance for a string:slice:pattern."""
    if pattern == u':' or pattern == u'::':
        return (SLICE, slice(None))
    elif u':' not in pattern:
        if not pattern.startswith(u'-'):
            return (NAME, pattern)
        else:
            offset = int(pattern)
            if offset == -1:
                return (SLICE, slice(offset, None))
            return (SLICE, slice(offset, offset + 1))

    segs = pattern.split(u':', 2)
    start = segs[0] and int(segs[0]) or 0
    stop = segs[1] and int(segs[1]) or None

    if len(segs) < 3:
        return (SLICE, slice(start, stop))
    stride = segs[2] and int(segs[2]) or 1
    if not segs[0]:
        start = None
    return (SLICE, slice(start, stop, stride))

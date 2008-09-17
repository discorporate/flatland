from __future__ import absolute_import

import re
from collections import defaultdict

from .base import Schema, Node
from .scalars import Scalar, _ScalarNode
from flatland import util
from flatland.util import Unspecified


__all__ = 'List', 'Array', 'Dict'


class _ContainerNode(Node):
    """Holds other nodes."""


class Container(Schema):
    """Holds other schema items."""

    node_type = _ContainerNode


def _argument_to_node(index):
    """Argument filter, transforms a positional argument to a Node.

    Index counts up from 0, not including self.

    """
    @util.decorator
    def transform(fn, self, *args, **kw):
        target = args[index]
        if target is not None and not isinstance(target, Node):
            args = list(args)
            args[index] = self.schema.spec.new(value=target)
        return fn(self, *args, **kw)
    return transform


class _SequenceNode(_ContainerNode, list):
    def set(self, iterable):
        del self[:]
        self.extend(iterable)

    @_argument_to_node(0)
    def append(self, value):
        list.append(self, value)

    def extend(self, iterable):
        for v in iterable:
            self.append(v)

    # the slice protocol really uglies this up
    def __setitem__(self, index, value):
        if isinstance(index, slice):
            value = list(item if isinstance(item, Node)
                         else self.schema.spec.new(value=item)
                         for item in value)
        else:
            if not isinstance(value, Node):
                value = self.schema.spec.new(value=value)
        list.__setitem__(self, index, value)

    def __setslice__(self, i, j, value):
        self.__setitem__(slice(i, j), value)

    @_argument_to_node(1)
    def insert(self, index, value):
        list.insert(index, value)

    def _el(self, path):
        if path and path[0].isdigit():
            idx = int(path[0])
            if idx < len(self):
                return self[idx]._el(path[1:])
        elif not path:
            return self
        raise KeyError()

    @property
    def u(self):
        return u'[%s]' % ', '.join(value.u if isinstance(value, _ContainerNode)
                                           else repr(value.u)
                                   for value in self)

    @property
    def value(self):
        return list(value.value for value in self)


class Sequence(Container):
    """Base of sequence-like Containers."""

    node_type = _SequenceNode

    def __init__(self, name, **kw):
        super(Sequence, self).__init__(name, **kw)
        self.spec = None


class _ListNode(_SequenceNode):
    def __init__(self, schema, parent=None, value=Unspecified):
        _SequenceNode.__init__(self, schema, parent=parent)

        if value is not Unspecified:
            self.extend(value)
        elif schema.default:
            for idx in xrange(0, schema.default):
                list.append(self, self._new_slot())

    def _new_slot(self, value=Unspecified, **kw):
        wrapper = self.schema.slot_type(len(self), self)
        if value is Unspecified:
            member = self.schema.spec.new(parent=wrapper, **kw)
        elif isinstance(value, Node):
            member = value
            member.parent=wrapper
        else:
            member = self.schema.spec.new(parent=wrapper, value=value, **kw)
        wrapper.node = member
        return wrapper

    @property
    def _slots(self):
        """An iterator of the ListNode's otherwise hidden Slots."""
        return list.__iter__(self)

    def append(self, value):
        list.append(self, self._new_slot(value))

    def extend(self, iterable):
        for v in iterable:
            self.append(v)

    def __getitem__(self, index):
        if isinstance(index, slice):
            return [item.node for item in list.__getitem__(self, index)]
        return list.__getitem__(self, index).node

    def __getslice__(self, i, j):
        return self.__getitem__(slice(i, j))

    def __setitem__(self, index, value):
        if isinstance(index, slice):
            value = [self._new_slot(item) for item in value]
            list.__setitem__(self, index, value)
            self._renumber()
        else:
            slot = self[index]
            slot.set(value)

    def __setslice__(self, i, j, sequence):
        return self.__setitem__(slice(i, j), sequence)

    def __iter__(self):
        return list.__iter__(self)
        #for i in list.__iter__(self):
        #    yield i.node

    # index, count, __contains__
    # - handled by __eq__ proxy on Slot

    ## Reordering methods
    # Optimizing __delitem__ or pop when removing only the last item
    # doesn't seem worth it.
    def __delitem__(self, index):
        # slices ok
        list.__delitem__(self, index)
        self._renumber()

    def __delslice__(self, i, j):
        return self.__delitem__(slice(i, j))

    def pop(self, index=-1):
        value = list.pop(self, index)
        self._renumber()
        return value

    def insert(self, index, value):
        list.insert(self, index, self._new_slot(value))
        self._renumber()

    def remove(self, value):
        list.remove(self, value)
        self._renumber()

    def sort(self, *args, **kw):
        raise TypeError('List object may not be reordered.')
    reverse = sort

    def _renumber(self):
        for idx, node in enumerate(self):
            node.name = idx

    def apply(self, func, data=None, depth_first=False):
        if depth_first:
            r = []
        else:
            r = [func(self, data)]

        for child in [node.apply(func, data)
                      for node in list.__iter__(self)]:
            r.extend(child)

        if depth_first:
            r.extend([func(self, data)])

        return r

    def _set_flat(self, pairs, sep):
        del self[:]

        if not pairs:
            return

        regex = re.compile(u'^' + re.escape(self.name + sep) +
                           ur'(\d+)' + re.escape(sep))

        slots = defaultdict(list)
        prune = self.schema.prune_empty

        for key, value in pairs:
            if value == u'' and prune:
                continue
            m = regex.match(key)
            if not m:
                continue
            try:
                slot = long(m.group(1))
                slots[slot].append((key[len(m.group(0)):], value))
            except TypeError:
                # Ignore keys with outrageously large indexes- they
                # aren't valid data for us.
                pass

        if not slots:
            return

        # FIXME: lossy, not-lossy. allow maxidx on not-lossy
        # Only implementing lossy here.

        for slot_index in sorted(slots.keys()):
            slot = self._new_slot()
            list.append(self, slot)
            slot.node.set_flat(slots[slot_index], sep)


class _Slot(_ContainerNode):
    schema = Schema(None)

    def __init__(self, name, parent):
        self.name = name
        self.parent = parent
        self.node = None

    def _set_name(self, name):
        if isinstance(name, int):
            name = unicode(name)
        self._name = name

    name = property(lambda self: self._name, _set_name)

    def __repr__(self):
        return u'<ListSlot[%s] for %r>' % (self.name, self.node)

    def __eq__(self, other):
        return self.node == other

    def __ne__(self, other):
        return self.node != other

    def apply(self, func, data=None, depth_first=False):
        if depth_first:
            r = []
        else:
            r = [func(self, data)]

        r.extend(self.node.apply(func, data))

        if depth_first:
            r.extend([func(self, data)])
        return r


class List(Sequence):
    """An ordered, homogeneous Container."""
    node_type = _ListNode
    slot_type = _Slot

    def __init__(self, name, *schema, **kw):
        """

        default:
          Optional, number of child elements to build out by default.

        """
        super(List, self).__init__(name, **kw)

        # TODO: why? maybe only ok for non-Dict?
        self.prune_empty = kw.get('prune_empty', True)

        if not len(schema):
            raise TypeError
        elif len(schema) > 1:
            self.spec = Dict(None, *schema)
        else:
            self.spec = schema[0]


class _ArrayNode(_SequenceNode, _ScalarNode):
    def set(self, value):
        self.append(value)

    def _get_u(self):
        if not self:
            return u''
        else:
            return self[-1].u

    def _set_u(self, value):
        self.append(None)
        self[-1].u = value

    u = property(_get_u, _set_u)
    del _get_u, _set_u

    def _get_value(self):
        if not self:
            return None
        else:
            return self[-1].value

    def _set_value(self, value):
        self.append(None)
        self[-1].value = value

    value = property(_get_value, _set_value)
    del _get_value, _set_value

    def __nonzero__(self):
        # FIXME: this is a little troubling, given that it may not
        # match the appearance of the node in a scalar context.
        # (further: list context? scalar context? what is this, perl?)
        return len(self)

    def _set_flat(self, pairs, sep):
        prune = self.schema.prune_empty
        for key, value in pairs:
            if key == self.name:
                if value == u'' and prune:
                    continue
                self.set(value)


class Array(Sequence, Scalar):
    """A transparent homogeneous Container, for multivalued form elements.

    Arrays take on the name of their child.  When used as a scalar,
    they act as their last member.  All values are available when used
    as a sequence.

    TODO: is any of that a good idea? if so, should it be first rather
    than last?

    A `el.set(val)` on an Array element will add `val` to the Array.
    To set a full set of value at once, assign using slice syntax:
    `el[:] = [...]`

    """

    node_type = _ArrayNode

    def __init__(self, array_of, **kw):
        assert isinstance(array_of, Scalar)
        self.prune_empty = kw.pop('prune_empty', True)
        super(Array, self).__init__(array_of.name, **kw)
        self.spec = array_of


class Mapping(Container):
    """Base of mapping-like Containers."""


class _DictNode(_ContainerNode, dict):
    def __init__(self, schema, **kw):
        value = kw.pop('value', Unspecified)
        Node.__init__(self, schema, **kw)

        if schema.default:
            self.set(schema.default)
        elif value is not Unspecified:
            self.set(value)
        else:
            self._reset()

    def __setitem__(self, key, value):
        if not key in self:
            raise TypeError(u'May not set unknown key "%s" on Dict "%s"' %
                           (key, self.name))
        self[key].set(value)

    def __delitem__(self, key):
        # this may be overly pedantic
        if key not in self:
            raise KeyError(key)
        raise TypeError('Dict keys are immutable.')

    def clear(self):
        raise TypeError('Dict keys are immutable.')

    def _reset(self):
        """Set all child nodes to their defaults."""
        for key, spec in self.schema.fields.items():
            dict.__setitem__(self, key, spec.new(parent=self))

    def popitem(self):
        raise TypeError('Dict keys are immutable.')

    def pop(self, key):
        if key not in self:
            raise KeyError(key)
        raise TypeError('Dict keys are immutable.')

    def update(self, dictish=None, **kwargs):
        if dictish is not None:
            for key, value in util.to_pairs(dictish):
                self[key] = value
        for key, value in kwargs.iteritems():
            self[key] = value

    def setdefault(self, key, default=None):
        # The key will always either be present or not creatable.
        raise TypeError('Dict keys are immutable.')

    def get(self, key, default=None):
        if key not in self:
            raise KeyError(u'Immutable Dict "%s" schema does not contain '
                           u'key "%s".' % (self.name, key))
        # default will never be used.
        return self[key]

    def apply(self, func, data=None, depth_first=False):
        if depth_first:
            r = []
        else:
            r = [func(self, data)]

        for child in [self[key].apply(func, data) for key in self]:
            r.extend(child)

        if depth_first:
            r.extend([func(self, data)])
        return r

    def set(self, value, policy=None):
        pairs = util.to_pairs(value)
        self._reset()

        if policy is not None:
            assert policy in ('strict', 'subset', 'duck')
        else:
            policy = self.schema.policy

        # not really convinced yet that these modes are required
        # only testing 'subset' policy

        seen = set()
        for key, value in pairs:
            if key not in self:
                if policy != 'duck':
                    raise KeyError(
                        'Dict "%s" schema does not allow key "%r"' % (
                            self.name, key))
                continue
            self[key] = value
            seen.add(key)

        if policy == 'strict':
            required = set(self.iterkeys())
            if seen != required:
                missing = required - seen
                raise TypeError(
                    'strict-mode Dict requires all keys for '
                    'a set() operation, missing %s.' % (
                        ','.join(repr(key) for key in missing)))

    def _set_flat(self, pairs, sep):
        if self.name is None:
            possibles = pairs  # accept all
        else:
            possibles = []
            prefix = self.name + sep
            plen = len(prefix)
            for key, value in pairs:
                if key == prefix:
                    # No flat representation of dicts, ignore.
                    pass
                if key.startswith(prefix):
                    # accept child element
                    possibles.append( (key[plen:], value) )

        if not possibles:
            return

        # FIXME: pivot on length of pairs: top loop either fields or pairs
        # FIXME2: wtf does that mean

        for field in self:
            accum = []
            for key, value in possibles:
                if key.startswith(field):
                    accum.append((key, value))
            if accum:
                self[field].set_flat(accum, sep)

    def _el(self, path):
        if path:
            return self[path[0]]._el(path[1:])
        elif not path:
            return self
        raise KeyError()

    @property
    def u(self):
        pairs = ((key, value.u if isinstance(value, _ContainerNode)
                               else repr(value.u))
                  for key, value in self.iteritems())
        return u'{%s}' % ', '.join("%r: %s" % (k, v) for k, v in pairs)

    @property
    def value(self):
        return dict((key, value.value) for key, value in self.iteritems())

class Dict(Mapping):
    """A mapping Container with named members."""

    node_type = _DictNode
    policy = 'subset'

    def __init__(self, name, *specs, **kw):
        if not specs:
            raise TypeError()

        policy = kw.pop('policy', Unspecified)

        Mapping.__init__(self, name, **kw)
        self.fields = {}
        for spec in specs:
            self.fields[spec.name] = spec

        if policy is not Unspecified:
            self.policy = policy
        assert self.policy in ('strict', 'subset', 'duck')



from __future__ import absolute_import

import re
from collections import defaultdict

from .base import Schema, Node
from .scalar import Scalar, _ScalarNode


__all__ = 'List', 'Array', 'Dict', 'Form'


# FIXME
unspecified = object()

class Container(Schema):
    """Holds other schema items."""


class _SequenceNode(Node, list):
    def set(self, value):
        if isinstance(value, (list, tuple)) or hasattr(value, 'next'):
            # wtf!
            del self[:]
            self.extend(*value)
        elif value is None:
            # wtf part 2!
            del self[:]
        else:
            raise ValueError('Inappropriate value type to populate a '
                             'sequence: %s' % type(value))

    def append(self, value):
        if not isinstance(value, Node):
            value = self.schema.spec.new(value=value)
        list.append(self, value)

    def extend(self, iterable):
        for v in iterable:
            self.append(v)

    def __setitem__(self, index, value):
        if not isinstance(value, Node):
            value = self.schema.spec.new(value=value)
        list.__setitem__(self, index, value)

    def insert(self, index, value):
        if not isinstance(value, Node):
            value = self.schema.spec.new(value=value)
        list.insert(index, value)

    def _el(self, path):
        if path and path[0].isdigit():
            idx = int(path[0])
            if idx < len(self):
                return self[idx]._el(path[1:])
        elif not path:
            return self
        raise KeyError()


class Sequence(Container):
    """Base of sequence-like Containers."""

    node_type = _SequenceNode

    def __init__(self, name, *args, **kw):
        super(Sequence, self).__init__(name, **kw)
        self.spec = args


class _ListNode(_SequenceNode):
    def __init__(self, schema, **kw):
        super(_ListNode, self).__init__(schema, **kw)

        if schema.default:
            for i in xrange(0, schema.default):
                wrapper = self.schema.slot_type(i, self)
                member = schema.spec.new(parent=wrapper)
                wrapper.node = member
                list.append(self, wrapper)

    def _new_slot(self, value=unspecified, **kw):
        wrapper = self.schema.slot_type(len(self), self)
        if value is unspecified:
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
        for idx in xrange(0, len(self)):
            list.__getitem__(self, idx).name = idx

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
            m = regex.match(key)
            if m:
                try:
                    slot = long(m.group(1))
                    if value == u'' and prune:
                        continue
                    slots[slot].append((key[len(m.group(0)):], value))
                # Ignore keys with outrageously large indexes- they
                # aren't valid data for us.
                except TypeError:
                    pass

        if not slots:
            return

        # FIXME: lossy, not-lossy. allow maxidx on not-lossy
        # Only implementing lossy here.

        for slot_index in sorted(slots.keys()):
            slot = self._new_slot()
            list.append(self, slot)
            slot.node.set_flat(slots[slot_index], sep)


class _Slot(Node):
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

    def _get_value(self):
        if not self:
            return None
        else:
            return self[-1].value

    def _set_value(self, value):
        self.append(None)
        self[-1].value = value

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
    """An unordered, homogeneous Container, for multivalued form elements.

    Arrays take on the name of their child.  When used as a scalar,
    they act as their last member.  All values are available when used
    as a sequence.

    TODO: is any of that a good idea? if so, should it be first rather
    than last?

    """

    node_type = _ArrayNode

    def __init__(self, array_of, **kw):
        assert isinstance(array_of, Scalar)
        self.prune_empty = kw.pop('prune_empty', True)
        super(Array, self).__init__(array_of.name, **kw)
        self.spec = array_of



class Mapping(Container):
    """Base of mapping-like Containers."""


class _DictNode(Node, dict):
    def __init__(self, schema, **kw):
        Node.__init__(self, schema, **kw)

        for key, spec in schema.fields.items():
            dict.__setitem__(self, key, spec.new(parent=self))

        if schema.default:
            self.set(schema.default)
        elif 'value' in kw:
            self.set(kw['value'])

    def __setitem__(self, key, value):
        if not self.has_key(key):
            raise KeyError(u'May not set unknown key "%s" on Dict "%s"' %
                           (key, self.name))
        self[key].set(value)

    def clear(self):
        raise AssertionError('Dict keys are immutable.')
    popitem = clear

    def pop(self, key):
        raise KeyError('Dict keys are immutable.')

    def update(self, dictish=None, **attribs):
        if dictish is not None:
            self.set(dictish, policy='subset')
        if attribs:
            self.set(attribs, policy='subset')

    # punt: setdefault semantics don't make sense here- the key will
    # always be present.
    def setdefault(self, key, default=None):
        raise KeyError('Dict keys are immutable.')

    def get(self, key, default=None):
        if key not in self:
            raise KeyError(u'Immutable Dict "%s" schema does not contain '
                           u'key "%s".' % (self.name, key))
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
        if value is None:
            for key in self.keys():
                self[key] = None
        elif isinstance(value, dict) or hasattr(value, 'items'):
            my_fields = set(self.keys())

            if policy is not None:
                assert policy in ('strict', 'subset', 'duck')
            else:
                policy = self.schema.policy

            items = list(value.items())

            for key, value in items:
                if key not in my_fields:
                    if policy <> 'duck':
                        raise KeyError(u'Dict "%s" schema does not allow '
                                       u'key "%s".' % (self.name, key))
                    continue

                self[key] = value

            if policy == 'strict' and len(items) <> len(my_fields):
                got = set([key for key, _ in items])
                need = u', '.join([unicode(i) for i in my_fields - got])
                raise KeyError(u'strict-mode Dict requires all keys for '
                               u'a set() operation, missing "%s".' % need)

        else:
            raise ValueError(u'Inappropriate value type to populate '
                             u'Dict "%s": %s' % (self.name, type(value)))

    def _set_flat(self, pairs, sep):
        possibles = []
        if self.name is None:
            possibles = pairs  # accept all
        else:
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
        fields = list(self.keys())

        for field in fields:
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


class Dict(Mapping):
    """A mapping Container with named members."""

    node_type = _DictNode

    def __init__(self, name, *specs, **kw):
        Mapping.__init__(self, name, **kw)
        self.spec = None
        self.fields = {}
        for spec in specs:
            self.fields[spec.name] = spec

        self.policy = kw.get('policy', 'subset')
        assert self.policy in ('strict', 'subset', 'duck')



class MetaForm(type):
    def __call__(cls, *args, **kw):
        form = cls.__new__(cls)
        form.__init__(*args, **kw)
        return form.node()

class Form(Dict):
    """
    Schemas are the most common top-level mapping.  They behave like
    Dicts, but do not need to be named.  FIXME: Also magic schema holder.
    """
    __metaclass__ = MetaForm

    def __init__(self, *args, **kw):
        if args and isinstance(args[0], basestring):
            args = list(args)
            name = args.pop(0)
        else:
            name = None

        if hasattr(self, 'schema'):
            members = self.schema[:]
            members.extend(args)
        else:
            members = args

        if hasattr(self, 'validators'):
            if 'validators' in kw:
                v = self.validators[:]
                v.extend(kw['validators'])
                kw['validators'] = v
            else:
                kw['validators'] = self.validators[:]

        assert members
        Dict.__init__(self, name, *members, **kw)



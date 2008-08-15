import re
from collections import defaultdict

from flatland.schema.base import Schema, MetaSchema
from flatland.schema import scalar


__all__ = 'List', 'Array', 'Dict', 'Form'


class Container(Schema):
    pass

class Sequence(Container):
    def __init__(self, name, *args, **kw):
        super(Sequence, self).__init__(name, **kw)
        self.spec = args

    class Element(Container.Element, list):
        def set(self, value):
            if isinstance(value, (list, tuple)) or hasattr(value, 'next'):
                self._clear()
                self.extend(*value)
            elif value is None:
                self._clear()
            else:
                raise ValueError('Inappropriate value type to populate a '
                                 'sequence: %s' % type(value))
        def append(self, value):
            list.append(self, self.schema.spec.new(value=value))
        def extend(self, *values):
            for v in values:
                self.append(v)
        def _clear(self):
            while len(self):
                self.pop()

        def _el(self, path):
            if path and path[0].isdigit():
                idx = int(path[0])
                if idx < len(self):
                    return self[idx]._el(path[1:])
            elif not path:
                return self
            raise KeyError()


class List(Sequence):
    def __init__(self, name, *schema, **kw):
        super(List, self).__init__(name, **kw)

        self.prune_empty = kw.get('prune_empty', True)

        assert len(schema) > 0
        if len(schema) > 1:
            self.spec = Dict(None, *schema)
        else:
            self.spec = schema[0]

    class Element(Sequence.Element):
        def __init__(self, schema, **kw):
            super(List.Element, self).__init__(schema, **kw)

            if schema.default:
                for i in xrange(0, schema.default):
                    wrapper = List.Slot(i, self)
                    member = schema.spec.new(parent=wrapper)
                    wrapper.node = member
                    list.append(self, wrapper)

        def _new_slot(self, **kw):
            wrapper = List.Slot(len(self), self)
            member = self.schema.spec.new(parent=wrapper, **kw)
            wrapper.node = member
            return wrapper

        def append(self, value):
            list.append(self, self._new_slot(value=value))

        def extend(self, *values):
            for v in values:
                self.append(v)
        def __getitem__(self, index):
            return list.__getitem__(self, index).node

        def __setitem__(self, index, value):
            slot = self[index]
            slot.set(value)

        def __iter__(self):
            for i in list.__iter__(self):
                yield i.node

        ## index, count, __contains__:
        # handled by __eq__ proxy on Slot

        ## Reordering methods
        # Optimizing __delitem__ or pop when removing only the last item
        # doesn't seem worth it.
        def __delitem__(self, index):
            list.__delitem__(self, index)
            self._renumber()

        def pop(self, index=-1):
            value = list.pop(self, index)
            self._renumber()
            return value

        def insert(self, index, value):
            list.insert(self, index, value)
            self._renumber()

        def remove(self, value):
            list.remove(self, value)
            self._renumber()

        def sort(self, *args, **kw):
            raise ValueError('List object may not be reordered.')
        reverse = sort

        def __getslice__(self, i, j):
            slice = list.__getslice__(self, i, j)
            return [slot.node for slot in slice]

        def __setslice__(self, i, j, value):
            raise NotImplementedError('FIXME')

        def __delslice__(self, i, j):
            list.__delslice__(self, i, j)
            self._renumber()

        def _clear(self):
            while len(self):
                self.pop()

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
            self._clear()

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

    SlotSchema = Schema(None)

    class Slot(Schema.Element):
        def __init__(self, name, parent):
            self.name = name
            self.parent = parent
            self.node = None
            self.schema = List.SlotSchema

        def _set_name(self, name):
            if isinstance(name, int):
                name = unicode(name)
            self._name = name

        name = property(lambda self: self._name, _set_name)

        def __repr__(self):
            return u'<ListSlot[%s] for %s>' % (self.name, repr(self.node))

        def __eq__(self, other):
            return self.node == other

        def apply(self, func, data=None, depth_first=False):
            if depth_first:
                r = []
            else:
                r = [func(self, data)]

            r.extend(self.node.apply(func, data))

            if depth_first:
                r.extend([func(self, data)])

            return r


class Array(Sequence, scalar.Scalar):
    def __init__(self, array_of, **kw):
        assert isinstance(array_of, Scalar)
        super(Array, self).__init__(array_of.name, **kw)

        self.spec = array_of
        self.prune_empty = kw.get('prune_empty', True)

    class Element(Sequence.Element, scalar.Scalar.Element):
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
            return len(self)

        def _set_flat(self, pairs, sep):
            prune = self.schema.prune_empty
            for key, value in pairs:
                if key == self.name:
                    if value == u'' and prune:
                        continue
                    self.set(value)


class Mapping(Container):
    pass


class Dict(Mapping):
    def __init__(self, name, *specs, **kw):
        super(Dict, self).__init__(name, **kw)
        self.spec = None
        self.fields = {}
        for spec in specs:
            self.fields[spec.name] = spec

        self.policy = kw.get('policy', 'subset')
        assert self.policy in ('strict', 'subset', 'duck')

    class Element(Mapping.Element, dict):
        def __init__(self, schema, **kw):
            super(Dict.Element, self).__init__(schema, **kw)

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


class MetaForm(MetaSchema):
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
        super(Form, self).__init__(name, *members, **kw)



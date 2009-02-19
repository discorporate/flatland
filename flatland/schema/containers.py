from __future__ import absolute_import

import re
from collections import defaultdict

from .base import FieldSchema, Element, Slot, validate_element
from .scalars import Scalar, _ScalarElement
from flatland import util
from flatland.util import Unspecified


__all__ = 'List', 'Array', 'Dict'


class _ContainerElement(Element):
    """Holds other elements."""


class Container(FieldSchema):
    """Holds other schema items."""

    element_type = _ContainerElement
    descent_validators = ()

    def __init__(self, name, descent_validators=Unspecified, **kw):
        super(Container, self).__init__(name, **kw)
        if descent_validators is not Unspecified:
            self.descent_validators = descent_validators

    def validate_element(self, element, state, descending):
        """Validates on the second, upward pass.

        See :meth:`FieldSchema.validate_element`.
        """
        if descending:
            if self.descent_validators:
                return validate_element(element, state, self.descent_validators)
            else:
                return None
        else:
            return validate_element(element, state, self.validators)

def _argument_to_element(index):
    """Argument filter, transforms a positional argument to a Element.

    Index counts up from 0, not including self.

    """
    @util.decorator
    def transform(fn, self, *args, **kw):
        target = args[index]
        if not isinstance(target, Element):
            args = list(args)
            args[index] = self.schema.spec.new(value=target)
        return fn(self, *args, **kw)
    return transform


class _SequenceElement(_ContainerElement, list):
    def set(self, iterable):
        del self[:]
        self.extend(iterable)

    @_argument_to_element(0)
    def append(self, value):
        list.append(self, value)

    def extend(self, iterable):
        for v in iterable:
            self.append(v)

    # the slice protocol really uglies this up
    def __setitem__(self, index, value):
        if isinstance(index, slice):
            value = list(item if isinstance(item, Element)
                         else self.schema.spec.new(value=item)
                         for item in value)
        else:
            if not isinstance(value, Element):
                value = self.schema.spec.new(value=value)
        list.__setitem__(self, index, value)

    def __setslice__(self, i, j, value):
        self.__setitem__(slice(i, j), value)

    @_argument_to_element(1)
    def insert(self, index, value):
        list.insert(self, index, value)

    def _index(self, name):
        try:
            idx = int(name)
        except ValueError:
            raise IndexError(name)
        return self[idx]

    @property
    def children(self):
        return iter(self)

    @property
    def value(self):
        return list(value.value for value in self)

    @property
    def u(self):
        return u'[%s]' % ', '.join(
            element.u if isinstance(element, _ContainerElement)
                    else repr(element.u)
            for element in self)

    @property
    def is_empty(self):
        return not any(True for _ in self.children)

class Sequence(Container):
    """Base of sequence-like Containers."""

    element_type = _SequenceElement

    def __init__(self, name, **kw):
        super(Sequence, self).__init__(name, **kw)
        self.spec = None


class _ListElement(_SequenceElement):
    def __init__(self, schema, parent=None, value=Unspecified):
        _SequenceElement.__init__(self, schema, parent=parent)

        if value is not Unspecified:
            self.extend(value)

    def _new_slot(self, value=Unspecified, **kw):
        wrapper = self.schema.slot_type(len(self), self)
        if value is Unspecified:
            member = self.schema.spec.new(parent=wrapper, **kw)
        elif isinstance(value, Element):
            member = value
            member.parent=wrapper
        else:
            member = self.schema.spec.new(parent=wrapper, value=value, **kw)
        wrapper.element = member
        return wrapper

    @property
    def _slots(self):
        """An iterator of the ListElement's otherwise hidden Slots."""
        return list.__iter__(self)

    def append(self, value):
        list.append(self, self._new_slot(value))

    def extend(self, iterable):
        for v in iterable:
            self.append(v)

    def __getitem__(self, index):
        if isinstance(index, slice):
            return [item.element for item in list.__getitem__(self, index)]
        return list.__getitem__(self, index).element

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
        #    yield i.element

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
        for idx, element in enumerate(self):
            element.name = idx

    def apply(self, func, data=None, depth_first=False):
        if depth_first:
            r = []
        else:
            r = [func(self, data)]

        for child in [element.apply(func, data)
                      for element in list.__iter__(self)]:
            r.extend(child)

        if depth_first:
            r.extend([func(self, data)])

        return r

    @property
    def children(self):
        return iter(child.element for child in self)

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

        for slot_index in sorted(slots):
            slot = self._new_slot()
            list.append(self, slot)
            slot.element.set_flat(slots[slot_index], sep)

    def set_default(self):
        if self.schema.default:
            del self[:]
            for _ in xrange(0, self.schema.default):
                el = self._new_slot()
                list.append(self, el)
                el.set_default()

    @property
    def u(self):
        return u'[%s]' % ', '.join(
            value.u if isinstance(value.element, _ContainerElement)
                    else repr(value.u)
            for value in self)

class _SlotElement(_ContainerElement, Slot):
    schema = FieldSchema(None)

    def __init__(self, name, parent):
        self.name = name
        self.parent = parent
        self.element = None

    def _set_name(self, name):
        if isinstance(name, int):
            name = unicode(name)
        self._name = name

    name = property(lambda self: self._name, _set_name)

    @property
    def u(self):
        return self.element.u

    @property
    def value(self):
        return self.element.value

    def __repr__(self):
        return u'<ListSlot[%s] for %r>' % (self.name, self.element)

    def __getitem__(self, index):
        return self.element[index]

    def __setitem__(self, index, value):
        self.element[index] = value

    def __delitem__(self, index):
        del self.element[index]

    def __getslice__(self, slice):
        return self.element[slice]

    def __setslice__(self, slice, value):
        self.element[slice] = value

    def __delslice(self, slice):
        del self.element[slice]

    def apply(self, func, data=None, depth_first=False):
        if depth_first:
            r = []
        else:
            r = [func(self, data)]

        r.extend(self.element.apply(func, data))

        if depth_first:
            r.extend([func(self, data)])
        return r

    def set_default(self):
        self.element.set_default()


class List(Sequence):
    """An ordered, homogeneous Container."""
    element_type = _ListElement
    slot_type = _SlotElement

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


class _ArrayElement(_SequenceElement):

    def __init__(self, schema, parent=None, value=Unspecified):
        _SequenceElement.__init__(self, schema, parent=parent)
        if value is not Unspecified:
            self.extend(value)

    def _set_flat(self, pairs, sep):
        prune = self.schema.prune_empty
        self.set(value for key, value in pairs
                 if key == self.name and not prune or value != u'')

    def set_default(self):
        if self.schema.default:
            del self[:]
            self.extend(self.schema.default)


class _MultiValueElement(_ArrayElement, _ScalarElement):
    def u(self):
        """The .u of the first item in the sequence, or u''."""
        if not self:
            return u''
        else:
            return self[0].u

    def _set_u(self, value):
        if not self:
            self.append(None)
        self[0].u = value

    u = property(u, _set_u)
    del _set_u

    def value(self):
        """The .value of the first item in the sequence, or None."""
        if not self:
            return None
        else:
            return self[0].value

    def _set_value(self, value):
        if not self:
            self.append(None)
        self[0].value = value

    value = property(value, _set_value)
    del _set_value

    def __nonzero__(self):
        # this is a little troubling, given that it may not match the
        # appearance of the element in a scalar context.
        return len(self)


class Array(Sequence):
    """A transparent homogeneous Container, for multivalued form elements.

    Arrays hold a collection of values under a single name, allowing
    all values of a repeated `(key, value)` pair to be captured and
    used.  Elements are sequence-like.

    """

    element_type = _ArrayElement

    def __init__(self, array_of, **kw):
        assert isinstance(array_of, Scalar)
        self.prune_empty = kw.pop('prune_empty', True)
        super(Array, self).__init__(array_of.name, **kw)
        self.spec = array_of


class MultiValue(Array, Scalar):
    """A transparent homogeneous Container, for multivalued form elements.

    MultiValues combine aspects of :class:`Scalar` and
    :class:`Sequence` fields, allowing all values of a repeated `(key,
    value)` pair to be captured and used.

    MultiValues take on the name of their child and have no identity
    of their own when flattened.  Elements are mostly sequence-like
    and can be indexed and iterated. However the :attr:`.u` or
    :attr:`.value` are scalar-like, and return values from the first
    element in the sequence.

    """

    element_type = _MultiValueElement


class Mapping(Container):
    """Base of mapping-like Containers."""


class _DictElement(_ContainerElement, dict):
    def __init__(self, schema, **kw):
        value = kw.pop('value', Unspecified)
        Element.__init__(self, schema, **kw)

        self._reset()
        if value is not Unspecified:
            self.set(value)

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
        """Set all child elements to their defaults."""
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

    @property
    def children(self):
        return self.itervalues()

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

    def set_default(self):
        if self.schema.default:
            self.set(self.schema.default)
        for child in self.children:
            child.set_default()

    def _index(self, name):
        return self[name]

    @property
    def u(self):
        pairs = ((key, value.u if isinstance(value, _ContainerElement)
                               else repr(value.u))
                  for key, value in self.iteritems())
        return u'{%s}' % ', '.join("%r: %s" % (k, v) for k, v in pairs)

    @property
    def value(self):
        return dict((key, value.value) for key, value in self.iteritems())

    @property
    def is_empty(self):
        """Mappings are never empty."""
        return False

    def update_object(self, obj, include=None, omit=None, rename=None, key=str):
        """Update an object's attributes using the element's values.

        Produces a :meth:`slice` using *include*, *omit*, *rename* and *key*,
        and sets the selected attributes on *obj* using ``setattr``.

        :returns: nothing. *obj* is modified directly.

        """
        data = self.slice(include=include, omit=omit, rename=rename, key=key)
        for attribute, value in data.iteritems():
            setattr(obj, attribute, value)

    def slice(self, include=None, omit=None, rename=None, key=None):
        """Return a new dict containing a subset of the element's values."""
        return dict(
            util.keyslice_pairs(
                ((key, element.value) for key, element in self.iteritems()),
                include=include, omit=omit, rename=rename, key=key))


class Dict(Mapping):
    """A mapping Container with named members."""

    element_type = _DictElement
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



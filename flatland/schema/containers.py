# -*- coding: utf-8; fill-column: 78 -*-
from collections import defaultdict
import re

from flatland.util import (
    Unspecified,
    class_cloner,
    keyslice_pairs,
    to_pairs,
    )
from .base import Element, Unevaluated, Slot, validate_element
from .scalars import Scalar


__all__ = (
    'Array',
    'Container',
    'Dict',
    'List',
    'Mapping',
    'MultiValue',
    'Sequence',
    )


class Container(Element):
    """Holds other schema items.

    Base class for schemas that can contain other schemas, such as
    :class:`List` and :class:`Dict`.

    :param descent_validators: optional, a sequence of validators that
      will be run before contained elements are validated.

    :param validators: optional, a sequence of validators that will be
      run after contained elements are validated.

    :param \*\*kw: other arguments common to
      :class:`~flatland.schema.base.FieldSchema`.

    """

    #######################################################################
    validates_down = 'descent_validators'
    validates_up = 'validators'

    descent_validators = ()

    def validate_element(self, element, state, descending):
        """Validates on the first (downward) and second (upward) pass.

        If :attr:`descent_validators` are defined on the schema, they
        will be evaluated before children are validated.  If a
        validation function returns :obj:`flatland.SkipAll` or
        :obj:`flatland.SkipFalse`, downward validation will halt on
        this container and children will not be validated.

        If :attr:`validators` are defined, they will be evaluated
        after children are validated.

        See :meth:`FieldSchema.validate_element`.

        """
        if descending:
            if self.descent_validators:
                return validate_element(
                    element, state, self.descent_validators)
            else:
                return None
        else:
            return validate_element(element, state, self.validators)


    def _validate(self, state, descending):
        """Run validation, transforming None into success. Internal."""
        # FIXME: refactor this to allow for this logic ("Don't apply default
        # validation on downward pass") to be defined declaratively.
        if descending:
            if self.validates_down:
                validators = getattr(self, self.validates_down, None)
                if not validators:
                    return Unevaluated
                return validate_element(self, state, validators)
        else:
            if self.validates_up:
                validators = getattr(self, self.validates_up, None)
                return validate_element(self, state, validators)
        return Unevaluated



    #######################################################################


class Sequence(Container, list):
    """Base of sequence-like Containers."""

    #######################################################################

    child_schema = None

    def __init__(self, value=Unspecified, **kw):
        Container.__init__(self, value, **kw)
        if not self.child_schema:
            raise TypeError("Invalid schema: %r has no child_schema" %
                            type(self))

    @class_cloner
    def of(cls, *fields):
        for field in fields:
            if isinstance(field, Element):
                raise TypeError("'of' must be initialized with types, got "
                                "instance %r" % field)
        if len(fields) == 1:
            cls.child_schema = fields[0]
        else:
            cls.child_schema = Dict.of(*fields)
        return cls

    #######################################################################

    def set(self, iterable):
        del self[:]
        self.extend(self.child_schema(value=v) for v in iterable)

    def set_default(self):
        default = self.default
        if default is not None and default is not Unspecified:
            del self[:]
            self.extend(default)

    def _set_flat(self, pairs, sep):
        raise NotImplementedError()

    @property
    def children(self):
        return iter(self)

    @property
    def is_empty(self):
        return not any(True for _ in self.children)

    def _index(self, name):
        try:
            idx = int(name)
        except ValueError:
            raise IndexError(name)
        return self[idx]

    def append(self, value):
        if not isinstance(value, Element):
            value = self.child_schema(value=value)
        value.parent = self
        list.append(self, value)

    def extend(self, iterable):
        for value in iterable:
            self.append(value)

    def insert(self, index, value):
        if not isinstance(value, Element):
            value = self.child_schema(value=value)
        value.parent = self
        list.insert(self, index, value)

    def __setitem__(self, index, value):
        if isinstance(index, slice):
            as_elements = []
            for item in value:
                if not isinstance(item, Element):
                    item = self.child_schema(value=item)
                item.parent = self
                as_elements.append(item)
            value = as_elements
        else:
            if not isinstance(value, Element):
                value = self.child_schema(value=value)
                value.parent = self
        list.__setitem__(self, index, value)

    def __setslice__(self, i, j, value):
        self.__setitem__(slice(i, j), value)

    def remove(self, value):
        if not isinstance(value, Element):
            value = self.child_schema(value=value)
        list.remove(self, value)

    def index(self, value):
        if not isinstance(value, Element):
            value = self.child_schema(value=value)
        return list.index(self, value)

    def count(self, value):
        if not isinstance(value, Element):
            value = self.child_schema(value=value)
        return list.count(self, value)

    def __contains__(self, value):
        if not isinstance(value, Element):
            value = self.child_schema(value=value)
        return list.__contains__(self, value)

    @property
    def value(self):
        return list(value.value for value in self.children)

    @property
    def u(self):
        return u'[%s]' % ', '.join(
            element.u if isinstance(element, Container)
                      else repr(element.u)
            for element in self.children)


class ListSlot(Container, Slot):
    """Wraps elements of Lists & models their position in the list.

    :class:`List ` makes these mostly invisible to the outside, appearing only
    when flattening names.  The :attr:`name` is set by the List and will be a
    unicoded integer index.  Flattening a list name will join the parent's
    name with the slot's name with the child element's name:

      'listname_0_childname', 'listname_1_childname'

    """

    def __init__(self, name, parent, element):
        self.name = name
        self.parent = parent
        self.element = element
        element.parent = self

    @property
    def u(self):
        return self.element.u

    @property
    def value(self):
        return self.element.value

    def __repr__(self):
        return u'<ListSlot[%s] for %r>' % (self.name, self.element)


class List(Sequence):
    """An ordered, homogeneous Container.

    Example:

    .. doctest::

      >>> from flatland import List
      >>> Names = List.named('names').of(String.named('name'))
      >>> names = Names()
      >>> names.set([u'a', u'b'])
      >>> names.append(u'c')
      >>> names.value
      [u'a', u'b', u'c']
      >>> names.flatten()
      [(u'names_0_name', u'a'), (u'names_1_name', u'b'), (u'names_2_name', u'c')]

    :param name: field name

    :param \*schema: one or more
      :class:`~flatland.schema.base.FieldSchema` to contain.  If
      multiple are provided, an anonymous :class:`Dict` will be
      implicitly created to hold them.

    :param default: optional, the number of child elements to build
      out by default.

    :param descent_validators: optional, a sequence of validators that
      will be run before contained elements are validated.

    :param validators: optional, a sequence of validators that will be
      run after contained elements are validated.

    :param \*\*kw: other arguments common to
      :class:`~flatland.schema.base.FieldSchema`.

    """

    ###
    slot_type = ListSlot
    prune_empty = True
    child_schema = None

    ###

    def _as_element(self, value):
        """TODO"""
        if value is Unspecified:
            return self.child_schema()
        if isinstance(value, Element):
            return value
        else:
            return self.child_schema(value)

    def _new_slot(self, value=Unspecified):
        """Wrap *element* in a Slot named as the element's index in the list."""
        return self.slot_type(name=unicode(len(self)),
                              parent=self,
                              element=self._as_element(value))

    @property
    def _slots(self):
        """An iterator of the List's otherwise hidden Slots."""
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
        for i in list.__iter__(self):
            yield i.element

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
        value.parent = None
        return value

    def insert(self, index, value):
        list.insert(self, index, self._new_slot(value))
        self._renumber()

    def remove(self, value):
        list.remove(self, self._as_element(value))
        self._renumber()

    # TODO count, index?

    def sort(self, *args, **kw):
        # TODO: implementing this is do-able
        raise TypeError('List object may not be reordered.')
    reverse = sort

    def _renumber(self):
        for idx, element in enumerate(self._slots):
            element.name = unicode(idx)

    @property
    def children(self):
        return iter(child.element for child in self._slots)

    def _set_flat(self, pairs, sep):
        del self[:]

        if not pairs:
            return

        regex = re.compile(u'^' + re.escape(self.name + sep) +
                           ur'(\d+)' + re.escape(sep))

        slots = defaultdict(list)
        prune = self.prune_empty

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
        default = self.default
        if default is not None and default is not Unspecified:
            del self[:]
            for _ in xrange(0, default):
                slot = self._new_slot()
                list.append(self, slot)
                slot.element.set_default()


class Array(Sequence):
    """A transparent homogeneous Container, for multivalued form elements.

    Arrays hold a collection of values under a single name, allowing
    all values of a repeated `(key, value)` pair to be captured and
    used.  Elements are sequence-like.

    """

    #######################################################################
    prune_empty = True

    def __init__(self, value=Unspecified, **kw):
        Sequence.__init__(self, value=value, **kw)
        # FIXME: is this true?
        if self.name is None:
            self.name = self.child_schema.name

    #######################################################################

    def _set_flat(self, pairs, sep):
        prune = self.prune_empty
        self.set(value for key, value in pairs
                 if key == self.name and not prune or value != u'')


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


class Mapping(Container):
    """Base of mapping-like Containers."""

    @class_cloner
    def of(cls, *fields):
        # TODO: doc
        # TODO: maybe accept **kw?
        for field in fields:
            if isinstance(field, Element):
                raise TypeError("'of' must be initialized with types, got "
                                "instance %r" % field)

        unique_names = set(field.name for field in fields)
        # TODO: ensure these are types, not instances
        if len(unique_names) != len(fields):
            names = [field.name for field in fields]
            dupes = [name for name in unique_names if names.count(name) > 1]
            raise TypeError(
                "All fields in a %s must have unique names. "
                "Duplicates of: %s " % (
                    cls.__name__,
                    ', '.join(repr(f) for f in dupes)))

        cls.field_schema = fields
        return cls


class Dict(Mapping, dict):
    """A mapping Container with named members."""

    #######

    #######################################################################
    policy = 'subset'
    field_schema = ()

    def __init__(self, value=Unspecified, **kw):
        Container.__init__(self, **kw)
        if not self.field_schema:
            raise TypeError("%r dictionary type has no fields defined" % (
                type(self).__name__))
        self._reset()
        if value is not Unspecified:
            self.set(value)


    @classmethod
    def from_object(cls, obj, include=None, omit=None, rename=None, **kw):
        """Return an element initialized with an object's attributes.

        :param obj: any object
        :param include: optional, an iterable of attribute names to pull from
            *obj*, if present on the object.  Only these attributes will be
            included.
        :param omit: optional, an iterable of attribute names to ignore on
            **obj**.  All other attributes matching a named field on the Form
            will be included.
        :param rename: optional, a mapping of attribute-to-field name
            transformations.  Attributes specified in the mapping will be
            included regardless of *include* or *omit*.
        :param \*\*kw: keyword arguments will be passed to the element's
            constructor.

        *include* and *omit* are mutually exclusive.

        Creates and initializes an element, using as many attributes as
        possible from *obj*.  Object attributes that do not correspond to
        field names are ignored.

        Elements have two corresponding methods useful for round-tripping
        values in and out of your domain objects.

        .. testsetup::

          # FIXME
          from flatland import Form, String
          class UserForm(Form):
              login = String
              password = String
              verify_password = String

          class User(object):
              def __init__(self, login=None, password=None):
                  self.login = login
                  self.password = password

          user = User('squiznart')

        :meth:`DictElement.update_object` performs the inverse of
        :meth:`from_object`, and :meth:`DictElement.slice` is useful
        for constructing new objects.

        .. doctest::

          >>> form = UserForm.from_object(user)
          >>> form.update_object(user, omit=['verify_password'])
          >>> new_user = User(**form.slice(omit=['verify_password'], key=str))

        """
        self = cls(**kw)

        fields = set(self.iterkeys())
        attributes = fields.copy()
        if rename:
            rename = list(to_pairs(rename))
            attributes.update(key for key, value in rename
                                  if value in attributes)
        if omit:
            omit = list(omit)
            attributes.difference_update(omit)

        possible = ((attr, getattr(obj, attr))
                    for attr in attributes
                    if hasattr(obj, attr))

        sliced = keyslice_pairs(possible, include=include,
                                omit=omit, rename=rename)
        final = dict((key, value)
                     for key, value in sliced
                     if key in fields)
        self.set(final)
        return self

    #######################################################################

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
        for child_schema in self.field_schema:
            key = child_schema.name
            dict.__setitem__(
                self, key, child_schema.create_element(parent=self))

    def popitem(self):
        raise TypeError('Dict keys are immutable.')

    def pop(self, key):
        if key not in self:
            raise KeyError(key)
        raise TypeError('Dict keys are immutable.')

    def update(self, dictish=None, **kwargs):
        if dictish is not None:
            for key, value in to_pairs(dictish):
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

    @property
    def children(self):
        return self.itervalues()

    def set(self, value, policy=None):
        pairs = to_pairs(value)
        self._reset()

        if policy is not None:
            assert policy in ('strict', 'subset', 'duck')
        else:
            policy = self.policy

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
            self[key].set(value)
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
        default = self.default
        if default is not None and default is not Unspecified:
            self.set(default)
        else:
            for child in self.children:
                child.set_default()

    def _index(self, name):
        return self[name]

    @property
    def u(self):
        pairs = ((key, value.u if isinstance(value, Container)
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

    def update_object(self, obj, include=None, omit=None, rename=None,
                      key=str):
        """Update an object's attributes using the element's values.

        Produces a :meth:`slice` using *include*, *omit*, *rename* and
        *key*, and sets the selected attributes on *obj* using
        ``setattr``.

        :returns: nothing. *obj* is modified directly.

        """
        data = self.slice(include=include, omit=omit, rename=rename, key=key)
        for attribute, value in data.iteritems():
            setattr(obj, attribute, value)

    def slice(self, include=None, omit=None, rename=None, key=None):
        """Return a new dict containing a subset of the element's values."""
        return dict(
            keyslice_pairs(
                ((key, element.value) for key, element in self.iteritems()),
                include=include, omit=omit, rename=rename, key=key))


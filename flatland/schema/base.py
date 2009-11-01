# -*- coding: utf-8; fill-column: 78 -*-
import collections
import itertools
import operator
from flatland.signals import validator_validated
from flatland.util import (
    Unspecified,
    assignable_class_property,
    assignable_property,
    class_cloner,
    named_int_factory,
    symbol,
    )


__all__ = 'Element'

NoneType = type(None)
Root = symbol('Root')
NotEmpty = symbol('NotEmpty')

Skip = named_int_factory('Skip', True, doc="""\
Abort validation of the element & mark as valid.
""")

SkipAll = named_int_factory('SkipAll', True, doc="""\
Abort validation of the element and its children & mark as valid.

The :attr:`~Element.valid` of child elements will not be changed by skipping.
Unless otherwise set, the child elements will retain the default value
(:obj:`Unevaluated`).  Only meaningful during a decent validation.  Functions
as :obj:`Skip` on upward validation.
""")

SkipAllFalse = named_int_factory('SkipAllFalse', False, doc="""\
Aborts validation of the element and its children & mark as invalid.

The :attr:`~Element.valid` of child elements will not be changed by skipping.
Unless otherwise set, the child elements will retain the default value
(:obj:`Unevaluated`). Only meaningful during a decent validation.  Functions
as ``False`` on upward validation.
""")

Unevaluated = named_int_factory('Unevaluated', True, doc="""\
A psuedo-boolean representing a presumptively valid state.

Assigned to newly created elements that have never been evaluated by
:meth:`Element.validate`.  Evaluates to true.
""")

# TODO: implement a lighter version of the xml quoters
xml = None


class _BaseElement(object):
    # Required by the genshi support's __bases__ manipulation, unfortunately.
    pass


class Element(_BaseElement):
    """Base class for form fields.

    A data node that stores a Python and a text value plus added state.
    """

    name = None
    """The Unicode name of the element."""

    optional = False
    """If True, :meth:`validate` with return True if no value has been set.

    :attr:`validators` are not called for optional, empty elements.
    """

    validators = ()
    """A sequence of validators, invoked by :meth:`validate`.

    See `Validation`_
    """

    default_factory = None
    """A callable to generate default element values.  Passed an element.

    *default_factory* will be used preferentially over :attr:`default`.
    """

    ugettext = None
    """If set, provides translation support to validation messages.

    See `Message Internationalization`_.
    """

    ungettext = None
    """If set, provides translation support to validation messages.

    See `Message Internationalization`_.
    """

    value = None
    """The element's native Python value.

    Only validation routines should write this attribute directly: use
    :meth:`set` to update the element's value.
    """

    u = u''
    """A Unicode representation of the element's value.

    As in :attr:`value`, writing directly to this attribute should be
    restricted to validation routines.
    """

    flattenable = False
    validates_down = None
    validates_up = None

    def __init__(self, value=Unspecified, **kw):
        self.parent = kw.pop('parent', None)

        self.valid = Unevaluated
        self.errors = []
        self.warnings = []

        # FIXME This (and 'using') should also do descent_validators
        # via lookup - or don't copy at all
        if 'validators' in kw:
            kw['validators'] = list(kw['validators'])

        for attribute, override in kw.items():
            if hasattr(self, attribute):
                setattr(self, attribute, override)
            else:
                raise TypeError(
                    "%r is an invalid keyword argument: not a known "
                    "argument or an overridable class property of %s" % (
                        attribute, type(self).__name__))

        if value is not Unspecified:
            self.set(value)

    @class_cloner
    def named(cls, name):
        """Return a class with ``name`` = *name*

        :param name: a string or None.  ``str`` will be converted to
          ``unicode``.
        :returns: a new class

        """
        if not isinstance(name, (unicode, NoneType)):
            name = unicode(name)
        cls.name = name
        return cls

    @class_cloner
    def using(cls, **overrides):
        """Return a class with attributes set from *\*\*overrides*.

        :param \*\*overrides: new values for any attributes already present on
          the class.  A ``TypeError`` is raised for unknown attributes.
        :returns: a new class
        """

        # TODO: See TODO in __init__
        if 'validators' in overrides:
            overrides['validators'] = list(overrides['validators'])

        for attribute, value in overrides.iteritems():
            # TODO: must make better
            if callable(value):
                value = staticmethod(value)
            if hasattr(cls, attribute):
                setattr(cls, attribute, value)
                continue
            raise TypeError(
                "%r is an invalid keyword argument: not a known "
                "argument or an overridable class property of %s" % (
                    attribute, cls.__name__))
        return cls

    def validate_element(self, element, state, descending):
        """Assess the validity of an element.

        TODO: this method is dead.  Evaluate docstring for good bits that
        should be elsewhere.

        :param element: an :class:`Element`
        :param state: may be None, an optional value of supplied to
            ``element.validate``
        :param descending: a boolean, True the first time the element
            has been seen in this run, False the next

        :returns: boolean; a truth value or None

        The :meth:`Element.validate` process visits each element in
        the tree twice: once heading down the tree, breadth-first, and
        again heading back up in the reverse direction.  Scalar fields
        will typically validate on the first pass, and containers on
        the second.

        Return no value or None to ``pass``, accepting the element as
        presumptively valid.

        Exceptions raised by :meth:`validate_element` will not be
        caught by :meth:`Element.validate`.

        Directly modifying and normalizing :attr:`Element.value` and
        :attr:`Element.u` within a validation routine is acceptable.

        The standard implementation of validate_element is:

         - If :attr:`element.is_empty` and :attr:`self.optional`,
           return True.

         - If :attr:`self.validators` is empty and
           :attr:`element.is_empty`, return False.

         - If :attr:`self.validators` is empty and not
           :attr:`element.is_empty`, return True.

         - Iterate through :attr:`self.validators`, calling each
           member with (*element*, *state*).  If one returns a false
           value, stop iterating and return False immediately.

         - Otherwise return True.

        """
        return validate_element(element, state, self.validators)

    @classmethod
    def from_flat(cls, pairs, **kw):
        """Return a new element with its value initialized from *pairs*.

        :param \*\*kw: passed through to the :attr:`element_type`.

        .. testsetup::

          import flatland
          cls = flatland.String
          pairs = kw = {}

        This is a convenience constructor for:

        .. testcode::

          element = cls(**kw)
          element.set_flat(pairs)

        """
        element = cls(**kw)
        element.set_flat(pairs)
        return element

    @classmethod
    def from_defaults(cls, **kw):
        """Return a new element with its value initialized from field defaults.

        :param \*\*kw: passed through to the :attr:`element_type`.

        .. testsetup::

          import flatland
          cls = flatland.String
          kw = {}

        This is a convenience constructor for:

        .. testcode::

          element = cls(**kw)
          element.set_default()

        """
        element = cls(**kw)
        element.set_default()
        return element

    def __eq__(self, other):
        try:
            return self.value == other.value and self.u == other.u
        except AttributeError:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    @assignable_class_property
    def label(self, cls):
        """The label of this element.

        If unassigned, the *label* will evaluate to the :attr:`name`.

        """
        return cls.name if self is None else self.name

    # TODO: assignable_class_property, return None for class?
    @assignable_property
    def default(self):
        """The default value of this element.

        If unset, the default will be derived from the
        :attr:`~flatland.schema.base.Element.default_factory`.

        """
        if self.default_factory is not None:
            return self.default_factory(self)
        else:
            return None

    def _get_all_valid(self):
        """True if this element and all children are valid."""
        if not self.valid:
            return False
        for element in self.all_children:
            if not element.valid:
                return False
        return True

    def _set_all_valid(self, value):
        self.valid = value
        for element in self.all_children:
            element.valid = value
    all_valid = property(_get_all_valid, _set_all_valid)
    del _get_all_valid, _set_all_valid

    @property
    def root(self):
        """The top-most parent of the element."""
        try:
            return list(self.parents)[-1]
        except IndexError:
            return self

    @property
    def parents(self):
        """An iterator of all parent elements."""
        element = self.parent
        while element is not None:
            yield element
            element = element.parent
        raise StopIteration()

    @property
    def path(self):
        """An iterator of all elements from root to the Element, inclusive."""
        return itertools.chain(reversed(list(self.parents)), (self,))

    @property
    def children(self):
        """An iterator of immediate child elements."""
        return iter(())

    @property
    def all_children(self):
        """An iterator of all child elements, breadth-first."""

        seen, queue = set((id(self),)), collections.deque(self.children)
        while queue:
            element = queue.popleft()
            if id(element) in seen:
                continue
            seen.add(id(element))
            yield element
            queue.extend(element.children)

    def fq_name(self, sep=u'.'):
        """Return the fully qualified path name of the element.

        Returns a *sep*-separated string of :meth:`.el` compatible element
        indexes starting from the :attr:`Element.root` (``.``) down to the
        element.

          >>> from flatland import Dict, Integer
          >>> Point = Dict.named(u'point').of(Integer.named(u'x'),
          ...                                 Integer.named(u'y'))
          >>> p = Point(dict(x=10, y=20))
          >>> p.name
          u'point'
          >>> p.fq_name()
          u'.'
          >>> p['x'].name
          u'x'
          >>> p['x'].fq_name()
          u'.x'

        The index used in a path may not be the :attr:`.name` of the
        element.  For example, sequence members are referenced by their
        numeric index.

          >>> from flatland import List, String
          >>> Addresses = List.named('addresses').of(String.named('address'))
          >>> form = Addresses([u'uptown', u'downtown'])
          >>> form.name
          u'addresses'
          >>> form.fq_name()
          u'.'
          >>> form[0].name
          u'address'
          >>> form[0].fq_name()
          u'.0'

        """
        if self.parent is None:
            return sep

        children_of_root = reversed(list(self.parents)[:-1])

        parts, mask = [], None
        for element in list(children_of_root) + [self]:
            # allow Slot elements to mask the names of their child
            # e.g.
            #     <List name='l'> <Slot name='0'> <String name='s'>
            # has an .el()/Python path of just
            #   l.0
            # not
            #   l.0.s
            if isinstance(element, Slot):
                mask = element.name
                continue
            elif mask:
                parts.append(mask)
                mask = None
                continue
            parts.append(element.name)
        return sep + sep.join(parts)

    def el(self, path, sep=u'.'):
        """Find a child element by string path.

        :param path: a *sep*-separated string of element names, or an
            iterable of names
        :param sep: optional, a string separator used to parse *path*

        :returns: an :class:`Element` or raises :exc:`KeyError`.

        .. testsetup:: el

          from flatland import Form, Dict, List, String
          class Profile(Form):
              contact = Dict.of(List.named('addresses').
                                of(Dict.of(String.named('street1'),
                                           String.named('city'))).
                                using(default=1))
          form = Profile.from_defaults()

        .. doctest:: el

          >>> first_address = form.el('contact.addresses.0')
          >>> first_address.el('street1')
          <String u'street1'; value=None>

        Given a relative path as above, :meth:`el` searches for a matching
        path among the element's children.

        If *path* begins with *sep*, the path is considered fully qualified
        and the search is resolved from the :attr:`Element.root`.  The
        leading *sep* will always match the root node, regardless of its
        :attr:`.name`.

        .. doctest:: el

          >>> form.el('.contact.addresses.0.city')
          <String u'city'; value=None>
          >>> first_address.el('.contact.addresses.0.city')
          <String u'city'; value=None>

        """
        try:
            names = list(self._parse_element_path(path, sep)) or ()
            if names[0] is Root:
                element = self.root
                names.pop(0)
            else:
                element = self
            while names:
                element = element._index(names.pop(0))
            return element
        except LookupError:
            raise KeyError('No element at %r' % (path,))

    def _index(self, name):
        """Return a named child or raise LookupError."""
        raise NotImplementedError()

    @classmethod
    def _parse_element_path(self, path, sep):
        if isinstance(path, basestring):
            if path == sep:
                return [Root]
            elif path.startswith(sep):
                path = path[len(sep):]
                parts = [Root]
            else:
                parts = []
            parts.extend(path.split(sep))
            return iter(parts)
        else:
            return iter(path)
        # fixme: nuke?
        if isinstance(path, (list, tuple)) or hasattr(path, 'next'):
            return path
        else:
            assert False
            return None

    def add_error(self, message):
        "Register an error message on this element, ignoring duplicates."
        if message not in self.errors:
            self.errors.append(message)

    def add_warning(self, message):
        "Register a warning message on this element, ignoring duplicates."
        if message not in self.warnings:
            self.warnings.append(message)

    def flattened_name(self, sep='_'):
        """Return the element's complete flattened name as a string.

        Joins this element's :attr:`path` with *sep* and returns the fully
        qualified, flattened name.  Encodes all :class:`Container` and other
        structures into a single string.

        Example::

          >>> import flatland
          >>> form = flatland.List('addresses',
          ...                      flatland.String('address'))
          >>> element = form()
          >>> element.set([u'uptown', u'downtown'])
          >>> element.el('0').value
          u'uptown'
          >>> element.el('0').flattened_name()
          u'addresses_0_address'

        """
        return sep.join(parent.name
                        for parent in self.path
                        if parent.name is not None)

    def flatten(self, sep=u'_', value=operator.attrgetter('u')):
        """Export an element hierarchy as a flat sequence of key, value pairs.

        :arg sep: a string, will join together element names.

        :arg value: a 1-arg callable called once for each
            element. Defaults to a callable that returns the
            :attr:`.u` of each element.

        Encodes the element hierarchy in a *sep*-separated name
        string, paired with any representation of the element you
        like.  The default is the Unicode value of the element, and the
        output of the default :meth:`flatten` can be round-tripped
        with :meth:`set_flat`.

        Given a simple form with a string field and a nested dictionary::

          >>> from flatland import Dict, String
          >>> class Nested(Form):
          ...     contact = Dict.of(String.named(u'name'),
          ...                       Dict.named(u'address').\
          ...                            of(String.named(u'email')))
          ...
          >>> element = Nested()
          >>> element.flatten()
          [(u'contact_name', u''), (u'contact_address_email', u'')]

        The value of each pair can be customized with the *value* callable::

          >>> element.flatten(value=operator.attrgetter('u'))
          [(u'contact_name', u''), (u'contact_address_email', u'')]
          >>> element.flatten(value=lambda el: el.value)
          [(u'contact_name', None), (u'contact_address_email', None)]

        Solo elements will return a sequence containing a single pair::

          >>> element['name'].flatten()
          [(u'contact_name', u'')]

        """
        if self.flattenable:
            pairs = [(self.flattened_name(sep), value(self))]
        else:
            pairs = []
        pairs.extend((e.flattened_name(sep), value(e))
                     for e in self.all_children
                     if e.flattenable)
        return pairs

    def set(self, value):
        """Assign the native and Unicode value.

        Attempts to adapt the given *value* and assigns this element's
        :attr:`value` and :attr:`u` attributes in tandem.  Returns True if the
        adaptation was successful.

        If adaptation succeeds, :attr:`value` will contain the adapted native
        value and :attr:`u` will contain a Unicode serialized version of it. A
        native value of None will be represented as u'' in :attr:`u`.

        If adaptation fails, :attr:`value` will be ``None`` and :attr:`u` will
        contain ``unicode(value)`` or ``u''`` for None.

          >>> from flatland import Integer
          >>> el = Integer()
          >>> el.u, el.value
          (u'', None)

          >>> el.set('123')
          True
          >>> el.u, el.value
          (u'123', 123)

          >>> el.set(456)
          True
          >>> el.u, el.value
          (u'456', 456)

          >>> el.set('abc')
          False
          >>> el.u, el.value
          (u'abc', None)

          >>> el.set(None)
          True
          >>> el.u, el.value
          (u'', None)

        """
        raise NotImplementedError()

    def set_flat(self, pairs, sep='_'):
        """Set element values from pairs, expanding the element tree as needed.

        Given a sequence of name/value tuples or a dict, build out a
        structured tree of value elements.

        """
        if hasattr(pairs, 'items'):
            pairs = pairs.items()

        return self._set_flat(pairs, sep)

    def _set_flat(self, pairs, sep):
        raise NotImplementedError()

    def set_default(self):
        """set() the element to the schema default."""
        raise NotImplementedError()

    @property
    def is_empty(self):
        """True if the element has no value."""
        return True if (self.value is None and self.u == u'') else False

    def validate(self, state=None, recurse=True):
        """Assess the validity of this element and its children.

        :param state: optional, will be passed unchanged to all validator
            callables.

        :param recurse: if False, do not validate children.  :returns: True or
          False

        Iterates through this element and all of its children, invoking each
        element's :meth:`schema.validate_element`.  Each element will be
        visited twice: once heading down the tree, breadth-first, and again
        heading back up in reverse order.

        Returns True if all validations pass, False if one or more fail.

        """
        if not recurse:
            down = self._validate(state, True)
            if down is Unevaluated:
                self.valid = down
            else:
                self.valid = bool(down)

            up = self._validate(state, False)
            # an Unevaluated ascent validator does not override the results
            # of descent validation
            if up is not Unevaluated:
                self.valid = bool(up)
            return self.valid

        valid = True
        elements, seen, queue = [], set(), collections.deque([self])

        # descend breadth first, skipping any branches that return All*
        while queue:
            element = queue.popleft()
            if id(element) in seen:
                continue
            seen.add(id(element))
            elements.append(element)
            validated = element._validate(state, True)

            if validated is Unevaluated:
                element.valid = validated
            else:
                element.valid = bool(validated)
                if valid:
                    valid &= validated
            if validated is SkipAll or validated is SkipAllFalse:
                continue
            queue.extend(element.children)

        # back up, visiting only the elements that weren't skipped above
        for element in reversed(elements):
            validated = element._validate(state, False)

            # an Unevaluated ascent validator does not override the results
            # of descent validation
            if validated is Unevaluated:
                pass
            elif element.valid:
                element.valid = bool(validated)
                if valid:
                    valid &= validated
        return bool(valid)

    def _validate(self, state, descending):
        """Run validation, transforming None into success. Internal."""
        if descending:
            if self.validates_down:
                validators = getattr(self, self.validates_down, None)
                return validate_element(self, state, validators)
        else:
            if self.validates_up:
                validators = getattr(self, self.validates_up, None)
                return validate_element(self, state, validators)
        return Unevaluated

    @property
    def x(self):
        """Sugar, the xml-escaped value of :attr:`.u`."""
        global xml
        if xml is None:
            import xml.sax.saxutils
        return xml.sax.saxutils.escape(self.u)

    @property
    def xa(self):
        """Sugar, the xml-attribute-escaped value of :attr:`.u`."""
        global xml
        if xml is None:
            import xml.sax.saxutils
        return xml.sax.saxutils.quoteattr(self.u)[1:-1]

    def __hash__(self):
        raise TypeError('%s object is unhashable', self.__class__.__name__)


class Slot(object):
    """Marks a semi-visible Element-holding Element, like the 0 in list[0]."""


def validate_element(element, state, validators):
    """Apply a set of validators to an element.

    :param element: a `~flatland.Element`

    :param state: may be None, an optional value of supplied to
      ``element.validate``

    :param validators: an iterable of validation functions

    :return: a truth value

    If validators is empty or otherwise false, a fallback validation
    of ``not element.is_empty`` will be used.  Empty but optional
    elements are considered valid.

    Emits :class:`flatland.signals.validator_validated` after each
    validator is tested.

    """
    if element.is_empty and element.optional:
        return True
    if not validators:
        valid = not element.is_empty
        if validator_validated.receivers:
            validator_validated.send(
                NotEmpty, element=element, state=state, result=valid)
        return valid
    for fn in validators:
        valid = fn(element, state)
        if validator_validated.receivers:
            validator_validated.send(
                fn, element=element, state=state, result=valid)
        if valid is None:
            return False
        elif valid is Skip:
            return True
        elif not valid or valid is SkipAll:
            return valid
    return True

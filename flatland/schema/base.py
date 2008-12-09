# -*- coding: utf-8; fill-column: 78 -*-
import collections
import itertools
import operator

from flatland import util
from flatland.util import Unspecified


__all__ = 'FieldSchema', 'Element'

NoneType = type(None)
Root = util.symbol('Root')
xml = None

class _BaseElement(object):
    pass


class Element(_BaseElement):
    """TODO

    :param schema: the :class:`FieldSchema` that defined the element.

    :param parent: a parent :class:`Element` or None.

    Elements can be supplied to template environments and used to
    great effect there: elements contain all of the information needed
    to display or redisplay a HTML form field, including errors
    specific to a field.

    The :attr:`.u`, :attr:`.x`, :attr:`.xa` and :meth:`el` members are
    especially useful in templates and have shortened names to help
    preserve your sanity when used in markup.

    """

    flattenable = False
    value = None
    u = u''

    def __init__(self, schema, parent=None):
        self.schema = schema
        self.parent = parent

        self.errors = []
        self.warnings = []

    @property
    def name(self):
        """The element's name."""
        return self.schema.name

    @property
    def label(self):
        """The element's label."""
        return self.schema.label

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
          >>> p = Dict('point', Integer('x'), Integer('y')).create_element()
          >>> p.set(dict(x=10, y=20))
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
          >>> form = List('addresses', String('address')).create_element()
          >>> form.set([u'uptown', u'downtown'])
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

        .. testsetup::

          from flatland import Form, Dict, List, String
          schema = Dict(None,
                        Dict('contact',
                             List('addresses',
                                  Dict(None,
                                       String('street1'),
                                       String('city')),
                                  default=1
                       )))
          form = schema.create_element()
          form.set_default()

        .. doctest::

          >>> first_address = form.el('contact.addresses.0')
          >>> first_address.el('street1')
          <String u'street1'; value=None>

        Given a relative path as above, :meth:`el` searches for a matching
        path among the element's children.

        If *path* begins with *sep*, the path is considered fully qualified
        and the search is resolved from the :attr:`Element.root`.  The
        leading *sep* will always match the root node, regardless of its
        :attr:`.name`.

        .. doctest::

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

    ## Errors and warnings- any element can have them.
    def add_error(self, message):
        "Register an error message on this element, ignoring duplicates."
        if message not in self.errors:
            self.errors.append(message)

    def add_warning(self, message):
        "Register a warning message on this element, ignoring duplicates."
        if message not in self.warnings:
            self.warnings.append(message)

    ## Element value and wrangling
    def apply(self, func, data=None, depth_first=False):
        """TODO"""
        return [func(self, data)]

    def flattened_name(self, sep='_'):
        """Return the element's complete flattened name as a string.

        Joins this element's :attr:`path` with *sep* and returns the fully
        qualified, flattened name.  Encodes all :class:`Container` and other
        structures into a single string.

        Example::

          >>> import flatland
          >>> form = flatland.List('addresses',
          ...                      flatland.String('address'))
          >>> element = form.create_element()
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

        Given a simple form with a nested dictionary::

          >>> import flatland
          >>> form = flatland.Dict('contact',
          ...                      flatland.String('name'),
          ...                      flatland.Dict('address',
          ...                                    flatland.String('email')))
          >>> element = form.create_element()

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
        pairs = []
        def serialize(element, data):
            if element.flattenable:
                data.append((element.flattened_name(sep), value(element)))

        self.apply(serialize, pairs)
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

          >>> import flatland
          >>> field = flatland.Integer('number')
          >>> el = field.create_element()
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
        """Set element value to the schema default."""
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
            return (self._validate(state, True) &
                    self._validate(state, False))

        elements = [self] + list(self.all_children)

        # validate down, and then back up
        return (reduce(operator.and_, (e._validate(state, True)
                                       for e in elements), True)
                &
                reduce(operator.and_, (e._validate(state, False)
                                      for e in reversed(elements)), True))

    def _validate(self, state, descending):
        """Run validation, transforming None into success. Internal."""
        res = self.schema.validate_element(self, state, descending)
        return True if (res is None or res) else False

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


class FieldSchema(object):
    """Base class for form fields.

    :param name: the Unicode name of the field.

    :param label: optional, a human readable name for the field.  Defaults to
      *name* if not provided.

    :param default: optional. A default value for elements created from this
      Field template.  The interpretation of the *default* is subclass
      specific.

    :param validators: optional, overrides the class's default validators.

    :param optional: if True, element of this field will be considered valid
      by :meth:`Element.validate` if no value has been set.


    **Instance Attributes**

      .. attribute:: name
      .. attribute:: label
      .. attribute:: default
      .. attribute:: optional

    """
    element_type = Element
    ugettext = None
    ungettext = None
    validators = ()

    def __init__(self, name, label=Unspecified, default=None,
                 validators=Unspecified, optional=False,
                 ugettext=Unspecified, ungettext=Unspecified):
        if not isinstance(name, (unicode, NoneType)):
            name = unicode(name, errors='strict')

        self.name = name
        self.label = name if label is Unspecified else label
        self.default = default

        if validators is not Unspecified:
            self.validators = list(validators)
        self.optional = optional

        for override in ('ugettext', 'ungettext'):
            value = locals()[override]
            if value is not Unspecified:
                setattr(self, override, value)

    def create_element(self, **kw):
        """Returns a new Element.

        :param \*\*kw: passed through to the :attr:`element_type`.

        """
        return self.element_type(self, **kw)
    new = create_element

    def validate_element(self, element, state, descending):
        """Assess the validity of an element.

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
        if element.is_empty and self.optional:
            return True
        if not self.validators:
            return not element.is_empty
        for fn in self.validators:
            if not fn(element, state):
                return False
        return True

    def from_flat(self, pairs, **kw):
        """Return a new element with its value initialized from *pairs*.

        :param \*\*kw: passed through to the :attr:`element_type`.

        .. testsetup::

          import flatland
          field = flatland.String('test')
          pairs = {}

        This is a convenience constructor for:

        .. testcode::

          element = field.create_element()
          element.set_flat(pairs)

        """
        element = self.create_element(**kw)
        element.set_flat(pairs)
        return element

    def from_value(self, value, **kw):
        """Return a new element with its value initialized from *value*.

        :param \*\*kw: passed through to the :attr:`element_type`.

        .. testsetup::

          import flatland
          field = flatland.String('test')
          value = 'val'

        This is a convenience constructor for:

        .. testcode::

          element = field.create_element()
          element.set(value)

        """
        element = self.create_element(**kw)
        element.set(value)
        return element

    def from_defaults(self, **kw):
        """Return a new element with its value initialized from field defaults.

        :param \*\*kw: passed through to the :attr:`element_type`.

        .. testsetup::

          import flatland
          field = flatland.String('test')

        This is a convenience constructor for:

        .. testcode::

          element = field.create_element()
          element.set_default()

        """
        element = self.create_element(**kw)
        element.set_default()
        return element


class Slot(object):
    """Marks a semi-visible Element-holding Element, like the 0 in list[0]."""

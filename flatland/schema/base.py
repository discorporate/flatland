import collections
import operator
import xml.sax.saxutils
from flatland.util import Unspecified


NoneType = type(None)


class Element(object):
    """TODO


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
    def path(self):
        "A tuple of element names, starting at this element's topmost parent."
        p, element = [], self
        while element is not None:
            if element.name is not None:
                p.append(element.name)
            element = element.parent

        return tuple(reversed(p))

    @property
    def root(self):
        """The top-most parent of this element."""
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

    def fq_name(self, sep='_'):
        """Return the element's path as a string.

        Joins this element's :attr:`path` with *sep* and returns the
        fully qualified, flattened name.

        """
        return sep.join(self.path)

    def el(self, path, sep=u'.'):
        """Find an element by string path.

          >>> form.el('addresses.0.street1')

        """
        search = self._parse_element_path(path, sep)
        if search is None:
            raise KeyError(u'No element at "%s".' % path)

        try:
            return self._el(search)
        except KeyError:
            raise KeyError(u'No element found at "%s"' % path)

    def _el(self, path):
        raise NotImplementedError()

    @classmethod
    def _parse_element_path(self, path, sep):
        if isinstance(path, basestring):
            steps = path.split(sep)
        elif isinstance(path, (list, tuple)) or hasattr(path, 'next'):
            steps = path
        else:
            return None

        return [None if step in (u'""', u"''") else step for step in steps]

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

        Solo elements will return a sequence containing a single pair.

          >>> form.flatten(value=operator.attrgetter('u'))
          ... [(u'name', u''), (u'email', u'')]
          >>> form.flatten(value=lambda el: el.value)
          ... [(u'name', None), (u'email', None)]

        """
        pairs = []
        def serialize(element, data):
            if element.flattenable:
                data.append((element.fq_name(sep), value(element)))

        self.apply(serialize, pairs)
        return pairs

    def set(self, value):
        """Set the element's value.

        TODO: value is type-specific.

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

    @property
    def is_empty(self):
        return True if (self.value is None and self.u == u'') else False

    def validate(self, state=None, recurse=True):
        """Assess the validity of this element and its children.

        :param state: optional, will be passed unchanged to all
            validator callables.
        :param recurse: if False, do not validate children.
        :returns: True or False

        Iterates through this element and all of its children,
        invoking each element's :meth:`schema.validate_element`.  Each
        element will be visited twice: once heading down the tree,
        breadth-first, and again heading back up in reverse order.

        Returns True if all validations pass, False if one or more
        fail.

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

    def _validate(self, state, decending):
        """Run validation, transforming None into success. Internal."""
        res = self.schema.validate_element(self, state, decending)
        return True if (res is None or res) else False

    @property
    def x(self):
        """Sugar, the xml-escaped value of :attr:`.u`."""
        return xml.sax.saxutils.escape(self.u)

    @property
    def xa(self):
        """Sugar, the xml-attribute-escaped value of :attr:`.u`."""
        return xml.sax.saxutils.quoteattr(self.u)[1:-1]

    def __hash__(self):
        raise TypeError('%s object is unhashable', self.__class__.__name__)


class FieldSchema(object):
    """Base of all fields.

    :arg name: the Unicode name of the field.
    :arg label: optional, a human readable name for the field.
                Defaults to *name* if not provided.
    :arg default: optional. A default value for elements created from
                  this Field template.  The interpretation of the *default*
                  is subclass specific.
    :arg validators: optional, overrides the class's default validators.
    :arg optional: if True, this field will be considered valid if no
                    value has been set.

    """
    element_type = Element
    ugettext = None
    ungettext = None
    locale = None
    validators = ()

    def __init__(self, name, label=Unspecified, default=None,
                 validators=Unspecified, optional=False,
                 ugettext=Unspecified, ungettext=Unspecified,
                 locale=Unspecified):
        if not isinstance(name, (unicode, NoneType)):
            name = unicode(name, errors='strict')

        self.name = name
        self.label = name if label is Unspecified else label
        self.default = default

        if validators is not Unspecified:
            self.validators = list(validators)
        self.optional = optional

        for override in ('ugettext', 'ungettext', 'locale'):
            value = locals()[override]
            if value is not Unspecified:
                setattr(self, override, value)

    def create_element(self, *args, **kw):
        """TODO"""
        return self.element_type(self, *args, **kw)
    new = create_element

    def validate_element(self, element, state, decending):
        """Assess the validity of an element.

        :param element: an :class:`Element`
        :param state: may be None, an optional value of supplied to
            ``element.validate``
        :param decending: a boolean, True the first time the element
            has been seen in this run, False the next

        :returns boolean: a truth value or None

        The :meth:`Element.validate` process visits each element in
        the tree twice: once heading down the tree, breadth-first, and
        again heading back up in the reverse direction.  Scalar fields
        will typically validate on the first pass, and containers on
        the second.

        Return no value or None to pass, accepting the element as
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
        element = self.create_element(**kw)
        element.set_flat(pairs)
        return element

    def from_value(self, value, **kw):
        element = self.create_element(**kw)
        element.set(value)
        return element

    def from_defaults(self, **kw):
        return self.create_element(**kw)

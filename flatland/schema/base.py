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

    def validate(self, state=None, recurse=True, validators=None):
        """TODO"""
        if not recurse:
            return self._validate(state, validators=validators)

        def collector(element, _):
            return element._validate(state=state, validators=None)

        return reduce(operator.and_, self.apply(collector, None), True)

    def _validate(self, state=None, validators=None):
        if validators is None:
            if not self.schema.validators:
                return True
        validators = self.schema.validators

        valid = True
        for v in validators:
            valid &= bool(v(self, state))
            if not valid:
                return False

        return valid

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
    validators = ()

    def __init__(self, name, label=Unspecified, default=None,
                 validators=Unspecified, optional=False):
        if not isinstance(name, (unicode, NoneType)):
            name = unicode(name, errors='strict')

        self.name = name
        self.label = name if label is Unspecified else label
        self.default = default

        if validators is not Unspecified:
            self.validators = list(validators)
        self.optional = optional

    def create_element(self, *args, **kw):
        """TODO"""
        return self.element_type(self, *args, **kw)
    new = create_element

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

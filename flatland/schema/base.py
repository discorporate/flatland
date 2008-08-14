import logging
import operator
import weakref
import xml.sax.saxutils
from types import NoneType

from flatland import exc
from flatland.util import lateproperty, lazyproperty, GetitemGetattrProxy


__all__ = 'Ref'

class MetaSchema(type):
    def __init__(self, name, bases, class_dict):
        if not 'Element' in class_dict and bases <> (object,):
            # Take left-most superclass
            super_cls = bases[0]
            if not 'Element' in super_cls.__dict__:
                logging.debug("Building %s, but no %s.Element!" %
                              (name, super_cls.__name__))
                return
            super_node = super_cls.__dict__['Element']

            class_dict['Element'] = type('Element', (super_node,), dict())
            # The above isn't enough all of the time.  Some day find out why.
            setattr(self, 'Element', class_dict['Element'])

        node_cls = class_dict['Element']
        n = node_cls.__name__ = '%s.%s' % (name, node_cls.__name__)
        type.__init__(self, name, bases, class_dict)


class Schema(object):
    __metaclass__ = MetaSchema

    def __init__(self, name, **kw):
        if not isinstance(name, (unicode, NoneType)):
            name = unicode(name, errors='strict')
        self.name = name
        self.label = kw.get('label', name)

        self.default = kw.get('default', None)

        self.validators = kw.get('validators', None)
        self.optional = kw.get('optional', False)

    def new(self, *args, **kw):
        return self.Element(self, *args, **kw)
    node = new

    class Element(object):
        flattenable = False

        def __init__(self, schema, parent=None, **kw):
            self.schema = schema
            self.parent = parent

            self.errors = []
            self.warnings = []

        ##  Hierarchy
        def _get_parent(self):
            return self._parent
        def _set_parent(self, parent):
            "Store a weakref to this node's parent."
            if parent is None:
                self._parent = None
            else:
                self._parent = weakref.proxy(parent)

        parent = property(_get_parent, _set_parent)

        name = property(lambda self: self.schema.name)
        label = property(lambda self: self.schema.label)

        @property
        def path(self):
            "A tuple of node names, starting at this node's topmost parent."
            p, node = [], self
            while node is not None:
                if node.name is not None:
                    p.append(node.name)
                node = node.parent
            return tuple(reversed(p))

        @property
        def root(self):
            node = self
            while node is not None:
                if node.parent is None:
                    break
                node = node.parent
            return node

        def fq_name(self, sep='_'):
            """
            Joins this node's path with sep and return the fully qualified,
            flattened name.
            """
            return sep.join(self.path)

        def el(self, path, sep=u'.'):
            search = self._parse_node_path(path, sep)
            if search is None:
                raise KeyError(u'No element at "%s".' % path)

            try:
                return self._el(search)
            except KeyError:
                raise KeyError(u'No element found at "%s"' % path)

        def _el(self, path):
            raise NotImplementedError()

        @classmethod
        def _parse_node_path(self, path, sep):
            if isinstance(path, basestring):
                steps = path.split(sep)
            elif isinstance(path, (list, tuple)) or hasattr('next', path):
                steps = path
            else:
                return None

            return [None if step in (u'""', u"''") else step for step in steps]


        ## Errors and warnings- any node can have them.
        def add_error(self, message):
            "Register an error message on this node, ignoring duplicates."
            if message not in self.errors:
                self.errors.append(message)

        def add_warning(self, message):
            "Register a wawrning message on this node, ignoring duplicates."
            if message not in self.warnings:
                self.warnings.append(message)


        ## Element value and wrangling
        def apply(self, func, data=None, depth_first=False):
            return [func(self, data)]

        def flatten(self, sep=u'_', value=lambda node: node.u):
            pairs = []
            def serialize(node, data):
                if node.flattenable:
                    data.append((node.fq_name(sep), value(node)))

            self.apply(serialize, pairs)
            return pairs

        def set(self, value):
            raise NotImplementedError()

        def set_flat(self, pairs, sep='_'):
            """
            Given a sequence of name/value tuples or a dict, build out a
            structured tree of value nodes.
            """
            if hasattr(pairs, 'items'):
                pairs = pairs.items()

            return self._set_flat(pairs, sep)

        def _set_flat(self, pairs, sep):
            raise NotImplementedError()

        def validate(self, state=None, recurse=True, validators=None):
            if not recurse:
                return self._validate(state, validators=validators)

            def collector(node, _):
                return node._validate(state=state, validators=None)

            return reduce(operator.and_, self.apply(collector, None), True)

        def _validate(self, state=None, validators=None):
            if validators is None:
                if not self.schema.validators:
                    return True
                validators = self.schema.validators

            if not isinstance(validators, (tuple, list)):
                validators = validators,

            valid = True
            for v in validators:
                valid &= v(self, state)
                if not valid:
                    return False

            return valid


class Scalar(Schema):

    def parse(self, node, value):
        """
        Given any value, try to coerce it into native format.
        Raises ParseError on failure.
        """
        raise NotImplementedError()

    def serialize(self, node, value):
        """
        Given any value, try to coerce it into a Unicode representation for
        this type.  No special effort is made to coerce values not of native
        or compatible type.  *Must* return a Unicode object, always.
        """
        return unicode(value)

    class Element(Schema.Element):
        flattenable = True

        def __init__(self, schema, **kw):
            super(Scalar.Element, self).__init__(schema, **kw)

            self._u = u''
            self._value = None

            if 'value' in kw:
                self.set(kw['value'])
            # This prevents sub-types from implementing special sauce
            # for default value of None, but it does make construction
            # faster.
            elif schema.default is not None:
                self.set(schema.default)

        ## String representation
        def _get_u(self):
            return self._u

        def _set_u(self, ustr):
            #if self.immutable:
            #    raise ValueError('Element is immutable')
            if ustr is None:
                self._u = u''
            elif not isinstance(ustr, unicode):
                raise ValueError(u"Value must be a unicode value, got %s" %
                                 repr(ustr))
            else:
                self._u = ustr

        u = lateproperty(_get_u, _set_u)

        @property
        def x(self):
            """Sugar: xml-escaped string value."""
            return xml.sax.saxutils.escape(self.u)

        # Sugar: xml-attribute-escaped string value.
        @property
        def xa(self):
            """Sugar: xml-attribute-escaped string value."""
            return xml.sax.saxutils.quoteattr(self.u)[1:-1]

        ## Native representation
        def _get_value(self):
            return self._value
        def _set_value(self, value):
            #if self.immutable:
            #    raise ValueError('Element is immutable')
            self._value = value
        value = lateproperty(_get_value, _set_value)

        def _el(self, path):
            if not path:
                return self
            raise KeyError()

        ## Multi-value Maintenance
        def set(self, value):
            try:
                value = self.value = self.parse(value)
            except exc.ParseError:
                pass

            if value is None:
                self.u = u''
            else:
                self.u = self.serialize(value)

        def parse(self, value):
            return self.schema.parse(self, value)

        def serialize(self, value):
            return self.schema.serialize(self, value)

        def _set_flat(self, pairs, sep):
            for key, value in pairs:
                if key == self.name:
                    self.set(value)
                    break

        def __eq__(self, other):
            """
            Overloaded comparison: when comparing nodes, compare name and
            value. When comparing non-nodes, coerce our value into something
            comparable.
            """
            if ((type(self) is type(other)) or isinstance(other, Scalar.Element)):
                if self.name == other.name:
                    if self.u == other.u:
                        if self.value == other.value:
                            return True
                return False
            elif isinstance(other, Ref.Element):
                if self.path == other.schema.path:
                    if self.u == other.u:
                        if self.value == other.value:
                            return True
                return False
            elif isinstance(other, Schema.Element):
                return False
            else:
                if isinstance(other, basestring):
                    if isinstance(self.value, basestring):
                        return self.value == other
                    else:
                        return self.u == other
                else:
                    return self.value == other

        #def __hash__(self):
        #    if not self.immutable:
        #        raise TypeError('Element is unhashable')
        #    return hash(self.value)

        def __nonzero__(self):
            return True if self.u and self.value else False

        def _validate(self, state=None, validators=None):
            if self.schema.optional and self.u == u'':
                return True
            else:
                return super(Scalar.Element, self)._validate(state, validators)

        ## Debugging
        def __unicode__(self):
            return u'%s=%s' % (self.name, self.u)

        def __str__(self):
            return '%s=%s' % (self.name.encode('unicode-escape'),
                              self.u.encode('unicode-escape'))

        def __repr__(self):
            return u"%s(%s, value=%s)" % (type(self).__name__,
                                           repr(self.name), repr(self.value))

class Container(Schema):
    pass

class Ref(Scalar):
    flattenable = False

    def __init__(self, name, path, writable='ignore', sep='.', **kw):
        super(Ref, self).__init__(name, **kw)

        self.path = self.Element._parse_node_path(path, sep)
        assert self.path is not None

        self.writable = writable

    def parse(self, node, value):
        return node.target.schema.parse(node, value)

    def serialize(self, node, value):
        return node.target.schema.serialize(node, value)

    class Element(Scalar.Element):
        @lazyproperty
        def target(self):
            return self.root.el(self.schema.path)

        def _get_u(self):
            return self.target._get_u()

        def _set_u(self, ustr):
            if self.schema.writable == 'ignore':
                return
            elif self.schema.writable:
                self.target._set_u(ustr)
            else:
                raise ValueError(u'Ref "%s" is not writable.' % self.name)

        def _get_value(self):
            return self.target._get_value()

        def _set_value(self, value):
            if self.schema.writable == 'ignore':
                return
            elif self.schema.writable:
                self.target._set_value(value)
            else:
                raise ValueError(u'Ref "%s" is not writable.' % self.name)

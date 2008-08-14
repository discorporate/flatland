import datetime
import logging
import operator
import re
import weakref
import xml.sax.saxutils
from collections import defaultdict
from types import NoneType

from util import lateproperty, lazyproperty, GetitemGetattrProxy

__all__ = ('Scalar', 'String',
           'Integer', 'Long', 'Float',
           'Boolean',
           'Date', 'Time',
           'Ref',
           'List', 'Dict', 'Form',
           'Array')

class ParseError(Exception):
    pass


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

        def _get_path(self):
            "A tuple of node names, starting at this node's topmost parent."
            p, node = [], self
            while node is not None:
                if node.name is not None:
                    p.append(node.name)
                node = node.parent
            return tuple(reversed(p))

        path = property(_get_path)

        def _get_root(self):
            node = self
            while node is not None:
                if node.parent is None:
                    break
                node = node.parent
            return node
        root = property(_get_root)

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
                if (isinstance(node, Scalar.Element) and
                    not isinstance(node, (Compound.Element, Ref.Element))):
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

        # Sugar: xml-escaped string value.
        x = property(lambda self: xml.sax.saxutils.escape(self.u))

        # Sugar: xml-attribute-escaped string value.
        xa = property(lambda self: xml.sax.saxutils.quoteattr(self.u)[1:-1])

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
            except ParseError:
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


class String(Scalar):
    def __init__(self, name, strip=True, **kw):
        super(String, self).__init__(name, **kw)
        self.strip = strip

    def parse(self, node, value):
        if value is None:
            return None
        elif self.strip:
            return unicode(value).strip()
        else:
            return unicode(value)

    def serialize(self, node, value):
        if value is None:
            return u''
        elif self.strip:
            return unicode(value).strip()
        else:
            return unicode(value)


class Number(Scalar):
    type_ = None
    format = u'%s'

    def __init__(self, name, signed=True, format=None, **kw):
        super(Number, self).__init__(name, **kw)
        self.signed = signed
        if format is not None:
            assert isinstance(format, unicode)
            self.format = format

    def parse(self, node, value):
        if value is None:
            return None
        try:
            native = self.type_(value)
            if not self.signed:
                if native < 0:
                    return None
            return native
        except ValueError:
            raise ParseError()

    def serialize(self, node, value):
        if type(value) is self.type_:
            return self.format % value
        return unicode(value)

class Integer(Number):
    type_ = int
    format = u'%i'

class Long(Number):
    type_ = long
    format = u'%i'

class Float(Number):
    type_ = float
    format = u'%f'

class Boolean(Scalar):
    def __init__(self, name, true=u'1', false=u'', **kw):
        super(Scalar, self).__init__(name, **kw)
        assert isinstance(true, unicode)
        assert isinstance(false, unicode)

        self.true = true
        self.false = false

    def parse(self, node, value):
        if value in (self.true, u'on', u'true', u'True', u'1'):
            return True
        if value in (self.false, u'off', u'false', u'False', u'0'):
            return False

        return False

    def serialize(self, node, value):
        if value:
            return self.true
        else:
            return self.false

class Temporal(Scalar):
    type_ = None
    regex = None
    format = None
    used = None

    def __init__(self, name, **kw):
        super(Temporal, self).__init__(name, **kw)

        if 'type_' in kw:
            self.type_ = kw['type_']
        if 'regex' in kw:
            self.regex = kw['regex']
        if 'format' in kw:
            assert isinstance(kw['format'], unicode)
            self.format = kw['format']
        if 'used' in kw:
            self.used = kw['used']

    def parse(self, node, value):
        if isinstance(value, self.type_):
            return value
        elif isinstance(value, basestring):
            match = self.regex.match(value)
            if not match:
                raise ParseError()
            try:
                args = [int(match.group(f)) for f in self.used]
                return self.type_(*args)
            except TypeError:
                raise ParseError()
        else:
            raise ParseError()

    def serialize(self, node, value):
        if isinstance(value, self.type_):
            return self.format % GetitemGetattrProxy(value)
        else:
            return unicode(value)


class DateTime(Temporal):
    type_ = datetime.datetime
    regex = re.compile(ur'^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2}) '
                       ur'(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})$')
    format = (u'%(year)04i-%(month)02i-%(day)02i '
              u'%(hour)02i:%(minute)02i:%(second)02i')
    used = ('year', 'month', 'day', 'hour', 'minute', 'second')


class Date(Temporal):
    type_ = datetime.date
    regex = re.compile(ur'^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})$')
    format = u'%(year)04i-%(month)02i-%(day)02i'
    used = ('year', 'month', 'day')


class Time(Temporal):
    type_ = datetime.time
    regex = re.compile(ur'^(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})$')
    format = u'%(hour)02i:%(minute)02i:%(second)02i'
    used = ('hour', 'minute', 'second')


class Ref(Scalar):
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

##############################################################################

class Container(Schema):
    def __init__(self, name, *args, **kw):
        super(Container, self).__init__(name, **kw)
        self.spec = None


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


class Array(Sequence, Scalar):
    def __init__(self, array_of, **kw):
        assert isinstance(array_of, Scalar)
        super(Array, self).__init__(array_of.name, **kw)

        self.spec = array_of
        self.prune_empty = kw.get('prune_empty', True)

    class Element(Sequence.Element, Scalar.Element):
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


class Form(Dict):
    """
    Schemas are the most common top-level mapping.  They behave like
    Dicts, but do not need to be named.  FIXME: Also magic schema holder.
    """
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



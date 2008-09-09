from __future__ import absolute_import

import datetime
import re
import xml.sax.saxutils

from .base import Schema
from .node import Node
from flatland.util import lateproperty, lazyproperty, GetitemGetattrProxy
import flatland.exc as exc


__all__ = ('String', 'Integer', 'Long', 'Float', 'Boolean', 'Date', 'Time',
           'Ref')


class _ScalarNode(Node):
    flattenable = True

    def __init__(self, schema, **kw):
        Node.__init__(self, schema, **kw)

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
        if ((type(self) is type(other)) or isinstance(other, _ScalarNode)):
            if self.name == other.name:
                if self.u == other.u:
                    if self.value == other.value:
                        return True
            return False
        elif isinstance(other, _RefNode):
            if self.path == other.schema.path:
                if self.u == other.u:
                    if self.value == other.value:
                        return True
            return False
        elif isinstance(other, Node):
            return False
        else:
            if isinstance(other, basestring):
                if isinstance(self.value, basestring):
                    return self.value == other
                else:
                    return self.u == other
            else:
                return self.value == other

    def __nonzero__(self):
        return True if self.u and self.value else False

    def _validate(self, state=None, validators=None):
        if self.schema.optional and self.u == u'':
            return True
        else:
            return super(_ScalarNode, self)._validate(state, validators)

    ## Debugging
    def __unicode__(self):
        return u'%s=%s' % (self.name, self.u)

    def __str__(self):
        return '%s=%s' % (self.name.encode('unicode-escape'),
                          self.u.encode('unicode-escape'))

    def __repr__(self):
        return u"%s(%s, value=%s)" % (type(self).__name__,
                                       repr(self.name), repr(self.value))


class Scalar(Schema):
    node_type = _ScalarNode

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
            raise exc.ParseError()

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
                raise exc.ParseError()
            try:
                args = [int(match.group(f)) for f in self.used]
                return self.type_(*args)
            except TypeError:
                raise exc.ParseError()
        else:
            raise exc.ParseError()

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


class _RefNode(Node):
    flattenable = False

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

class Ref(Scalar):
    node_type = _RefNode

    def __init__(self, name, path, writable='ignore', sep='.', **kw):
        super(Ref, self).__init__(name, **kw)

        self.path = self.node_type._parse_node_path(path, sep)
        assert self.path is not None

        self.writable = writable

    def parse(self, node, value):
        return node.target.schema.parse(node, value)

    def serialize(self, node, value):
        return node.target.schema.serialize(node, value)

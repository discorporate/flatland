import datetime
import re

from flatland.schema.base import Scalar
from flatland.util import GetitemGetattrProxy
import flatland.exc as exc


__all__ = 'String', 'Integer', 'Long', 'Float', 'Boolean', 'Date', 'Time'



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



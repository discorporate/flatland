import operator
from flatland.exc import AdaptationError
from . import scalars, containers


class CompoundElement(containers.Dict, scalars.Scalar):

    def u(self):
        uni, value = self.schema.compose(self)
        return uni

    def set_u(self, value):
        self.schema.explode(self, value)

    u = property(u, set_u)
    del set_u

    def value(self):
        uni, value = self.schema.compose(self)
        return value

    def set_value(self, value):
        self.schema.explode(self, value)

    value = property(value, set_value)
    del set_value

    def set(self, value):
        self.schema.explode(self, value)

    def _set_flat(self, pairs, sep):
        containers.DictElement._set_flat(self, pairs, sep)

    def __repr__(self):
        try:
            return scalars.Scalar.__repr__(self)
        except Exception, exc:
            return '<%s %r; value raised %s>' % (
                type(self.schema).__name__, self.name, type(exc).__name__)

    @property
    def is_empty(self):
        """True if all subfields are empty."""
        return reduce(operator.and_, (c.is_empty for c in self.children))


class Compound(containers.Mapping, scalars.Scalar):
    """A mapping container that acts as a scalar proxy for its children.

    Compound fields are dictionary-like fields that can assemble a
    :attr:`.u` and :attr:`.value` from their children, and can apply a
    structures value passed to a :meth:`.set` to its children.

    A simple example is a logical calendar date field composed of 3
    separate component fields, year, month and day.  The Compound can
    wrap the 3 parts up into a single field that handles
    :class:`datetime.date` values.

    :class:`Compound` is an abstract class.  Subclasses must implement
    :meth:`compose` and :meth:`explode`.

    Composites run validation after their children.

    """

    element_type = CompoundElement

    def __init__(self, name, *fields, **kw):
        super(Compound, self).__init__(name, **kw)

        if any(not field.name for field in fields):
            raise TypeError("Child fields of %s %r must be named." %
                            type(self).__name__, name)

        self.fields = dict((field.name, field) for field in fields)

    def compose(self, element):
        """Return a unicode, native tuple built from children's state.

        :param element: a :class:`CompoundElement`, a dict-like
            element type.
        :returns: a 2-tuple of unicode representation, native value.
           These correspond to the :meth:`Scalar.serialize_element`
           and :meth:`Scalar.adapt_element` methods of :class:`Scalar`
           objects.

        For example, a compound date field may return a '-' delimited
        string of year, month and day digits and a
        :class:`datetime.date`.

        """
        raise NotImplementedError()

    def explode(self, element, value):
        """Given a compound value, assign values to children.

        :param element: a :class:`CompoundElement`, a dict-like
            element type.
        :param value: a value to be adapted and exploded

        For example, a compound date field may read attributes from a
        :class:`datetime.date` value and :meth:`.set()` them on child
        fields.

        The decision to perform type checking on *value* is completely
        up to you and you may find you want different rules for
        different compound types.

        """
        raise NotImplementedError()

    def serialize(self, element, value):
        raise TypeError("Not implemented for Compound types.")


class DateYYYYMMDD(Compound, scalars.Date):
    def __init__(self, name, *fields, **kw):
        assert len(fields) <= 3
        fields = list(fields)
        optional = kw.get('optional', False)

        if len(fields) == 0:
            fields.append(scalars.Integer('year', format=u'%04i',
                                          optional=optional))
        if len(fields) == 1:
            fields.append(scalars.Integer('month', format=u'%02i',
                                          optional=optional))
        if len(fields) == 2:
            fields.append(scalars.Integer('day', format=u'%02i',
                                          optional=optional))
        super(DateYYYYMMDD, self).__init__(name, *fields, **kw)
        self.ordered_fields = fields

    def compose(self, element):
        try:
            data = dict( [(label, element[child_schema.name].value)
                          for label, child_schema
                          in zip(self.used, self.ordered_fields)] )
            as_str = self.format % data
            value = scalars.Date.adapt(self, element, as_str)
            return as_str, value
        except (AdaptationError, TypeError):
            return u'', None

    def explode(self, element, value):
        try:
            value = scalars.Date.adapt(self, element, value)
            for attrib, child_schema in zip(self.used, self.ordered_fields):
                element[child_schema.name].set(getattr(value, attrib))
        except (AdaptationError, TypeError):
            for child_schema in self.ordered_fields:
                element[child_schema.name].set(None)

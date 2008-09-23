from __future__ import absolute_import

from . import scalars, containers
from flatland import exc


class _CompoundElement(scalars._ScalarElement, containers._DictElement):
    def _get_u(self):
        u, value = self.compose()
        return u

    def _set_u(self, value):
        self.explode(value)

    u = property(_get_u, _set_u)

    def _get_value(self):
        u, value = self.schema.compose(self)
        return value

    def _set_value(self, value):
        self.schema.explode(value)

    value = property(_get_value, _set_value)

    def compose(self):
        return self.schema.compose(self)

    def explode(self, value):
        return self.schema.explode(self, value)

    def set(self, value):
        self.schema.explode(self, value)

    def _el(self, path):
        if path:
            return self[path[0]]._el(path[1:])
        elif not path:
            return self
        raise KeyError()

    def _set_flat(self, pairs, sep):
        containers._DictElement._set_flat(self, pairs, sep)


class Compound(scalars.Scalar, containers.Mapping):
    element_type = _CompoundElement

    def __init__(self, name, *specs, **kw):
        super(Compound, self).__init__(name, **kw)

        self.fields = {}
        for spec in specs:
            if hasattr(spec, 'name') and spec.name:
                self.fields[spec.name] = spec
        self.specs = specs

    def compose(self, element):
        raise NotImplementedError()

    def explode(self, element, value):
        raise NotImplementedError()


class DateYYYYMMDD(Compound, scalars.Date):
    def __init__(self, name, *specs, **kw):
        assert len(specs) <= 3
        specs = list(specs)

        if len(specs) == 0:
            specs.append(scalars.Integer('year', format=u'%04i'))
        if len(specs) == 1:
            specs.append(scalars.Integer('month', format=u'%02i'))
        if len(specs) == 2:
            specs.append(scalars.Integer('day', format=u'%02i'))

        super(DateYYYYMMDD, self).__init__(name, *specs, **kw)

    def compose(self, element):
        try:
            data = dict( [(label, element[spec.name].value)
                          for label, spec
                          in zip(self.used, self.specs)] )
            as_str = self.format % data
            value = scalars.Date.adapt(self, element, as_str)
            return as_str, value
        except (exc.AdaptationError, TypeError):
            return None, None

    def explode(self, element, value):
        try:
            value = scalars.Date.adapt(self, element, value)
            for attrib, spec in zip(self.used, self.specs):
                element[spec.name].set(getattr(value, attrib))
        except (exc.AdaptationError, TypeError):
            for spec in self.specs:
                element[spec.name].set(None)

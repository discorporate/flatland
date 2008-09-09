from __future__ import absolute_import

from . import container, scalar
from flatland import exc


class _CompoundNode(scalar._ScalarNode, container._DictNode):
    def _get_u(self):
        u, value = self.compose()
        return u

    def _set_u(self, value):
        self.explode(value)

    def _get_value(self):
        u, value = self.compose()
        return value

    def _set_value(self, value):
        self.explode(value)

    def compose(self):
        return self.schema.compose(self)

    def explode(self, value):
        return self.schema.explode(self, value)

    def set(self, value):
        self.explode(value)

    def _el(self, path):
        if path:
            return self[path[0]]._el(path[1:])
        elif not path:
            return self
        raise KeyError()

    def _set_flat(self, pairs, sep):
        container._DictNode._set_flat(self, pairs, sep)


class Compound(scalar.Scalar, container.Mapping):
    node_type = _CompoundNode

    def __init__(self, name, *specs, **kw):
        super(Compound, self).__init__(name, **kw)

        self.fields = {}
        for spec in specs:
            if hasattr(spec, 'name') and spec.name:
                self.fields[spec.name] = spec
        self.specs = specs

    def compose(self, node):
        raise NotImplementedError()

    def explode(self, node, value):
        raise NotImplementedError()


class DateYYYYMMDD(Compound, scalar.Date):
    def __init__(self, name, *specs, **kw):
        assert len(specs) <= 3
        specs = list(specs)

        if len(specs) == 0:
            specs.append(scalar.Integer('year', format=u'%04i'))
        if len(specs) == 1:
            specs.append(scalar.Integer('month', format=u'%02i'))
        if len(specs) == 2:
            specs.append(scalar.Integer('day', format=u'%02i'))

        super(DateYYYYMMDD, self).__init__(name, *specs, **kw)

    def compose(self, node):
        try:
            data = dict( [(label, node[spec.name].value)
                          for label, spec
                          in zip(self.used, self.specs)] )
            as_str = self.format % data
            value = scalar.Date.parse(self, node, as_str)
            return as_str, value
        except (exc.ParseError, TypeError):
            return None, None

    def explode(self, node, value):
        try:
            value = scalar.Date.parse(self, node, value)
            for attrib, spec in zip(self.used, self.specs):
                node[spec.name].set(getattr(value, attrib))
        except (exc.ParseError, TypeError):
            for spec in self.specs:
                node[spec.name].set(None)

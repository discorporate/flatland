import schema


class Compound(schema.Scalar, schema.Mapping):
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

    class Element(schema.Scalar.Element, schema.Dict.Element):
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
            Dict.Element._set_flat(self, pairs, sep)


class DateYYYYMMDD(Compound, schema.Date):
    def __init__(self, name, *specs, **kw):
        assert len(specs) <= 3
        specs = list(specs)

        if len(specs) == 0:
            specs.append(schema.Integer('year', format=u'%04i'))
        if len(specs) == 1:
            specs.append(schema.Integer('month', format=u'%02i'))
        if len(specs) == 2:
            specs.append(schema.Integer('day', format=u'%02i'))

        super(DateYYYYMMDD, self).__init__(name, *specs, **kw)

    def compose(self, node):
        try:
            data = dict( [(label, node[spec.name].value)
                          for label, spec
                          in zip(self.used, self.specs)] )
            as_str = self.format % data
            value = schema.Date.parse(self, node, as_str)
            return as_str, value
        except (schema.ParseError, TypeError):
            return None, None

    def explode(self, node, value):
        try:
            value = schema.Date.parse(self, node, value)
            for attrib, spec in zip(self.used, self.specs):
                node[spec.name].set(getattr(value, attrib))
        except (schema.ParseError, TypeError):
            for spec in self.specs:
                node[spec.name].set(None)

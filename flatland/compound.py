import schema
import datetime
import re

class DateYYYYMMDD(schema.Compound, schema.Date):
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

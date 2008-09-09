from .node import Node


NoneType = type(None)

class Schema(object):
    node_type = Node

    def __init__(self, name, **kw):
        if not isinstance(name, (unicode, NoneType)):
            name = unicode(name, errors='strict')

        self.name = name
        self.label = kw.get('label', name)
        self.default = kw.get('default', None)

        validators = kw.get('validators', None)
        if validators is not None:
            self.validators = validators
        elif not hasattr(self, 'validators'):
            self.validators = []
        self.optional = kw.get('optional', False)

    def new(self, *args, **kw):
        return self.node_type(self, *args, **kw)
    node = new






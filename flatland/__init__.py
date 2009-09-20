import sys
import types


class deferred_module(types.ModuleType):
    """A module whose __all__ members are loaded on first access."""

    @classmethod
    def shadow(cls, module_name, deferred, **attributes):
        """Replace *module_name* in ``sys.modules`` with a deferred clone."""
        module = sys.modules[module_name]
        sys.modules[module_name] = cls(module, deferred, **attributes)

    def __init__(self, module, deferred, **attributes):
        types.ModuleType.__init__(self, module.__name__, module.__doc__ or None)
        self.__dict__.update(attributes)
        self.__shadowing = module
        self.__all__ = []
        self.__pushed_up = {}
        self.__file__ = module.__file__
        self.__path__ = module.__path__

        for submodule, pushed_up in deferred.iteritems():
            self.__all__.append(submodule)
            if pushed_up:
                for member in pushed_up:
                    self.__pushed_up[member] = submodule
                self.__all__.extend(pushed_up)

    def __getattr__(self, key):
        if key in self.__pushed_up:
            owner = self.__pushed_up[key]
            value = getattr(getattr(self, owner), key)
            setattr(self, key, value)
            if 'sphinx' in sys.modules and isinstance(value, type):
                value.__module__ = self.__name__
            return value
        elif key in self.__all__:
            module = __import__(
                self.__name__ + '.' + key, None, None, [self.__name__])
            setattr(self, key, module)
            return module
        else:
            try:
                return types.ModuleType.__getattribute__(self, key)
            except AttributeError:
                raise AttributeError(
                    'module %r has no attribute %r' % (self.__name__, key))


deferred_module.shadow('flatland',
                       { 'exc': (),
                         'schema': ('Array',
                                    'Boolean',
                                    'Compound',
                                    'Constrained',
                                    'Date',
                                    'DateTime',
                                    'DateYYYYMMDD',
                                    'Dict',
                                    'Enum',
                                    'FieldSchema',
                                    'Float',
                                    'Form',
                                    'Integer',
                                    'List',
                                    'Long',
                                    'MultiValue',
                                    'Ref',
                                    'Skip',
                                    'SkipAll',
                                    'SkipAllFalse',
                                    'String',
                                    'Time',
                                    ),
                         'signals': (),
                         'util': (),
                         'valid': (),
                         })


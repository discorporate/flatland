import re

# From ASPN Cookbook, modified?  Lost reference.
class lateproperty(property):
    __doc__ = property.__dict__['__doc__'] # see bug #576990

    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        if fget:
            fget = lambda s, n=fget.__name__: getattr(s, n)()
        if fset:
            fset = lambda s, v, n=fset.__name__: getattr(s, n)(v)
        if fdel:
            fdel = lambda s, n=fdel.__name__: getattr(s, n)()
        property.__init__(self, fget, fset, fdel, doc)

# From ASPN Cookbook (#36302)
class lazyproperty(object):
    def __init__(self, deferred):
        self._deferred = deferred
    def __get__(self, obj, _=None):
        if obj is None:
            return self
        value = self._deferred(obj)
        setattr(obj, self._deferred.func_name, value)
        return value

class GetitemGetattrProxy(object):
    __slots__ = ['target']
    def __init__(self, target):
        self.target = target

    def __getitem__(self, key):
        if hasattr(self.target, key):
            return getattr(self.target, key)
        raise KeyError(u'No key "%s"' % key)

    def has_key(self, key):
        return hasattr(self.target, key)
    __contains__ = has_key

class GetitemGetattrMultiProxy(object):
    __slots__ = ['targets']
    def __init__(self, *targets):
        assert targets
        self.targets = targets

    def __getitem__(self, key):
        for t in self.targets:
            if hasattr(t, key):
                return getattr(t, key)
        raise KeyError(u'No key "%s"' % key)

    def has_key(self, key):
        for t in self.targets:
            if hasattr(t, key):
                return True
        return False
    __contains__ = has_key

def re_ucompile(pattern, flags=0):
    return re.compile(pattern, flags | re.UNICODE)

def luhn10(number):
    assert isinstance(number, (int, long))

    sum = 0
    while number:
        r = number % 100
        number //= 100
        z = r % 10
        r = r // 10 * 2
        sum += r // 10 + r % 10 + z

    return 0 == sum % 10

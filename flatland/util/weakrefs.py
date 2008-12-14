import weakref
from . import _saferef


WeakTypes = weakref.ref, _saferef.BoundMethodWeakref

class annotatable_weakref(weakref.ref):
    pass


def reference(object, callback=None, **annotations):
    if callable(object):
        weak = callable_reference(object, callback)
    else:
        weak = annotatable_weakref(object, callback)
    for key, value in annotations.items():
        setattr(weak, key, value)
    return weak

def callable_reference(object, callback=None):
    if hasattr(object, 'im_self') and object.im_self is not None:
        return _saferef.BoundMethodWeakref(target=object, onDelete=callback)
    return annotatable_weakref(object, callback)


def ref_any(object, callback=None):
    """Try to weakref.ref() anything."""
    if callable(object):
        return weakcallableref(object, callback)
    else:
        return weakref.ref(object. callback)

def weakcallableref(callable, callback=None):
    """Return a weak reference to *callable*."""
    return _saferef.safeRef(callable, callback)

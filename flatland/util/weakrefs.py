"""Weak reference helpers."""
import weakref
from . import _saferef


WeakTypes = weakref.ref, _saferef.BoundMethodWeakref

class annotatable_weakref(weakref.ref):
    """A weakref.ref that supports custom instance attributes."""

    def __init__(self, object, callback=None, **kw):
        """Build a ref, optionally assigning arbitrary **kw as attributes."""
        weakref.ref.__init__(self, object, callback)
        for key, value in kw.iteritems():
            setattr(self, key, value)


def reference(object, callback=None, **annotations):
    """Return an annotated weak ref."""
    if callable(object):
        weak = callable_reference(object, callback)
    else:
        weak = annotatable_weakref(object, callback)
    for key, value in annotations.items():
        setattr(weak, key, value)
    return weak

def callable_reference(object, callback=None):
    """Return an annotated weak ref, supporting bound instance methods."""
    if hasattr(object, 'im_self') and object.im_self is not None:
        return _saferef.BoundMethodWeakref(target=object, onDelete=callback)
    return annotatable_weakref(object, callback)

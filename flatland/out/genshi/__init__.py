"""

"""
from __future__ import absolute_import
from . import elements
from . import taglistener
from . import filter
from . filter import flatland_filter


___all__ = 'flatland_filter'

def install_element_mixin():
    from flatland.schema.base import Element
    if elements.GenshiAccessMixin in Element.__bases__:
        return
    assert Element.__bases__ != (object,)
    Element.__bases__ += (elements.GenshiAccessMixin,)

def uninstall_element_mixin():
    from flatland.schema.base import Element
    if elements.GenshiAccessMixin not in Element.__bases__:
        return
    bases = list(Element.__bases__)
    bases.remove(elements.GenshiAccessMixin)
    Element.__bases__ = tuple(bases)

install_element_mixin()




from flatland.out.genshi.filter import flatland_filter

___all__ = ['flatland_filter', 'setup']


def setup(template, use_version=None):
    """Register the flatland directives with a template.

    :param template: a `Template` instance
    """
    if use_version is None:
        use_version = 6 if hasattr(template, 'add_directives') else 5

    if use_version == 6:
        from flatland.out.genshi_06 import setup
        setup(template)
    else:
        install_element_mixin()
        template.filters.append(flatland_filter)


def install_element_mixin():
    from flatland.out.genshi.elements import GenshiAccessMixin
    from flatland.schema.base import Element
    if GenshiAccessMixin in Element.__bases__:
        return
    assert Element.__bases__ != (object,)
    Element.__bases__ += (GenshiAccessMixin,)


def uninstall_element_mixin():
    from flatland.out.genshi.elements import GenshiAccessMixin
    from flatland.schema.base import Element
    if GenshiAccessMixin not in Element.__bases__:
        return
    bases = list(Element.__bases__)
    bases.remove(GenshiAccessMixin)
    Element.__bases__ = tuple(bases)

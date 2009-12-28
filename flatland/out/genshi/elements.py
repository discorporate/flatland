from flatland.schema import base


# FIXME:
# unicode(wrapped) should probably eval to either the fq_name or the
# result of a configured formatting function.  clean up the set_prefix
# bandaid and make it do this.
#
# FIXME: continue to simplify the wrapper. this is all hella bogus :(

class GenshiAccessMixin(object):
    def set_prefix(self, prefix):
        self._genshi_prefix = prefix

    @property
    def bind(self):
        return WrappedElement(self)

    @property
    def binds(self):
        return dict((child.name, WrappedElement(child))
                    for child in self.children)

def get_prefix(element):
    if hasattr(element, '_genshi_prefix'):
        return element._genshi_prefix
    else:
        for element in element.parents:
            if hasattr(element, '_genshi_prefix'):
                return element._genshi_prefix
        return None


class WrappedElement(unicode):
    """Wrap an Element into something Genshi expressions can use.

    Genshi AST transformations don't play well with rich objects like
    Elements.  Anything iterable will iterate on insert into the
    template, even if it defines a __unicode__.  Normal objects
    defining __getitem__ or __getattr__ or even __getattribute__
    confuse Genshi's dotted expression adapter.

    ``unicode``-derived objects are immune from these problems.  These
    wrappers will str() as Genshi-evalable string.

    """
    def __new__(cls, element):
        return unicode.__new__(cls, cls._format(element))

    def __init__(self, element):
        self.element = element

    @staticmethod
    def _format(element):
        prefix = get_prefix(element)
        path = element.fq_name()
        if not prefix:
            root = element.root
            if root.name is None:
                prefix = u'form'
            else:
                prefix = u'forms.%s' % (root.name,)
        return u"%s.el(%s)" % (prefix, repr(path).decode('raw_unicode_escape'))

    def __getitem__(self, key):
        if isinstance(key, str):
            try:
                key = key.decode('ascii')
            except UnicodeError:
                raise KeyError(key)
        item = self.element._index(key)
        if isinstance(item, base.Element):
            return WrappedElement(item)
        else:
            return item

    def __getattr__(self, attribute):
        return getattr(self.element, attribute)

    def __unicode__(self):
        return self._format(self.element)

    def __iter__(self):
        return (WrappedElement(child) if isinstance(child, base.Element)
                                      else child
                for child in self.element.children)

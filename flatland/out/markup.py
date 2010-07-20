from collections import defaultdict

from flatland.out.generic import Context, transform
from flatland.out.util import parse_trool


_default_options = {u'ordered_attributes': True}
_static_attribute_order = [u'type', u'name', u'value']


class Generator(Context):

    def __init__(self, markup='xhtml', **options):
        Context.__init__(self)
        if markup == 'html':
            self.xml = False
        elif markup in ('xhtml', 'xml'):
            self.xml = True
        else:
            raise TypeError("Unknown markup type %r" % markup)
        self._tags = defaultdict(list)
        self._frames[-1].update(_default_options)
        self.push()
        self.update(options)

    def begin(self, **settings):
        self.push(**settings)
        return self['markup_wrapper'](u'')

    def end(self):
        if len(self._frames) == 2:
            raise RuntimeError("end() without matching begin()")
        self.pop()
        return self['markup_wrapper'](u'')

    def set(self, **settings):
        for key, value in settings.items():
            if key not in self:
                raise TypeError(
                    "%r is not a valid argument." % key)
            if key.startswith('auto_'):
                value = parse_trool(value)
            self[key] = value
        return self['markup_wrapper'](u'')

    @property
    def form(self):
        return self._tag(u'form', False, True)

    @property
    def input(self):
        return self._tag(u'input', True)

    @property
    def textarea(self):
        return self._tag(u'textarea', False, True)

    @property
    def button(self):
        return self._tag(u'button')

    @property
    def select(self):
        return self._tag(u'select', False, True)

    @property
    def option(self):
        return self._tag(u'option', False, True)

    @property
    def label(self):
        return self._tag(u'label')

    def tag(self, tagname, bind=None, **kw):
        if isinstance(tagname, str):  # pragma: nocover
            tagname = unicode(tagname)
        tagname = tagname.lower()
        if bind is None and not kw:
            return self._tag(tagname)
        else:
            return self._tag(tagname)(bind, **kw)

    def _tag(self, tagname, empty_in_html=False, always_paired=False):
        if self._tags[tagname]:
            return self._tags[tagname][-1]
        return Tag(tagname, self, empty_in_html, always_paired)


class Tag(object):
    __slots__ = ('tagname', 'contents', '_context',
                 '_html_dangle', '_always_paired')

    def __init__(self, tagname, context, dangle, paired):
        self.tagname = tagname
        self._context = context
        self._html_dangle = dangle
        self._always_paired = paired
        self.contents = None

    def open(self, bind=None, **attributes):
        if self not in self._context._tags[self.tagname]:
            self._context._tags[self.tagname].append(self)
        return self._markup(self._open(bind, attributes) + u'>')

    def close(self):
        try:
            self._context._tags[self.tagname].remove(self)
        except ValueError:
            pass
        return self._markup(self._close())

    def _open(self, bind, kwargs):
        """Return a '<partial' opener tag with no terminator."""
        contents = kwargs.pop('contents', None)
        attributes = _unicode_keyed(kwargs)
        tagname = self.tagname
        new_contents = transform(
            tagname, attributes, contents, self._context, bind)

        if not new_contents:
            new_contents = u''
        elif hasattr(new_contents, '__html__'):
            new_contents = new_contents.__html__()
        self.contents = self._markup(new_contents)

        if self._context['ordered_attributes']:
            pairs = sorted(attributes.items(), key=_attribute_sort_key)
        else:
            pairs = attributes.iteritems()
        guts = u' '.join(u'%s="%s"' % (k, _attribute_escape(v))
                         for k, v in pairs)
        if guts:
            return u'<' + tagname + u' ' + guts
        else:
            return u'<' + tagname

    def _close(self):
        return u'</' + self.tagname + u'>'

    def _markup(self, string):
        return self._context['markup_wrapper'](string)

    def __call__(self, bind=None, **attributes):
        header = self._open(bind, attributes)
        if not self.contents:
            if not self._always_paired:
                if self._context.xml:
                    return self._markup(header + u' />')
                elif self._html_dangle:
                    return self._markup(header + u'>')
        return self._markup(header + u'>' + self.contents + self._close())

    def __html__(self):
        return self()


def _attribute_escape(string):
    if not string:
        return u''
    elif hasattr(string, '__html__'):
        return string.__html__()
    else:
        return string. \
               replace(u'&', u'&amp;'). \
               replace(u'<', u'&lt;'). \
               replace(u'>', u'&gt;'). \
               replace(u'"', u'&quot;')


def _unicode_keyed(bytestring_keyed):
    rekeyed = {}
    for key, value in bytestring_keyed.items():
        as_unicode = key.rstrip('_').decode('ascii')
        rekeyed[as_unicode] = value
    return rekeyed


def _attribute_sort_key(item):
    try:
        return (0, _static_attribute_order.index(item[0]))
    except ValueError:
        return (1, item[0])

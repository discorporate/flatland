from collections import defaultdict

from flatland.out.generic import Context, transform, _unpack
from flatland.out.util import parse_trool

_default_settings = {"ordered_attributes": True}
_static_attribute_order = ["type", "name", "value"]

# HTML5 void elements that should never have separate closing tags.
# These are elements that cannot have content and should be:
# - self-closing in X(HT)ML, like <br />, or
# - dangling (no closing tag) in HTML5, like <br>
# If an element is not in this set, it should have a separate closing
# tag, like: <div>content</div>
VOID_ELEMENTS = frozenset(
    [
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    ]
)


class Generator(Context):
    """General XML/HTML tag generator"""

    def __init__(self, markup="xhtml", **settings):
        """Create a generator.

        Accepts any :ref:`markupsettings`, as well as the following:

        :param markup: tag output style: ``'xml'``, ``'xhtml'`` or ``'html'``

        :param ordered_attributes: if True (default), output markup attributes
          in a predictable order.  Useful for tests and generally a little
          more pleasant to read.

        """
        Context.__init__(self)
        if markup == "html":
            self.xml = False
        elif markup in ("xhtml", "xml"):
            self.xml = True
        else:
            raise TypeError("Unknown markup type %r" % markup)
        self._tags = defaultdict(list)
        self._frames[-1].update(_default_settings)
        self.push()
        self.update(settings)

    def begin(self, **settings):
        r"""Begin a new :ref:`markupsettings` context.

        Puts \*\*settings into effect until a matching :meth:`end` is called.
        Each setting specified will mask the current value, reverting when
        :meth:`end` is called.

        """
        self.push(**settings)
        return self["markup_wrapper"]("")

    def end(self):
        """End a :ref:`markupsettings` context.

        Restores the settings that were in effect before :meth:`begin`.

        """
        if len(self._frames) == 2:
            raise RuntimeError("end() without matching begin()")
        self.pop()
        return self["markup_wrapper"]("")

    def set(self, **settings):
        r"""Change the :ref:`markupsettings` in effect.

        Change the \*\*settings in the current scope.  Changes remain in
        effect until another :meth:`set` or a :meth:`end` ends the current
        scope.

        """

        for key, value in settings.items():
            if key not in self:
                raise TypeError("%r is not a valid argument." % key)
            if key.startswith("auto_"):
                value = parse_trool(value)
            self[key] = value
        return self["markup_wrapper"]("")

    @property
    def form(self):
        r"""Generate a ``<form/>`` tag.

        :param bind: optional, a flatland element.
        :param \*\*attributes: any desired XML/HTML attributes.
        :returns: a printable :class:`Tag`

        If provided with a bind, form tags can generate the *name* attribute.

        """
        return self._tag("form")

    @property
    def input(self):
        r"""Generate an ``<input/>`` tag.

        :param bind: optional, a flatland element.
        :param \*\*attributes: any desired XML/HTML attributes.
        :returns: a printable :class:`Tag`

        If provided with a bind, input tags can generate the *name*, *value*
        and *id* attributes.  Input tags support *tabindex* attributes.

        """
        return self._tag("input")

    @property
    def textarea(self):
        r"""Generate a ``<textarea/>`` tag.

        :param bind: optional, a flatland element.
        :param \*\*attributes: any desired XML/HTML attributes.
        :returns: a printable :class:`Tag`

        If provided with a bind, textarea tags can generate the *name* and
        *id* attributes.  If the bind has a value, it will be used as the tag
        body.  Textarea tags support *tabindex* attributes.  To provide an
        alternate tag body, either supply *contents* or use the
        :meth:`~Tag.open` and :meth:`~Tag.close` method of the returned tag.

        """
        return self._tag("textarea")

    @property
    def button(self):
        r"""Generate a ``<button/>`` tag.

        :param bind: optional, a flatland element.
        :param \*\*attributes: any desired XML/HTML attributes.
        :returns: a printable :class:`Tag`

        If provided with a bind, button tags can generate the *name*, *value*,
        and *id* attributes.  Button tags support *tabindex* attributes.

        """
        return self._tag("button")

    @property
    def select(self):
        r"""Generate a ``<select/>`` tag.

        :param bind: optional, a flatland element.
        :param \*\*attributes: any desired XML/HTML attributes.
        :returns: a printable :class:`Tag`

        If provided with a bind, select tags can generate the *name* and *id*
        attributes.  Select tags support *tabindex* attributes.

        """
        return self._tag("select")

    @property
    def option(self):
        r"""Generate an ``<option/>`` tag.

        :param bind: optional, a flatland element.
        :param \*\*attributes: any desired XML/HTML attributes.
        :returns: a printable :class:`Tag`

        If provided with a bind, option tags can generate the *value*
        attribute.  To provide tag body, either supply *contents* or use the
        :meth:`~Tag.open` and :meth:`~Tag.close` method of the returned tag::

           print(generator.option.open(style='bold'))
           print('<strong>contents</strong>')
           print(generator.option.close())

        """
        return self._tag("option")

    @property
    def label(self):
        r"""Generate a ``<label/>`` tag.

        :param bind: optional, a flatland element.
        :param \*\*attributes: any desired XML/HTML attributes.
        :returns: a printable :class:`Tag`

        If provided with a bind, label tags can generate the *for* attribute
        and fill in the tag body with the element's
        :attr:`~flatland.Element.label`, if present.

        """
        return self._tag("label")

    def tag(self, tagname, bind=None, **attributes):
        r"""Generate any tag.

        :param tagname: the name of the tag.
        :param bind: optional, a flatland element.
        :param \*\*attributes: any desired XML/HTML attributes.
        :returns: a printable :class:`Tag`

        The attribute rules appropriate for *tagname* will be applied.  For
        example, ``tag('input')`` is equivalent to ``input()``.

        """
        if isinstance(tagname, bytes):  # pragma: nocover
            tagname = str(tagname)
        tagname = tagname.lower()
        if bind is None and not attributes:
            return self._tag(tagname)
        else:
            return self._tag(tagname)(bind, **attributes)

    def _tag(self, tagname):
        if self._tags[tagname]:
            return self._tags[tagname][-1]
        return Tag(tagname, self)


class Tag:
    """A printable markup tag.

    Tags are generated by :class:`Generator` and are usually called
    immediately, returning a fully formed markup string::

      print(generator.textarea(contents="hello!"))

    For more fine-tuned control over your markup, you may instead choose to
    use the :meth:`open` and :meth:`close` methods of the tag::

      print(generator.textarea.open())
      print("hello!")
      print(generator.textarea.close())

    """

    __slots__ = ("tagname", "contents", "_context")

    def __init__(self, tagname, context):
        self.tagname = tagname
        self._context = context
        self.contents = None

    def open(self, bind=None, **attributes):
        r"""Return the opening half of the tag, e.g. ``<p>``.

        :param bind: optional, a flatland element.
        :param \*\*attributes: any desired tag attributes.

        """
        if self.tagname in VOID_ELEMENTS:
            raise ValueError(
                f"Cannot call open() on void element '<{self.tagname}>'. "
                f"Void elements must be generated as complete tags. "
                f"Use: gen.{self.tagname}(...) instead of gen.{self.tagname}.open(...)"
            )
        if self not in self._context._tags[self.tagname]:
            self._context._tags[self.tagname].append(self)
        return self._markup(self._open(bind, attributes) + ">")

    def close(self):
        """Return the closing half of the tag, e.g. ``</p>``."""
        if self.tagname in VOID_ELEMENTS:
            raise ValueError(
                f"Cannot call close() on void element '<{self.tagname}>'. "
                f"Void elements cannot have closing tags. "
                f"Use: gen.{self.tagname}(...) instead of gen.{self.tagname}.open(...) + gen.{self.tagname}.close()"
            )
        try:
            self._context._tags[self.tagname].remove(self)
        except ValueError:
            pass
        return self._markup(self._close())

    def _open(self, bind, kwargs):
        """Return a ``'<partial'`` opener tag with no terminator."""
        contents = kwargs.pop("contents", None)
        attributes = _transform_keys(kwargs)
        tagname = self.tagname
        new_contents = transform(tagname, attributes, contents, self._context, bind)

        if not new_contents:
            new_contents = ""
        elif hasattr(new_contents, "__html__"):
            new_contents = _unpack(new_contents)
        self.contents = self._markup(new_contents)

        if self._context["ordered_attributes"]:
            pairs = sorted(attributes.items(), key=_attribute_sort_key)
        else:
            pairs = attributes.items()
        guts = " ".join(f'{k}="{_attribute_escape(v)}"' for k, v in pairs)
        if guts:
            return "<" + tagname + " " + guts
        else:
            return "<" + tagname

    def _close(self):
        return "</" + self.tagname + ">"

    def _markup(self, string):
        return self._context["markup_wrapper"](string)

    def __call__(self, bind=None, **attributes):
        """Return a complete, closed markup string."""
        header = self._open(bind, attributes)
        if self.tagname in VOID_ELEMENTS:
            # we ignore self.contents here, there must not be any.
            return self._markup(header + (" />" if self._context.xml else ">"))
        contents = self.contents
        if hasattr(contents, "__html__"):
            contents = _unpack(contents)
        return self._markup(header + ">" + contents + self._close())

    def __html__(self):
        return self()


def _attribute_escape(string):
    if not string:
        return ""
    elif hasattr(string, "__html__"):
        return _unpack(string)
    else:
        return (
            string.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )


def _transform_keys(d):
    rekeyed = {}
    for key, value in d.items():
        key = key.rstrip("_")
        rekeyed[key] = value
    return rekeyed


def _attribute_sort_key(item):
    try:
        return (0, _static_attribute_order.index(item[0]))
    except ValueError:
        return (1, item[0])

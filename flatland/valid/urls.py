"""URL validation."""
import urlparse
from . base import Validator, N_


# ordered generic URL part names according to urlparse
_url_parts = ['scheme', 'netloc', 'path', 'params', 'query', 'fragment']

class URLValidator(Validator):
    """A general URL validator.

    Validates that a URL is well-formed and may optionally restrict
    the set of valid schemes and other URL components.

    **Attributes**

    .. attribute:: allowed_schemes

      Restrict URLs to just this sequence of named schemes, or allow
      all schemes with ('*',).  Defaults to all schemes.  Example::

        allowed_schemes = ('http', 'https', 'ssh')

    .. attribute:: allowed_parts

      A sequence of 0 or more part names in :mod:`urlparse`'s
      vocabulary::

        'scheme', 'netloc', 'path', 'params', 'query', 'fragment'

      Defaults to all parts allowed.

    .. attribute:: urlparse

      By default the :mod:`urlparse` module, but may be replaced by
      any object that implements :func:`urlparse.urlparse` and
      :func:`urlparse.urlunparse`.

    **Messages**

    .. attribute:: bad_format

      Emitted for an unparseable URL.

    .. attribute:: blocked_scheme

      Emitted if the URL ``scheme:`` is not present in
      :attr:`allowed_schemes`.

    .. attribute:: blocked_part

      Emitted if the URL has a component not present in
      :attr:`allowed_parts`.

    """

    bad_format = N_("%(label)s is not a valid URL.")
    blocked_scheme = N_("%(label)s is not a valid URL.")
    blocked_part = N_("%(label)s is not a valid URL.")

    allowed_schemes = ('*',)
    allowed_parts = set(_url_parts)
    urlparse = urlparse

    def validate(self, element, state):
        if element.value is None:
            return self.note_error(element, state, 'bad_format')

        try:
            url = self.urlparse.urlparse(element.value.strip())
        except Exception:
            return self.note_error(element, state, 'bad_format')

        scheme_name = url.scheme
        if scheme_name == u'':
            return self.note_error(element, state, 'blocked_scheme')
        elif self.allowed_schemes != ('*',):
            if scheme_name not in self.allowed_schemes:
                return self.note_error(element, state, 'blocked_scheme')

        for part in _url_parts:
            if (part not in self.allowed_parts and
                getattr(url, part) != ''):
                return self.note_error(element, state, 'blocked_part')
        return True


class HTTPURLValidator(Validator):
    """Validates ``http`` and ``https`` URLs.

    Validates that an ``http``-like URL is well-formed and may
    optionally require and restrict the permissible values of its
    components.

    **Attributes**

    .. attribute:: all_parts

      A sequence of known URL parts.  Defaults to the full 10-tuple of
      names in :mod:`urlparse`'s vocabulary for http-like URls.

    .. attribute:: required_parts

      A mapping of part names.  If value is True, the part is
      required.  The value may also be a sequence of strings; the
      value of the part must be present in this collection to
      validate.

      The default requires a ``scheme`` of 'http' or 'https'.

    .. attribute:: forbidden_parts

      A mapping of part names.  If value is True, the part is
      forbidden and validation fails.  The value may also be a
      sequence of strings; the value of the part must not be present
      in this collection to validate.

      The default forbids ``username`` and ``password`` parts.

    .. attribute:: urlparse

      By default the :mod:`urlparse` module, but may be replaced by
      any object that implements :func:`urlparse.urlparse` and
      :func:`urlparse.urlunparse`.

    **Messages**

    .. attribute:: bad_format

      Emitted for an unparseable URL.

    .. attribute:: required_part

      Emitted if URL is missing a part present in
      :attr:`required_parts`.

    .. attribute:: forbidden_part

      Emitted if URL contains a part present in
      :attr:`forbidden_parts`.

    """

    bad_format = N_(u'%(label)s is not a valid URL.')
    required_part = N_(u'%(label)s is not a valid URL.')
    forbidden_part = N_(u'%(label)s is not a valid URL.')

    all_parts = ('scheme', 'username', 'password', 'hostname', 'port',
                 'path', 'params', 'query', 'fragment')
    required_parts = dict(schema=('http', 'https'), hostname=True)
    forbidden_parts = dict(username=True, password=True)
    urlparse = urlparse

    def validate(self, element, state):
        url = element.value
        if url is None or not url.startswith('http'):
            return True
        parsed = self.urlparse.urlparse(url)

        for part in self.all_parts:
            try:
                value = getattr(parsed, part)
                if part == 'port':
                    value = None if value is None else str(value)
            except ValueError:
                return self.note_error(element, state, 'bad_format')
            required = self.required_parts.get(part)
            if required is True:
                if value is None:
                    return self.note_error(element, state, 'required_part')
            elif required:
                if value not in required:
                    return self.note_error(element, state, 'required_part')
            forbidden = self.forbidden_parts.get(part)
            if forbidden is True:
                if value:
                    return self.note_error(element, state, 'forbidden_part')
            elif forbidden:
                if value in forbidden:
                    return self.note_error(element, state, 'forbidden_part')
        return True


class URLCanonicalizer(Validator):
    """A URL canonicalizing validator.

    Given a valid URL, re-writes it with unwanted parts removed.  The
    default implementation drops the ``#fragment`` from the URL, if
    present.

    **Attributes**

    .. attribute:: discard_parts

      A sequence of 0 or more part names in :mod:`urlparse`'s
      vocabulary::

        'scheme', 'netloc', 'path', 'params', 'query', 'fragment'

    .. attribute:: urlparse

      By default the :mod:`urlparse` module, but may be replaced by
      any object that implements :func:`urlparse.urlparse` and
      :func:`urlparse.urlunparse`.

    **Messages**

    .. attribute:: bad_format

      Emitted for an unparseable URL.  This is impossible to hit with
      the Python's standard library implementation of urlparse.

    """

    bad_format = N_(u'%(label)s is not a valid URL.')

    discard_parts = 'fragment',
    urlparse = urlparse

    def validate(self, element, state):
        if not self.discard_parts:
            return True
        try:
            url = self.urlparse.urlparse(element.value)
        except Exception:
            return self.note_error(element, state, 'bad_format')

        url = list(url)
        for part in self.discard_parts:
            idx = _url_parts.index(part)
            current = url[idx]
            url[idx] = '' if current is not None else None

        element.value = self.urlparse.urlunparse(url)
        return True


# -*- coding: utf-8; fill-column: 78 -*-
"""Network address and URL validation."""
import re

from base import N_, Validator


class IsEmail(Validator):
    """Validates email addresses.

    The default behavior takes a very permissive stance on allowed characters
    in the **local part** and a relatively strict stance on the **domain**.
    Given **local-part@domain**:

    - **local-part** must be present and contain at least one non-whitespace
      character.  Any character is permitted, including international
      characters.

    - **domain** must be preset, less than 253 characters and each
      dot-separated component must be 63 characters or less.  **domain** may
      contain non-ASCII international characters, and will be converted to IDN
      representation before length assertions are applied.

    **Attributes**

    .. attribute:: nonlocal

      Default ``True``.  When true, require at minimum two domain name
      components and reject local email addresses such as
      ``postmaster@localhost`` or ``user@workstation``.

    .. attribute:: local_part_pattern

      No default.  If present, a compiled regular expression that will be
      matched to the **local-part**.  Override this to implement more
      stringent checking such as RFC-compliant addresses.

    .. attribute:: domain_pattern

      Defaults to a basic domain-validating regular expression with no notion
      of valid top level domains.  Override this to require certain TLDs (or
      alternately and more simply, add another validator to your chain that
      checks the endings of the string against your list of TLDs.)

      The default pattern rejects the valid but obscure quoted IP-address form
      (``[1.2.3.4]``).

    **Messages**

    .. attribute:: invalid

      Emitted if the email address is not valid.

    """

    invalid = N_(u'%(label)s is not a valid email address.')

    nonlocal = True

    local_part_pattern = None

    domain_pattern = re.compile(r'^(?:[a-z0-9\-]+\.)*[a-z0-9\-]+$',
                                re.IGNORECASE)

    def validate(self, element, state):
        addr = element.u
        if addr.count(u'@') != 1:
            return self.note_error(element, state, 'invalid')

        local_part, domain = addr.split(u'@')

        if not local_part:
            return self.note_error(element, state, 'invalid')

        # optional local part validation
        if (self.local_part_pattern and
            not self.local_part_pattern.match(local_part)):
            return self.note_error(element, state, 'invalid')

        try:
            # convert domain to ascii
            domain = domain.encode('idna')
        except UnicodeError:
            return self.note_error(element, state, 'invalid')

        if len(domain) > 253:
            return self.note_error(element, state, 'invalid')

        if not self.domain_pattern.match(domain):
            return self.note_error(element, state, 'invalid')

        labels = domain.split('.')
        if len(labels) == 1 and self.nonlocal:
            return self.note_error(element, state, 'invalid')

        if not all(len(label) < 64 for label in labels):
            return self.note_error(element, state, 'invalid')

        return True

import re
from flatland.util import re_ucompile
from base import N_, Validator


class IsEmail(Validator):
    invalid = N_(u'%(label)s is not a valid email.')

    pattern = re.compile(r'^.+@[^.].*\.[a-z]{2,4}$', re.IGNORECASE)

    def validate(self, element, state):
        if not self.pattern.match(element.u):
            return self.note_error(element, state, 'invalid')
        return True

import re
from flatland.util import re_ucompile
from base import Validator


class NANPphone(Validator):
    invalid = u'The %(label)s is not valid.'
    noext = (u'%(label)s must be a ten-digit phone number '
             u'without extension.')

    re_cleaner = re_ucompile(ur'\D')
    re_lowbit = re.compile('^[0-9]+$')
    fmt_line = u'(%i03) %i03-%i04'
    fmt_ext = fmt_line + ' x%i'

    def __init__(self, extensions=False):
        super(NANPphone, self).__init__()
        self.extensions = extensions

    def validate(self, element, state):
        value = element.u if element.value is None else element.value
        value = self.re_cleaner.sub('', value)

        if value == u'':
            return self.note_error(element, state, 'invalid')

        if not self.re_lowbit.match(value):
            # Translate to single-byte numbers.
            value = unicode(str(long(value)))

        if len(value) < 10:
            return self.note_error(element, state, 'invalid')
        elif len(value) == 10 or self.extensions == 'strip':
            value = self.fmt_line % (value[0:3], value[3:6], value[6:10])
        else:
            if not self.extensions:
                return self.note_error(element, state, 'noext')
            value = self.fmt_ext % (value[0:3], value[3:6], value[6:10],
                                    value[10:])

        element.set(value)
        return True

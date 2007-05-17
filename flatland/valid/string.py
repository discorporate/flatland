from flatland.util import re_ucompile
from base import Validator, message
import re

class NANPphone(Validator):
    invalid = message(u'The %(label)s is not valid.')
    noext = message(u'%(label)s must be a ten-digit phone number '
                    u'without extension.')

    re_cleaner = re_ucompile(ur'\D')
    re_lowbit = re.compile('^[0-9]+$')
    fmt_line = u'(%i03) %i03-%i04'
    fmt_ext = fmt_line + ' x%i'

    def __init__(self, extensions=False):
        super(NANPphone, self).__init__()
        self.extensions = extensions

    def validate(self, node, state):
        value = node.u if node.value is None else node.value
        value = self.re_cleaner.sub('', value)

        if value == u'':
            return self.failure(node, state, 'invalid')

        if not self.re_lowbit.match(value):
            # Translate to single-byte numbers.
            value = unicode(str(long(value)))

        if len(value) < 10:
            return self.failure(node, state, 'invalid')
        elif len(value) == 10 or self.extensions == 'strip':
            value = self.fmt_line % (value[0:3], value[3:6], value[6:10])
        else:
            if not self.extensions:
                return self.failure(node, state, 'noext')
            value = self.fmt_ext % (value[0:3], value[3:6], value[6:10],
                                    value[10:])

        node.set(value)
        return True


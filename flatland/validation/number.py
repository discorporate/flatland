from __future__ import division
from .base import N_, Validator


class Luhn10(Validator):
    """True if a numeric value passes luhn10 checksum validation."""

    invalid = N_('The %(label)s was not entered correctly.')

    def validate(self, element, state):
        num = element.value
        if num is None:
            return self.note_error(element, state, 'invalid')

        if luhn10_check(num):
            return True

        return self.note_error(element, state, 'invalid')


def luhn10_check(number):
    """Return True if the number passes the Luhn checksum algorithm."""

    sum = 0
    while number:
        r = number % 100
        number //= 100
        z = r % 10
        r = r // 10 * 2
        sum += r // 10 + r % 10 + z

    return 0 == sum % 10

from __future__ import division
from base import Validator, message
import flatland.util as util
import types

class NANPnxx(Validator):
    """Integer"""
    
    def validate(self, node, state):
        if node.value is None:
            return False

        nxx = node.value

        if nxx < 200 or nxx in (311, 411, 511, 611, 711, 811, 911,
                                555, 990, 959, 958, 950, 700,
                                976,):
            return False

        node.u = unicode(nxx)
        return True

class NANPnpa_nxx(Validator):
    "A compound validator; checks the combined validity of npa and nxx nodes."
    
    incomplete = message(False)
    invalid = message(u'The %(label)s can not be verified.')
        
    def __init__(self, npa_node, nxx_node, errors_to=None,
                 lookup='aq', method='valid_npanxx'):
        assert isinstance(npa_node, basestring)
        assert isinstance(nxx_node, basestring)
        assert isinstance(errors_to, (basestring, types.NoneType))

        super(NANPnpa_nxx, self).__init__()

        self.npa = npa_node
        self.nxx = nxx_node
        self.lookup = lookup
        self.method = method

    def validate(self, node, state):
        npa = node.el(self.npa).value
        nxx = node.el(self.nxx).value

        if self.errors_to:
            err = node.el(self.errors_to)
        else:
            err = node
        
        if npa is None or nxx is None:
            return self.failure(err, state, 'incomplete')

        # Will explode at run-time if state does not contain the lookup
        # tool.
        if hasattr(state, self.lookup):
            lookup = getattr(state, self.lookup)
        else:
            lookup = state[self.lookup]

        # catch exceptions here?
        valid = getattr(lookup, self.method)(npa, nxx)
        
        if not valid:
            return self.failure(err, state, 'invalid')

        return true
        

class Luhn10(Validator):
    """Int or Long"""    
    invalid = message('The %(label)s was not entered correctly.')

    def validate(self, node, state):
        num = node.value
        if num is None:
            return self.failure(node, state, 'invalid')

        if util.luhn10(num):
            return True

        return self.failure(node, state, 'invalid')
        

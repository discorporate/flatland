# Copyright 2006 Virtuous, Inc.
# All rights reserved.
#
# Author: Jason Kirtland <jason@virtuous.com>
#
# TODO:
#  Populate multi-value elements (checkbox, select) when Springy
#  supports list values.

from springy.util import *
from springy.node import _Node
from springy.out.genshi.taglistener import TagListener, default_start
from genshi.core import Attrs, Namespace, Stream, START, TEXT, Markup
from genshi.eval import Expression

__all__ = ['genshi_springy_filter', 'SpringyForm']

NAMESPACE  = Namespace('http://code.discorporate.us/springy-form')
D_WITH     = NAMESPACE.__getitem__('with')
D_SET      = NAMESPACE.__getitem__('set')

F_TABINDEX = NAMESPACE.__getitem__('auto-tabindex')
F_ID       = NAMESPACE.__getitem__('auto-domid')
F_FOR      = NAMESPACE.__getitem__('auto-for')
F_NAME     = NAMESPACE.__getitem__('auto-name')
F_VALUE    = NAMESPACE.__getitem__('auto-value')
F_BIND     = NAMESPACE.bind

AUTOTABINDEXABLE = ('input', 'button', 'select', 'textarea')
AUTODOMID = ('input', 'button', 'select', 'textarea' )
AUTONAME = ('input', 'button', 'select', 'textarea' )
AUTOVALUE = ('input', 'select', 'textarea')

VALUE_CHILD  = ('textarea')
VALUE_MIXED  = ('button')

MAYBE = ('auto')
YES   = ('1', 'true', 't', 'on', 'yes')
NO    = ('0', 'false', 'nil', 'off', 'no')

DEFAULT_DOMID_ASSIGN    = True
DEFAULT_DOMID_FMT       = 'f_%s'
DEFAULT_TABINDEX_ASSIGN = True
DEFAULT_TABINDEX_START  = 100
DEFAULT_NAME_ASSIGN     = True
DEFAULT_VALUE_ASSIGN    = True

CTX_AUTO_TABINDEX     = 'auto-tabindex'
CTX_CUR_TABINDEX      = 'auto-tabindex_value'
CTX_AUTO_DOMID        = 'auto-domid'
CTX_FMT_DOMID         = 'auto-domid_format'
CTX_AUTO_NAME         = 'auto-name'
CTX_AUTO_VALUE        = 'auto-value'

CONTEXT_TOGGLES = (CTX_AUTO_TABINDEX, CTX_AUTO_DOMID,
                   CTX_AUTO_NAME, CTX_AUTO_VALUE)

def genshi_springy_filter(stream, context):
  """genshi_springy_filter(stream, context) -> stream

  Filter a stream through SpringyForm."""

  filter_ = SpringyForm()
  return Stream(filter_(stream, context))

class SpringyForm(TagListener):
  """TODO: Document

  Binds template form elements to Springy data nodes and automatically sets
  name, and value.  Manages DOM id generation, links <label> to matching
  elements and manages tabindex.

  """
  def inspect(self, event, context):
    if event[0] is not START:
      return False

    kind, (tag, attributes), pos = event

    if tag in NAMESPACE:
      if   tag.localname == DIR_WITH.name:
        return (DIR_WITH.start, DIR_WITH.end)
      elif tag.localname == DIR_SET.name:
        return (DIR_SET.start, DIR_SET.end)
    else:
      for attr, value in attributes:
        if attr in NAMESPACE:
          return (DIR_EL.start, DIR_EL.end)

class ImmediateVarDirective(object):
  name = 'set'
  
  def start(self, event, context):
    kind, (tag, attrs), pos = event
    attrs = Attrs(attrs)

    for toggle in CONTEXT_TOGGLES:
      val = attrs.get(toggle, None)
      if val is not None:
        context[toggle] = parse_bool(val) or False

    val = parse_int(attrs.get('tabindex', None))
    if val is not None:
      context[CTX_CUR_TABINDEX] = val

    val = parse_int(attrs.get('domid-format', None))
    if val is not None:
      context[CTX_FMT_DOMID] = val

    return None, None

  def end(self, start, end, stream, context, history):
    return None, None, stream

class ScopedVarDirective(ImmediateVarDirective):
  name = 'with'
  
  def start(self, event, context):
    context.push({})
    return ImmediateVarDirective.start(self, event, context)

  def end(self, start, end, stream, context, history):
    context.pop()
    return ImmediateVarDirective.end(self, start, end, stream,
                                     context, history)

class DecoratedElementDirective(object):
  def start(self, event, context):
    kind, (tag, attrs), pos = event
    attrs = Attrs(attrs)

    node = find_binding(tag, attrs, context)

    # Node-free transformations
    set_tabindex(tag, attrs, context)

    # Node-sensitive transformations
    set_domid(tag, attrs, context, node)

    return (kind, (tag, attrs), pos), { 'binding': node }

  def end(self, start, end, stream, context, history):
    kind, tag, pos = end
    start_kind, (start_tag, attrs), start_pos = start

    attrs = Attrs(attrs)

    node = history.get('binding', None)
    attrs.remove(F_BIND)

    # Set <... name=""> for bound nodes.
    set_name(tag, attrs, context, node)

    # Map <label for="..."> to bound tags.
    set_for(tag, attrs, context, node)

    # Set <... value=""> or tag-specific equivalent.
    stream = set_value(tag, attrs, stream, context, node)
    
    # Re-assemble the start event.
    start = (start_kind, (start_tag, attrs), start_pos)

    return start, end, stream

DIR_WITH = ScopedVarDirective()
DIR_SET  = ImmediateVarDirective()
DIR_EL   = DecoratedElementDirective()

######################################################################

def set_tabindex(tag, attrs, context):
  scoped   = parse_bool(context.get(CTX_AUTO_TABINDEX, False))
  override = parse_trool(consume_attribute(attrs, F_TABINDEX, 'auto'))

  tabindex = context.get(CTX_CUR_TABINDEX, 0)

  if (tabindex is not 0 and
      ( ((override is not False & scoped) and
         tag.localname in AUTOTABINDEXABLE) or
        (override is True) )):
    current = attrs.get('tabindex', None)

    if current is None or override is True:
      attrs.set('tabindex', tabindex)
      tabindex += 1
      context[CTX_CUR_TABINDEX] = tabindex

def set_domid(tag, attrs, context, el): 
  scoped   = parse_bool(context.get(CTX_AUTO_DOMID, False))
  override = parse_trool(consume_attribute(attrs, F_ID, 'auto'))
  
  if ( ((override is not False & scoped) and tag.localname in AUTODOMID) or
       (override is True)):
    current = attrs.get('id', None)

    if current is None or override is True:
      if el is not None:
        domid = domid_for_bound(el, context)
      else:
        domid = domid_for_unbound(tag, attrs)
      attrs.set('id', domid)

def set_for(tag, attrs, context, node):
  # Auto set 'for="other-element's-dom-id"' if we're currently setting ids.
  # This is an optimistic calculation- we don't lookup the target node's
  # actual assigned or effective ID, because there is no 1:1 mapping of nodes
  # to tags.
  scoped   = parse_bool(context.get(CTX_AUTO_DOMID, False))
  override = parse_trool(consume_attribute(attrs, F_FOR, 'auto'))

  # If the element is not bound or this isn't a <label>, stop early.  (After
  # consuming our "for" attribute, if present.)
  if tag.localname != 'label' or node is None: return

  if ((override is not False & scoped) or override is True):
    current = attrs.get('for', None)

    if current is None or override is True:
       attrs.set('for', domid_for_bound(node, context))

def set_name(tag, attrs, context, node):
  scoped   = parse_bool(context.get(CTX_AUTO_NAME, False))
  override = parse_trool(consume_attribute(attrs, F_NAME, 'auto'))

  # Abort on unbound nodes.
  if node is None: return

  if ( ((override is not False & scoped) and tag.localname in AUTONAME) or
       (override is True)):
    current = attrs.get('name', None)

    if current is None or override is True:
      attrs.set('name', node.flat_name())

def set_value(tag, attrs, stream, context, node):
  scoped   = parse_bool(context.get(CTX_AUTO_VALUE, False))
  override = parse_trool(consume_attribute(attrs, F_VALUE, 'auto'))

  # Abort on unbound nodes.
  if node is None: return stream

  # Abort if we're sure we won't set the value.
  if not ( ((override is not False & scoped) and tag.localname in AUTOVALUE) or
           override is True):
    return stream

  # VALUE_CHILD (e.g. <textarea>) always replaces the stream with
  # the node's string value.
  if tag.localname in VALUE_CHILD:
    stream = _set_stream_value(node.str)

  elif tag.localname == 'select':
    stream = _set_select(override, attrs, stream, node)

  elif tag.localname in VALUE_MIXED:
    stream = _set_mixed_value(override, attrs, stream, node)

  elif tag.localname == 'input':
    _set_input(override, attrs, node)

  else:
    _set_simple_value(override, attrs, node)

  return stream

def _set_stream_value(text):
  return Stream([(TEXT, text, (None, -1, -1))])  

def _set_simple_value(override, attrs, node):
  current = attrs.get('value')
  if current is None or override is True:
    attrs.set('value', node.str)

def _set_mixed_value(override, attrs, stream, node):
  """For output nodes that may either take a 'value=""' or
  encode their value in nested content.  Node value will be passed
  along as unescaped markup if child nodes are generated!"""
  if attrs.get('value', None) is None:
    stream = _set_stream_value(Markup(node))
  else:
    stream = Stream([])
    _set_simple_value(True, attrs, node)

  return stream

def _set_input(override, attrs, node):
  type = attrs.get('type', 'text').lower()
  
  for case in switch(type):
    if case('text', 'password', 'hidden'):
      _set_simple_value(override, attrs, node)
      break
    if case('submit', 'image', 'button'):
      if override is True:
        _set_simple_value(override, attrs, node)
        break
    if case('checkbox'):
      value = attrs.get('value', None)
      if value is None:
        value = 'on'
        attrs.set('value', value)
      if value == node.str:
        attrs.set('checked', 'checked')
      break
    if case('radio'):
      value = attrs.get('value', None)
      if value is not None and value == node.str:
        attrs.set('checked', 'checked')
      break
    if case('file'):
      # nothing to do
      break

def _set_select(override, attrs, stream, node):
  return OptionToggler(node.str)(stream)
  
class OptionToggler(TagListener):
  __slots__ = ['value']

  def __init__(self, value):
    self.value = value

  def inspect(self, event, context):
    kind, data, pos = event

    if kind is START and data[0].localname == 'option':
      return (default_start, self.end)
    else:
      return False

  def end(self, start, end, stream, context, history):
    kind, (tag, attrs), pos = start
    attrs = Attrs(attrs)
    attrs.remove('selected')

    value = attrs.get('value', None)
    if value == self.value:
      attrs.set('selected', 'selected')
    else:
      children = list(stream)
      value = ''
      for ck, cd, cp in children:
        if ck is TEXT: value += cd
      stream = Stream(children)

      if value == self.value:
        attrs.set('selected', 'selected')

    start = kind, (tag, attrs), pos

    return start, end, stream
    

######################################################################

def domid_for_bound(node, context):
  fmt = context.get(CTX_FMT_DOMID, DEFAULT_DOMID_FMT)
  return fmt % node.flat_name()

def domid_for_unbound(tag, attrs):
  if tag in AUTODOMID:
    name = attrs.get('name', None)
    if name is not None:
      fmt = context.get(CTX_FMT_DOMID, DEFAULT_DOMID_FMT)
      return fmt % name
  return None
  

_not_found = []
def consume_attribute(attributes, name, default=None):
  value = attributes.get(name, _not_found)
  if value is not _not_found:
    attributes.remove(name)
    return value
  return default


def find_binding(tag, attributes, context):
  expr = attributes.get(F_BIND, None)
  if expr is None: return expr

  el = Expression(expr).evaluate(context)
  if el is not None and hasattr(el, 'node'):
    return el.node
  else:
    return None

######################################################################

def parse_bool(value, yes=YES, no=NO):
  if value is True or value is False or value is None: return value
  value = str(value).lower()
  if value in yes: return True
  if value in no: return False
  return None

def parse_trool(value):
  if value is True or value is False or value is Maybe: return value
  value = str(value).lower()
  if value in YES:   return True
  if value in NO:    return False
  if value in MAYBE: return Maybe
  return Maybe
  
def parse_int(text):
  if type(text) is int: return text
  try:
    return int(text)
  except:
    return None

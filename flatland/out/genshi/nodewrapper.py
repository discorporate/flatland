from genshi.core import Stream
from genshi.template import MarkupTemplate
__all__ = ['genshi_add_to_context', 'genshi_wrap_nodes']

def genshi_add_to_context(fieldset, context, key='forms', unnamed='form'):
  if fieldset.name is None:
    context[unnamed] = genshi_wrap_nodes(fieldset.data, unnamed)
  else:
    if not key in context:
      context[key] = {}
    context[key][fieldset.name] = genshi_wrap_nodes(fieldset.data, key)

def genshi_wrap_nodes(node, prefix=''):
  """Proxies a node tree for use in a Genshi context.  Access the original node
  with the .node property, or values with .str and .native.  Collection node
  types are indexable.

  Nodes stringify into an evaluatable object path representation of
  themselves.  E.g.:

  Given a genshiwrapper in the Context:

    nodes['a']['node'] = 'a value'
    context = { 'form': genshiwrapper(nodes, 'form') }

  Accessing a wrapped node in a template:

    <tag thing="${form.a.node.str}" />
    <tag thing="${form.a.node.native}" />
    <tag thing="${form.a.node}" />

  ...will expand to:

    <tag thing="a value" />
    <tag thing="a value" />
    <tag thing="form['a']['node']" />

  A declaration of filter can use the third form (stringification) to
  pull the true node from the Context.

    nodexpr = attributes.get('thing')
    wrappednode = Expression(nodexpr).evaluate(context)
"""

  if node.is_container:
    return Container(node, prefix)
  elif node.is_compound:
    return Compound(node, prefix)
  else:
    return Scalar(node, prefix)

class Wrapped(object):
  __slots__ = ['node', '_prefix']
  def __init__(self, node, prefix):
    self.node, self._prefix = node, prefix
  def __str__(self):
    return (self._prefix +
            ''.join( ["[%s]" % `str(n)` for n in self.node.path] ))

class Scalar(Wrapped):
  native = property(lambda s: s.node.native, lambda s,v: None)
  str    = property(lambda s: s.node.str, lambda s,v: None)

class Indexable(Wrapped):
  def __getitem__(self, key):
    try:
      sub = self.node.get_key(key)
    except:
      return None

    if not sub: return None
    if sub.is_container: return Container(sub, self._prefix)
    if sub.is_compound: return Compound(sub, self._prefix)
    return Scalar(sub, self._prefix)

  def __iter__(self):
    return None

class Compound(Scalar, Indexable):
  pass

class Container(Indexable):
  def __iter__(self):
    return iter(self.node)

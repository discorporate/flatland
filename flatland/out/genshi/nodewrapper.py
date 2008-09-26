from flatland.schema import containers


__all__ = 'genshi_add_to_context', 'genshi_wrap_element'


ContainerElement = containers.Container.element_type


def genshi_add_to_context(element, context, key='forms', unnamed='form'):
    if element.name is None:
        context[unnamed] = genshi_wrap_element(element, unnamed)
    else:
        if not key in context:
            context[key] = {}
        lookup = u"%s[%r]" % (key, element.name)
        context[key][element.name] = genshi_wrap_element(element, lookup)

def genshi_wrap_element(element, prefix=''):
    """Proxies a node tree for use in a Genshi context.

    Access the original node with the .node property, or values with
    .str and .native.  Collection node types are indexable.

    Nodes stringify into an evaluatable object path representation of
    themselves.  E.g.::

    Given a genshiwrapper in the Context:

        nodes['a']['node'] = 'a value'
        context = { 'form': genshiwrapper(nodes, 'form') }

    Accessing a wrapped node in a template::

        <tag thing="${form.a.node.u}" />
        <tag thing="${form.a.node.value}" />
        <tag thing="${form.a.node}" />

    ...will expand to::

        <tag thing="a value" />
        <tag thing="a value" />
        <tag thing="form['a']['node']" />

    A declaration of filter can use the third form (stringification)
    to pull the true node from the Context.

        nodexpr = attributes.get('thing')
        wrappednode = Expression(nodexpr).evaluate(context)
    """
    if isinstance(element, ContainerElement):
        return Container(element, prefix)
    # FIXME
    #elif node.is_compound:
    #    return Compound(node, prefix)
    else:
        return Scalar(element, prefix)


class Wrapped(object):
    __slots__ = 'node', '_prefix'

    def __init__(self, node, prefix):
        self.node, self._prefix = node, prefix

    def __unicode__(self):
        return u'%s.el(%r)' % (self._prefix, self.node.fq_name())

    value = property(lambda s: s.node.value)
    u     = property(lambda s: s.node.u)
    el    = property(lambda s: s.node.el)

class Scalar(Wrapped):
    pass

class Indexable(Wrapped):
    def __getitem__(self, key):
        try:
            return genshi_wrap_element(self.node.el(key), self._prefix)
        except LookupError:
            return None

    def __iter__(self):
        return iter(())

class Compound(Scalar, Indexable):
    pass

class Container(Indexable):
    def __iter__(self):
        return (genshi_wrap_element(child, self._prefix)
                for child in self.node.children)

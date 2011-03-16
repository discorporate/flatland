Jinja2 Templates
================

Markup Generator Usage
------------------------------

Printing an input tag::

   >>> import flatland
   >>> from flatland.out.markup import Generator
   >>> gen = Generator()
   >>> el = flatland.String('foo', name='thinger')
   >>> print gen.input(el)
   <input name="thinger" value="foo" />
   
It's quite simple to output any tag you need with flatland::

    >>> from flatland.out.markup import Generator
    >>> from jinja2 import Template
    >>> template = Template('''\
    ... Hi I'm a generator, see my tag: {{ gen.tag('a', href='#') }}
    ... ''')
    >>> gen = Generator()
    >>> print template.render(gen=gen)
    Hi I'm a generator, see my tag: <a href="#" />

There's also no requirement that these tags exist in any current standard::

    >>> from flatland.out.markup import Generator
    >>> gen = Generator()
    >>> print gen.tag('wookie', contents="wookies are not really real")
    <wookie>wookies are not really real</wookie>

    
In Progress
-----------

Support for Jinja2 and Mako is underway with a feature set similar to
the Genshi support.

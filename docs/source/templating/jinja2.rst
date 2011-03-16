Jinja2 Templates
================

.. _markupsettings:

Markup Settings
---------------

Placeholder... this should be in its own file and shared with a reworked
Genshi guide.

auto_name

auto_value

auto_domid

auto_for

auto_tabindex

auto_filter


Markup Generator Usage
----------------------

The markup generator makes it easy to generate HTML and XML markup
tags, and when combined with Flatland elements make it easy to create
HTML forms that capture and redisplay input, and communicate
validation errors to users right at the fields that generated them.

.. doctest:: generatorintro

   >>> from flatland import String
   >>> from flatland.out.markup import Generator

.. doctest:: generatorintro

   >>> gen = Generator()
   >>> el = String('foo', name='thinger')
   >>> print gen.input(el)
   <input name="thinger" value="foo" />

It's quite simple to output any tag you need with flatland.

.. doctest:: generatorintro

   >>> print gen.tag('a', href="/", contents="Home")
   <a href="/">Home</a>

Flatland markup generators can be used anywhere you'd use a Unicode
string, and are completely at home in template languages such as
Jinja2 and Mako.

.. doctest:: generatorintro

    >>> from jinja2 import Template
    >>> template = Template('''\
    ... {{ gen.input(el) }}
    ... ''')
    >>> el = String(name='username')
    >>> print template.render(gen=gen, el=el)
    <input name="username" value="" />

And some time-saving generation features are available.

.. doctest:: generatorintro

    >>> template = Template('''\
    ... {{ gen.set(auto_domid=True, auto_for=True) -}}
    ... {{ gen.label(el) }}
    ... {{ gen.input(el) }}
    ... ''')
    >>> el = String(name='username')
    >>> gen = Generator(markup='html')
    >>> print template.render(gen=gen, el=el)
    <label for="f_username"></label>
    <input name="username" value="" id="f_username">


There's also no requirement that these tags exist in any current standard:

.. doctest:: generatorintro

    >>> print gen.tag('wookie', contents="wookies are not really real")
    <wookie>wookies are not really real</wookie>


Generator
---------

Placeholder.

.. currentmodule:: flatland.out.markup


.. autoclass:: Generator
   :members:


.. autoclass:: Tag
   :members:


In Progress
-----------

Support for Jinja2 and Mako is underway with a feature set similar to
the Genshi support.

"""Genshi integration for Springy forms.

This package provides Genshi template tools for generating XHTML input
controls bound to Springy form nodes, as well as some bonus form and document
management features.

Any number of forms can be bound and managed.  Just drop them into the context
using genshi_add_to_context().  This adds a special wrapper to the context
that allows direct access to Springy nodes during regular Genshi processing
and again during the form binding pass.

Example::

  context = { 'title':'Sign-In' }

  loginform = LoginForm.from_request('login', request)

  genshi_add_to_context(loginform, context)

  tmpl = loader.load('login.html')
  stream = genshi_springy_filter(tmpl.generate(**context), context)
  return stream.render('xhtml')

Springy Node Access
-------------------

You can access the Springy node hierarchy directly from your templates::

  Your sign-in ID is: ${forms.login.loginid.str}

Or, more conveniently::

  <py:with vars="form=forms.login">
     Your sign-in ID is ${loginid.str}
  </py:with>

Nodes are available for error and warning queries as well.

Basic Input Control Binding
---------------------------

Input  element name  and value  can be  auto-decorated by binding the
document element to a Springy node with "bind"::

  <fieldset xmlns:form="http://code.discorporate.us/springy-form"
    py:with="form=forms.login">
    <input type="text" form:bind="${form.loginid}"/>
  </fieldset>

The element will be assigned the flat-mapped name for the loginid
node.  Here's another example of binding a nested list of strings to a
flat form::

  <ul>
    <li py:for="i in form.notes">
      <input type="text" form:bind="${form.notes[i].note}"/>
    </li>
  </ul>

The name attribute will receive the flat name to each node using the
separator and scoping rules in effect for the node tree, e.g.::

    <li>
      <input type="text" name="login_notes_1_note" value="Hi!"/>
    </li>

Interaction With Genshi
-----------------------

Variable expansion, <py:match> and friends happen before Springy
binding is complete.

Example::

  Imagine a <py:match> that provides <select> <option> values for each
  month of the year.  You can bind this templated element to a Springy
  node like so::

    <select py:match="select[@options=months]">...</select>
    <select options="months" form:bind="${form.month}"/>

  The select element will be filled out with <options> by py:match,
  and if one matches the bound element it will be selected in the
  generated output.

DOM ID Generation and Tabindex Management
-----------------------------------------

Elements can have unique DOM IDs auto-assigned.  These are convenient
for scripting and for automatically relating <LABEL> elements to input
controls.

  <form:with auto-domid="on">
    <label form:bind="${form.loginid}">Login Id:</label>
    <input type="text" form:bind="${form.loginid}"/>
  </form:with>

  Generates:
    <label for="f_login_loginid">Login Id:</label>
    <input type="text" name="login_loginid" id="f_login_loginid" />

DOM ID decoration defaults to on, and can be toggled via "set" or
"with".  The format for generated ID strings can also be set with
"domid-format".

Tabindex Management
-------------------

Elements can also have their tabindexes managed, each receiving an
ascending tabindex value.  This decoration defaults to on for bound
elements.  However any document element can be decorated with an
automatic tabindex.

  <input type="text" form:bind="${form.loginid}" />
  <input type="submit" form:auto-tabindex="yes" />
  <a href="/cancel" form:auto-tabindex="true">Cancel</a>

  Generates:
  <input type="text" name="login_loginid" tabindex="100"/>
  <input type="submit" tabindex="101"/>
  <a href="/cancel" tabindex="102">Cancel</a>

The starting tabindex can be specified via "set" or "with" using
"tabindex".

Controlling and Overriding Auto-Decoration
------------------------------------------

All aspects of the form generation can be turned on and off within a
template, both on a global level and on individual fields.

  <form:set option=value [...]/>

Like simple variable assignment, "set" modifies the option directly.

  <form:with option=value [...] />

Like the Genshi <py:with> directive, this applies the changes within a
block scope.

Boolean Controls:
  auto-name
  auto-value
  auto-domid
  auto-tabindex

  Turn these auto-decorations on or off.  Values can be true, false,
  on, off, yes, no, 1, or 0.

Decoration Options:
  tabindex

  An integer, used for the next tabindex assignment.

  domid-format

  A string format for generating DOM IDs, by default "f_%s".  The format
  will be passed a single string: the flat name of the node.

Element-Level Control
---------------------

  The auto-* controls can also be applied directly to document elements.

  <form:with auto-tabindex="off">
    <input form:bind="${form.element}" form:auto-tabindex="on"/>
  </form:with>

  <form:with auto-tabindex="on">
    <input form:bind="${form.element}" form:auto-tabindex="off"/>
  </form:with>

  Element level toggles can be controlled with a boolean value plus
  "maybe".  Maybes will be applied if the document or scope-level
  control is true, otherwise not.  All bound elements have a default
  of "maybe" if not specified.

Literal Attributes
------------------

  If the source element already contains the attribute that would be
  generated, it will be left untouched by default and no generation
  will be applied.  Generation can be forced by turning on the
  matching element-level auto-* control.

  <input name="untouched" form:bind="${form.el}"/>
  <input name="overridden" form:bind="${form.el}" form:auto-name="yes"/>

"""

import filter, nodewrapper, taglistener
from nodewrapper import genshi_add_to_context, genshi_wrap_nodes
from filter import genshi_springy_filter


__all__ = ['genshi_add_to_context',
           'genshi_springy_filter']

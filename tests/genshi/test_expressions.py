from flatland import (
    Dict,
    List,
    String,
    )

from tests.genshi._util import FilteredRenderTest, from_docstring


class TestExpressions(FilteredRenderTest):
    def form():
        schema = Dict.named(u'field0').of(
            String.named(u'field1'),
            String.named(u'field2'),
            List.named(u'field3').of(String.named(u'field4')),
            List.named(u'field5').of(
                List.named(u'field6').of(String.named(u'field7'))))

        element = schema(
            {u'field1': u'val1',
             u'field2': u'val2',
             u'field3': [u'val3'],
             u'field5': [[u'val4']]})
        element.set_prefix(u'form')
        return {'form': element, 'bound': element.bind}

    @from_docstring(context_factory=form)
    def test_field0(self):
        """
:: test
${form}
:: eq  # FIXME: b0rk3n, hash sensitive
field2field3field1field5
:: endtest

:: test
${bound}
:: eq
form.el(u'.')
:: endtest

:: test
${form.bind}
:: eq
form.el(u'.')
:: endtest

:: test
<py:for each="name in form">${type(name).__name__} </py:for>
::eq
unicode unicode unicode unicode
:: endtest
        """

    @from_docstring(context_factory=form)
    def test_field1(self):
        """
:: test
${form['field1']}
:: eq
val1
:: endtest

:: test
${form.field1}
:: eq
val1
:: endtest

:: test
${form.field1.u}
:: eq
val1
:: endtest

:: test
${form.field1.bind.u}
:: eq
val1
:: endtest

:: test
${form.field1.bind.bind.bind.u}
:: eq
val1
:: endtest
        """

    @from_docstring(context_factory=form)
    def test_field3(self):
        """
:: test
${form.field3}
:: eq
val3
:: endtest

:: test
${form.field3.bind}
:: eq
form.el(u'.field3')
:: endtest

:: test
${form.field3[0]}
:: eq
val3
:: endtest

:: test
${form.field3[0].bind}
:: eq
form.el(u'.field3.0')
:: endtest

:: test
<py:for each="x in form.field3.binds">${x}</py:for>
:: eq
field4
:: endtest

:: test
${type(form.binds.field3).__name__}
:: eq
WrappedElement
:: endtest

:: test
<py:for each="x in form.binds.field3">${type(x).__name__}</py:for>
:: eq
WrappedElement
:: endtest

:: test
<py:for each="x in form.binds.field3">${x}</py:for>
:: eq
form.el(u'.field3.0')
:: endtest
        """

    @from_docstring(context_factory=form)
    def test_field5(self):
        """
:: test
${bound.field5}
:: eq
form.el(u'.field5')
:: endtest

:: test
${form.field5.value}
:: eq
[u'val4']
:: endtest

:: test
${bound.field5[0]}
:: eq
form.el(u'.field5.0')
:: endtest

:: test
${form['field5'][0].bind}
:: eq
form.el(u'.field5.0')
:: endtest

:: test
<py:for each="e in bound.field5">${type(e).__name__}</py:for>
:: eq
WrappedElement
:: endtest

:: test
<py:for each="e in bound.field5">${e}</py:for>
:: eq
form.el(u'.field5.0')
:: endtest
        """

    @from_docstring(context_factory=form)
    def test_field7(self):
        """
:: test
${bound.field5[0][0]}
:: eq
form.el(u'.field5.0.0')
:: endtest

:: test
${form.field5[0][0].bind}
:: eq
form.el(u'.field5.0.0')
:: endtest

:: test
${form.field5[0][0].u}
:: eq
val4
:: endtest
        """

    del form


class TestShadowed(FilteredRenderTest):
    def shadow():
        schema = Dict.named(u'dict_name').of(
            String.named(u'name'),
            String.named(u'u'))

        element = schema({u'name': u'string name',
                          u'u': u'string u'})
        element.set_prefix(u'top')
        return {'top': element, 'bound': element.bind}

    @from_docstring(context_factory=shadow)
    def test_shadow(self):
        """
:: test
${bound}
:: eq
top.el(u'.')
:: endtest

:: test
${bound}
:: eq
top.el(u'.')
:: endtest

:: test
${top.name}
:: eq
dict_name
:: endtest

:: test
${top.binds.name}
:: eq
top.el(u'.name')
:: endtest

:: test
${top.binds.name.name}
:: eq
name
:: endtest

:: test
${top.binds.u}
:: eq
top.el(u'.u')
:: endtest

:: test
${top.binds.u.name}
:: eq
u
:: endtest

:: test
${top['name']}
:: eq
string name
:: endtest

:: test
${top['name'].u}
:: eq
string name
:: endtest

:: test
${top['name'].name}
:: eq
name
:: endtest
        """

    del shadow


class TestPrefixes(FilteredRenderTest):
    def elements():
        from flatland import Dict, String
        anon = Dict.of(String.named(u'anon_field'))()
        named = Dict.named(u'named').of(String.named(u'named_field'))()
        prefixed = Dict.named(u'prefixed').of(String.named(u'prefixed_field'))()
        prefixed.set_prefix(u'three.levels.down')

        return {'form': anon,
                'forms': {'named': named },
                'three': {'levels': {'down': prefixed}}}

    @from_docstring(context_factory=elements)
    def test_prefixes(self):
        """
:: test
${form.bind}
:: eq
form.el(u'.')
:: endtest

:: test
${form.binds}
:: eq
anon_field
:: endtest

:: test
${form.anon_field.bind}
:: eq
form.el(u'.anon_field')
:: endtest

:: test
${form.binds.anon_field}
:: eq
form.el(u'.anon_field')
:: endtest

:: test
${forms.named.named_field.bind}
:: eq
forms.named.el(u'.named_field')
:: endtest

:: test
${forms.named.binds.named_field}
:: eq
forms.named.el(u'.named_field')
:: endtest

:: test
${three.levels.down.prefixed_field.bind}
:: eq
three.levels.down.el(u'.prefixed_field')
:: endtest

:: test
${three.levels.down.binds.prefixed_field}
:: eq
three.levels.down.el(u'.prefixed_field')
:: endtest


        """

    del elements

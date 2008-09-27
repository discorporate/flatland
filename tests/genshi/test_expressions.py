from tests.genshi._util import rendered_markup_eq_


class TestExpressions(object):
    def setup(self):
        from flatland import Dict, String, List

        self.schema = Dict('field0',
                           String('field1'),
                           String('field2'),
                           List('field3', String('field4')),
                           List('field5',
                                List('field6', String('field7'))))

        self.element = self.schema.create_element(
            value={'field1': u'val1',
                   'field2': u'val2',
                   'field3': [u'val3'],
                   'field5': [['val4']]})

    def check(self, template_text):
        element = self.element
        element.set_prefix('form')
        rendered_markup_eq_(template_text, form=element)

    def test_field0(self):
        self.check("""
<py:with vars="bound=form.bind" xmlns:py="http://genshi.edgewall.org/">
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
</py:with>
        """)

    def test_field1(self):
        self.check("""
<py:with vars="bound=form.bind" xmlns:py="http://genshi.edgewall.org/">
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

</py:with>
        """)

    def test_field3(self):
        self.check("""
<py:with vars="bound=form.bind" xmlns:py="http://genshi.edgewall.org/">
:: test
${form.field3}
:: eq
&lt;ListSlot[0] for &lt;String u'field4'; value=u'val3'&gt;&gt;
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
</py:with>
        """)

    def test_field5(self):
        self.check("""
<py:with vars="bound=form.bind" xmlns:py="http://genshi.edgewall.org/">

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

</py:with>
        """)

    def test_field7(self):
        self.check("""
<py:with vars="bound=form.bind" xmlns:py="http://genshi.edgewall.org/">

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

</py:with>
        """)


def test_shadow():
    template_text = """
<py:with vars="bound=top.bind" xmlns:py="http://genshi.edgewall.org/">

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

</py:with>
"""
    from flatland import Dict, String
    s = Dict('dict_name',
             String('name'),
             String('u'))

    element = s.create_element(value={'name': u'string name',
                                      'u': u'string u'})
    element.set_prefix('top')
    rendered_markup_eq_(template_text, top=element)

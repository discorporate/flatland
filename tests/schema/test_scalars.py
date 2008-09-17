import datetime
from nose.tools import eq_, assert_raises

from flatland import schema


def test_scalar_abstract():
    sc = schema.scalars.Scalar('foo')

    node = sc.new()
    assert_raises(NotImplementedError, node.set, 'blagga')

def test_scalar_assignments_are_independent():
    sc = schema.scalars.Scalar('foo')

    node = sc.new()
    assert not node.u
    assert not node.value
    node.u = u'abc'
    assert node.value is None

    node = sc.new()
    assert not node.u
    assert not node.value
    node.value = u'abc'
    eq_(node.u, u'')
    eq_(node.value, u'abc')

def test_scalar_set_flat():
    """Scalars take on the first value if duplicates are present."""

    class SimpleScalar(schema.scalars.Scalar):
        def parse(self, node, value):
            return value

    data = ((u'a', 1),
            (u'b', 2),
            (u'a', 3))

    def node_for(name):
        s = SimpleScalar(name)
        node = s.node()
        node.set_flat(data)
        return node

    eq_(node_for(u'a').value, 1)
    eq_(node_for(u'b').value, 2)
    eq_(node_for(u'c').value, None)

def test_string():
    assert_raises(TypeError, schema.String)

    for value, expected in ((u'abc', u'abc'), ('abc', u'abc'), (123, u'123'),
                            (u'abc ', u'abc'), (' abc ', u'abc')):
        for st in schema.String('foo'), schema.String('foo', strip=True):
            node = st.new()
            node.set(value)
            eq_(node.u, expected)
            eq_(unicode(node), expected)
            eq_(node.value, expected)

    for value, expected in ((u'abc ', u'abc '), (' abc ', u' abc ')):
        st = schema.String('foo', strip=False)
        node = st.new()
        node.set(value)
        eq_(node.u, expected)
        eq_(unicode(node), expected)
        eq_(node.value, expected)

def validate_node_set(type_, raw, value, uni, schema_opts={}):
    node = type_('i', **schema_opts).node()
    node.set(raw)
    eq_(node.value, value)
    eq_(node.u, uni)
    eq_(unicode(node), uni)
    eq_(node.__nonzero__(), bool(uni and value))

def test_scalar_set():
    # a variety of scalar set() failure cases, shoved through Integer
    for spec in (
        ([],         None, u'[]'),
        ('\xef\xf0', None, ur'\ufffd\ufffd'),
        (None,       None, u'')):
        yield (validate_node_set, schema.Integer) + spec

def test_integer():
    for spec in ((u'123',    123,  u'123'),
                 (u' 123 ',  123,  u'123'),
                 (u'xyz',    None, u'xyz'),
                 (u'xyz123', None, u'xyz123'),
                 ('123xyz',  None, u'123xyz'),
                 ('123.0',   None, u'123.0'),
                 (u'+123',   123,  u'123'),
                 (u'-123',   -123, u'-123'),
                 (u' +123 ', 123,  u'123'),
                 (u' -123 ', -123, u'-123'),
                 (u'+123',   123,  u'123', dict(signed=False)),
                 (u'-123',   None, u'-123', dict(signed=False)),
                 (123,       123,  u'123'),
                 (-123,      None, u'-123', dict(signed=False))):
        yield (validate_node_set, schema.Integer) + spec

def test_long():
    for spec in ((u'123',    123L,  u'123'),
                 (u' 123 ',  123L,  u'123'),
                 (u'xyz',    None,  u'xyz'),
                 (u'xyz123', None,  u'xyz123'),
                 ('123xyz',  None,  u'123xyz'),
                 ('123.0',   None,  u'123.0'),
                 (u'+123',   123L,  u'123'),
                 (u'-123',   -123L, u'-123'),
                 (u' +123 ', 123L,  u'123'),
                 (u' -123 ', -123L, u'-123'),
                 (u'+123',   123L,  u'123', dict(signed=False)),
                 (u'-123',   None,  u'-123', dict(signed=False))):
        yield (validate_node_set, schema.Long) + spec

def test_float():
    for spec in ((u'123',    123.0,  u'123.000000'),
                 (u' 123 ',  123.0,  u'123.000000'),
                 (u'xyz',    None,  u'xyz'),
                 (u'xyz123', None,  u'xyz123'),
                 ('123xyz',  None,  u'123xyz'),
                 ('123.0',   123.0,  u'123.000000'),
                 (u'+123',   123.0,  u'123.000000'),
                 (u'-123',   -123.0, u'-123.000000'),
                 (u' +123 ', 123.0,  u'123.000000'),
                 (u' -123 ', -123.0, u'-123.000000'),
                 (u'+123',   123.0,  u'123.000000', dict(signed=False)),
                 (u'-123',   None,  u'-123', dict(signed=False))):
        yield (validate_node_set, schema.Float) + spec

    class TwoDigitFloat(schema.Float):
        format = u'%0.2f'

    for spec in ((u'123',    123.0,  u'123.00'),
                 (u' 123 ',  123.0,  u'123.00'),
                 (u'xyz',    None,  u'xyz'),
                 (u'xyz123', None,  u'xyz123'),
                 ('123xyz',  None,  u'123xyz'),
                 ('123.0',   123.0,  u'123.00'),
                 ('123.00',   123.0,  u'123.00'),
                 ('123.005',   123.005,  u'123.00')):
        yield (validate_node_set, TwoDigitFloat) + spec

def test_boolean():
    for ok in schema.Boolean.true_synonyms:
        yield validate_node_set, schema.Boolean, ok, True, u'1'
        yield (validate_node_set, schema.Boolean, ok, True, u'baz',
               dict(true=u'baz'))

    for not_ok in schema.Boolean.false_synonyms:
        yield validate_node_set, schema.Boolean, not_ok, False, u''
        yield (validate_node_set, schema.Boolean, not_ok, False, u'quux',
               dict(false=u'quux'))

    for bogus in u'abc', u'1.0', u'0.0', u'None':
        yield validate_node_set, schema.Boolean, bogus, None, u''

def test_date():
    t = datetime.date
    for spec in (
        (u'2009-10-10', t(2009, 10, 10), u'2009-10-10'),
        (u'2010-08-02', t(2010, 8, 2), u'2010-08-02'),
        (u'2011-8-2', None, u'2011-8-2'),
        (u'blagga', None, u'blagga')):
        yield (validate_node_set, schema.Date) + spec

def test_time():
    t = datetime.time
    for spec in (
        (u'08:09:10', t(8, 9, 10), u'08:09:10'),
        (u'23:24:25', t(23, 24, 25), u'23:24:25'),
        (u'24:25:26', None, u'24:25:26'),
        (u'bogus', None, u'bogus')):
        yield (validate_node_set, schema.Time) + spec

def test_datetime():
    t = datetime.datetime
    for spec in (
        (u'2009-10-10 08:09:10', t(2009, 10, 10, 8, 9, 10),
         u'2009-10-10 08:09:10'),
        (u'2010-08-02 25:26:27', None, u'2010-08-02 25:26:27'),
        (u'2010-13-22 09:09:09', None, u'2010-13-22 09:09:09')):
        yield (validate_node_set, schema.DateTime) + spec


from flatland import schema, util
from flatland.schema import base, containers
from flatland.util import Unspecified
from tests._util import eq_, assert_raises


def test_simple_validation_shortcircuit():
    def boom(element, state):
        assert False
    all_ok = lambda element, state: base.SkipAll

    el = schema.Dict('d', schema.Integer('i', validators=[boom]),
                     validators=[all_ok]).create_element()


class TestContainerValidation(object):

    def setup(self):
        self.canary = []

    def validator(self, name, result):
        def fn(element, state):
            self.canary.append(name)
            return result
        fn.__name__ = name
        return fn

    def test_regular(self):
        s = schema.Dict('d', schema.Integer('i'),
                        validators=[self.validator('1', True)])
        el = s.create_element()
        assert not el.validate()
        eq_(self.canary, ['1'])
        assert el.valid
        assert not el.all_valid

    def test_descent(self):
        s = schema.Dict('d', schema.Integer('i'),
                        descent_validators=[self.validator('1', True)])
        el = s.create_element()
        assert not el.validate()
        eq_(self.canary, ['1'])
        assert el.valid
        assert not el.all_valid

    def test_paired(self):
        s = schema.Dict('d', schema.Integer('i'),
                        descent_validators=[self.validator('1', True)],
                        validators=[self.validator('2', True)])
        el = s.create_element()
        assert not el.validate()
        eq_(self.canary, ['1', '2'])
        assert el.valid
        assert not el.all_valid

    def test_paired2(self):
        s = schema.Dict('d', schema.Integer('i'),
                        descent_validators=[self.validator('1', False)],
                        validators=[self.validator('2', True)])
        el = s.create_element()
        assert not el.validate()
        eq_(self.canary, ['1', '2'])
        assert not el.valid
        assert not el.all_valid

    def test_paired3(self):
        s = schema.Dict('d', schema.Integer('i', validators=[
                               self.validator('2', True)]),
                        descent_validators=[self.validator('1', True)],
                        validators=[self.validator('3', True)])
        el = s.create_element()
        assert el.validate()
        eq_(self.canary, ['1', '2', '3'])
        assert el.valid
        assert el.all_valid

    def test_shortcircuit_down_true(self):
        s = schema.Dict('d', schema.Integer('i', validators=[
                               self.validator('2', False)]),
                        descent_validators=[self.validator('1', base.SkipAll)],
                        validators=[self.validator('3', True)])
        el = s.create_element()
        assert el.validate()
        eq_(self.canary, ['1', '3'])
        assert el.valid
        assert el.all_valid

    def test_shortcircuit_down_false(self):
        s = schema.Dict('d', schema.Integer('i', validators=[
                               self.validator('2', True)]),
                        descent_validators=[
                            self.validator('1', base.SkipAllFalse)],
                        validators=[self.validator('3', True)])
        el = s.create_element()
        assert not el.validate()
        eq_(self.canary, ['1', '3'])
        assert not el.valid
        assert not el.all_valid
        assert el['i'].valid is schema.Unevaluated

    def test_shortcircuit_up(self):
        s = schema.Dict('d', schema.Integer('i', validators=[
                               self.validator('2', True)]),
                        descent_validators=[self.validator('1', True)],
                        validators=[self.validator('3', base.SkipAll)])
        el = s.create_element()
        assert el.validate()
        eq_(self.canary, ['1', '2', '3'])
        assert el.valid
        assert el.all_valid


def test_sequence():
    assert_raises(TypeError, schema.containers.Sequence, 's',
                  schema.String('a'))

    s = schema.containers.Sequence('s')
    assert hasattr(s, 'child_schema')


def test_mixed_all_children():
    data = {'A1': 1,
            'A2': 2,
            'A3': { 'A3B1': { 'A3B1C1': 1,
                              'A3B1C2': 2, },
                    'A3B2': { 'A3B2C1': 1 },
                    'A3B3': [ ['A3B3C0D0', 'A3B3C0D1'],
                              ['A3B3C1D0', 'A3B3C1D1'],
                              ['A3B3C2D0', 'A3B3C2D1'] ] } }

    s = schema.Dict(
        'R',
        schema.String('A1'),
        schema.String('A2'),
        schema.Dict('A3',
                    schema.Dict('A3B1',
                                schema.String('A3B1C1'),
                                schema.String('A3B1C2')),
                    schema.Dict('A3B2',
                                schema.String('A3B2C1')),
                    schema.List('A3B3',
                                schema.List('A3B3Cx',
                                            schema.String('A3B3x')))))
    top = s.from_value(data)

    names = list(e.name for e in top.all_children)

    assert set(names[0:3]) == set(['A1', 'A2', 'A3'])
    assert set(names[3:6]) == set(['A3B1', 'A3B2', 'A3B3'])
    # same-level order the intermediates isn't important
    assert set(names[12:]) == set(['A3B3x'])
    assert len(names[12:]) == 6


def test_corrupt_all_children():
    """all_children won't spin out if the graph becomes cyclic."""
    s = schema.List('R', schema.String('A1'))
    e = s.create_element()

    e.append('x')
    e.append('y')
    dupe = schema.String('A1').create_element(value='z')
    e.append(dupe)
    e.append(dupe)

    assert list(_.value for _ in e.children) == list('xyzz')
    assert list(_.value for _ in e.all_children) == list('xyz')


def test_naming_bogus():
    e = schema.String('s').create_element()

    assert_raises(LookupError, e.el, u'')
    assert_raises(TypeError, e.el, None)
    assert_raises(LookupError, e.el, ())
    assert_raises(LookupError, e.el, iter(()))
    assert_raises(TypeError, e.el)


def test_naming_shallow():
    s1 = schema.String('s')
    root = s1.create_element()
    assert root.fq_name() == '.'
    assert root.flattened_name() == 's'
    assert root.el('.') is root

    s2 = schema.String(None)
    root = s2.create_element()
    assert root.fq_name() == '.'
    assert root.flattened_name() == ''
    assert root.el('.') is root
    assert_raises(LookupError, root.el, ())
    assert root.el([schema.base.Root]) is root


def test_naming_dict():
    for name, root_flat, leaf_flat in (('d', 'd', 'd_s'),
                                       (None, '', 's')):
        s1 = schema.Dict(name, schema.String('s'))
        root = s1.create_element()
        leaf = root['s']

        assert root.fq_name() == '.'
        assert root.flattened_name() == root_flat
        assert root.el('.') is root

        assert leaf.fq_name() == '.s'
        assert leaf.flattened_name() == leaf_flat
        assert root.el('.s') is leaf
        assert root.el('s') is leaf
        assert leaf.el('.s') is leaf
        assert_raises(LookupError, leaf.el, 's')
        assert leaf.el('.') is root

        assert root.el([schema.base.Root]) is root
        assert root.el(['s']) is leaf
        assert root.el([schema.base.Root, 's']) is leaf
        assert root.el(iter(['s'])) is leaf
        assert root.el(iter([schema.base.Root, 's'])) is leaf


def test_naming_dict_dict():
    for name, root_flat, leaf_flat in (('d', 'd', 'd_d2_s'),
                                       (None, '', 'd2_s')):
        s1 = schema.Dict(name, schema.Dict('d2', schema.String('s')))
        root = s1.create_element()
        leaf = root['d2']['s']

        assert root.fq_name() == '.'
        assert root.flattened_name() == root_flat
        assert root.el('.') is root

        assert leaf.fq_name() == '.d2.s'
        assert leaf.flattened_name() == leaf_flat
        assert root.el('.d2.s') is leaf
        assert root.el('d2.s') is leaf
        assert leaf.el('.d2.s') is leaf
        assert_raises(LookupError, leaf.el, 'd2.s')
        assert leaf.el('.') is root

        assert root.el(['d2', 's']) is leaf


def test_naming_list():
    for name, root_flat, leaf_flat in (('l', 'l', 'l_0_s'),
                                       (None, '', '0_s')):
        s1 = schema.List(name, schema.String('s'))
        root = s1.create_element(value=['x'])
        leaf = root[0]

        assert root.fq_name() == '.'
        assert root.flattened_name() == root_flat
        assert root.el('.') is root

        assert leaf.fq_name() == '.0'
        assert leaf.flattened_name() == leaf_flat
        assert root.el('.0') is leaf
        assert root.el('0') is leaf
        assert leaf.el('.0') is leaf
        assert_raises(LookupError, leaf.el, '0')
        assert_raises(LookupError, leaf.el, 's')
        assert leaf.el('.') is root

        assert root.el(['0']) is leaf


def test_naming_list_list():
    # make sure nested Slots-users don't bork
    for name, root_flat, leaf_flat in (('l', 'l', 'l_0_l2_0_s'),
                                       (None, '', '0_l2_0_s')):
        s1 = schema.List(name, schema.List('l2', schema.String('s')))

        root = s1.create_element(value=[['x']])
        leaf = root[0][0]

        assert root.fq_name() == '.'
        assert root.flattened_name() == root_flat
        assert root.el('.') is root

        assert leaf.fq_name() == '.0.0'
        assert leaf.flattened_name() == leaf_flat
        assert root.el('.0.0') is leaf
        assert root.el('0.0') is leaf
        assert leaf.el('.0.0') is leaf
        assert_raises(LookupError, leaf.el, '0')
        assert_raises(LookupError, leaf.el, 's')
        assert leaf.el('.') is root

        assert root.el(['0', '0']) is leaf

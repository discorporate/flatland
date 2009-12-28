from flatland import (
    Dict,
    Integer,
    List,
    Sequence,
    SkipAll,
    SkipAllFalse,
    String,
    Unevaluated,
    )
from flatland.schema.base import Root
from tests._util import eq_, assert_raises


def test_dsl_of():
    assert_raises(TypeError, Sequence.of)

    t1 = Sequence.of(Integer)
    assert t1.member_schema is Integer

    t2 = Sequence.of(Integer.named(u'x'), Integer.named(u'y'))
    assert issubclass(t2.member_schema, Dict)
    assert sorted(t2.member_schema().keys()) == [u'x', u'y']


def test_simple_validation_shortcircuit():
    Regular = Dict.of(Integer.using(optional=False))
    el = Regular()
    assert not el.validate()

    def boom(element, state):
        assert False
    all_ok = lambda element, state: SkipAll

    Boom = Integer.named(u'i').using(validators=[boom])

    ShortCircuited = Dict.of(Boom).using(descent_validators=[all_ok])
    el = ShortCircuited()
    assert el.validate()


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
        schema = (Dict.of(Integer).
                  using(validators=[self.validator('1', True)]))
        el = schema()

        assert not el.validate()
        eq_(self.canary, ['1'])
        assert el.valid
        assert not el.all_valid

    def test_descent(self):
        schema = Dict.of(Integer).using(
            descent_validators=[self.validator('1', True)])
        el = schema()
        assert not el.validate()
        eq_(self.canary, ['1'])
        assert el.valid
        assert not el.all_valid

    def test_paired(self):
        schema = Dict.of(Integer).using(
            descent_validators=[self.validator('1', True)],
            validators=[self.validator('2', True)])
        el = schema()
        assert not el.validate()
        eq_(self.canary, ['1', '2'])
        assert el.valid
        assert not el.all_valid

    def test_paired2(self):
        schema = Dict.of(Integer).using(
            descent_validators=[self.validator('1', False)],
            validators=[self.validator('2', True)])
        el = schema()
        assert not el.validate()
        eq_(self.canary, ['1', '2'])
        assert not el.valid
        assert not el.all_valid

    def test_paired3(self):
        schema = (
            Dict.of(
                Integer.using(validators=[self.validator('2', True)])).
            using(
                descent_validators=[self.validator('1', True)],
                validators=[self.validator('3', True)]))
        el = schema()
        assert el.validate()
        eq_(self.canary, ['1', '2', '3'])
        assert el.valid
        assert el.all_valid

    def test_shortcircuit_down_true(self):
        schema = (
            Dict.of(
                Integer.using(validators=[self.validator('2', False)])).
            using(
                descent_validators=[self.validator('1', SkipAll)],
                validators=[self.validator('3', True)]))
        el = schema()
        assert el.validate()
        eq_(self.canary, ['1', '3'])
        assert el.valid
        assert el.all_valid

    def test_shortcircuit_down_false(self):
        schema = (
            Dict.of(
                Integer.named(u'i').using(
                    validators=[self.validator('2', True)])).
            using(descent_validators=[self.validator('1', SkipAllFalse)],
                  validators=[self.validator('3', True)]))
        el = schema()
        assert not el.validate()
        eq_(self.canary, ['1', '3'])
        assert not el.valid
        assert not el.all_valid
        assert el[u'i'].valid is Unevaluated

    def test_shortcircuit_up(self):
        schema = (
            Dict.of(
                Integer.using(validators=[self.validator('2', True)])).
            using(
                descent_validators=[self.validator('1', True)],
                validators=[self.validator('3', SkipAll)]))
        el = schema()
        assert el.validate()
        eq_(self.canary, ['1', '2', '3'])
        assert el.valid
        assert el.all_valid


def test_sequence():
    schema = Sequence.named(u's')
    assert hasattr(schema, 'member_schema')


def test_mixed_all_children():
    data = {u'A1': u'1',
            u'A2': u'2',
            u'A3': {u'A3B1': {u'A3B1C1': u'1',
                              u'A3B1C2': u'2'},
                    u'A3B2': {u'A3B2C1': u'1'},
                    u'A3B3': [[u'A3B3C0D0', u'A3B3C0D1'],
                             [u'A3B3C1D0', u'A3B3C1D1'],
                             [u'A3B3C2D0', u'A3B3C2D1']]}}

    schema = (
        Dict.named(u'R').of(
            String.named(u'A1'),
            String.named(u'A2'),
            Dict.named(u'A3').of(
                Dict.named(u'A3B1').of(
                    String.named(u'A3B1C1'),
                    String.named(u'A3B1C2')),
                Dict.named(u'A3B2').of(
                    String.named(u'A3B2C1')),
                List.named(u'A3B3').of(
                    List.named(u'A3B3Cx').of(
                        String.named(u'A3B3x'))))))

    top = schema(data)

    names = list(e.name for e in top.all_children)

    assert set(names[0:3]) == set([u'A1', u'A2', u'A3'])
    assert set(names[3:6]) == set([u'A3B1', u'A3B2', u'A3B3'])
    assert set(names[6:12]) == set([u'A3B1C1', u'A3B1C2',
                                    u'A3B2C1', u'A3B3Cx'])
    assert set(names[12:]) == set([u'A3B3x'])
    assert len(names[12:]) == 6


def test_corrupt_all_children():
    # Ensure all_children won't spin out if the graph becomes cyclic.
    schema = List.of(String)
    el = schema()

    el.append(String(u'x'))
    el.append(String(u'y'))
    dupe = String(u'z')
    el.append(dupe)
    el.append(dupe)

    assert list(_.value for _ in el.children) == list(u'xyzz')
    assert list(_.value for _ in el.all_children) == list(u'xyz')


def test_naming_bogus():
    e = String(name=u's')

    assert e.el(u'.') is e
    assert_raises(LookupError, e.el, u'')
    assert_raises(TypeError, e.el, None)
    assert_raises(LookupError, e.el, ())
    assert_raises(LookupError, e.el, iter(()))
    assert_raises(TypeError, e.el)


def test_naming_shallow():
    root = String(name=u's')
    assert root.fq_name() == u'.'
    assert root.flattened_name() == u's'
    assert root.el(u'.') is root

    root = String(name=None)
    assert root.fq_name() == u'.'
    assert root.flattened_name() == u''
    assert root.el(u'.') is root
    assert_raises(LookupError, root.el, ())
    assert root.el([Root]) is root


def test_naming_dict():
    for name, root_flat, leaf_flat in ((u'd', u'd', u'd_s'),
                                       (None, u'', u's')):
        schema = Dict.named(name).of(String.named(u's'))
        root = schema()
        leaf = root[u's']

        assert root.fq_name() == u'.'
        assert root.flattened_name() == root_flat
        assert root.el(u'.') is root

        assert leaf.fq_name() == u'.s'
        assert leaf.flattened_name() == leaf_flat
        assert root.el(u'.s') is leaf
        assert root.el(u's') is leaf
        assert leaf.el(u'.s') is leaf
        assert_raises(LookupError, leaf.el, u's')
        assert leaf.el(u'.') is root

        assert root.el([Root]) is root
        assert root.el([u's']) is leaf
        assert root.el([Root, u's']) is leaf
        assert root.el(iter([u's'])) is leaf
        assert root.el(iter([Root, u's'])) is leaf


def test_naming_dict_dict():
    for name, root_flat, leaf_flat in ((u'd', u'd', u'd_d2_s'),
                                       (None, u'', u'd2_s')):
        schema = Dict.named(name).of(
            Dict.named(u'd2').of(String.named(u's')))
        root = schema()
        leaf = root[u'd2'][u's']

        assert root.fq_name() == u'.'
        assert root.flattened_name() == root_flat
        assert root.el(u'.') is root

        assert leaf.fq_name() == u'.d2.s'
        assert leaf.flattened_name() == leaf_flat
        assert root.el(u'.d2.s') is leaf
        assert root.el(u'd2.s') is leaf
        assert leaf.el(u'.d2.s') is leaf
        assert_raises(LookupError, leaf.el, u'd2.s')
        assert leaf.el(u'.') is root

        assert root.el([u'd2', u's']) is leaf


def test_naming_list():
    for name, root_flat, leaf_flat in ((u'l', u'l', u'l_0_s'),
                                       (None, u'', u'0_s')):
        schema = List.named(name).of(String.named(u's'))
        root = schema([u'x'])
        leaf = root[0]

        assert root.fq_name() == u'.'
        assert root.flattened_name() == root_flat
        assert root.el(u'.') is root

        assert leaf.fq_name() == u'.0'
        assert leaf.flattened_name() == leaf_flat
        assert root.el(u'.0') is leaf
        assert root.el(u'0') is leaf
        assert leaf.el(u'.0') is leaf
        assert_raises(LookupError, leaf.el, u'0')
        assert_raises(LookupError, leaf.el, u's')
        assert leaf.el(u'.') is root

        assert root.el([u'0']) is leaf


def test_naming_list_list():
    # make sure nested Slots-users don't bork
    for name, root_flat, leaf_flat in ((u'l', u'l', u'l_0_l2_0_s'),
                                       (None, u'', u'0_l2_0_s')):
        schema = List.named(name).of(List.named(u'l2').of(String.named(u's')))

        root = schema([u'x'])
        leaf = root[0][0]

        assert root.fq_name() == u'.'
        assert root.flattened_name() == root_flat
        assert root.el(u'.') is root

        assert leaf.fq_name() == u'.0.0'
        assert leaf.flattened_name() == leaf_flat
        assert root.el(u'.0.0') is leaf
        assert root.el(u'0.0') is leaf
        assert leaf.el(u'.0.0') is leaf
        assert_raises(LookupError, leaf.el, u'0')
        assert_raises(LookupError, leaf.el, u's')
        assert leaf.el(u'.') is root

        assert root.el([u'0', u'0']) is leaf

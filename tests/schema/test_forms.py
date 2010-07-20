from flatland import (
    Form,
    Integer,
    String,
    )

from tests._util import eq_, requires_unicode_coercion


@requires_unicode_coercion
def test_from_object():

    class Obj(object):

        def __init__(self, **kw):
            for (k, v) in kw.items():
                setattr(self, k, v)

    class Schema(Form):
        x = String
        y = String

    from_obj = lambda obj, **kw: Schema.from_object(obj, **kw).value

    eq_(from_obj(None), dict(x=None, y=None))
    eq_(from_obj([]), dict(x=None, y=None))
    eq_(from_obj(123), dict(x=None, y=None))

    eq_(from_obj(Obj()), dict(x=None, y=None))

    eq_(from_obj(Obj(x='x!')), dict(x='x!', y=None))
    eq_(from_obj(Obj(x='x!', y='y!')), dict(x='x!', y='y!'))
    eq_(from_obj(Obj(x='x!', z='z!')), dict(x='x!', y=None))

    eq_(from_obj(Obj(x='x!', y='y!'), include=['x']),
        dict(x='x!', y=None))
    eq_(from_obj(Obj(x='x!', y='y!'), omit=['y']),
        dict(x='x!', y=None))

    eq_(from_obj(Obj(x='x!', z='z!'), rename={'z': 'y'}),
        dict(x='x!', y='z!'))

    eq_(from_obj(Obj(x='x!', z='z!'), rename={'z': 'x'}),
        dict(x='z!', y=None))

    eq_(from_obj(Obj(x='x!', z='z!'), rename={'z': 'z'}),
        dict(x='x!', y=None))

    eq_(from_obj(Obj(x='x!', z='z!'), rename={'x': 'z'}),
        dict(x=None, y=None))


@requires_unicode_coercion
def test_composition():

    class Inner(Form):
        sound = String.using(default='bleep')

    class Outer(Form):
        the_in = Inner
        way_out = String.using(default='mooooog')

    unset = {'the_in': {'sound': None}, 'way_out': None}
    wanted = {'the_in': {'sound': 'bleep'}, 'way_out': 'mooooog'}

    el = Outer.from_defaults()
    eq_(el.value, wanted)

    el = Outer()
    eq_(el.value, unset)

    el.set(wanted)
    eq_(el.value, wanted)


@requires_unicode_coercion
def test_inheritance_straight():

    class Base(Form):
        base_member = String

    assert len(Base.field_schema) == 1
    assert Base().keys() == ['base_member']

    class Sub(Base):
        added_member = String

    assert len(Base.field_schema) == 1
    assert Base().keys() == ['base_member']

    assert len(Sub.field_schema) == 2
    assert set(Sub().keys()) == set(['base_member', 'added_member'])


@requires_unicode_coercion
def test_inheritance_diamond():

    class A(Form):
        a_member = String

    class B(Form):
        b_member = String

    class AB1(A, B):
        pass

    class BA1(B, A):
        pass

    for cls in AB1, BA1:
        assert len(cls.field_schema) == 2
        assert set(cls().keys()) == set(['a_member', 'b_member'])

    class AB2(A, B):
        ab_member = String

    assert len(AB2.field_schema) == 3
    assert set(AB2().keys()) == set(['a_member', 'b_member', 'ab_member'])

    class AB3(A, B):
        a_member = Integer

    assert len(AB3.field_schema) == 2
    assert isinstance(AB3()['a_member'], Integer)

    class BA2(B, A):
        a_member = Integer
        b_member = Integer

    assert len(BA2.field_schema) == 2
    assert isinstance(BA2()['a_member'], Integer)
    assert isinstance(BA2()['b_member'], Integer)

    class BA3(B, A):
        field_schema = [Integer.named('b_member')]

        a_member = Integer

    assert len(BA3.field_schema) == 2
    assert isinstance(BA3()['a_member'], Integer)
    assert isinstance(BA3()['b_member'], Integer)

    class BA4(B, A):
        field_schema = [Integer.named('ab_member')]

        ab_member = String

    assert len(BA4.field_schema) == 3
    assert isinstance(BA4()['ab_member'], String)

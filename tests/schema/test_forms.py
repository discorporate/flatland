from flatland import (
    Form,
    String,
    )

from tests._util import eq_


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

    el = Outer.create_blank()
    eq_(el.value, unset)

    el.set(wanted)
    eq_(el.value, wanted)

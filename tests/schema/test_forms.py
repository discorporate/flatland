from nose.tools import eq_, assert_raises, set_trace

from flatland import schema


def test_from_object():
    class Obj(object):
        def __init__(self, **kw):
            for (k, v) in kw.items():
                setattr(self, k, v)

    class Form(schema.Form):
        schema = [schema.String('x'),
                  schema.String('y')]

    from_obj = lambda obj, **kw: Form.from_object(obj, **kw).value

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


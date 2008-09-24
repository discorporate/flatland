import flatland as fl
from flatland import valid


class GetTextish(object):
    catalog = {
        u'%(label)s is not correct.':
            u'reg %(label)s',

        u'%(label)s may not exceed %(maxlength)s characters.':
            u'default %(label)s %(maxlength)s',

        u'%(label)s max is %(maxlength)s characters.':
            u'plural %(label)s %(maxlength)s',

        u'%(label)s max is %(maxlength)s character.':
            u'single %(label)s %(maxlength)s',

        u'age': u'AGE',
        u'name': u'NAME',
        }

    def ugettext(self, text):
        try:
            return self.catalog[text]
        except KeyError:
            return text

    def ungettext(self, single, plural, n):
        lookup = single if n == 1 else plural
        return self.ugettext(lookup)


class LocalizedShort(valid.NoLongerThan):
    exceeded = (u'%(label)s max is %(maxlength)s character.',
                u'%(label)s max is %(maxlength)s characters.',
                'maxlength')


def test_regular_gettext():
    catalog = GetTextish()
    root = fl.Dict('root',
                   fl.String('age', validators=[valid.Converted()]),
                   ugettext=catalog.ugettext,
                   ungettext=catalog.ungettext)

    data = root.create_element()
    data.validate()
    assert data['age'].errors == [u'reg AGE']

def test_local_gettext():
    catalog = GetTextish()
    root = fl.Dict('root',
                   fl.String('age', validators=[valid.Converted()],
                             ugettext=catalog.ugettext,
                             ungettext=catalog.ungettext))

    data = root.create_element()
    data.validate()
    assert data['age'].errors == [u'reg AGE']

def test_local_gettext_search_is_not_overeager():
    catalog = GetTextish()
    def poision(*a):
        assert False

    root = fl.Dict('root',
                   fl.String('age', validators=[valid.Converted()],
                             ugettext=catalog.ugettext,
                             ungettext=catalog.ungettext),
                   ugettext=catalog.ugettext,
                   ungettext=catalog.ungettext)

    data = root.create_element()
    data.validate()
    assert data['age'].errors == [u'reg AGE']

def test_builtin_gettext():
    catalog = GetTextish()
    root = fl.Dict('root',
                   fl.String('age', validators=[valid.Converted()]))

    data = root.create_element()
    try:
        import __builtin__
        __builtin__.ugettext = catalog.ugettext
        __builtin__.ungettext = catalog.ungettext
        data.validate()
        assert data['age'].errors == [u'reg AGE']
    finally:
        del __builtin__.ugettext
        del __builtin__.ungettext

def test_tuple_single():
    catalog = GetTextish()
    root = fl.Dict('root',
                   fl.String('name', validators=[LocalizedShort(1)]),
                   ugettext=catalog.ugettext,
                   ungettext=catalog.ungettext)

    data = root.from_value(dict(name='xxx'))
    data.validate()
    assert data['name'].errors == [u'single NAME 1']

def test_tuple_plural():
    catalog = GetTextish()
    root = fl.Dict('root',
                   fl.String('name', validators=[LocalizedShort(2)]),
                   ugettext=catalog.ugettext,
                   ungettext=catalog.ungettext)

    data = root.from_value(dict(name='xxx'))
    data.validate()
    assert data['name'].errors == [u'plural NAME 2']


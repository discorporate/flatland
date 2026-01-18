from flatland import Array, Boolean, Integer
from flatland.out import generic
from flatland.out.generic import Context

from tests._util import unicode_coercion_allowed, textstr


Unspecified = object()
Unique = object()
schema = Integer.named('number')
boolean_schema = Boolean.named('bool')
partial_anon_schema = Array.named('array').of(Integer)
full_anon_schema = Array.of(Integer)


def assert_bound_transform(fn, tagname, given, expected, **kw):
    return assert_transform(fn, tagname, given, expected, **kw)


def assert_unbound_transform(fn, tagname, given, expected, **kw):
    kw['bind'] = None
    return assert_transform(fn, tagname, given, expected, **kw)


def assert_transform(fn, tagname, given, expected,
                     context=Unspecified,
                     bind=Unspecified,
                     contents=Unspecified,
                     expected_contents=Unspecified):
    if context is Unspecified:
        context = Context()
    if bind is Unspecified:
        bind = schema(123)

    got = given.copy()
    got_contents = fn(tagname, got, contents, context, bind)
    assert got == expected
    assert (got_contents is expected_contents or
            got_contents == expected_contents)

    types = zip(sorted(got.keys()), sorted(expected.keys()))
    for got_key, expected_key in types:
        assert type(got_key) is type(expected_key)


class _TestAttributeTransform:
    attribute = NotImplemented
    applied_value = NotImplemented
    control_attribute = NotImplemented
    tagname = NotImplemented
    skip_tags = ()
    operates_on_unbound = False

    bind_factory = lambda: schema(123)
    transform = NotImplemented
    base_context = ()

    def assert_transform(self, given, expected,
                         context=None,
                         tagname=None,
                         bind=Unspecified):
        if hasattr(self.transform, '__func__'):
            transform = self.transform.__func__
        else:
            transform = self.transform
        if context is None:
            context = self._context()
        if tagname is None:
            tagname = self.tagname
        if bind is Unspecified:
            if hasattr(self.bind_factory, '__func__'):
                bind = self.bind_factory.__func__()
            else:
                bind = self.bind_factory()

        assert_transform(transform, tagname, given, expected, context, bind)

    def _context(self, overrides=()):
        context = Context()
        context.push()
        context.update(self.base_context)
        context.update(overrides)
        return context

    def test_known_tag(self):
        given = {}
        if generic._default_context[self.control_attribute] is True:
            expected = {self.attribute: self.applied_value}
        elif generic._default_context[self.control_attribute] is False:
            expected = {}
        else:
            raise AssertionError

        for tagname in generic._auto_tags[self.attribute]:
            if tagname in self.skip_tags:
                continue
            self.assert_transform(given, expected, None, tagname)

    def test_unknown_tag(self):
        given = {}
        expected = {}
        self.assert_transform(given, expected, tagname='xyzzy')

    def test_unknown_tag_existing_value_unchanged(self):
        given = {self.attribute: 'existing'}
        expected = {self.attribute: 'existing'}
        self.assert_transform(given, expected, tagname='xyzzy')

    def test_existing_value_unchanged(self):
        given = {self.attribute: 'local'}
        expected = {self.attribute: 'local'}
        self.assert_transform(given, expected)

    def test_existing_value_force_changed(self):
        given = {self.attribute: 'local', self.control_attribute: 'on'}
        expected = {self.attribute: self.applied_value}
        self.assert_transform(given, expected)

    def test_context_off(self):
        given = {}
        expected = {}
        context = self._context({self.control_attribute: False})
        self.assert_transform(given, expected, context=context)

    def test_context_on(self):
        given = {}
        expected = {self.attribute: self.applied_value}
        context = self._context({self.control_attribute: True})
        self.assert_transform(given, expected, context=context)

    def test_context_on_unknown_tag(self):
        given = {}
        expected = {}
        context = self._context({self.control_attribute: True})
        self.assert_transform(given, expected,
                              context=context, tagname='xyzzy')

    def test_context_auto(self):
        given = {}
        default = generic._default_context[self.control_attribute]
        if default is True:
            expected = {self.attribute: self.applied_value}
        elif default is False:
            expected = {}
        else:
            raise AssertionError()
        context = self._context({self.control_attribute: 'auto'})
        self.assert_transform(given, expected, context=context)

    def test_local_off(self):
        given = {self.control_attribute: False}
        expected = {}
        self.assert_transform(given, expected)

    def test_local_on(self):
        given = {self.control_attribute: True}
        expected = {self.attribute: self.applied_value}
        context = self._context({self.control_attribute: False})
        self.assert_transform(given, expected, context=context)

    def test_local_auto(self):
        given = {self.control_attribute: 'auto'}
        expected = {self.attribute: self.applied_value}
        context = self._context({self.control_attribute: True})
        self.assert_transform(given, expected, context=context)

        expected = {}
        context = self._context({self.control_attribute: False})
        self.assert_transform(given, expected, context=context)

    def test_local_on_unbound(self):
        # some can't be forced unless a bind is also present
        given = {self.control_attribute: True}
        if self.operates_on_unbound:
            expected = {self.attribute: self.applied_value}
        else:
            expected = {}
        self.assert_transform(given, expected, bind=None)


class TestName(_TestAttributeTransform):
    attribute = 'name'
    control_attribute = 'auto_name'
    applied_value = 'number'
    transform = generic.transform_name
    tagname = 'input'


# basic smoke test for context issues only
class TestTextboxValue(_TestAttributeTransform):
    attribute = 'value'
    control_attribute = 'auto_value'
    applied_value = '123'
    transform = generic.transform_value
    tagname = 'input'
    skip_tags = ['textarea', 'option']


class TestButtonValue(_TestAttributeTransform):
    attribute = 'value'
    control_attribute = 'auto_value'
    applied_value = '123'
    transform = generic.transform_value
    tagname = 'button'
    skip_tags = ['textarea', 'option']


class TestDomID(_TestAttributeTransform):
    attribute = 'id'
    control_attribute = 'auto_domid'
    applied_value = 'f_number'
    transform = generic.transform_domid
    tagname = 'input'


class TestFor(_TestAttributeTransform):
    attribute = 'for'
    control_attribute = 'auto_for'
    applied_value = 'f_number'
    transform = generic.transform_for
    tagname = 'label'


class TestTabindex(_TestAttributeTransform):
    attribute = 'tabindex'
    control_attribute = 'auto_tabindex'
    applied_value = '5'
    operates_on_unbound = True
    transform = generic.transform_tabindex
    tagname = 'input'
    base_context = {'tabindex': 5}


def test_name_anonymous_bind():
    bind = partial_anon_schema([123])[0]
    given = {}
    expected = {'name': 'array'}
    assert_transform(generic.transform_name,
                     'input', given, expected, bind=bind)

    bind = full_anon_schema([123])[0]
    given = {}
    expected = {}
    assert_transform(generic.transform_name,
                     'input', given, expected, bind=bind)


def test_contents_textarea():
    given = None
    expected = '123'
    assert_bound_transform(generic.transform_value,
                           'textarea', {}, {},
                           contents=given, expected_contents=expected)

    for given in 'existing_value', '', generic.Markup('xyzzy'), []:
        expected = given
        assert_bound_transform(generic.transform_value,
                               'textarea', {}, {},
                               contents=given, expected_contents=expected)


def test_value_checkable():
    # check Scalar(..) and Array.of(..)
    for bind in schema(123), partial_anon_schema([123, 456]):
        for type in 'checkbox', 'radio':
            given = {
                'type': type,
                'value': '123',
                }
            expected = {
                'type': type,
                'value': '123',
                'checked': 'checked',
                }
            assert_transform(generic.transform_value,
                             'input', given, expected, bind=bind)

            given = {
                'type': type,
                'value': '999',
                }
            expected = {
                'type': type,
                'value': '999',
                }
            assert_transform(generic.transform_value,
                             'input', given, expected, bind=bind)

            given = {
                'type': type,
                'value': '999',
                'checked': 'checked',
                }
            expected = {
                'type': type,
                'value': '999',
                }
            assert_transform(generic.transform_value,
                             'input', given, expected, bind=bind)

            given = {
                'type': type,
                'value': '999',
                'checked': '',
                }
            expected = {
                'type': type,
                'value': '999',
                }
            assert_transform(generic.transform_value,
                             'input', given, expected, bind=bind)


def test_value_checkbox_boolean():
    bind = boolean_schema(True)
    given = {
        'type': 'checkbox',
        }
    expected = {
        'type': 'checkbox',
        'value': '1',
        'checked': 'checked',
        }
    assert_transform(generic.transform_value,
                     'input', given, expected, bind=bind)

    bind = boolean_schema(False)
    given = {
        'type': 'checkbox',
        }
    expected = {
        'type': 'checkbox',
        'value': '1',
        }
    assert_transform(generic.transform_value,
                     'input', given, expected, bind=bind)

    bind = boolean_schema(True)
    given = {
        'type': 'checkbox',
        'value': '2',
        }
    expected = {
        'type': 'checkbox',
        'value': '2',
        }
    assert_transform(generic.transform_value,
                     'input', given, expected, bind=bind)


def test_value_omitted():
    bind = schema(123)

    for type in 'password', 'file', 'image':
        given = {
            'type': type,
            }
        expected = {
            'type': type,
            }
        assert_transform(generic.transform_value,
                         'input', given, expected, bind=bind)
        given = {
            'type': type,
            'value': '999',
            }
        expected = {
            'type': type,
            'value': '999',
            }
        assert_transform(generic.transform_value,
                         'input', given, expected, bind=bind)
        given = {
            'type': type,
            'auto_value': True,
            }
        expected = {
            'type': type,
            'value': '123',
            }
        assert_transform(generic.transform_value,
                         'input', given, expected, bind=bind)

        given = {
            'type': type,
            'auto_value': True,
            'value': '999',
            }
        expected = {
            'type': type,
            'value': '123',
            }
        assert_transform(generic.transform_value,
                         'input', given, expected, bind=bind)


def test_value_option():
 # check Scalar(..) and Array.of(..)
    for bind in schema(123), partial_anon_schema([123, 456]):
        given = {
            'value': '123',
            }
        expected = {
            'value': '123',
            'selected': 'selected',
            }
        assert_transform(generic.transform_value,
                         'option', given, expected, bind=bind)

        given = {
            'value': '999',
            }
        expected = {
            'value': '999',
            }
        assert_transform(generic.transform_value,
                         'option', given, expected, bind=bind)

        contents = expected_contents = '123'
        given = {
            }
        expected = {
            'selected': 'selected',
            }
        assert_transform(generic.transform_value,
                         'option', given, expected, bind=bind,
                         contents=contents,
                         expected_contents=expected_contents)

        contents = expected_contents = '    123     '
        given = {
            }
        expected = {
            'selected': 'selected',
            }
        assert_transform(generic.transform_value,
                         'option', given, expected, bind=bind,
                         contents=contents,
                         expected_contents=expected_contents)

        contents = expected_contents = '999'
        given = {
            }
        expected = {
            }
        assert_transform(generic.transform_value,
                         'option', given, expected, bind=bind,
                         contents=contents,
                         expected_contents=expected_contents)

        contents = expected_contents = None
        given = {
            }
        expected = {
            }
        assert_transform(generic.transform_value,
                         'option', given, expected, bind=bind,
                         contents=contents,
                         expected_contents=expected_contents)

        # This matches value = contents via a sentinel object
        with unicode_coercion_allowed():
            given = {
                }
            expected = {
                }
            assert_transform(generic.transform_value,
                             'option', given, expected, bind=bind)

        contents = expected_contents = '123'
        given = {
            'value': '999',
            }
        expected = {
            'value': '999',
            }
        assert_transform(generic.transform_value,
                         'option', given, expected, bind=bind,
                         contents=contents,
                         expected_contents=expected_contents)

        given = {
            'value': '999',
            'selected': 'selected',
            }
        expected = {
            'value': '999',
            }
        assert_transform(generic.transform_value,
                         'option', given, expected, bind=bind)

        given = {
            'value': '999',
            'selected': '',
            }
        expected = {
            'value': '999',
            }
        assert_transform(generic.transform_value,
                         'option', given, expected, bind=bind)


def test_domid_checkable_array():
    bind = partial_anon_schema([123, 456])
    context = Context()
    context['auto_domid'] = True

    assert_ = lambda given, expected: assert_transform(
        generic.transform_domid, 'input', given, expected,
        context=context, bind=bind)

    for type in 'radio', 'checkbox':
        given = {
            'type': 'radio',
            'value': 'xxx',
            }
        expected = {
            'type': 'radio',
            'value': 'xxx',
            'id': 'f_array_xxx',
            }
        assert_(given, expected)

        given = {
            'type': 'radio',
            }
        expected = {
            'type': 'radio',
            'id': 'f_array',
            }
        assert_(given, expected)

        given = {
            'type': 'radio',
            'value': 'Ḑộộḏ!',
            }
        expected = {
            'type': 'radio',
            'value': 'Ḑộộḏ!',
            'id': 'f_array',
            }
        assert_(given, expected)

        given = {
            'type': 'radio',
            'value': 'Ḑộộḏ! yo',
            }
        expected = {
            'type': 'radio',
            'value': 'Ḑộộḏ! yo',
            'id': 'f_array_yo',
            }
        assert_(given, expected)


def test_domid_checkable_scalar():
    context = Context()
    context['auto_domid'] = True

    for type in 'radio', 'checkbox':
        given = {
            'type': 'radio',
            'value': 'xxx',
            }
        expected = {
            'type': 'radio',
            'value': 'xxx',
            'id': 'f_number_xxx',
            }
        assert_bound_transform(generic.transform_domid,
                               'input', given, expected, context=context)


def test_domid_anonymous_bind():
    bind = partial_anon_schema([123])[0]
    given = {'auto_domid': True}
    expected = {'id': 'f_array'}
    assert_transform(generic.transform_domid,
                     'input', given, expected, bind=bind)

    bind = full_anon_schema([123])[0]
    given = {'auto_domid': True}
    expected = {}
    assert_transform(generic.transform_domid,
                     'input', given, expected, bind=bind)


def test_domid_unbound_naming():
    given = {'name': 'unbound',
             'auto_domid': 'on'}
    expected = {'id': 'f_unbound', 'name': 'unbound'}
    assert_unbound_transform(generic.transform_domid,
                             'input', given, expected)


def test_domid_custom_formatting():
    context = Context()
    context['domid_format'] = '--%s--'
    given = {'auto_domid': 'on'}
    expected = {'id': '--number--'}
    assert_bound_transform(generic.transform_domid,
                           'input', given, expected, context=context)


def test_for_anonymous_bind():
    bind = partial_anon_schema([123])[0]
    given = {'auto_for': True}
    expected = {'for': 'f_array'}
    assert_transform(generic.transform_for,
                     'label', given, expected, bind=bind)

    bind = full_anon_schema([123])[0]
    given = {'auto_for': True}
    expected = {}
    assert_transform(generic.transform_for,
                     'label', given, expected, bind=bind)


def test_tabindex_stop_numbers():
    given = {'auto_tabindex': 'on'}

    for stop_num in -1, -2:
        context = Context()
        context['tabindex'] = stop_num
        expected = {'tabindex': textstr(stop_num)}
        assert_bound_transform(generic.transform_tabindex,
                               'input', given, expected, context=context)
        assert_unbound_transform(generic.transform_tabindex,
                                 'input', given, expected, context=context)
        assert context['tabindex'] == stop_num


def test_tabindex_zero():
    given = {}
    context = Context()
    context['auto_tabindex'] = True
    context['tabindex'] = 0

    expected = {}
    assert_unbound_transform(generic.transform_tabindex,
                             'input', given, expected, context=context)


def test_tabindex_increment():
    given = {}
    context = Context()
    context['auto_tabindex'] = True
    context['tabindex'] = 1

    expected = {'tabindex': '1'}
    assert_unbound_transform(generic.transform_tabindex,
                             'input', given, expected, context=context)

    expected = {'tabindex': '2'}
    assert_unbound_transform(generic.transform_tabindex,
                             'input', given, expected, context=context)

    assert context['tabindex'] != 1


def test_filter():

    given = {}

    def filter1(tagname, attributes, contents, context, bind):
        attributes['donut'] = 'xyzzy'
        return contents

    context = Context()
    context['auto_filter'] = True
    context['filters'] = [filter1]

    expected = {
        'donut': 'xyzzy',
        }
    assert_bound_transform(generic.transform_filters,
                           'div', given, expected, context=context)

    def filter2(tagname, attributes, contents, context, bind):
        return bind.label

    context = Context()
    context['auto_filter'] = True
    context['filters'] = [filter2, filter1]
    contents = 'bbq'
    expected_contents = 'number'

    expected = {
        'donut': 'xyzzy',
        }
    assert_bound_transform(generic.transform_filters,
                           'div', given, expected, context=context,
                           contents=contents,
                           expected_contents=expected_contents)

    context = Context()
    context['auto_filter'] = True
    context['filters'] = ()
    contents = 'bbq'
    expected_contents = 'bbq'

    expected = {}
    assert_bound_transform(generic.transform_filters,
                           'div', given, expected, context=context,
                           contents=contents,
                           expected_contents=expected_contents)


def test_filter_want():

    def filter1(tagname, attributes, contents, context, bind):
        attributes['donut'] = 'xyzzy'
        return contents

    filter1.tags = ['div', 'input']

    for tag in 'div', 'input':
        context = Context()
        context['auto_filter'] = True
        context['filters'] = [filter1]
        given = {}
        expected = {
            'donut': 'xyzzy',
            }
        assert_bound_transform(generic.transform_filters,
                           tag, given, expected, context=context)


    context = Context()
    context['auto_filter'] = True
    context['filters'] = [filter1]
    given = {}
    expected = {}
    assert_bound_transform(generic.transform_filters,
                           'horse', given, expected, context=context)

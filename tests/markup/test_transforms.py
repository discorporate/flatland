#! -*- coding: utf-8 -*-
from flatland import Array, Boolean, Integer
from flatland.out import generic
from flatland.out.generic import Context


Unspecified = object()
Unique = object()
schema = Integer.named(u'number')
boolean_schema = Boolean.named(u'bool')
partial_anon_schema = Array.named(u'array').of(Integer)
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
    assert got_contents == expected_contents

    types = zip(sorted(got.keys()), sorted(expected.keys()))
    for got_key, expected_key in types:
        assert type(got_key) is type(expected_key)


class _TestAttributeTransform(object):
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
        if hasattr(self.transform, 'im_func'):
            transform = self.transform.im_func
        else:
            transform = self.transform
        if context is None:
            context = self._context()
        if tagname is None:
            tagname = self.tagname
        if bind is Unspecified:
            if hasattr(self.bind_factory, 'im_func'):
                bind = self.bind_factory.im_func()
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
            yield self.assert_transform, given, expected, None, tagname

    def test_unknown_tag(self):
        given = {}
        expected = {}
        self.assert_transform(given, expected, tagname=u'xyzzy')

    def test_unknown_tag_existing_value_unchanged(self):
        given = {self.attribute: u'existing'}
        expected = {self.attribute: u'existing'}
        self.assert_transform(given, expected, tagname=u'xyzzy')

    def test_existing_value_unchanged(self):
        given = {self.attribute: u'local'}
        expected = {self.attribute: u'local'}
        self.assert_transform(given, expected)

    def test_existing_value_force_changed(self):
        given = {self.attribute: u'local', self.control_attribute: u'on'}
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
                              context=context, tagname=u'xyzzy')

    def test_context_auto(self):
        given = {}
        default = generic._default_context[self.control_attribute]
        if default is True:
            expected = {self.attribute: self.applied_value}
        elif default is False:
            expected = {}
        else:
            raise AssertionError()
        context = self._context({self.control_attribute: u'auto'})
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
        given = {self.control_attribute: u'auto'}
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
    attribute = u'name'
    control_attribute = u'auto_name'
    applied_value = u'number'
    transform = generic.transform_name
    tagname = u'input'


# basic smoke test for context issues only
class TestTextboxValue(_TestAttributeTransform):
    attribute = u'value'
    control_attribute = u'auto_value'
    applied_value = u'123'
    transform = generic.transform_value
    tagname = u'input'
    skip_tags = ['textarea', 'option']


class TestButtonValue(_TestAttributeTransform):
    attribute = u'value'
    control_attribute = u'auto_value'
    applied_value = u'123'
    transform = generic.transform_value
    tagname = u'button'
    skip_tags = ['textarea', 'option']


class TestDomID(_TestAttributeTransform):
    attribute = u'id'
    control_attribute = u'auto_domid'
    applied_value = u'f_number'
    transform = generic.transform_domid
    tagname = u'input'


class TestFor(_TestAttributeTransform):
    attribute = u'for'
    control_attribute = u'auto_for'
    applied_value = u'f_number'
    transform = generic.transform_for
    tagname = u'label'


class TestTabindex(_TestAttributeTransform):
    attribute = u'tabindex'
    control_attribute = u'auto_tabindex'
    applied_value = u'5'
    operates_on_unbound = True
    transform = generic.transform_tabindex
    tagname = u'input'
    base_context = {u'tabindex': 5}


def test_name_anonymous_bind():
    bind = partial_anon_schema([123])[0]
    given = {}
    expected = {u'name': u'array'}
    assert_transform(generic.transform_name,
                     u'input', given, expected, bind=bind)

    bind = full_anon_schema([123])[0]
    given = {}
    expected = {}
    assert_transform(generic.transform_name,
                     u'input', given, expected, bind=bind)


def test_contents_textarea():
    given = None
    expected = u'123'
    assert_bound_transform(generic.transform_value,
                           u'textarea', {}, {},
                           contents=given, expected_contents=expected)

    for given in u'existing_value', u'', generic.Markup('xyzzy'), []:
        expected = given
        assert_bound_transform(generic.transform_value,
                               u'textarea', {}, {},
                               contents=given, expected_contents=expected)


def test_value_checkable():
    # check Scalar(..) and Array.of(..)
    for bind in schema(123), partial_anon_schema([123, 456]):
        for type in u'checkbox', u'radio':
            given = {
                u'type': type,
                u'value': u'123',
                }
            expected = {
                u'type': type,
                u'value': u'123',
                u'checked': u'checked',
                }
            assert_transform(generic.transform_value,
                             u'input', given, expected, bind=bind)

            given = {
                u'type': type,
                u'value': u'999',
                }
            expected = {
                u'type': type,
                u'value': u'999',
                }
            assert_transform(generic.transform_value,
                             u'input', given, expected, bind=bind)

            given = {
                u'type': type,
                u'value': u'999',
                u'checked': u'checked',
                }
            expected = {
                u'type': type,
                u'value': u'999',
                }
            assert_transform(generic.transform_value,
                             u'input', given, expected, bind=bind)

            given = {
                u'type': type,
                u'value': u'999',
                u'checked': u'',
                }
            expected = {
                u'type': type,
                u'value': u'999',
                }
            assert_transform(generic.transform_value,
                             u'input', given, expected, bind=bind)


def test_value_checkbox_boolean():
    bind = boolean_schema(True)
    given = {
        u'type': u'checkbox',
        }
    expected = {
        u'type': u'checkbox',
        u'value': u'1',
        u'checked': u'checked',
        }
    assert_transform(generic.transform_value,
                     u'input', given, expected, bind=bind)

    bind = boolean_schema(False)
    given = {
        u'type': u'checkbox',
        }
    expected = {
        u'type': u'checkbox',
        u'value': u'1',
        }
    assert_transform(generic.transform_value,
                     u'input', given, expected, bind=bind)

    bind = boolean_schema(True)
    given = {
        u'type': u'checkbox',
        u'value': u'2',
        }
    expected = {
        u'type': u'checkbox',
        u'value': u'2',
        }
    assert_transform(generic.transform_value,
                     u'input', given, expected, bind=bind)


def test_value_omitted():
    bind = schema(123)

    for type in u'password', u'file', u'image':
        given = {
            u'type': type,
            }
        expected = {
            u'type': type,
            }
        assert_transform(generic.transform_value,
                         u'input', given, expected, bind=bind)
        given = {
            u'type': type,
            u'value': u'999',
            }
        expected = {
            u'type': type,
            u'value': u'999',
            }
        assert_transform(generic.transform_value,
                         u'input', given, expected, bind=bind)
        given = {
            u'type': type,
            u'auto_value': True,
            }
        expected = {
            u'type': type,
            u'value': u'123',
            }
        assert_transform(generic.transform_value,
                         u'input', given, expected, bind=bind)

        given = {
            u'type': type,
            u'auto_value': True,
            u'value': u'999',
            }
        expected = {
            u'type': type,
            u'value': u'123',
            }
        assert_transform(generic.transform_value,
                         u'input', given, expected, bind=bind)


def test_value_option():
 # check Scalar(..) and Array.of(..)
    for bind in schema(123), partial_anon_schema([123, 456]):
        given = {
            u'value': u'123',
            }
        expected = {
            u'value': u'123',
            u'selected': u'selected',
            }
        assert_transform(generic.transform_value,
                         u'option', given, expected, bind=bind)

        given = {
            u'value': u'999',
            }
        expected = {
            u'value': u'999',
            }
        assert_transform(generic.transform_value,
                         u'option', given, expected, bind=bind)

        contents = expected_contents = u'123'
        given = {
            }
        expected = {
            u'selected': u'selected',
            }
        assert_transform(generic.transform_value,
                         u'option', given, expected, bind=bind,
                         contents=contents,
                         expected_contents=expected_contents)

        contents = expected_contents = u'    123     '
        given = {
            }
        expected = {
            u'selected': u'selected',
            }
        assert_transform(generic.transform_value,
                         u'option', given, expected, bind=bind,
                         contents=contents,
                         expected_contents=expected_contents)

        contents = expected_contents = u'999'
        given = {
            }
        expected = {
            }
        assert_transform(generic.transform_value,
                         u'option', given, expected, bind=bind,
                         contents=contents,
                         expected_contents=expected_contents)

        contents = expected_contents = None
        given = {
            }
        expected = {
            }
        assert_transform(generic.transform_value,
                         u'option', given, expected, bind=bind,
                         contents=contents,
                         expected_contents=expected_contents)

        # This matches value = contents via a sentinel object
        given = {
            }
        expected = {
            }
        assert_transform(generic.transform_value,
                         u'option', given, expected, bind=bind)

        contents = expected_contents = u'123'
        given = {
            u'value': u'999',
            }
        expected = {
            u'value': u'999',
            }
        assert_transform(generic.transform_value,
                         u'option', given, expected, bind=bind,
                         contents=contents,
                         expected_contents=expected_contents)

        given = {
            u'value': u'999',
            u'selected': u'selected',
            }
        expected = {
            u'value': u'999',
            }
        assert_transform(generic.transform_value,
                         u'option', given, expected, bind=bind)

        given = {
            u'value': u'999',
            u'selected': u'',
            }
        expected = {
            u'value': u'999',
            }
        assert_transform(generic.transform_value,
                         u'option', given, expected, bind=bind)


def test_domid_checkable_array():
    bind = partial_anon_schema([123, 456])
    context = Context()
    context[u'auto_domid'] = True

    assert_ = lambda given, expected: assert_transform(
        generic.transform_domid, u'input', given, expected,
        context=context, bind=bind)

    for type in 'radio', 'checkbox':
        given = {
            u'type': u'radio',
            u'value': u'xxx',
            }
        expected = {
            u'type': u'radio',
            u'value': u'xxx',
            u'id': u'f_array_xxx',
            }
        assert_(given, expected)

        given = {
            u'type': u'radio',
            }
        expected = {
            u'type': u'radio',
            u'id': u'f_array',
            }
        assert_(given, expected)

        given = {
            u'type': u'radio',
            u'value': u'Ḑộộḏ!',
            }
        expected = {
            u'type': u'radio',
            u'value': u'Ḑộộḏ!',
            u'id': u'f_array',
            }
        assert_(given, expected)

        given = {
            u'type': u'radio',
            u'value': u'Ḑộộḏ! yo',
            }
        expected = {
            u'type': u'radio',
            u'value': u'Ḑộộḏ! yo',
            u'id': u'f_array_yo',
            }
        assert_(given, expected)


def test_domid_checkable_scalar():
    context = Context()
    context[u'auto_domid'] = True

    for type in 'radio', 'checkbox':
        given = {
            u'type': u'radio',
            u'value': u'xxx',
            }
        expected = {
            u'type': u'radio',
            u'value': u'xxx',
            u'id': u'f_number',
            }
        assert_bound_transform(generic.transform_domid,
                               u'input', given, expected, context=context)


def test_domid_anonymous_bind():
    bind = partial_anon_schema([123])[0]
    given = {u'auto_domid': True}
    expected = {u'id': u'f_array'}
    assert_transform(generic.transform_domid,
                     u'input', given, expected, bind=bind)

    bind = full_anon_schema([123])[0]
    given = {u'auto_domid': True}
    expected = {}
    assert_transform(generic.transform_domid,
                     u'input', given, expected, bind=bind)


def test_domid_unbound_naming():
    given = {u'name': u'unbound',
             u'auto_domid': u'on'}
    expected = {u'id': u'f_unbound', u'name': u'unbound'}
    assert_unbound_transform(generic.transform_domid,
                             u'input', given, expected)


def test_domid_custom_formatting():
    context = Context()
    context[u'domid_format'] = u'--%s--'
    given = {u'auto_domid': u'on'}
    expected = {u'id': u'--number--'}
    assert_bound_transform(generic.transform_domid,
                           u'input', given, expected, context=context)


def test_for_anonymous_bind():
    bind = partial_anon_schema([123])[0]
    given = {u'auto_for': True}
    expected = {u'for': u'f_array'}
    assert_transform(generic.transform_for,
                     u'label', given, expected, bind=bind)

    bind = full_anon_schema([123])[0]
    given = {u'auto_for': True}
    expected = {}
    assert_transform(generic.transform_for,
                     u'label', given, expected, bind=bind)


def test_tabindex_stop_numbers():
    given = {u'auto_tabindex': u'on'}

    for stop_num in -1, -2:
        context = Context()
        context[u'tabindex'] = stop_num
        expected = {u'tabindex': unicode(stop_num)}
        assert_bound_transform(generic.transform_tabindex,
                               u'input', given, expected, context=context)
        assert_unbound_transform(generic.transform_tabindex,
                                 u'input', given, expected, context=context)
        assert context[u'tabindex'] == stop_num


def test_tabindex_zero():
    given = {}
    context = Context()
    context[u'auto_tabindex'] = True
    context[u'tabindex'] = 0

    expected = {}
    assert_unbound_transform(generic.transform_tabindex,
                             u'input', given, expected, context=context)


def test_tabindex_increment():
    given = {}
    context = Context()
    context[u'auto_tabindex'] = True
    context[u'tabindex'] = 1

    expected = {u'tabindex': u'1'}
    assert_unbound_transform(generic.transform_tabindex,
                             u'input', given, expected, context=context)

    expected = {u'tabindex': u'2'}
    assert_unbound_transform(generic.transform_tabindex,
                             u'input', given, expected, context=context)

    assert context[u'tabindex'] != 1


def test_filter():

    given = {}

    def filter1(tagname, attributes, contents, context, bind):
        attributes[u'donut'] = u'xyzzy'
        return contents

    context = Context()
    context[u'auto_filter'] = True
    context[u'filters'] = [filter1]

    expected = {
        u'donut': u'xyzzy',
        }
    assert_bound_transform(generic.transform_filters,
                           u'div', given, expected, context=context)

    def filter2(tagname, attributes, contents, context, bind):
        return bind.label

    context = Context()
    context[u'auto_filter'] = True
    context[u'filters'] = [filter2, filter1]
    contents = u'bbq'
    expected_contents = u'number'

    expected = {
        u'donut': u'xyzzy',
        }
    assert_bound_transform(generic.transform_filters,
                           u'div', given, expected, context=context,
                           contents=contents,
                           expected_contents=expected_contents)

    context = Context()
    context[u'auto_filter'] = True
    context[u'filters'] = ()
    contents = u'bbq'
    expected_contents = u'bbq'

    expected = {}
    assert_bound_transform(generic.transform_filters,
                           u'div', given, expected, context=context,
                           contents=contents,
                           expected_contents=expected_contents)


def test_filter_want():

    def filter1(tagname, attributes, contents, context, bind):
        attributes[u'donut'] = u'xyzzy'
        return contents

    filter1.tags = [u'div', u'input']

    for tag in u'div', u'input':
        context = Context()
        context[u'auto_filter'] = True
        context[u'filters'] = [filter1]
        given = {}
        expected = {
            u'donut': u'xyzzy',
            }
        assert_bound_transform(generic.transform_filters,
                           tag, given, expected, context=context)


    context = Context()
    context[u'auto_filter'] = True
    context[u'filters'] = [filter1]
    given = {}
    expected = {}
    assert_bound_transform(generic.transform_filters,
                           u'horse', given, expected, context=context)

from functools import wraps

from nose import SkipTest


class Capabilities(dict):

    def __missing__(self, capability):
        probe = getattr(self, '_' + capability)
        self[capability] = have = probe()
        return have

    def _genshi(self):
        try:
            from XXXgenshi.template import MarkupTemplate
            # present only in >= 0.6
            return hasattr(MarkupTemplate, 'add_directives')
        except ImportError:
            return False

    def _jinja2(self):
        try:
            import jinja2
        except ImportError:
            return False
        else:
            return True

have = Capabilities()


def need(capability):
    def decorator(fn):
        @wraps(fn)
        def decorated(*args, **kw):
            if not have[capability]:
                raise SkipTest
            return fn(*args, **kw)
        return decorated
    return decorator


def alternate_expectation(backend, string):
    def decorator(fn):
        try:
            alternates = fn.alternates
        except AttributeError:
            alternates = fn.alternates = {}
        alternates[backend] = string.strip()
        return fn
    return decorator


class desired_output(object):

    def __init__(self, language, schema, **kw):
        self.language = language
        self.schema = schema
        self.expected = None
        self.alternate_expectations = {}
        self.render_context = kw

    def __call__(self, fn):
        self.expected = fn.__doc__.strip().decode('utf8')
        self.alternate_expectations = getattr(fn, 'alternates', {})
        return self

    def expectation_for(self, backend):
        try:
            return self.alternate_expectations[backend]
        except KeyError:
            return self.expected

    @property
    def genshi(self):
        def decorator(fn):
            markup = _wrap_with_xmlns(fn.__doc__, self.language)
            fn.__doc__ = None
            @wraps(fn)
            def runner():
                if not have['genshi']:
                    raise SkipTest
                got = _render_genshi(markup, self.language, self.schema,
                                     **self.render_context)
                expected = self.expectation_for('genshi')
                if expected != got:
                    print "\n" + fn.__name__
                    print "Expected:\n" + expected
                    print "Got:\n" + got
                assert expected == got
            return runner
        return decorator

    @property
    def markup(self):
        def decorator(fn):
            @wraps(fn)
            def runner():
                got = _render_markup_fn(fn, self.language, self.schema,
                                        **self.render_context)
                expected = self.expectation_for('markup')
                if expected != got:
                    print "\n" + fn.__name__
                    print "Expected:\n" + expected
                    print "Got:\n" + got
                assert expected == got
            return runner
        return decorator


def markup_test(markup='xml', schema=None):
    """Turn a function into a Generator markup test.

    Desired output is read from the docstring.  The function is passed a
    generator and an Element and is expected to return output matching the
    docstring.

    """
    def decorator(fn):
        expected = fn.__doc__.decode('utf8').strip()

        @wraps(fn)
        def test():
            from flatland.out.markup import Generator

            generator = Generator(markup=markup)
            if schema is not None:
                el = schema()
            else:
                el = None
            got = fn(generator, el)
            assert hasattr(got, '__html__')

            got = got.strip()
            if expected != got:
                print "\n" + fn.__name__
                print "Expected:\n" + expected
                print "Got:\n" + got
            assert expected == got
        return test
    return decorator


def render_genshi(markup, language, schema, wrap=True, **context):
    if wrap:
        markup = _wrap_with_xmlns(markup, language)
    return _render_genshi(markup, language, schema, **context)


def _render_markup_fn(fn, language, schema, **kw):
    from flatland.out.markup import Generator

    generator = Generator(markup=language)
    if schema is not None:
        form = schema()
    else:
        form = None
    output = fn(generator, form, **kw)
    return output.strip()


def _render_genshi(markup, language, schema, **kw):
    from genshi.template import MarkupTemplate
    from flatland.out.genshi import setup

    template = MarkupTemplate(markup)
    setup(template)

    if schema is not None:
        kw['form'] = schema()
    else:
        kw['form'] = None
    output = template.generate(**kw).render(language)

    # strip div wrapper off
    got = output[output.index(u'\n') + 1:output.rindex(u'\n')]
    got = got.strip()

    return got


def _wrap_with_xmlns(template, language):
    wrapped = u'<div '
    if language == u'xhtml':
        wrapped += u'xmlns="http://www.w3.org/1999/xhtml" '
    wrapped += (
        u'xmlns:form="http://ns.discorporate.us/flatland/genshi" ' +
        u'xmlns:py="http://genshi.edgewall.org/">\n' +
        template +
        u'\n</div>')
    return wrapped

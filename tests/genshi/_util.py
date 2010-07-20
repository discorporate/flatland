import inspect
import os
import re
import sys
from tests._util import eq_


__all__ = 'rendered_markup_eq_', 'RenderTest'

def rendered_markup_eq_(template_text, **context):
    import genshi, genshi.template

    chunked_raw = chunk_assertion_blocks(template_text)
    if not chunked_raw:
        raise AssertionError("No test chunks found in template text.")

    template = genshi.template.MarkupTemplate(template_text)
    stream = template.generate(**context)
    output = stream.render('xhtml')
    chunked_output = chunk_assertion_blocks(output)

    for idx, label, lhs, rhs in chunked_output:
        assert lhs == rhs, "test %s: %r != %r" % (label, lhs, rhs)

    eq_(len(chunked_raw), len(chunked_output))

class TextFileMixin(object):
    def wrap_with_xmlns(self, template):
        return ('<div xmlns="http://www.w3.org/1999/xhtml" '
                'xmlns:form="http://ns.discorporate.us/flatland/genshi" '
                'xmlns:py="http://genshi.edgewall.org/">\n'
                + template +
                '\n</div>')

    def _make_text_runner(self, filename, template, default_label=''):
        label = template.strip().splitlines()[0][3:].strip()
        if not label or label == 'test':
            label = "test %s" % default_label
        tester = lambda context, text: self.compare_(context, text)
        tester.description = "%s: %s" % (os.path.basename(filename), label)
        return tester

    def from_file(self, filename, context_factory=dict):
        modpath = sys.modules[self.__module__].__file__
        filepath = os.path.join(os.path.dirname(modpath), filename)
        chunks = chunk_file(filepath)

        for num, chunk in enumerate(chunks):
            wrapped = self.wrap_with_xmlns(chunk)
            yield (self._make_text_runner(filename, chunk, num + 1),
                   context_factory(),
                   wrapped)

    def from_string(self, collection, context_factory=dict, name=None):
        chunks = chunk_text(collection)
        if name is None:
            name = inspect.stack()[1][3]

        for num, chunk in enumerate(chunks):
            wrapped = self.wrap_with_xmlns(chunk)
            yield (self._make_text_runner(name, chunk, num + 1),
                   context_factory(),
                   wrapped)


def from_text_files(context_factory=dict):
    def wrap(fn):
        def test(self, *args, **kw):
            files = fn(self, *args, **kw)
            if isinstance(files, basestring):
                files = (files,)
            base = os.path.dirname(os.path.abspath(
                    inspect.getsourcefile(fn)))

            all_tests = []
            for name in files:
                filename = os.path.join(base, name)
                all_tests.extend(self.from_file(filename, context_factory))
            for test, context, template in all_tests:
                yield test, context, template

        test.func_name = fn.func_name
        return test
    return wrap

def from_docstring(context_factory=dict):
    def wrap(fn):
        def test(self, *args, **kw):
            tests = self.from_string(fn.__doc__, context_factory,
                                     name=fn.func_name)
            for test, context, template in tests:
                yield test, context, template
        test.func_name = fn.func_name
        return test
    return wrap


class RenderTest(TextFileMixin):
    format = 'xhtml'
    debug = False

    def compile(self, template_text):
        import genshi.template
        return genshi.template.MarkupTemplate(template_text)

    def to_genshi_context(self, context):
        import genshi.template
        if not isinstance(context, genshi.template.Context):
            return genshi.template.Context(**context)
        return context

    def generate(self, template, context):
        return template.generate(context)

    def render(self, stream, format=None):
        if format is None:
            format = self.format
        return stream.render(format)

    def compare_(self, context, template_text):
        chunked_raw = chunk_assertion_blocks(template_text)
        if not chunked_raw:
            raise AssertionError("No test chunks found in template text.")

        template = self.compile(template_text)
        genshi_context = self.to_genshi_context(context)
        stream = self.generate(template, genshi_context)
        output = self.render(stream)
        if self.debug:
            print template_text
            print output

        chunked_output = chunk_assertion_blocks(output)

        try:
            for idx, label, lhs, rhs in chunked_output:
                assert lhs == rhs, "test %s: %r != %r" % (label, lhs, rhs)

            eq_(len(chunked_raw), len(chunked_output))
        except:
            print output
            raise


class FilteredRenderTest(RenderTest):
    def generate(self, template, context):
        from flatland.out.genshi import flatland_filter
        return flatland_filter(template.generate(context), context)


class ChunkError(Exception):
    """Internal to chunk_assertion_blocks."""


def chunk_file(filepath):
    fh = open(filepath, 'rb')
    slurping, lines = False, []
    for line in fh.readlines():
        if not slurping and line.startswith('::'):
            slurping = True
        if slurping:
            lines.append(line)
            continue
    try:
        return chunk_text("\n".join(lines))
    finally:
        fh.close()

def chunk_text(string):
    return [(chunk + '\n:: endtest')
            for chunk in re.split(r'(?:^|\n):: *endtest', string)
            if re.search(r'(?:^|\n):: *test\b', chunk)]

def chunk_assertion_blocks(text):
    chunks = []
    buffer = None
    for lineno, line in enumerate(text.splitlines()):
        if not line.startswith('::'):
            if buffer:
                buffer[-1].append(line)
            continue
        tokens = line[2:].split()
        try:
            pragma, args = tokens[0], tokens[1:]
            if pragma == 'test':
                if buffer:
                    raise ChunkError("test out of order")
                chunknum = len(chunks) + 1
                if args:
                    title = ' '.join(args)
                else:
                    title = str(chunknum)
                buffer = [chunknum, title, []]
                continue
            elif pragma == 'endtest':
                if not buffer or len(buffer) == 3:
                    raise ChunkError("endtest out of order")
                buffer[2] = ' '.join(buffer[2]).strip()
                buffer[3] = ' '.join(buffer[3]).strip()
                chunks.append(buffer)
                buffer = None
                continue
            elif pragma == 'eq':
                if not buffer or len(buffer) > 3:
                    raise ChunkError("eq out of order")
                buffer.append([])
            else:
                raise ChunkError("unknown pragma" + pragma)
        except (ChunkError, IndexError), exc:
            lineno += 1
            arg = exc.args[0] if exc.args else ''
            raise AssertionError(
                "Invalid testing chunk specification: %s\n"
                "line %s:\n%r" % (
                    arg, lineno, line))
    return chunks

def test_chunk_assertion_blocks_1():
   input = """
foo
bar
:: test
thing
thing
:: eq
thing thing
:: endtest
"""
   eq_(chunk_assertion_blocks(input),
       [[1, '1', 'thing thing', 'thing thing']])

def test_chunk_assertion_blocks_2():
   input = """
<div>
:: test
  <b>thing
       </b>

:: eq
  <b>thing
       </b>

:: endtest
</div>

<p>
:: test label  label
foo
::eq
bar
:: endtest"""  # no final newline
   eq_(chunk_assertion_blocks(input),
       [[1, '1', '<b>thing        </b>', '<b>thing        </b>'],
        [2, 'label label', 'foo', 'bar']])

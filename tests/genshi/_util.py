from nose.tools import eq_


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

class RenderTest(object):
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

    def compare_(self, element, context, template_text):
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
        from flatland.out.genshi import genshi_springy_filter
        return genshi_springy_filter(template.generate(context), context)


class ChunkError(Exception):
    """Internal to chunk_assertion_blocks."""

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

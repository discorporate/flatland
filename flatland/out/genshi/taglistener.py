# Copyright 2006 Virtuous, Inc.
# All rights reserved.
#
# Author: Jason Kirtland <jason@virtuous.com>

from genshi.core import Namespace, Stream, Attrs, END, START

__all__ = ['TagListener', 'default_start', 'default_end']

class TagListener(object):
  """A Stream filter that operates on tag open/close events.  Events are
  buffered and close event handlers may modify or replace the tag and all of
  its children.  
  """

  def __prep__(self, stream, context):
    """___prep__(stream, context) -> stream, context
    Filtering and setup hook called before processing begins."""    

    return stream, context

  def __call__(self, stream, context=None):
    stream, context = self.__prep__(stream, context)

    eb = EventBuffer()

    for event in stream:
      if event[0] is START:
        listen = self.inspect(event, context)
      else:
        listen = False
      eb.push(event, listen, context)

    for event in eb.events:
      yield event
  
  def inspect(self, event, context):
    """inspect(event, context) -> False | (callable | None, callable | None)

    Called for each START event in the stream.  To register a callback for a
    tag open/close pair, return a 2-tuple of callables to consume the start
    and end events.

    The start callable takes the form:
      start(event, context) -> event, user-data

    You can modify the open event if you wish.  The event you return will
    be used in place of the original event.

    User-data can be anything you like, and will be passed along to the
    end-tag handler.  You can use this to maintain state between open
    and close events.

    The end callable takes the form:
      end(start, end, stream, context, user-data) -> start, end, stream

    You will be called with the opening and closing events (kind = START and
    kind = END) as well as the stream of events that occured between them.
    You'll also recieve the filter context and any user-data you returned from
    the matching start callable.

    The start, end, and stream you return will be used in place of the
    original input.  Any of the three can be omitted (None), and those events
    will not propagate to the output stream.

    For example, here's a processor that discards children of the matched tag.

      def child_remover(start, event, stream, context, history):
        return start, end, None

    And one that removes itself but leaves children intact:

      def self_remover(start, event, stream, context, history):
        return None, None, stream
    
    """
    return False

def default_start(event, context):
  """A default start-listener implementation."""
  return event, None

def default_end(start, end, stream, context, history):
  """A default end-listener implementation."""
  return start, end, stream


class ChildRemover(TagListener):
  """Sample TagListener implementation that discards all children from
  matching nodes."""
  NAMESPACE = Namespace('http://code.discorporate.us/child-remover')

  def inspect(event, context):
    if event[0] is not START:
      return False

    kind, (tag, attributes), pos = event

    if tag in self.NAMESPACE:
      return (self.start, self.end)
    else:
      for attr, value in attributes:
        if attr in self.NAMESPACE:
          return (default_start, self.end)

    return False      

  def end(self, start, event, stream, context, history):
    """I remove all children."""
    return start, end, None

class EventBuffer(object):
  __slots__ = ['streams', 'tags']

  def __init__(self):
    self.streams = [[]]
    self.tags    = []

  def push(self, event, listen=False, context=None):
    kind, data, pos = event
    
    if kind is START:
      if listen:
        on_start, on_end = listen

        if callable(on_start):
          event, history = on_start(event, context)
        else:
          history = None

        self.tags.append((event, on_end, history))
        self.streams.append([])
      else:
        self.tags.append((event, False, None))
        self.streams[-1].append(event)

    elif kind is END:
      start, on_end, history = self.tags.pop()

      if not on_end:
        self.streams[-1].append(event)
      else:
        children = Stream(self.streams.pop())

        if callable(on_end):
          start, end, children = on_end(start, event, children,
                                        context, history)
        else:
          end = event

        if start is not None:
          self.streams[-1].append(start)
        if children:
          self.streams[-1].extend(iter(children))
        if end is not None:
          self.streams[-1].append(end)

    else:
      self.streams[-1].append(event)

  events = property(lambda s: s.streams[-1], lambda s,v: None)


# -*- coding: utf-8 -*-
"""Signals and events.

A small implementation of signals, inspired by a snippet of Django signal API
client code seen in a blog post.  Signals are first-class objects and each
manages its own receivers and message emission.

The :func:`signal` function provides singleton behavior for named
signals.

"""
from collections import defaultdict
import weakref
from . base import threading
from . import weakrefs


_signals = weakref.WeakValueDictionary()
_signals.lock = threading.Lock()

def signal(name):
    """Return the :class:`Signal` named *name*, creating if required."""
    lock = _signals.lock
    lock.acquire()
    try:
        return _signals[name]
    except KeyError:
        _signals[name] = instance = Signal(name)
        return instance
    finally:
        lock.release()

ANY = 0

class Signal(object):
    """A generic notification emitter."""

    # convenience for importers, allows Signal.ANY
    ANY = ANY

    def __init__(self, name):
        self.name = name
        self.has_connected = False
        self._receivers = {}
        self._by_receiver = defaultdict(set)
        self._by_sender = defaultdict(set)
        self._sender_cleanups = {}

    def connect(self, receiver, sender=ANY, weak=True):
        """Connect *receiver* to signal events send by *sender*.

        :param receiver: A callable.  Will be invoked by :meth:`send`.
          Will be invoked with `sender=` as a named argument and any
          **kwargs that were provided to a call to :meth:`send`.

        :param sender: Any object or :attr:`Signal.ANY`.  Restricts
          notifications to *receiver* to only those :meth:`send`
          emissions sent by *sender*.  If ``ANY``, the receiver will
          always be notified.  A *receiver* may be connected to
          multiple *sender* on the same Signal.  Defaults to ``ANY``.

        :param weak: If true, the Signal will hold a weakref to
          *receiver* and automatically disconnect when *receiver* goes
          out of scope or is garbage collected.  Defaults to True.

        """
        receiver_id = _hashable_identity(receiver)
        if weak:
            receiver_ref = weakrefs.reference(receiver, self._cleanup_receiver)
            receiver_ref.receiver_id = receiver_id
        else:
            receiver_ref = receiver
        sender_id = ANY if sender is ANY else _hashable_identity(sender)

        self.has_connected = True
        self._receivers[receiver_id] = receiver_ref
        self._by_sender[sender_id].add(receiver_id)
        self._by_receiver[receiver_id].add(sender_id)

        if sender is not ANY and sender_id not in self._sender_cleanups:
            # wire together a cleanup for weakref-able senders
            try:
                sender_ref = weakrefs.reference(sender, self._cleanup_sender)
                sender_ref.sender_id = sender_id
            except TypeError:
                pass
            else:
                # stash away the weakref and a set of connections to cleanup.
                stash = self._sender_cleanups.setdefault(
                    sender_id, (sender_ref, set()))
                stash[1].add(receiver_id)
        # broadcast this connection.  if receivers raise, disconnect.
        if receiver_connected.has_connected and self is not receiver_connected:
            try:
                receiver_connected.send(self,
                                        receiver_arg=receiver,
                                        sender_arg=sender,
                                        weak_arg=weak)
            except:
                self.disconnect(receiver, sender)
                raise

    def send(self, sender=None, **kwargs):
        """Emit this signal on behalf of *sender*, passing on **kwargs.

        Returns a list of 2-tuples, pairing receivers with their return
        value. The ordering of receiver notification is undefined.

        """
        results = []
        for receiver in self.receivers_for(sender):
            results.append((receiver, receiver(sender=sender, **kwargs)))
        return results

    def has_receivers_for(self, sender):
        """True if there is probably a receiver for *sender*.

        Performs an optimistic check for receivers only.  Does not guarantee
        that all weakly referenced receivers are still alive.  See
        :meth:`receivers_for` for a stronger search.

        """
        if not self.has_connected:
            return False
        if self._by_sender[ANY]:
            return True
        if sender is ANY:
            return False
        return _hashable_identity(sender) in self._by_sender

    def receivers_for(self, sender):
        """Iterate all live receivers listening for *sender*."""
        if self.has_connected:
            seen = set()
            for bucket in ANY, _hashable_identity(sender):
                for receiver_id in list(self._by_sender[bucket]):
                    receiver = self._receivers.get(receiver_id)
                    if receiver is None:
                        continue
                    if isinstance(receiver, weakrefs.WeakTypes):
                        strong = receiver()
                        if strong is None:
                            self._disconnect(receiver_id, ANY)
                            continue
                        receiver = strong
                    if bucket is ANY:
                        seen.add(id(receiver))
                        yield receiver
                    elif id(receiver) not in seen:
                        yield receiver

    def disconnect(self, receiver, sender=ANY):
        """Disconnect *receiver* from this signal's events."""
        sender_id = ANY if sender is ANY else _hashable_identity(sender)
        receiver_id = _hashable_identity(receiver)
        self._disconnect(receiver_id, sender_id)

    def _disconnect(self, receiver_id, sender_id):
        if sender_id == ANY:
            if self._by_receiver.pop(receiver_id, False):
                for bucket in self._by_sender.values():
                    bucket.discard(receiver_id)
            self._receivers.pop(receiver_id, None)
        else:
            self._by_sender[sender_id].discard(receiver_id)

    def _cleanup_receiver(self, receiver_ref):
        """Disconnect a receiver from all senders."""
        self._disconnect(receiver_ref.receiver_id, ANY)

    def _cleanup_sender(self, sender_ref):
        """Disconnect all receivers from a sender."""
        sender_id = sender_ref.sender_id
        assert sender_id != ANY
        self._by_sender.pop(sender_id, None)
        _, receiver_ids = self._sender_cleanups.pop(sender_id, (None, ()))
        for receiver_id in receiver_ids:
            self._by_receiver[receiver_id].discard(sender_id)

    def __repr__(self):
        return '<Signal 0x%x; %r>' % (id(self), self.name)


receiver_connected = Signal('receiver_connected')

def clear_state(signal):
    """Throw away all signal state.  Useful for unit tests."""
    signal._sender_cleanups.clear()
    signal._receivers.clear()
    signal._by_sender.clear()
    signal._by_receiver.clear()
    signal.has_connected = False

def _hashable_identity(obj):
    if hasattr(obj, 'im_func'):
        return (id(obj.im_func), id(obj.im_self))
    else:
        return id(obj)

from blinker import signal

element_set = signal('element_set', doc="""\
Emitted after ``set()`` has been called on an element.

:param sender: the element

:param adapted: boolean, True if the set() adapted successfully.

""")


validator_validated = signal('validator_validated', doc="""\
Emitted after a validator has processed an element.

:param sender: the validator callable doing validation

:param element: the element being validated

:param state: the *state* passed to
  :meth:`~flatland.schema.base.Element.validate`

:param result: the result of validator execution

""")

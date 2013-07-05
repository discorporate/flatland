.. -*- fill-column: 78 -*-

=======
Signals
=======

Flatland can notify your code when events of interest occur during flatland
processing using :py:class:`Blinker <blinker.base.Signal>` signals.  These
signals can be used for advanced customization in your application or simply
as a means for tracing and logging flatland activity during development.


.. autodata:: flatland.signals.validator_validated

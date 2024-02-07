magneto 0.0.3
-------------

(Unreleased)

* Fixed bug where Magstim status (armed/disarmed/ready) was sometimes reported
  incorrectly.
* Added an informative exception when attempting to interact with a
  :class:`~magneto.Magstim` object before its ``connect()`` method has been
  called.
* Added detailed debug printing of the serial communcations log when a
  communication error occurs with the stimulator.
* Fixed rare startup crash when Magstim sends a message consisting only of null
  bytes.


magneto 0.0.2
-------------

Released May 26, 2023.

* First vaguely stable release!
* Basic support for Magstim 200 and BiStim hardware.

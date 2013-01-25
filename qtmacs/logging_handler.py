# Copyright 2012, Oliver Nagy <qtmacsdev@gmail.com>
#
# This file is part of Qtmacs.
#
# Qtmacs is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Qtmacs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Qtmacs. If not, see <http://www.gnu.org/licenses/>.

"""
Define a custom logging handler class for the logger module.

This handler is subclassed from ``logging.Handler``, stores all
log-records that have every occurred, and triggers the signal supplied
to the constructor whenever a new record is available.

The constructor of ``QtmacsMain`` will instantiate this
object. Subsequently, all its methods, as well as all macros and
applets, can log messages with::

    self.qteLogger.debug('This is a debug message.')
    self.qteLogger.info('This is an info message.')
    self.qteLogger.warn('This is a warning message.')
    self.qteLogger.error('This is an error message.')
    self.qteLogger.exception('Only use inside Except block.',
                              exc_info-True, stack_info-True)

The class will not re-trigger ``sigNewLog`` until its ``fetch`` method
was called, which will return all the log request accumulated since
the last call. This can greatly reduce the system load if
``sigNewLog`` is connected asynchronously via::

    sigLogReady.connect(receiver_slot, type=QtCore.Qt.QueuedConnection)

In this case the signal will not be emitted until control returns to
the Qt event loop the macro and focus manager were fully executed.
The ``receiver_slot`` from the above example will therefore only be
called once and can batch process the queued up messages, instead
doing it separately for log record that arrives. The performance
improvement of this implementation is non-negligible.

It is safe to create multiple instances of this handler and use::

    from logging_handler import something

Use example (see also documentation of ``logging`` module)::

    # Define a new signal and create a new handler for logging messages.
    self.sigLogReady = QtCore.pysqtSignal()
    log_handler = QtmacsLoggingHandler(self.sigLogReady)
    log_handler.setLevel(logging.DEBUG)

    # Connect the newly create signal to the method that should receive
    # logging requests.
    sigLogReady.connect(self.qteUpdateLogSlot, type=QtCore.Qt.QueuedConnection)

    # Attach the handler to the Qtmacs wide logger ``self.qteLogger``
    # (every macro and applet has this variable defined)
    self.qteLogger.addHandler(self.log_handler)
"""
import logging


class QtmacsLoggingHandler(logging.Handler):
    """
    A new handler for the logger module that uses Qt signals to signal
    new log messages.

    The class stores all log records internally and provides a fetch()
    method to distribute them to whomever asks. The arrival of new log
    messages is indicated with a Qt signal. Ideally, this signal
    should be connected as a ``QueuedConnection`` as the class is
    smart enough to trigger it only once until data is fetched. This
    keeps the event loop as congestion free as possible and allows for
    batch processing of the log messages, instead of on a one-by-one
    basis.

    The class also keeps a record of all log messages it has every
    issued and are not deleted when ``fetch`` is called.

    |Args|

    * ``sigNewLog`` (**pyqtSignal**): the signal to trigger when a new
      log record arrives.

    """
    def __init__(self, sigNewLog):
        super().__init__()
        self.sigNewLog = sigNewLog

        # Buffer for all logger records.
        self.log = []

        # Flag to indicate whether a fetch signal was already
        # triggered. If True, then the fetch signal was delivered but
        # no one has yet called the fetch() method. If false, then no
        # new log messages have arrived since someone last called the
        # fetch() method.
        self.waitForFetch = False

    def emit(self, record):
        """
        Overloaded emit() function from the logger module.

        The supplied log record is added to the log buffer and the
        sigNewLog signal triggered.

        .. note:: this method is always only called from the
          ``logger`` module.
        """
        self.log.append(record)

        # Do not trigger the signal again if no one has fetched any
        # data since it was last set.
        if not self.waitForFetch:
            self.waitForFetch = True
            self.sigNewLog.emit()

    def fetch(self, start=None, stop=None):
        """
        Fetch log records and return them as a list.

        |Args|

        * ``start`` (**int**): non-negative index of the first log
          record to return.
        * ``stop`` (**int**):  non-negative index of the last log
          record to return.

        |Returns|

        * **list**: list of log records (see ``logger`` module for
          definition of log record).

        |Raises|

        * **None**
        """

        # Set defaults if no explicit indices were provided.
        if not start:
            start = 0
        if not stop:
            stop = len(self.log)

        # Sanity check: indices must be valid.
        if start < 0:
            start = 0
        if stop > len(self.log):
            stop = len(self.log)

        # Clear the fetch flag. It will be set again in the emit()
        # method once new data arrives.
        self.waitForFetch = False

        # Return the specified range of log records.
        return self.log[start:stop]

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
Format and display log-messages.

This applet creates an instance of ``QtmacsLoggingHandler`` which, in
turn, is linked into the Qtmacs wide logging mechanism (which is taken
from the ``logger`` module in the standard Python library).

It displays all received log messages and applies basic formatting to
distinguish between debug/status messages (black), warnings (blue),
and errors (red). If a stack trace is available it prints a formatted
version of it that resembles the stack trace usually seen by the
Python interpreter itself.

This applet is based on ``QTextEdit`` and thus capable of interpreting
HTML tags. For instance, calling::

    qteMain.qteLogger.info('This is a <b>bold</b> statement')

will result in the message \"This is a **bold** statement\".

.. note: This is (one of the few) modules that Qtmacs automatically
   registers and instantiates at startup.

As with every applet, do **not** use::

    from qtmacs.applets.logviewer import LogViewer

"""

import re
import logging
import traceback
import qtmacs.base_applet
import qtmacs.logging_handler
import qtmacs.extensions.qtmacstextedit_widget
from PyQt4 import QtCore, QtGui

# Shorthands:
QtmacsTextEdit = qtmacs.extensions.qtmacstextedit_widget.QtmacsTextEdit


class LogViewer(qtmacs.base_applet.QtmacsApplet):
    """
    Display log messages.

    The class instantiates its own handler to connect to the Qtmacs
    logger (from the logger module).

    |Args|

    * ``appletID`` (**str**): unique ID used by ``QtmacsMain`` to
      distinguish applets.
    """
    sigLogReady = QtCore.pyqtSignal()

    def __init__(self, appletID):
        # Initialise the base class.
        super().__init__(appletID)

        # Add the QTextEdit widget that will display the log messages.
        self.qteText = self.qteAddWidget(QtmacsTextEdit(self))

        # Binary flag used by the log parser to indicate that it is
        # probably a good idea to switch to the message window
        # immediately, eg. because an error was logged.
        self.qteAutoActivate = False

        # Specify the applet type. This information determines which
        # macros are compatible.
        self.qteSetAppletSignature('QTextEdit')

        # Make sure the cursor is at the end of the buffer. This will
        # ensure that subsequently added log entries remain visible, ie.
        # the QTextEdit will auto-scroll with the text.
        self.qteMoveToEndOfBuffer()

        # Define the colors for the different message types.
        self.qteColorCode = {'DEBUG': 'Green', 'INFO': 'Black',
                             'WARNING': 'Blue', 'ERROR': 'Red',
                             'CRITICAL': 'Purple'}

        # Count the number of processed log records.
        self.qteLogCnt = 0

        # Format the output messages as "{INFO, WARNING,...} - message".
        log_format = logging.Formatter('%(levelname)s - %(message)s')

        # Instantiate a custom logging handler that uses Qt signals.
        self.logHandler = qtmacs.logging_handler.QtmacsLoggingHandler(
            self.sigLogReady)
        self.logHandler.setLevel(logging.DEBUG)
        self.logHandler.setFormatter(log_format)

        # The sigLogReady signal triggers whenever a new log message
        # arrives. It is better to use a QueuedConnection for this
        # signal because then it is not processed until the event loop
        # regains control. This has the advantage that not every log
        # message is immediately processed, but log messages can
        # accumulate and are only fetched and displayed once the event
        # loop is idle again.
        self.sigLogReady.connect(self.qteUpdateLogSlot,
                                 type=QtCore.Qt.QueuedConnection)

        # Register the handler with the logger module.
        self.qteLogger.addHandler(self.logHandler)

        # Register shutdown handler.
        self.qteMain.qtesigCloseQtmacs.connect(self.qteToBeKilled)

    def qteFormatMessage(self, logRecord, numRepeat):
        # Shorthand.
        msg = logRecord.msg

        # Bring up the log viewer automatically for any of the
        # following log levels.
        if logRecord.levelname in ('ERROR', 'CRITICAL'):
            self.qteAutoActivate = True

        if logRecord.exc_info:
            # If an error trace exists format it with the help of the
            # traceback module. The result is a list of strings which
            # end in a new line character.
            tb_format = traceback.format_exception(*logRecord.exc_info)

            # Join the list into a string and pre-pend some
            # whitespaces to improve the readability in the message
            # applet. Escape the '<' symbol with '&lt;'.
            out = ''
            for _ in tb_format:
                out += '  ' + _.replace('<', '&lt;')

            # Strip trailing white spaces and add the PRE tag to
            # ensure that the text is displayed verbatim because the
            # text edit widget interprets HTML.
            out = out.strip('\n')
            tb_format = '<HR><PRE>' + out + '</PRE><HR><br />'
            del out
        elif logRecord.stack_info:
            # No error trace but a stack trace was provided. The stack
            # trace is directly available as a string and there is no
            # need for an extra formatting function from the traceback
            # module. The string is split into lines to prefix them
            # with some white space characters for better readability
            # in the log.
            stack = logRecord.stack_info.split('\n')

            # Join the list into a string and pre-pend a some white
            # spaces to improve the readability in the message
            # applet. Escape the '<' symbol with '&lt;'. Also add the
            # newline character removed by the split method above.
            out = ''
            for _ in stack:
                out += '  ' + _.replace('<', '&lt;') + '\n'

            # Strip trailing white spaces and add the PRE tag to
            # ensure that the text is displayed verbatim because the
            # text edit widget interprets HTML.
            out = out.strip('\n')
            tb_format = '<HR><PRE>' + out + '</PRE><HR><br />'
            del out
        else:
            tb_format = '<br />'

        # Add a line that specifies the number of repetitions.
        if numRepeat > 0:
            rep_msg = ' -- (Repeated {} times)'.format(numRepeat)
        else:
            rep_msg = ""

        # Pick the appropriate color for the message type.
        try:
            col = self.qteColorCode[logRecord.levelname]
        except KeyError:
            col = 'Black'

        # Return the HTML formatted message.
        return '<font color="{}">'.format(col) + msg + rep_msg + tb_format

    def qteUpdateLogSlot(self):
        """
        Fetch and display the next batch of log messages.
        """

        # Fetch all log records that have arrived since the last
        # fetch() call and update the record counter.
        log = self.logHandler.fetch(start=self.qteLogCnt)
        self.qteLogCnt += len(log)

        # Return immediately if no log message is available (this case
        # should be impossible).
        if not len(log):
            return

        # Remove all duplicate entries and count their repetitions.
        log_pruned = []
        last_entry = log[0]
        num_rep = -1
        for cur_entry in log:
            # If the previous log message is identical to the current
            # one increase its repetition counter. If the two log
            # messages differ, add the last message to the output log
            # and reset the repetition counter.
            if last_entry.msg == cur_entry.msg:
                num_rep += 1
            else:
                log_pruned.append([last_entry, num_rep])
                num_rep = 0
                last_entry = cur_entry

        # The very last entry must be added by hand.
        log_pruned.append([cur_entry, num_rep])

        # Format the log entries (eg. color coding etc.)
        log_formatted = ""
        for cur_entry in log_pruned:
            log_formatted += self.qteFormatMessage(cur_entry[0], cur_entry[1])
            log_formatted + '\n'

        # Insert the formatted text all at once as calls to insertHtml
        # are expensive.
        self.qteText.insertHtml(log_formatted)
        self.qteMoveToEndOfBuffer()

        # If the log contained an error (or something else of interest
        # to the user) then switch to the messages buffer (ie. switch
        # to this very applet).
        if self.qteAutoActivate:
            self.qteAutoActivate = False
            self.qteMain.qteMakeAppletActive(self)

    def qteMoveToEndOfBuffer(self):
        """
        Move cursor to the end of the buffer to facilitate auto
        scrolling.

        Technically, this is exactly the 'endOfBuffer' macro but to
        avoid swamping Qtmacs with 'qteRunMacroStarted' messages to no
        avail it was implemented here natively.
        """
        tc = self.qteText.textCursor()
        tc.movePosition(QtGui.QTextCursor.End)
        self.qteText.setTextCursor(tc)

    def qteToBeKilled(self):
        # Disconnect the update slot when Qtmacs shuts down. It is necessary
        # to do this explicitly because when this object is deleted the pending
        # signals (because of the queued connection, see the constructor) may
        # still be delivered. Not sure if this is a bug in PyQt4, or if this
        # behaviour is intentional.
        try:
            self.sigLogReady.disconnect(self.qteUpdateLogSlot)
        except Exception:
            pass

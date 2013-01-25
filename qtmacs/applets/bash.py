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
A Bash-applet demonstration.

This is a proof-of-concept to spawn a Bash shell inside Qtmacs. The
idiosyncratic layout separates the shell output (top) from the shell
input (bottom) because I do not know how to sensibly interact with the
shell via pipes. As a result, the applet is clumsy and lacks the
expected shell completion feature --> suggestions welcome.

This applet requires ``pexpect-u`` which can be installed via:

.. code-block:: bash

    pip-3.2 install pexpect-u

.. note:: pip-3.x is usually available as a `python3-pip` package.

As with every applet, do **not** use::

    from qtmacs.applets.bash import Bash

"""
import re
import pexpect
import qtmacs.qte_global as qte_global
import qtmacs.extensions.qtmacsscintilla_widget

from qtmacs.base_macro import QtmacsMacro
from qtmacs.base_applet import QtmacsApplet
from PyQt4 import QtCore, QtGui, QtWebKit, Qsci

#Shorthands:
QtmacsScintilla = qtmacs.extensions.qtmacsscintilla_widget.QtmacsScintilla

# Global variables:
colorCodes = [0x0, 0xcd, 0xcd00, 0xcdcd, 0xee0000,
              0xcd00cd, 0xcdcd00, 0xe5e5e5,
              0x7f7f7f, 0xff, 0xff00, 0xffff,
              0xff5c5c, 0xff00ff, 0xffff00, 0xffffff]


class Bash(QtmacsApplet):
    """
    Spawn an applet with a built-in Bash shell.
    """
    def __init__(self, appletID):
        # Initialise the base class.
        super().__init__(appletID)
        self.qteBash = pexpect.spawn('/bin/bash')

        # The shell output will be displayed in a QtmacsTextEdit widget
        # and shell input will be taken from a separate widget beneath.
        self.qteShellOut = self.qteAddWidget(QtmacsScintilla(self))
        self.qteShellIn = self.qteAddWidget(QtmacsScintilla(self))

        # Limit the height of the input applet to a single line.
        fm = self.qteShellIn.fontMetrics().size(0, 'X')
        self.qteShellIn.setMaximumHeight(2 * fm.height())
        del fm

        # Place the widget in a vertical layout and remove any spacing
        # in between them.
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.qteShellOut)
        layout.addWidget(self.qteShellIn)
        layout.setSpacing(0)
        self.setLayout(layout)
        self.qteMakeWidgetActive(self.qteShellIn)

        # Remove the margins.
        self.qteShellIn.setMarginWidth(1, 0)
        self.qteShellOut.setMarginWidth(1, 0)

        # Define the colors and fonts for all styles used in this applet.
        SCI = self.qteShellOut
        font = bytes('courier new', 'utf-8')
        for idx, col in enumerate(colorCodes):
            self.qteShellIn.SendScintilla(SCI.SCI_STYLESETFONT, idx, font)
            self.qteShellOut.SendScintilla(SCI.SCI_STYLESETFORE, idx, col)
            self.qteShellOut.SendScintilla(SCI.SCI_STYLESETFONT, idx, font)
        self.qteShellIn.zoomTo(2)
        self.qteShellOut.zoomTo(2)

        # Turn off the horizontal scroll bars because they behave... weirdly.
        self.qteShellOut.SendScintilla(SCI.SCI_SETHSCROLLBAR, 0, 0)
        self.qteShellIn.SendScintilla(SCI.SCI_SETHSCROLLBAR, 0, 0)

        # Use word wrapping instead of horizontal scroll bars.
        self.qteShellIn.setWrapMode(SCI.WrapWord)
        self.qteShellOut.setWrapMode(SCI.WrapWord)
        self.qteShellOut.setWrapVisualFlags(SCI.WrapFlagByText,
                                            SCI.WrapFlagByText, 2)
        del SCI

        # ------------------------------------------------------------
        # Bind custom macros
        # ------------------------------------------------------------
        qteBindKeyWidget = self.qteMain.qteBindKeyWidget

        # <enter> will parse the input for the typed command and send
        # it to the shell.
        name = self.qteMain.qteRegisterMacro(QueryShell)
        qteBindKeyWidget('<return>', name, self.qteShellIn)

        # Implement the <ctrl>+c functionality as in a normal shell.
        name = self.qteMain.qteRegisterMacro(ShellSigInt)
        qteBindKeyWidget('<ctrl>+c', name, self.qteShellOut)
        qteBindKeyWidget('<ctrl>+c', name, self.qteShellIn)

        # Bring up previous element in the history.
        name = self.qteMain.qteRegisterMacro(BackInHistory)
        qteBindKeyWidget('<Alt>+p', name, self.qteShellIn)
        qteBindKeyWidget('<Alt>+p', name, self.qteShellOut)

        # Bring up next element in the history.
        name = self.qteMain.qteRegisterMacro(NextInHistory)
        qteBindKeyWidget('<Alt>+n', name, self.qteShellIn)
        qteBindKeyWidget('<Alt>+n', name, self.qteShellOut)

        # Move to the previous line traversing widget boundaries.
        name = self.qteMain.qteRegisterMacro(PreviousLine)
        qteBindKeyWidget('<Ctrl>+p', name, self.qteShellIn)

        # Move to the next line traversing widget boundaries.
        name = self.qteMain.qteRegisterMacro(NextLine)
        qteBindKeyWidget('<Ctrl>+n', name, self.qteShellOut)

        # Give the shell some time to start up, then trigger
        # the timer routine. That routine will continuously
        # re-trigger itself for as long as the process is alive.
        self.startTimer(0)

        # Private variables to indicate if the shell is still active and
        # keep track of where the user input starts.
        self._isActive = True

        # Command history.
        self._commandHistory = []
        self._historyIdx = -1

        # The last used Scintilla style.
        self._lastStyle = 0

    def _Ascii2ScintillaStyle(self, asciiCode):
        """
        Convert Ascii escape sequences to Scintilla style codes.

        The ``asciiCode`` variable contains the colour code excluding
        the CSI (ie. '\x1b') character, but with the trailing 'm'. For
        instance, if the full escape sequence is '\x1b[01;32m' then
        only pass '01;32m'.

        The result can be used directly with the `SCI_SETSTYLING`
        command for the Scintilla widget, eg. to style the next
        ``numChar`` characters with the color specified by the Ascii
        code '01;32m' use::

            style = _Ascii2ScintillaStyle('01;32m')
            SendScintilla(SCI_SETSTYLING, numChar, style)

        |Args|

        * ``asciiCode`` (**str**): the ASCII code without the CSI
          (ie. without the '\x1b[' prefix).

        |Returns|

        * ``styleID`` (**int**): the Scintilla style or **None** if
          the code was not recognised.

        |Raises|

        * **QtmacsArgumentError** if the arguments do not have the
            correct type.
        """
        # If there is no style code use the previous one.
        if asciiCode is None:
            return None

        # If the code does not terminate with an 'm' character then
        # it is invalid.
        if asciiCode[-1] != 'm':
            return None
        else:
            # Remove the 'm' postfix.
            asciiCode = asciiCode[:-1]

        # Color codes can have one- or two values separated by a
        # semicolon. Therefore, split the string there convert
        # the strings into integers. If the conversion fails
        # then the code is invalid.
        asciiCode = asciiCode.split(';')
        try:
            asciiCode = [int(_) for _ in asciiCode]
        except ValueError:
            return None

        # If the sequence to parse is empty return immediately.
        if len(asciiCode) == 0:
            return None

        # --------------------------------------------------
        # Associate Ascii codes with styles. This is a very
        # rudimentary implementation at the moment but
        # works well enough for a decent proof-of-concept.
        # --------------------------------------------------
        # Check for the reset command (a single Zero)
        if asciiCode == [0]:
            return 0

        # Ignore all code sequence with a single element unless
        # it is zero (handled above).
        if len(asciiCode) < 2:
            return None
        else:
            # Convert the Ascii colors (denoted by 30 + color offset
            # where {0: Black, 1: Red, 2: Green, 3:Yellow, 4:Blue,
            # 5: Magenta, 6: Cyan, 7:White}) to a Scintilla style.
            # At the moment the formula is simply to subtract 28
            # as this maps to some (random) colors in the Scintilla
            # widget.
            if asciiCode[0] == 1:
                return asciiCode[1] - 30
            else:
                return asciiCode[1] - 30 + 8

    def timerEvent(self, event):
        """
        Periodically poll for new data in the output pipe of the shell.
        """
        self.killTimer(event.timerId())

        # Return immediately if the shell terminated.
        if not self._isActive:
            return

        # Read the next chunk of data from the process and re-start the
        # timer for this routine, unless the pipe was closed (EOF error).
        try:
            out = self.qteBash.read_nonblocking(size=1000, timeout=0)
            self.startTimer(500)
        except pexpect.TIMEOUT:
            self.startTimer(500)
            return
        except pexpect.EOF:
            self._isActive = False
            self.qteShellOut.append('Shell closed.')
            return

        if len(out) == 0:
            return

        # Remove redundant newline characters.
        out = out.replace('\r\n', '\n')

        # Split the string at each Control Sequence Introducer (CSI).
        out2 = out.split('\x1b[')
        textStyle = []

        # Parse the beginnings of the sub-strings for ASCII codes.
        # These codes always start with '\x1b[' (which was already
        # removed in the splitting process) followed by semicolons
        # and numbers, and terminated with 'm'.
        # For instance: '\x1b[0m' or '\x1b[0,31m'
        # More information is available at the Wikipedia page
        # http://en.wikipedia.org/wiki/ANSI_escape_code
        pat = re.compile('[;0-9]*?m')
        for text in out2:
            match = pat.match(text)
            if match is None:
                # This can happen if the original string did not feature
                # any CSI at all.
                textStyle.append((text, 0))
            else:
                # Determine the character set that make up the control
                # code and convert it to a Scintilla style.
                start, stop = match.span()
                code = text[start:stop]
                style = self._Ascii2ScintillaStyle(code)

                # Save the text and associated style for later.
                textStyle.append((text[stop:], style))

        # Shorthand.
        SCI = self.qteShellOut

        # Position the cursor and styling offset at the end of the
        # document.
        SCI.SendScintilla(SCI.SCI_DOCUMENTEND, 0, 0)
        line, col = SCI.getCursorPosition()
        pos = SCI.positionFromLineIndex(line, col)
        SCI.SendScintilla(SCI.SCI_STARTSTYLING, pos, 0xFF)

        # Insert each text fragment with the associated style. Keep
        # track of the last used style in case the next ASCII code
        # cannot be decoded properly.
        for text, style in textStyle:
            if style is None:
                style = self._lastStyle
            SCI.insert(text)
            SCI.SendScintilla(SCI.SCI_SETSTYLING, len(text), style)
            SCI.SendScintilla(SCI.SCI_DOCUMENTEND, 0, 0)
            SCI.SendScintilla(SCI.SCI_LINESCROLL, -len(text), 0)
            self._lastStyle = style

    def qteParseUserInput(self):
        """
        Send the user input to the shell.
        """
        # Get the user input.
        cmd = self.qteShellIn.text()
        self.qteShellIn.clear()

        # Send the command to the shell and trigger the timer quickly
        # because the shell will at least output the command echo.
        self.qteBash.sendline(cmd)

        # Add the command to the history list.
        self._commandHistory.insert(0, cmd)
        self.startTimer(10)

    def showPreviousCommand(self):
        """
        Replace current user input with next older command.
        """
        shellIn = self.qteShellIn
        self._historyIdx += 1
        if self._historyIdx >= len(self._commandHistory):
            self._historyIdx = len(self._commandHistory) - 1
            return
        shellIn.setText(self._commandHistory[self._historyIdx])
        shellIn.SendScintilla(shellIn.SCI_DOCUMENTEND, 0, 0)

    def showNextCommand(self):
        """
        Replace current user input with next newer command.
        """
        shellIn = self.qteShellIn
        self._historyIdx -= 1
        if self._historyIdx < 0:
            self._historyIdx = -1
            shellIn.clear()
            return
        shellIn.setText(self._commandHistory[self._historyIdx])
        shellIn.SendScintilla(shellIn.SCI_DOCUMENTEND, 0, 0)

    def addShellOutput(self, html):
        # Remove the user input, append the just arrived shell
        # output, then re-insert the user input again.
        self.qteShellOut.insert(html)
        self.qteShellOut.ensureCursorVisible()


class QueryShell(QtmacsMacro):
    """
    Parse user input and send it to the shell.
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('Bash')
        self.qteSetWidgetSignature('QtmacsScintilla')

    def qteRun(self):
        self.qteApplet.qteParseUserInput()


class ShellSigInt(QtmacsMacro):
    """
    Send <ctrl>+c to the shell and clear the input field.
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('Bash')
        self.qteSetWidgetSignature(('QtmacsTextEdit', 'QtmacsScintilla'))

    def qteRun(self):
        self.qteApplet.qteBash.sendcontrol('c')
        self.qteApplet.qteShellIn.clear()


class BackInHistory(QtmacsMacro):
    """
    Bring up the next older command in the history list.
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('Bash')
        self.qteSetWidgetSignature(('QtmacsTextEdit', 'QtmacsScintilla'))

    def qteRun(self):
        self.qteApplet.showPreviousCommand()


class NextInHistory(QtmacsMacro):
    """
    Bring up the next newer command in the history list.
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('Bash')
        self.qteSetWidgetSignature(('QtmacsTextEdit', 'QtmacsScintilla'))

    def qteRun(self):
        self.qteApplet.showNextCommand()


class PreviousLine(QtmacsMacro):
    """
    Move cursor to next line crossing to the input shell input
    if necessary.
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('Bash')
        self.qteSetWidgetSignature('QtmacsScintilla')

    def qteRun(self):
        line, col = self.qteWidget.getCursorPosition()
        if line > 0:
            line -= 1
            text = self.qteWidget.text(line)
            if col >= len(text):
                col = len(text) - 1
            self.qteWidget.setCursorPosition(line, col)
        else:
            app = self.qteApplet
            app.qteMakeWidgetActive(app.qteShellOut)
            last_line, last_col = app.qteShellOut.getNumLinesAndColumns()
            app.qteShellIn.setCursorPosition(last_line, last_col)


class NextLine(QtmacsMacro):
    """
    Move cursor to next line crossing to the input shell input
    if necessary.
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('Bash')
        self.qteSetWidgetSignature('QtmacsScintilla')

    def qteRun(self):
        line, col = self.qteWidget.getCursorPosition()
        last_line, last_col = self.qteWidget.getNumLinesAndColumns()
        if line < last_line:
            line += 1
            text = self.qteWidget.text(line)
            if col >= len(text):
                col = len(text)
            self.qteWidget.setCursorPosition(line, col)
        else:
            app = self.qteApplet
            app.qteMakeWidgetActive(app.qteShellIn)
            text = app.qteShellIn.text()
            app.qteShellIn.setCursorPosition(0, len(text))

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
Default macros and key bindings for ``QtmacsScintilla``.

The ``qteAddWidget`` method of ``QtmacsApplet`` uses this file to
endow ``QtmacsScintilla`` widgets with their default macros and
key bindings. The entry point to this module is the function
``install_macros_and_bindings``.

.. note: Macros are only registered if they do not yet exist. However,
   if a macro with the same name already does exists, then it is *not*
   replaced.
"""

import re
import math
import qtmacs.kill_list
import qtmacs.undo_stack
import qtmacs.auxiliary
import qtmacs.type_check
import qtmacs.miniapplets.base_query
import qtmacs.qte_global as qte_global
import qtmacs.extensions.qtmacsscintilla_widget as scintilla_widget
from PyQt4 import QtCore, QtGui
from qtmacs.base_macro import QtmacsMacro

# Shorthands:
QtmacsMessage = qtmacs.auxiliary.QtmacsMessage
type_check = qtmacs.type_check.type_check
KillListElement = qtmacs.kill_list.KillListElement
QtmacsUndoStack = qtmacs.undo_stack.QtmacsUndoStack
QtmacsUndoCommand = qtmacs.undo_stack.QtmacsUndoCommand
MiniAppletBaseQuery = qtmacs.miniapplets.base_query.MiniAppletBaseQuery

# Global variables:
qteKilledTextFromRectangle = None


# ------------------------------------------------------------
#                   Movement macros
# ------------------------------------------------------------


class ForwardChar(QtmacsMacro):
    """
    Move cursor one character to the right.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QtmacsScintilla``
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QtmacsScintilla')

    def qteRun(self):
        self.qteWidget.SendScintilla(self.qteWidget.SCI_CHARRIGHT, 0, 0)


class BackwardChar(QtmacsMacro):
    """
    Move cursor one character to the left.
    |Signature|

    * *applet*: '*'
    * *widget*: ``QtmacsScintilla``
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QtmacsScintilla')

    def qteRun(self):
        self.qteWidget.SendScintilla(self.qteWidget.SCI_CHARLEFT, 0, 0)


class ForwardWord(QtmacsMacro):
    """
    Move cursor to beginning of next word.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QtmacsScintilla``
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QtmacsScintilla')

    def qteRun(self):
        self.qteWidget.SendScintilla(self.qteWidget.SCI_WORDRIGHT, 0, 0)


class BackwardWord(QtmacsMacro):
    """
    Move cursor to beginning of previous word.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QtmacsScintilla``
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QtmacsScintilla')

    def qteRun(self):
        self.qteWidget.SendScintilla(self.qteWidget.SCI_WORDLEFT, 0, 0)


class MoveStartOfLine(QtmacsMacro):
    """
    Move cursor to the beginning of the line.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QtmacsScintilla``
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QtmacsScintilla')

    def qteRun(self):
        line, col = self.qteWidget.getCursorPosition()
        self.qteWidget.setCursorPosition(line, 0)


class MoveEndOfLine(QtmacsMacro):
    """
    Move cursor to the end of the line.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QtmacsScintilla``
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QtmacsScintilla')

    def qteRun(self):
        self.qteWidget.SendScintilla(self.qteWidget.SCI_LINEEND, 0, 0)


class NextLine(QtmacsMacro):
    """
    Move cursor to next line.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QtmacsScintilla``
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QtmacsScintilla')

    def qteRun(self):
        # Determine the current positing, number of lines in the
        # document, and columns in the last line of the document.
        last_line, last_col = self.qteWidget.getNumLinesAndColumns()
        line, col = self.qteWidget.getCursorPosition()

        # Return immediately if there is no next line.
        if line >= last_line:
            return

        # Try to place the cursor at the same index in the next line
        # if possible (ie. if the next line has sufficiently many
        # characters).
        num_char = len(self.qteWidget.text(line + 1))
        if col < num_char:
            self.qteWidget.setCursorPosition(line + 1, col)
        else:
            self.qteWidget.setCursorPosition(line + 1, num_char - 1)


class PreviousLine(QtmacsMacro):
    """
    Move cursor to previous line.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QtmacsScintilla``
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QtmacsScintilla')

    def qteRun(self):
        line, col = self.qteWidget.getCursorPosition()

        # Return immediately if there is no next line.
        if line < 1:
            return

        # Try to place the cursor at the same index in the next line
        # if possible (ie. if the next line has sufficiently many
        # characters).
        num_char = len(self.qteWidget.text(line - 1))
        if col < num_char:
            self.qteWidget.setCursorPosition(line - 1, col)
        else:
            self.qteWidget.setCursorPosition(line - 1, num_char - 1)


class EndOfDocument(QtmacsMacro):
    """
    Move cursor to the very end of the ``QTextEdit``.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QtmacsScintilla``
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QtmacsScintilla')

    def qteRun(self):
        self.qteWidget.SendScintilla(self.qteWidget.SCI_DOCUMENTEND, 0, 0)


class BeginningOfDocument(QtmacsMacro):
    """
    Move cursor to the very beginning of the ``QTextEdit``.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QtmacsScintilla``
    * *widget*: '*'
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QtmacsScintilla')

    def qteRun(self):
        self.qteWidget.setCursorPosition(0, 0)


class ScrollDown(QtmacsMacro):
    """
    Scroll up by approximately as much as is currently visible.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QtmacsScintilla``
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QtmacsScintilla')

    def qteRun(self):
        # Move the visible portion of the widget down by 90%
        # of the currently visible area.
        bar = self.qteWidget.verticalScrollBar()
        tot_height = self.qteWidget.maximumViewportSize().height()
        new_value = bar.value() + int(0.9 * tot_height)
        bar.setValue(new_value)

        # Set the cursor to the first visible line.
        line, col = self.qteWidget.getCursorPosition()
        line = self.qteWidget.firstVisibleLine()
        self.qteWidget.setCursorPosition(line, col)


class ScrollUp(QtmacsMacro):
    """
    Scroll down by approximately as much as is currently visible.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QtmacsScintilla``
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QtmacsScintilla')

    def qteRun(self):
        # Move the visible portion of the widget up by 90%
        # of the currently visible area.
        bar = self.qteWidget.verticalScrollBar()
        tot_height = self.qteWidget.maximumViewportSize().height()
        new_value = bar.value() - int(0.9 * tot_height)
        bar.setValue(new_value)

        # Set the cursor to the first visible line.
        line, col = self.qteWidget.getCursorPosition()
        line = self.qteWidget.firstVisibleLine()
        self.qteWidget.setCursorPosition(line, col)


# ------------------------------------------------------------
#                     Editing macros
# ------------------------------------------------------------


class SelfInsert(QtmacsMacro):
    """
    Insert the last character from ``last_key_sequence`` defined in
    the global name space.

    The ``last_key_sequence`` variable is overwritten/updated every
    time the event handler in Qtmacs receives a new keyboard event.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QtmacsScintilla``
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QtmacsScintilla')

    def qteRun(self):
        """
        Extract the last ``QKeyEvent`` from the keyboard sequence
        (there should only be one anyway, but just to be sure). Then
        extract the human readable text it represents and call the
        ``keyPressEvent`` method to insert it.

        Note that the method simply calls the original ``keyPressEvent``
        method and does not implement undo commands. The reason for the
        latter is that ``keyPressEvent`` takes care of updating the undo
        stack accordingly.
        """
        keyEvent = qte_global.last_key_sequence.toQKeyEventList()[-1]
        self.qteWidget.keyPressEvent(keyEvent)


class InsertNewline(QtmacsMacro):
    """
    Insert line break at current position.

    The EOL character used to implement this line break complies with
    the convention in the document and is handled internally by
    ``QtmacsScintilla`` widget.

    If the previous line was indented, then the new line will be too,
    at the same level. Indentation characters are always white spaces,
    never tabs.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QtmacsScintilla``
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QtmacsScintilla')
        self._pat = re.compile(' *')

    def qteRun(self):
        # Determine the indentation level of the current line.
        line, col = self.qteWidget.getCursorPosition()
        match = self._pat.match(self.qteWidget.text(line))
        numIndent = len(match.group())

        # On Windows a new-line is prefixed with a '\r' character.
        eolmode = self.qteWidget.eolMode()
        if eolmode == scintilla_widget.QtmacsScintilla.EolWindows:
            self.qteWidget.insert('\r\n' + ' ' * numIndent)
        else:
            self.qteWidget.insert('\n' + ' ' * numIndent)


class SetMark(QtmacsMacro):
    """
    Place the default mark at the current position in the document.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QtmacsScintilla``
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QtmacsScintilla')

    def qteRun(self):
        (line, col) = self.qteWidget.qteSetMark()
        self.qteMain.qteStatus('New mark at ({}, {})'.format(line, col))


class IndentLine(QtmacsMacro):
    """
    Indent the current line one more level.

    Indentation characters are always white spaces, never tabs.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QtmacsScintilla``
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QtmacsScintilla')
        self._pat = re.compile(' *')

    def qteRun(self):
        # Shorthands.
        indentWidth = self.qteWidget.tabWidth()
        line, col = self.qteWidget.getCursorPosition()

        # Backup the current state of the document for the undo
        # object later.
        textBefore = self.qteWidget.text()

        # Get the entire line. Do not use 'text(line)' to prevent
        # problematic EOL symbols from occurring in the string, as
        # these are platform specific.
        self.qteWidget.setSelection(line, 0, line, 0)
        self.qteWidget.SendScintilla(
            self.qteWidget.SCI_LINEENDEXTEND, 0, 0)
        text = self.qteWidget.selectedText()

        # Match the largest chunk of white space at the beginning of
        # the string. Note that _pat.match(text) will always match at
        # least an empty string and therefore never return a ``None``
        # object, which is why this case is not checked explicitly.
        white = self._pat.match(text).group()
        if len(white) == len(text):
            # If the entire string consists only of white spaces then
            # delete it entirely and insert as many white space characters
            # as necessary to reach the next indentation level.
            tmp = col + indentWidth
            numIndent = indentWidth * math.floor(tmp / indentWidth)
            newText = ' ' * numIndent
        else:
            # If there is text on the line then indent it one more level.
            tmp = indentWidth + len(white)
            numIndent = indentWidth * math.floor(tmp / indentWidth)
            numIndent -= len(white)
            newText = ' ' * numIndent + text

        # Replace the current line with the newly indented line and place
        # the cursor at the first non-whitespace character.
        self.qteWidget.replaceSelectedText(newText)
        self.qteWidget.setCursorPosition(line, len(white) + numIndent)


class DelCharBackward(QtmacsMacro):
    """
    Delete the character to the left of the cursor.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QtmacsScintilla``
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QtmacsScintilla')

    def qteRun(self):
        line, col = self.qteWidget.getCursorPosition()
        if (line == 0) and (col == 0):
            return

        self.qteWidget.setSelection(line, col, line, col)
        self.qteWidget.SendScintilla(
            self.qteWidget.SCI_CHARLEFTEXTEND, 0, 0)
        self.qteWidget.removeSelectedText()


class DelChar(QtmacsMacro):
    """
    Delete character to the right of the cursor.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QtmacsScintilla``
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QtmacsScintilla')

    def qteRun(self):
        # Determine the number of lines and columns in last line.
        last_line, last_col = self.qteWidget.getNumLinesAndColumns()

        # Return immediately if we are the end of the file.
        line, col = self.qteWidget.getCursorPosition()
        if (line == last_line) and (col == last_col):
            return

        self.qteWidget.setSelection(line, col, line, col)
        self.qteWidget.SendScintilla(
            self.qteWidget.SCI_CHARRIGHTEXTEND, 0, 0)
        self.qteWidget.removeSelectedText()


class KillWord(QtmacsMacro):
    """
    Delete the word to the right of the cursor.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QtmacsScintilla``
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QtmacsScintilla')

    def qteRun(self):
        # Determine the number of lines and columns in last line.
        last_line, last_col = self.qteWidget.getNumLinesAndColumns()

        # Return immediately if we are the end of the file.
        line, col = self.qteWidget.getCursorPosition()
        if (line == last_line) and (col == last_col):
            return

        # Let QsciScintilla select the word to the right
        # of the cursor.
        line, col = self.qteWidget.getCursorPosition()
        self.qteWidget.setSelection(line, col, line, col)
        self.qteWidget.SendScintilla(
            self.qteWidget.SCI_WORDRIGHTENDEXTEND, 0, 0)
        self.qteWidget.removeSelectedText()


class BackwardKillWord(QtmacsMacro):
    """
    Delete word to the left of the cursor.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QtmacsScintilla``
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QtmacsScintilla')

    def qteRun(self):
        # Return immediately if we are the start of the file.
        line, col = self.qteWidget.getCursorPosition()
        if (line == 0) and (col == 0):
            return

        line, col = self.qteWidget.getCursorPosition()
        self.qteWidget.setSelection(line, col, line, col)
        self.qteWidget.SendScintilla(self.qteWidget.SCI_WORDLEFTEXTEND, 0, 0)
        self.qteWidget.removeSelectedText()


class UpperWord(QtmacsMacro):
    """
    Make the current word all upper case.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QtmacsScintilla``
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QtmacsScintilla')

    def qteRun(self):
        line, col = self.qteWidget.getCursorPosition()
        self.qteWidget.setSelection(line, col, line, col)

        # Select the current word by first moving to the end of it,
        # and then asking Scintilla to select it leftwards.
        self.qteWidget.SendScintilla(
            self.qteWidget.SCI_WORDRIGHTEND, 0, 0)
        self.qteWidget.SendScintilla(
            self.qteWidget.SCI_WORDLEFTEXTEND, 0, 0)
        word = self.qteWidget.selectedText()
        self.qteWidget.replaceSelectedText(word.upper())


class LowerWord(QtmacsMacro):
    """
    Make the current word all lower case.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QtmacsScintilla``
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QtmacsScintilla')

    def qteRun(self):
        line, col = self.qteWidget.getCursorPosition()
        self.qteWidget.setSelection(line, col, line, col)

        # Select the current word by first moving to the end of it,
        # and then asking Scintilla to select it leftwards.
        self.qteWidget.SendScintilla(
            self.qteWidget.SCI_WORDRIGHTEND, 0, 0)
        self.qteWidget.SendScintilla(
            self.qteWidget.SCI_WORDLEFTEXTEND, 0, 0)
        word = self.qteWidget.selectedText()
        self.qteWidget.replaceSelectedText(word.lower())


class CapitaliseWord(QtmacsMacro):
    """
    Capitalise the current word.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QtmacsScintilla``
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QtmacsScintilla')

    def qteRun(self):
        line, col = self.qteWidget.getCursorPosition()
        self.qteWidget.setSelection(line, col, line, col)

        # Select the current word by first moving to the end of it,
        # and then asking Scintilla to select it leftwards.
        self.qteWidget.SendScintilla(
            self.qteWidget.SCI_WORDRIGHTEND, 0, 0)
        self.qteWidget.SendScintilla(
            self.qteWidget.SCI_WORDLEFTEXTEND, 0, 0)
        word = self.qteWidget.selectedText()
        self.qteWidget.replaceSelectedText(word.capitalize())


class TransposeWord(QtmacsMacro):
    """
    Transpose current- for previous word.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QtmacsScintilla``
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QtmacsScintilla')

    def qteRun(self):
        # Clear any selections.
        line, col = self.qteWidget.getCursorPosition()
        self.qteWidget.setSelection(line, col, line, col)

        # Select the current word by first moving to the end of it,
        # and then asking Scintilla to select it leftwards. Also
        # store the left- and right position of the word (for the
        # redo operation).
        self.qteWidget.SendScintilla(
            self.qteWidget.SCI_WORDRIGHTEND, 0, 0)
        pos0 = self.qteWidget.getCursorPosition()
        self.qteWidget.SendScintilla(
            self.qteWidget.SCI_WORDLEFTEXTEND, 0, 0)
        pos1 = self.qteWidget.getCursorPosition()

        # Continue in the same manner to identify the whitespace
        # gap between the two words.
        self.qteWidget.SendScintilla(
            self.qteWidget.SCI_WORDLEFTENDEXTEND, 0, 0)
        pos2 = self.qteWidget.getCursorPosition()

        # Continue in the same manner to identify the second
        # word to the left.
        self.qteWidget.SendScintilla(
            self.qteWidget.SCI_WORDLEFTEXTEND, 0, 0)
        pos3 = self.qteWidget.getCursorPosition()

        # Select and backup the right word.
        self.qteWidget.setSelection(pos0[0], pos0[1], pos1[0], pos1[1])
        right_word = self.qteWidget.selectedText()

        # Select and backup the white space between the two words.
        self.qteWidget.setSelection(pos1[0], pos1[1], pos2[0], pos2[1])
        space = self.qteWidget.selectedText()

        # Select and backup the left word.
        self.qteWidget.setSelection(pos2[0], pos2[1], pos3[0], pos3[1])
        left_word = self.qteWidget.selectedText()

        # Select, backup, and delete the union of all three regions.
        self.qteWidget.setSelection(pos0[0], pos0[1], pos3[0], pos3[1])

        self.qteWidget.replaceSelectedText(right_word + space + left_word)


class TransposeChar(QtmacsMacro):
    """
    Transpose the two characters on the left- and right side of the cursor.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QtmacsScintilla``
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QtmacsScintilla')

    def qteRun(self):
        # No transposition occurs at the beginning of the line.
        line, col = self.qteWidget.getCursorPosition()
        if col == 0:
            return

        # Clear the selection
        self.qteWidget.setSelection(line, col, line, col)

        # Select the character to the left and right of the cursor.
        # To do so, first move behind the next character, and then
        # extend the selection back two characters.
        self.qteWidget.SendScintilla(
            self.qteWidget.SCI_CHARRIGHT, 0, 0)
        self.qteWidget.SendScintilla(
            self.qteWidget.SCI_CHARLEFTEXTEND, 0, 0)
        self.qteWidget.SendScintilla(
            self.qteWidget.SCI_CHARLEFTEXTEND, 0, 0)

        # Replace the current selection with its reverse.
        chars = self.qteWidget.selectedText()
        self.qteWidget.replaceSelectedText(chars[::-1])


class KillLine(QtmacsMacro):
    """
    Kill to the end of the line and place the content into the kill-list.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QtmacsScintilla``
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QtmacsScintilla')

    def qteRun(self):
        # Shorthand variables and clear the selection.
        line, col = self.qteWidget.getCursorPosition()
        self.qteWidget.setSelection(line, col, line, col)

        # Determine the text to the right of the cursor.
        text = self.qteWidget.text(line)[col:]

        # If this text merely constitutes an end-of-line (EOL) character
        # then delete it, otherwise mark only the characters up to the
        # end-of-line character.
        if text == '\r\n':
            # EOL on Windows.
            self.qteWidget.setSelection(line, col, line, col + 2)
        elif text == '\n':
            # EOL on Mac and Unix.
            self.qteWidget.setSelection(line, col, line, col + 1)
        else:
            # There is more than just an EOL character left.
            self.qteWidget.SendScintilla(
                self.qteWidget.SCI_LINEENDEXTEND, 0, 0)
        self.qteWidget.removeSelectedText()


class KillRegion(QtmacsMacro):
    """
    Kill the text between the cursor and the last mark.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QtmacsScintilla``
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QtmacsScintilla')

    def qteRun(self):
        self.cursorPos = self.qteWidget.getCursorPosition()
        self.markerPos = self.qteWidget.qteGetMark()
        if self.markerPos is None:
            return

        # Shorthand variables for the position of the mark and cursor.
        cur_line, cur_col = self.cursorPos
        mark_line, mark_col = self.markerPos

        # Kill the selected text.
        self.qteWidget.setSelection(cur_line, cur_col, mark_line, mark_col)
        self.qteWidget.removeSelectedText()


class Yank(QtmacsMacro):
    """
    Re-insert the last killed element.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QtmacsScintilla``
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QtmacsScintilla')

    def qteRun(self):
        # Do nothing if the kill-list is empty.
        if len(qte_global.kill_list) == 0:
            return

        # Traverse the kill-list until an element with plain text data
        # was found.
        killListData = [_.dataText() for _ in qte_global.kill_list]
        for idx, text in enumerate(reversed(killListData)):
            if text is not None:
                # Yank the text and trigger the 'yank-qtmacs_scintilla'
                # which will be intercepted by YankPop.
                self.qteWidget.insert(text)
                msgObj = QtmacsMessage(idx)
                self.qteMain.qteRunHook('yank-qtmacs_scintilla', msgObj)
                return


class YankPop(QtmacsMacro):
    """
    Replace the just yanked element with the previous one in the
    kill-list.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QtmacsScintilla``
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QtmacsScintilla')

        self.killListIdx = -1
        self.qteMain.qteConnectHook('yank-qtmacs_scintilla', self.enableHook)

    def qteRun(self):
        # Do nothing if the kill-list contains no earlier element.
        if self.killListIdx < 0:
            return

        # Traverse the kill-list in reverse from where we left off.
        kill_list = qte_global.kill_list[:self.killListIdx]
        for el in reversed(kill_list):
            self.killListIdx -= 1
            if el.dataText() is not None:
                text = str(el.dataText())
                # Permanently remove the last undo object from the undo stack
                # and call its reverseCommit method to remove the previously
                # yanked kill-list element.
                undoObjOld = self.qteWidget.qteUndoStack.pop()
                undoObjOld.reverseCommit()

                # Insert the currently selected kill-list element instead.
                self.qteWidget.insert(text)
                return

    def disableHook(self, msgObj):
        """
        Disable yank-pop.

        The ``enableHook`` method (see below) connects this method
        to the ``qtesigKeyseqComplete`` signal to catch
        consecutive calls to this ``yank-pop`` macro. Once the user
        issues a key sequence for any other macro but this one, the
        kill-list index will be set to a negative index, effectively
        disabling the macro.
        """
        # Unpack the data structure.
        macroName, keysequence = msgObj.data
        if macroName != self.qteMacroName():
            self.qteMain.qtesigKeyseqComplete.disconnect(
                self.disableHook)
            self.killListIdx = -1

    def enableHook(self, msgObj):
        """
        Enable yank-pop.

        This method is connected to the 'yank-qtmacs_scintilla' hook
        (triggered by the yank macro) to ensure that yank-pop only
        gets activated after the yank-macro.
        """
        self.killListIdx = len(qte_global.kill_list) - msgObj.data - 1
        self.qteMain.qtesigKeyseqComplete.connect(self.disableHook)


class OpenLine(QtmacsMacro):
    """
    Open a new line (ie. insert a new-line at the current cursor position).

    |Signature|

    * *applet*: '*'
    * *widget*: ``QtmacsScintilla``
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QtmacsScintilla')

    def qteRun(self):
        # Shorthands.
        pos = self.qteWidget.getCursorPosition()
        eolmode = self.qteWidget.eolMode()

        # On Windows a new-line is prefixed with a '\r' character.
        if eolmode == scintilla_widget.QtmacsScintilla.EolWindows:
            self.qteWidget.insert('\r\n')
        else:
            self.qteWidget.insert('\n')

        # Return the cursor to the original position.
        self.qteWidget.setCursorPosition(*pos)


# ------------------------------------------------------------
# Macros that operate on rectangular regions. All these macros
# require customised undo objects which are defined in this
# section as well.
# ------------------------------------------------------------


class UndoKillRectangle(QtmacsUndoCommand):
    """
    Implement kill-rectangle and its inverse.

    This method works in tandem with ``UndoKillRectangle``. Whatever
    this class kills it stores in the module global variable
    ``qteKilledTextFromRectangle``, so that ``UndoYankRectangle`` can
    yank it again. Note that ``qteKilledTextFromRectangle`` is
    overwritten every time, ie. there is no equivalent to a kill-list
    like for the ``KillLine`` macro.

    |Args|

    * ``qteWidget`` (**QWidget**): the widget to use.
    """

    def __init__(self, qteWidget):
        super().__init__()
        self.qteWidget = qteWidget
        self.cursorPos = self.markerPos = None
        self.baseClass = super(type(qteWidget), qteWidget)

    def commit(self):
        """
        Insert the specified text in all selected lines, always
        at the same column position.
        """

        # Get the number of lines and columns in last line.
        last_line, last_col = self.qteWidget.getNumLinesAndColumns()

        # If this is the first ever call to this undo/redo element
        # then backup the current cursor- and marker position because
        # both will be required for the redo operation.
        if self.cursorPos is None:
            # Get the default marker and ensure it points to a
            # valid location inside the document.
            self.markerPos = self.qteWidget.qteGetMark()
            if self.markerPos is None:
                return
            if not self.qteWidget.isPositionValid(*self.markerPos):
                return

            # Backup the current cursor and marker position; swap
            # one for the other if necessary to ensure the marker
            # comes first.
            self.cursorPos = self.qteWidget.getCursorPosition()
            if self.cursorPos[0] < self.markerPos[0]:
                self.cursorPos, self.markerPos = self.markerPos, self.cursorPos

        # Shorthand for qteWidget and left/right position of rectangle.
        wid = self.qteWidget
        col1 = min((self.markerPos[1], self.cursorPos[1]))
        col2 = max((self.markerPos[1], self.cursorPos[1]))

        # Insert the specified string at the same position in every line
        # in between the mark and the cursor (inclusive).
        self.removedText = []
        for line in range(self.markerPos[0], self.cursorPos[0] + 1):
            text = wid.text(line)
            if col1 >= len(text):
                # If the line has no text in the specified column
                # range then ignore it.
                self.removedText.append('')
                continue
            if col2 > len(text):
                # If the col1-col2 range spans only part of the
                # line then select only that part.
                wid.setSelection(line, col1, line, col1)
                wid.SendScintilla(wid.SCI_LINEENDEXTEND, 0, 0)
            else:
                # If the col1-col2 range is a subset of the entire
                # line then select the entire range.
                wid.setSelection(line, col1, line, col2)

            # Backup and remove the selected text.
            self.removedText.append(self.qteWidget.selectedText())
            self.baseClass.removeSelectedText()

        self.qteWidget.setCursorPosition(self.cursorPos[0], self.markerPos[1])

        # Determine the user selected string length and initialise the global
        # variable qteKilledTextFromRectangle with an empty dictionary.
        strlen = col2 - col1
        global qteKilledTextFromRectangle
        qteKilledTextFromRectangle = []

        # Copy the removed text into the global variable
        # 'qteKilledTextFromRectangle' so that YankRectangle can
        # access it. However, ensure that every element has exactly
        # the length specified by the user defined rectangle; zero pad
        # elements that are too short. Note: do not apply this zero
        # padding to self.removedText because otherwise the text could
        # not be undone correctly.
        for el in self.removedText:
            # Determine how many white space characters are required
            # to make the string 'strLen' characters long.
            pad = strlen - len(el)

            # Sanity check.
            if pad < 0:
                qteKillTextFromRectangle = None
                self.qteWidget.setCursorPosition(*self.cursorPos)
                self.cursorPos = self.markerPos = None
                msg = 'Padding length cannot be negative --> this is a bug'
                self.qteLogger.error(msg)
                return

            # Store the padded version of the string.
            qteKilledTextFromRectangle.append(el + ' ' * pad)

    def reverseCommit(self):
        """
        Re-insert the previously deleted line.
        """

        if self.markerPos is None:
            return

        # Remove the specified string from the same position in every line
        # in between the mark and the cursor (inclusive).
        col = min((self.markerPos[1], self.cursorPos[1]))
        rng = range(self.markerPos[0], self.cursorPos[0] + 1)
        for idx, line in enumerate(rng):
            text = self.removedText[idx]
            if text != '':
                self.baseClass.insertAt(text, line, col)

        self.qteWidget.setCursorPosition(*self.cursorPos)


class KillRectangle(QtmacsMacro):
    """
    Kill the text in the rectangle spanned by the cursor and last mark.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QtmacsScintilla``
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QtmacsScintilla')

    def qteRun(self):
        if self.qteWidget.qteGetMark() is None:
            return

        undoObj = UndoKillRectangle(self.qteWidget)
        self.qteWidget.qteUndoStack.push(undoObj)


class UndoYankRectangle(QtmacsUndoCommand):
    """
    Implement yank-rectangle and its inverse.

    This method works in tandem with ``UndoKillRectangle``. Whatever
    UndoKillRectangle kills is written to the module global variable
    ``qteKilledTextFromRectangle``, which this class accesses to yank
    the text.

    |Args|

    * ``qteWidget`` (**QWidget**): the widget to use.
    """

    def __init__(self, qteWidget):
        super().__init__()
        self.qteWidget = qteWidget
        self.cursorPos = None
        self.baseClass = super(type(qteWidget), qteWidget)

    def commit(self):
        """
        Insert the specified text in all selected lines, always
        at the same column position.
        """

        # Get the number of lines and columns in the last line.
        last_line, last_col = self.qteWidget.getNumLinesAndColumns()

        # If this is the first ever call to this undo/redo element
        # then backup the current cursor position because
        # it will be required for the redo operation.
        if self.cursorPos is None:
            if qteKilledTextFromRectangle is None:
                return
            self.insertedText = list(qteKilledTextFromRectangle)
            self.cursorPos = self.qteWidget.getCursorPosition()
        else:
            self.qteWidget.setCursorPosition(*self.cursorPos)

        # Insert the killed strings into their respective lines.
        col = self.cursorPos[1]
        for ii, text in enumerate(self.insertedText):
            line = ii + self.cursorPos[0]
            self.baseClass.insertAt(text, line, col)

    def reverseCommit(self):
        """
        Re-insert the previously deleted line.
        """

        # Loop over all lines in the rectangle to remove the
        # previously yanked strings.
        col = self.cursorPos[1]
        for ii, text in enumerate(self.insertedText):
            line = ii + self.cursorPos[0]

            # Select as many characters as the string is long and remove
            # them.
            self.qteWidget.setSelection(line, col, line, col + len(text))
            self.baseClass.removeSelectedText()

        # Place the cursor at the original position.
        self.qteWidget.setCursorPosition(*self.cursorPos)


class YankRectangle(QtmacsMacro):
    """
    Yank the text killed at the last invocation of kill-rectangle.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QtmacsScintilla``
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QtmacsScintilla')

    def qteRun(self):
        if qteKilledTextFromRectangle is None:
            return
        undoObj = UndoYankRectangle(self.qteWidget)
        self.qteWidget.qteUndoStack.push(undoObj)


class UndoStringInsertRectangle(QtmacsUndoCommand):
    """
    Implement string-insert-rectangle and its inverse.

    |Args|

    * ``qteWidget`` (**QWidget**): the widget to use.
    * ``text`` (**str**): the string to insert.
    """

    def __init__(self, qteWidget, text):
        super().__init__()
        self.qteWidget = qteWidget
        self.baseClass = super(type(qteWidget), qteWidget)
        self.cursorPos = self.markerPos = None
        self.text = text

    def commit(self):
        """
        Insert the specified text in all selected lines, always
        at the same column position.
        """

        # Get the number of lines and columns in last line.
        last_line, last_col = self.qteWidget.getNumLinesAndColumns()

        # If this is the first ever call to this undo/redo element
        # then backup the current cursor- and marker position because
        # both will be required for the redo operation.
        if self.cursorPos is None:
            # Get the default marker and ensure it points to a
            # valid location inside the document.
            self.markerPos = self.qteWidget.qteGetMark()
            if self.markerPos is None:
                return
            if not self.qteWidget.isPositionValid(*self.markerPos):
                return

            # Backup the current cursor and marker position; swap
            # one for the other if necessary to ensure the marker
            # comes first.
            self.cursorPos = self.qteWidget.getCursorPosition()
            if self.cursorPos[0] < self.markerPos[0]:
                self.cursorPos, self.markerPos = self.markerPos, self.cursorPos

        # Insert the specified string at the same position in every line
        # in between the mark and the cursor (inclusive).
        col = min((self.markerPos[1], self.cursorPos[1]))
        for line in range(self.markerPos[0], self.cursorPos[0] + 1):
            self.baseClass.insertAt(self.text, line, col)

        self.qteWidget.setCursorPosition(*self.cursorPos)

    def reverseCommit(self):
        """
        Re-insert the previously deleted line.
        """

        if self.markerPos is None:
            return

        # Remove the specified string from the same position in every line
        # in between the mark and the cursor (inclusive).
        col = min((self.markerPos[1], self.cursorPos[1]))
        for line in range(self.markerPos[0], self.cursorPos[0] + 1):
            self.qteWidget.setSelection(line, col, line, col + len(self.text))
            self.baseClass.removeSelectedText()

        self.qteWidget.setCursorPosition(*self.cursorPos)


class StringInsertRectangle(QtmacsMacro):
    """
    Insert a string at every line in the selected rectangle.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QtmacsScintilla``
    """
    class Query(MiniAppletBaseQuery):
        """
        Query a string.
        """
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.defaultChoice = ''

        def generateCompletions(self, entry):
            return None

        def inputCompleted(self, userInput):
            if userInput == '':
                text = self.defaultChoice
            else:
                text = userInput
            undoObj = UndoStringInsertRectangle(self.qteWidget, text)
            self.qteWidget.qteUndoStack.push(undoObj)

    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QtmacsScintilla')

        # History of inserted strings.
        self.qteQueryHistory = []

    def qteRun(self):
        # Return immediately if no mark has been set.
        if self.qteWidget.qteGetMark() is None:
            return

        # Compile a description and default value for the insertion.
        prefixStr = 'String insert rectangle (default: {}):'
        if len(self.qteQueryHistory) == 0:
            default = ''
        else:
            default = self.qteQueryHistory[-1]
        prefixStr = prefixStr.format(repr(default))

        # Instantiate the customised new mini applet query object to
        # ask for the string to insert.
        query = self.Query(self.qteApplet, self.qteWidget,
                           prefix=prefixStr, history=self.qteQueryHistory)
        query.defaultChoice = default

        # Install the query object as the mini applet and return
        # control to the event loop.
        self.qteMain.qteAddMiniApplet(query)


class SearchForwardMiniApplet(MiniAppletBaseQuery):
    """
    Query a string and find all occurrences of it in the Scintilla widget.
    """
    class HighlightNextMatch(QtmacsMacro):
        """
        Call ``highlightNextMatch`` method in the ``SearchForward``
        mini applet.

        |Signature|

        * *applet*: 'MiniApplet'
        * *widget*: ``QTextEdit``

        """
        def __init__(self):
            super().__init__()
            self.qteSetAppletSignature('MiniApplet')
            self.qteSetWidgetSignature('QTextEdit')

        def qteRun(self):
            self.qteApplet.highlightNextMatch()

    class InsertNewlineChar(QtmacsMacro):
        """
        Insert a new line character into the search query.

        |Signature|

        * *applet*: 'MiniApplet'
        * *widget*: ``QTextEdit``

        """
        def __init__(self):
            super().__init__()
            self.qteSetAppletSignature('MiniApplet')
            self.qteSetWidgetSignature('QTextEdit')

        def qteRun(self):
            self.qteWidget.insertPlainText('\n')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.defaultChoice = ''

        # The default search string. This one is set manually
        # when the Query object is instantiated.
        self.defaultChoice = ''

        # Position and style of each match. Will be updated
        # as the user types.
        self.matchList = []

        # The currently selected match.
        self.selMatchIdx = 0

        # Original cursor position.
        self.cursorPosOrig = self.qteWidget.getCursorPosition()

        # Shorthands.
        SCI = self.qteWidget

        # Make a copy of the style bits.
        line, col = SCI.getNumLinesAndColumns()
        text, style = self.qteWidget.SCIGetStyledText((0, 0, line, col))
        self.styleOrig = style

        # Define two new text styles, one for highlighting all
        # matches, and one for highlighting only the currently
        # selected match.
        font = bytes('courier new', 'utf-8')
        SCI.SendScintilla(SCI.SCI_STYLESETFONT, 30, font)
        SCI.SendScintilla(SCI.SCI_STYLESETFORE, 30, 0xFFFFFF)
        SCI.SendScintilla(SCI.SCI_STYLESETBACK, 30, 0)
        SCI.SendScintilla(SCI.SCI_STYLESETFONT, 31, font)
        SCI.SendScintilla(SCI.SCI_STYLESETFORE, 31, 0x7f7f7f)
        SCI.SendScintilla(SCI.SCI_STYLESETBACK, 31, 0xcd00)

        # Disable the lexer to avoid interfering with the Scintilla
        # internal styling engine. The lexer will be re-enabled
        # when this widget is closed (see qteToBeKilled method).
        self.originalLexer = SCI.qteLexer()
        SCI.qteSetLexer(None)

        # Register the SearchForward macro and bind it to <ctrl>+s.
        register = self.qteMain.qteRegisterMacro
        bind = self.qteMain.qteBindKeyWidget
        macroName = register(self.HighlightNextMatch, replaceMacro=True)
        bind('<Ctrl>+s', macroName, self.qteText)

        macroName = register(self.InsertNewlineChar, replaceMacro=True)
        bind('<Ctrl>+q <ctrl>+j', macroName, self.qteText)

        # Connect to the Qt native textChanged slot to be informed whenever
        # the user has typed anything. This is more convenient and targeted
        # than using Qtmacs' internal qtesigKeypressed. Also connect to the
        # abort slot to restore the original cursor position.
        self.qteText.textChanged.connect(self.qteTextChanged)
        self.qteMain.qtesigAbort.connect(self.qteAbort)

    def clearHighlighting(self):
        """
        Restore the original style properties of all matches.

        This method effectively removes all visible traces of
        the match highlighting.
        """
        SCI = self.qteWidget
        self.qteWidget.SCISetStylingEx(0, 0, self.styleOrig)

        # Clear out the match set and reset the match index.
        self.selMatchIdx = 1
        self.matchList = []

    def highlightNextMatch(self):
        """
        Select and highlight the next match in the set of matches.
        """
        # If this method was called on an empty input field (ie.
        # if the user hit <ctrl>+s again) then pick the default
        # selection.
        if self.qteText.toPlainText() == '':
            self.qteText.setText(self.defaultChoice)
            return

        # If the mathIdx variable is out of bounds (eg. the last possible
        # match is already selected) then wrap it around.
        if self.selMatchIdx < 0:
            self.selMatchIdx = 0
            return
        if self.selMatchIdx >= len(self.matchList):
            self.selMatchIdx = 0
            return

        # Shorthand.
        SCI = self.qteWidget

        # Undo the highlighting of the previously selected match.
        start, stop = self.matchList[self.selMatchIdx - 1]
        line, col = SCI.lineIndexFromPosition(start)
        SCI.SendScintilla(SCI.SCI_STARTSTYLING, start, 0xFF)
        SCI.SendScintilla(SCI.SCI_SETSTYLING, stop - start, 30)

        # Highlight the next match.
        start, stop = self.matchList[self.selMatchIdx]
        SCI.SendScintilla(SCI.SCI_STARTSTYLING, start, 0xFF)
        SCI.SendScintilla(SCI.SCI_SETSTYLING, stop - start, 31)

        # Place the cursor at the start of the currently selected match.
        line, col = SCI.lineIndexFromPosition(start)
        SCI.setCursorPosition(line, col)
        self.selMatchIdx += 1

    def compileMatchList(self):
        # Get the new sub-string to search for.
        self.matchList = []
        curEntry = self.qteText.toPlainText()
        numChar = len(curEntry)

        # Return immediately if the input field is empty.
        if numChar == 0:
            return

        # Compile a list of all sub-string spans.
        stop = 0
        text = self.qteWidget.text()
        while True:
            start = text.find(curEntry, stop)
            if start == -1:
                break
            else:
                stop = start + numChar
                self.matchList.append((start, stop))

    def qteTextChanged(self):
        """
        Search for sub-string matches.

        This method is triggered by Qt whenever the text changes,
        ie. whenever the user has altered the input. Extract the
        new input, find all matches, and highlight them accordingly.
        """
        # Remove any previous highlighting.
        self.clearHighlighting()
        SCI = self.qteWidget

        # Compile a list of spans that contain the specified string.
        self.compileMatchList()

        # Return if the substring does not exist in the text.
        if len(self.matchList) == 0:
            return

        # ------------------------------------------------------------
        # Make a copy of the style bits of the document, overwrite
        # those parts containing a substring, and then write them
        # back all at once. This is much faster than calling the
        # styling methods repeatedly.
        # ------------------------------------------------------------

        # Make a copy of the document style bits and determine the
        # cursor position in the document.
        style = bytearray(self.styleOrig)
        cur = SCI.positionFromLineIndex(*self.cursorPosOrig)

        # Style all matches.
        self.selMatchIdx = 0
        for start, stop in self.matchList:
            if start < cur:
                self.selMatchIdx += 1
            style[start:stop] = bytes(b'\x1e') * (stop - start)

        # If the cursor is after the last possible match (eg. always
        # the case when the cursor is at the end of the file) then
        # self.selMatchIdx will point beyond the list.
        if self.selMatchIdx == len(self.matchList):
            self.selMatchIdx = 0

        # Style the first match after the current cursor position
        # differently to indicate that it is the currently
        # selected one.
        start, stop = self.matchList[self.selMatchIdx]
        style[start:stop] = bytes(b'\x1f') * (stop - start)

        # Place the cursor at the start of the currently selected match.
        line, col = SCI.lineIndexFromPosition(start)
        SCI.setCursorPosition(line, col)
        self.selMatchIdx += 1

        # Apply the modified style array to the document.
        self.qteWidget.SCISetStylingEx(0, 0, style)

    def qteAbort(self, msgObj):
        """
        Restore the original cursor position because the user hit abort.
        """
        self.qteWidget.setCursorPosition(*self.cursorPosOrig)
        self.qteMain.qtesigAbort.disconnect(self.qteAbort)

    def qteToBeKilled(self):
        """
        Remove all selections and install the original lexer.
        """
        self.clearHighlighting()
        self.qteWidget.qteSetLexer(self.originalLexer)
        self.qteText.textChanged.disconnect(self.qteTextChanged)


class SearchForward(QtmacsMacro):
    """
    Search for the occurrence of a substring.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QtmacsScintilla``
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QtmacsScintilla')

        # History of inserted strings.
        self.qteSearchHistory = []

    def qteRun(self):
        # Instantiate the customised new mini applet query object to
        # ask for the string to insert.
        query = SearchForwardMiniApplet(
            self.qteApplet, self.qteWidget,
            prefix='Search: ', history=self.qteSearchHistory)

        # The default choice is the last search term.
        if len(self.qteSearchHistory) > 0:
            query.defaultChoice = self.qteSearchHistory[-1]
        else:
            query.defaultChoice = ''

        # Install the query object as the mini applet and return
        # control to the event loop.
        self.qteMain.qteAddMiniApplet(query)


class SearchForwardRegexpMiniApplet(SearchForwardMiniApplet):
    """
    Interpret the user input as a regular expression and highlight
    all matches in the QtmacsScintilla widget as the user types.
    """
    def compileMatchList(self):
        # Get the new sub-string to search for.
        curEntry = self.qteText.toPlainText()

        # Return immediately if the input field is empty.
        if len(curEntry) == 0:
            return

        # If the current user input does not constitute a valid
        # regular expression then do nothing.
        try:
            pat = re.compile(curEntry, re.MULTILINE + re.DOTALL)
        except re.error:
            return

        # Compile a list of all sub-string spans.
        text = self.qteWidget.text()
        self.matchList = [_.span() for _ in pat.finditer(text)]


class SearchForwardRegexp(QtmacsMacro):
    """
    Search for sub-strings defined via a regular expression.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QtmacsScintilla``
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QtmacsScintilla')

        # History of inserted strings.
        self.qteSearchHistory = []

    def qteRun(self):
        # Instantiate the customised new mini applet query object to
        # ask for the string to insert.
        query = SearchForwardRegexpMiniApplet(
            self.qteApplet, self.qteWidget, prefix='Search: ',
            history=self.qteSearchHistory)

        # The default choice is the last search term.
        if len(self.qteSearchHistory) > 0:
            query.defaultChoice = self.qteSearchHistory[-1]
        else:
            query.defaultChoice = ''

        # Install the query object as the mini applet and return
        # control to the event loop.
        self.qteMain.qteAddMiniApplet(query)


class QueryReplaceMiniApplet(MiniAppletBaseQuery):
    """
    Query a two strings and replace all occurrences of the first with
    the second.
    """
    class NextQueryMode(QtmacsMacro):
        """
        Move to the next query mode (ie. from search string query to
        replacement string query to the final replacement operations).

        |Signature|

        * *applet*: 'MiniApplet'
        * *widget*: ``QTextEdit``

        """
        def __init__(self):
            super().__init__()
            self.qteSetAppletSignature('MiniApplet')
            self.qteSetWidgetSignature('QTextEdit')

        def qteRun(self):
            self.qteApplet.nextMode()

    class InsertNewlineChar(QtmacsMacro):
        """
        Insert a new line character into the search query to facilitate
        searching for newlines as well.

        |Signature|

        * *applet*: 'MiniApplet'
        * *widget*: ``QTextEdit``

        """
        def __init__(self):
            super().__init__()
            self.qteSetAppletSignature('MiniApplet')
            self.qteSetWidgetSignature('QTextEdit')

        def qteRun(self):
            self.qteWidget.insertPlainText('\n')

    class ReplaceAll(QtmacsMacro):
        """
        Replace all remaining matches.

        |Signature|

        * *applet*: 'MiniApplet'
        * *widget*: ``QTextEdit``

        """
        def __init__(self):
            super().__init__()
            self.qteSetAppletSignature('MiniApplet')
            self.qteSetWidgetSignature('QTextEdit')

        def qteRun(self):
            self.qteApplet.replaceAll()

    class ReplaceNext(QtmacsMacro):
        """
        Replace the next match.

        |Signature|

        * *applet*: 'MiniApplet'
        * *widget*: ``QTextEdit``

        """
        def __init__(self):
            super().__init__()
            self.qteSetAppletSignature('MiniApplet')
            self.qteSetWidgetSignature('QTextEdit')

        def qteRun(self):
            if not self.qteApplet.replaceSelected():
                self.qteMain.qteKillMiniApplet()

    class SkipNext(QtmacsMacro):
        """
        Skip the next match.

        |Signature|

        * *applet*: 'MiniApplet'
        * *widget*: ``QTextEdit``

        """
        def __init__(self):
            super().__init__()
            self.qteSetAppletSignature('MiniApplet')
            self.qteSetWidgetSignature('QTextEdit')

        def qteRun(self):
            self.qteApplet.highlightNextMatch()

    class Abort(QtmacsMacro):
        """
        Abort.

        |Signature|

        * *applet*: 'MiniApplet'
        * *widget*: ``QTextEdit``

        """
        def __init__(self):
            super().__init__()
            self.qteSetAppletSignature('MiniApplet')
            self.qteSetWidgetSignature('QTextEdit')

        def qteRun(self):
            self.qteApplet.qteAbort(QtmacsMessage())
            self.qteMain.qteKillMiniApplet()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.defaultChoice = ''

        # The default search string. This one is set manually
        # when the Query object is instantiated.
        self.defaultChoice = ''

        # Position and style of each match. Will be updated
        # as the user types.
        self.matchList = []

        # The currently selected match.
        self.selMatchIdx = 0

        # Original cursor position.
        self.cursorPosOrig = self.qteWidget.getCursorPosition()

        # Shorthands.
        SCI = self.qteWidget

        # Make a copy of the style bits.
        line, col = SCI.getNumLinesAndColumns()
        text, style = self.qteWidget.SCIGetStyledText((0, 0, line, col))
        self.styleOrig = style

        # Define two new text styles, one for highlighting all
        # matches, and one for highlighting only the currently
        # selected match.
        font = bytes('courier new', 'utf-8')
        SCI.SendScintilla(SCI.SCI_STYLESETFONT, 30, font)
        SCI.SendScintilla(SCI.SCI_STYLESETFORE, 30, 0xFFFFFF)
        SCI.SendScintilla(SCI.SCI_STYLESETBACK, 30, 0)
        SCI.SendScintilla(SCI.SCI_STYLESETFONT, 31, font)
        SCI.SendScintilla(SCI.SCI_STYLESETFORE, 31, 0x7f7f7f)
        SCI.SendScintilla(SCI.SCI_STYLESETBACK, 31, 0xcd00)

        # Disable the lexer to avoid interfering with the Scintilla
        # internal styling engine. The lexer will be re-enabled
        # when this widget is closed (see qteToBeKilled method).
        self.originalLexer = SCI.qteLexer()
        SCI.qteSetLexer(None)

        # Register the SearchForward macro and bind it to <ctrl>-s.
        register = self.qteMain.qteRegisterMacro
        bind = self.qteMain.qteBindKeyWidget

        macroName = register(self.NextQueryMode, replaceMacro=True)
        bind('<return>', macroName, self.qteText)

        macroName = register(self.InsertNewlineChar, replaceMacro=True)
        bind('<Ctrl>+q <ctrl>+j', macroName, self.qteText)

        # Connect to the Qt native textChanged slot to be informed
        # whenever the user has typed anything. This is more
        # convenient and targeted than using Qtmacs' internal
        # qtesigKeypressed. Also connect to the abort slot to restore
        # the original cursor position.
        self.qteText.textChanged.connect(self.qteTextChanged)
        self.qteMain.qtesigAbort.connect(self.qteAbort)

        # The string to replace, and its replacement.
        self.toReplace = self.toReplaceWith = None

        # Indicate whether we are querying for the string to replace
        # (0), the string to replace it with (1), or the replacement
        # operation (2).
        self.queryMode = 0

    def nextMode(self):
        """
        Put the search-replace macro into the next stage. The first stage
        is the query stage to ask the user for the string to replace,
        the second stage is to query the string to replace it with,
        and the third allows to replace or skip individual matches,
        or replace them all automatically.
        """
        # Terminate the replacement procedure if the no match was found.
        if len(self.matchList) == 0:
            self.qteAbort(QtmacsMessage())
            self.qteMain.qteKillMiniApplet()
            return

        self.queryMode += 1
        if self.queryMode == 1:
            # Disconnect the text-changed slot because no real time
            # highlighting is necessary when entering the replacement
            # string, unlike when entering the string to replace.
            self.qteText.textChanged.disconnect(self.qteTextChanged)

            # Store the string to replace and clear out the query field.
            self.toReplace = self.qteText.toPlainText()
            self.qteText.clear()
            self.qteTextPrefix.setText('mode 1')
        elif self.queryMode == 2:
            # Mode two is to replace or skip individual matches. For
            # this purpose rebind the "n", "!", and <space> keys
            # with the respective macros to facilitate it.
            register = self.qteMain.qteRegisterMacro
            bind = self.qteMain.qteBindKeyWidget

            # Unbind all keys from the input widget.
            self.qteMain.qteUnbindAllFromWidgetObject(self.qteText)

            macroName = register(self.ReplaceAll, replaceMacro=True)
            bind('!', macroName, self.qteText)

            macroName = register(self.ReplaceNext, replaceMacro=True)
            bind('<space>', macroName, self.qteText)

            macroName = register(self.SkipNext, replaceMacro=True)
            bind('n', macroName, self.qteText)

            macroName = register(self.Abort, replaceMacro=True)
            bind('q', macroName, self.qteText)
            bind('<enter>', macroName, self.qteText)

            self.toReplaceWith = self.qteText.toPlainText()
            self.qteTextPrefix.setText('mode 2')
            self.qteText.setText('<space> to replace, <n> to skip, '
                                 '<!> to replace all.')
        else:
            self.qteAbort(QtmacsMessage())
            self.qteMain.qteKillMiniApplet()

    def highlightNextMatch(self):
        """
        Select and highlight the next match in the set of matches.
        """
        # If this method was called on an empty input field (ie.
        # if the user hit <ctrl>+s again) then pick the default
        # selection.
        if self.qteText.toPlainText() == '':
            self.qteText.setText(self.defaultChoice)
            return

        # If the mathIdx variable is out of bounds (eg. the last possible
        # match is already selected) then wrap it around.
        if self.selMatchIdx < 0:
            self.selMatchIdx = 0
            return
        if self.selMatchIdx >= len(self.matchList):
            self.selMatchIdx = 0
            return

        # Shorthand.
        SCI = self.qteWidget

        # Undo the highlighting of the previously selected match.
        start, stop = self.matchList[self.selMatchIdx]
        line, col = SCI.lineIndexFromPosition(start)
        SCI.SendScintilla(SCI.SCI_STARTSTYLING, start, 0xFF)
        SCI.SendScintilla(SCI.SCI_SETSTYLING, stop - start, 30)
        self.selMatchIdx += 1

        # Highlight the next match.
        start, stop = self.matchList[self.selMatchIdx]
        SCI.SendScintilla(SCI.SCI_STARTSTYLING, start, 0xFF)
        SCI.SendScintilla(SCI.SCI_SETSTYLING, stop - start, 31)

        # Place the cursor at the start of the currently selected match.
        line, col = SCI.lineIndexFromPosition(start)
        SCI.setCursorPosition(line, col)

    def replaceSelected(self):
        """
        Replace the currently selected string with the new one.

        The method return **False** if another match to the right
        of the cursor exists, and **True** if not (ie. when the
        end of the document was reached).
        """
        SCI = self.qteWidget

        # Restore the original styling.
        self.qteWidget.SCISetStylingEx(0, 0, self.styleOrig)

        # Select the region spanned by the string to replace.
        start, stop = self.matchList[self.selMatchIdx]
        line1, col1 = SCI.lineIndexFromPosition(start)
        line2, col2 = SCI.lineIndexFromPosition(stop)
        SCI.setSelection(line1, col1, line2, col2)

        # Replace that region with the new string and move the cursor
        # to the end of that string.
        SCI.replaceSelectedText(self.toReplaceWith)
        line, col = SCI.lineIndexFromPosition(start + len(self.toReplaceWith))
        SCI.setCursorPosition(line, col)

        # Backup the new document style bits.
        line, col = SCI.getNumLinesAndColumns()
        text, style = self.qteWidget.SCIGetStyledText((0, 0, line, col))
        self.styleOrig = style

        # Determine if this was the last entry in the match list.
        if len(self.matchList) == self.selMatchIdx + 1:
            return False
        else:
            self.highlightAllMatches()
            return True

    def replaceAll(self):
        """
        Replace all matches after the current cursor position.

        This method calls ``replaceSelectedText`` until it returns
        **False**, and then closes the mini buffer.
        """
        while self.replaceSelected():
            pass

        self.qteWidget.SCISetStylingEx(0, 0, self.styleOrig)
        self.qteMain.qteKillMiniApplet()

    def compileMatchList(self):
        """
        Compile the list of spans of every match.
        """
        # Get the new sub-string to search for.
        self.matchList = []

        # Return immediately if the input field is empty.
        numChar = len(self.toReplace)
        if numChar == 0:
            return

        # Compile a list of all sub-string spans.
        stop = 0
        text = self.qteWidget.text()
        while True:
            start = text.find(self.toReplace, stop)
            if start == -1:
                break
            else:
                stop = start + numChar
                self.matchList.append((start, stop))

    def qteTextChanged(self):
        """
        Whenever the content of the input field changes renew
        the search for matches and highlight the new set.

        Note that this functionality is only enabled in Mode 1;
        Mode 2 (which queries for the replacement string)
        disconnects this slot.
        """
        self.toReplace = self.qteText.toPlainText()
        self.highlightAllMatches()

    def highlightAllMatches(self):
        """
        Search for sub-string matches.

        This method is triggered by Qt whenever the text changes,
        ie. whenever the user has altered the input. Extract the
        new input, find all matches, and highlight them accordingly.
        """
        # Remove any previous highlighting.
        self.qteWidget.SCISetStylingEx(0, 0, self.styleOrig)
        SCI = self.qteWidget

        # Compile a list of spans that contain the specified string.
        self.compileMatchList()

        # Return if the substring does not exist in the text.
        if len(self.matchList) == 0:
            return

        # ------------------------------------------------------------
        # Make a copy of the style bits of the document, overwrite
        # those parts containing a substring, and then write them
        # back all at once. This is much faster than calling the
        # styling methods repeatedly.
        # ------------------------------------------------------------

        # Make a copy of the document style bits and determine the
        # cursor position in the document.
        style = bytearray(self.styleOrig)
        pos = SCI.getCursorPosition()
        cur = SCI.positionFromLineIndex(*pos)

        # Style all matches.
        self.selMatchIdx = 0
        for start, stop in self.matchList:
            if start < cur:
                self.selMatchIdx += 1
            style[start:stop] = bytes(b'\x1e') * (stop - start)

        if self.selMatchIdx >= len(self.matchList):
            self.selMatchIdx = 0

        # Style the first match after the current cursor position
        # differently to indicate that it is the currently
        # selected one.
        start, stop = self.matchList[self.selMatchIdx]
        style[start:stop] = bytes(b'\x1f') * (stop - start)

        # Place the cursor at the start of the currently selected match.
        line, col = SCI.lineIndexFromPosition(start)
        SCI.setCursorPosition(line, col)

        # Apply the modified style array to the document.
        self.qteWidget.SCISetStylingEx(0, 0, style)

    def qteAbort(self, msgObj):
        """
        Restore the original cursor position because the user hit abort.
        """
        self.qteWidget.setCursorPosition(*self.cursorPosOrig)
        try:
            self.qteMain.qtesigAbort.disconnect(self.qteAbort)
        except TypeError:
            pass
        try:
            self.qteText.textChanged.disconnect(self.qteTextChanged)
        except TypeError:
            pass
        self.qteWidget.qteSetLexer(self.originalLexer)

    def qteToBeKilled(self):
        """
        Remove all selections and install the original lexer.
        """
        self.qteWidget.SCISetStylingEx(0, 0, self.styleOrig)
        self.qteWidget.qteSetLexer(self.originalLexer)


class QueryReplace(QtmacsMacro):
    """
    Search and replace.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QtmacsScintilla``
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QtmacsScintilla')

        # History of inserted strings.
        self.qteSearchHistory = []

    def qteRun(self):
        # Instantiate the customised new mini applet query object to
        # ask for the string to insert.
        query = QueryReplaceMiniApplet(
            self.qteApplet, self.qteWidget, prefix='Replace: ',
            history=self.qteSearchHistory)

        # The default choice is the last search term.
        if len(self.qteSearchHistory) > 0:
            query.defaultChoice = self.qteSearchHistory[-1]
        else:
            query.defaultChoice = ''

        # Install the query object as the mini applet and return
        # control to the event loop.
        self.qteMain.qteAddMiniApplet(query)


class QueryReplaceRegexpMiniApplet(QueryReplaceMiniApplet):
    """
    Query a regular expression and a substitution string.
    """

    def replaceSelected(self):
        """
        Replace the currently selected string with the new one.

        The method return **False** if another match to the right
        of the cursor exists, and **True** if not (ie. when the
        end of the document was reached).
        """
        SCI = self.qteWidget

        # Restore the original styling.
        self.qteWidget.SCISetStylingEx(0, 0, self.styleOrig)

        # Select the region spanned by the string to replace.
        start, stop = self.matchList[self.selMatchIdx]
        line1, col1 = SCI.lineIndexFromPosition(start)
        line2, col2 = SCI.lineIndexFromPosition(stop)
        SCI.setSelection(line1, col1, line2, col2)

        text = SCI.selectedText()
        text = re.sub(self.toReplace, self.toReplaceWith, text)

        # Replace that region with the new string and move the cursor
        # to the end of that string.
        SCI.replaceSelectedText(text)
        line, col = SCI.lineIndexFromPosition(start + len(text))
        SCI.setCursorPosition(line, col)

        # Backup the new document style bits.
        line, col = SCI.getNumLinesAndColumns()
        text, style = self.qteWidget.SCIGetStyledText((0, 0, line, col))
        self.styleOrig = style

        # Determine if this was the last entry in the match list.
        if len(self.matchList) == self.selMatchIdx + 1:
            return False
        else:
            self.highlightAllMatches()
            return True

    def compileMatchList(self):
        # Get the new sub-string to search for.
        curEntry = self.qteText.toPlainText()

        # Return immediately if the input field is empty.
        if len(curEntry) == 0:
            return

        # If the current user input does not constitute a valid
        # regular expression then do nothing.
        try:
            pat = re.compile(curEntry, re.MULTILINE + re.DOTALL)
        except re.error:
            return

        # Compile a list of all sub-string spans.
        text = self.qteWidget.text()
        self.matchList = [_.span() for _ in pat.finditer(text)]


class QueryReplaceRegexp(QtmacsMacro):
    """
    Search a regular expression and replace it with another custom string.

    This method uses Python's ``re`` module, in particular ``re.match``
    to find the string, and ``re.sub`` to replace it. As such, the
    search and replacement strings can be any regular expression syntax
    supported by the ``re`` module.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QtmacsScintilla``
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QtmacsScintilla')

        # History of inserted strings.
        self.qteSearchHistory = []

    def qteRun(self):
        # Instantiate the customised new mini applet query object to
        # ask for the string to insert.
        query = QueryReplaceRegexpMiniApplet(
            self.qteApplet, self.qteWidget, prefix='Replace: ',
            history=self.qteSearchHistory)

        # The default choice is the last search term.
        if len(self.qteSearchHistory) > 0:
            query.defaultChoice = self.qteSearchHistory[-1]
        else:
            query.defaultChoice = ''

        # Install the query object as the mini applet and return
        # control to the event loop.
        self.qteMain.qteAddMiniApplet(query)


# ------------------------------------------------------------
#                       Other macros
# ------------------------------------------------------------


class Undo(QtmacsMacro):
    """
    Trigger the ``undo`` function of the active widget.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QtmacsScintilla``
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QtmacsScintilla')

    def qteRun(self):
        self.qteWidget.undo()


class SaveFile(QtmacsMacro):
    """
    Save the current text to file.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QtmacsScintilla``
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QtmacsScintilla')

    def qteRun(self):
        fileName = self.qteApplet.qteAppletID()
        content = self.qteWidget.text()
        open(fileName, 'w').writelines(content)
        self.qteMain.qteStatus('Saved file <b>{}</b>'.format(fileName))
        self.qteWidget.setModified(False)


# ------------------------------------------------------------
#               Assign the default key bindings
# ------------------------------------------------------------

def install_macros_and_bindings(widgetObj):
    qteMain = qte_global.qteMain

    # ------------------------------------------------------------
    #  Install macros for alphanumeric characters. Note that all
    #  these characters are processed by the self-insert macro.
    # ------------------------------------------------------------

    # All alphanumerical characters are processed by the same macro,
    # namely 'self-insert'. Therefore, specify all alphanumerical
    # macros in a string and then install them in a loop. This is more
    # readable and flexible than writing three dozen bind commands.
    char_list = "abcdefghijklmnopqrstuvwxyz"
    char_list += char_list.upper()
    char_list += "0123456789"
    char_list += "'\\[],=-.;/`&^~*!|#(){}$<>%+?_"

    # Register the macro if it is not already.
    if not qteMain.qteIsMacroRegistered('self-insert', widgetObj):
        qteMain.qteRegisterMacro(SelfInsert, True, 'self-insert')

    # Install the self-insert macro for every character in the
    # char_list.
    for char in char_list:
        qteMain.qteBindKeyWidget(char, 'self-insert', widgetObj)

    # Install the self-insert macro for some additional keys that
    # cannot easily be added to char_list.
    qteMain.qteBindKeyWidget('"', 'self-insert', widgetObj)
    qteMain.qteBindKeyWidget('<space>', 'self-insert', widgetObj)
    qteMain.qteBindKeyWidget('<colon>', 'self-insert', widgetObj)

    # ------------------------------------------------------------
    #  Install macros and key-bindings for all other macros.
    # ------------------------------------------------------------

    # For readability purposes, compile a list where each entry
    # contains the macro name, macro class, and key binding associated
    # with this macro.
    macro_list = ((InsertNewline, '<return>'),
                  (InsertNewline, '<enter>'),
                  (DelCharBackward, '<backspace>'),
                  (DelChar, '<ctrl>+d'),
                  (ForwardChar, '<ctrl>+f'),
                  (ForwardWord, '<alt>+f'),
                  (BackwardChar, '<ctrl>+b'),
                  (BackwardWord, '<alt>+b'),
                  (KillWord, '<alt>+d'),
                  (BackwardKillWord, '<ctrl>+<backspace>'),
                  (MoveStartOfLine, '<ctrl>+a'),
                  (MoveEndOfLine, '<ctrl>+e'),
                  (NextLine, '<ctrl>+n'),
                  (PreviousLine, '<ctrl>+p'),
                  (EndOfDocument, '<alt>+>'),
                  (BeginningOfDocument, '<alt>+<'),
                  (OpenLine, '<ctrl>+o'),
                  (Undo, '<ctrl>+/'),
                  (ScrollDown, '<ctrl>+v'),
                  (ScrollUp, '<alt>+v'),
                  (KillLine, '<ctrl>+k'),
                  (Yank, '<ctrl>+y'),
                  (YankPop, '<alt>+y'),
                  (SaveFile, '<ctrl>+x <ctrl>+s'),
                  (IndentLine, '<tab>'),
                  (SetMark, '<ctrl>+<space>'),
                  (KillRegion, '<ctrl>+w'),
                  (UpperWord, '<alt>+u'),
                  (LowerWord, '<alt>+l'),
                  (CapitaliseWord, '<alt>+c'),
                  (TransposeWord, '<alt>+t'),
                  (TransposeChar, '<ctrl>+t'),
                  (StringInsertRectangle, None),
                  (KillRectangle, '<ctrl>+x <ctrl>+r'),
                  (YankRectangle, '<ctrl>+x <ctrl>+y'),
                  (SearchForward, '<ctrl>+s'),
                  (SearchForwardRegexp, None),
                  (QueryReplace, '<alt>+%'),
                  (QueryReplaceRegexp, None),
                  )

    # Iterate over the list of macros and their keybinding and
    # register them if they are not already.
    for macroCls, keysequence in macro_list:
        # Get the macro name.
        macroName = qteMain.qteMacroNameMangling(macroCls)

        # Register the macro if it has not been already.
        if not qteMain.qteIsMacroRegistered(macroName, widgetObj):
            qteMain.qteRegisterMacro(macroCls, True, macroName)

        # Assign the macro a keyboard shortcut if one is available.
        if keysequence is not None:
            qteMain.qteBindKeyWidget(keysequence, macroName, widgetObj)

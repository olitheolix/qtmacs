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
Default macros and key bindings for ``QTextEdit`` and its drop-in
replacement ``QtmacsTextEdit``.

The ``qteAddWidget`` method of ``QtmacsApplet`` uses this file to
endow ``QTextEdit`` and ``QtmacsTextEdit`` widgets with their default
macros and keybindings. The entry point to this module is the function
``install_macros_and_bindings``.

.. note: Macros are only registered if they do not yet exist. However,
   if a macro with the same name already does exists, then it is *not*
   replaced.

"""

import qtmacs.kill_list
import qtmacs.undo_stack
import qtmacs.type_check
import qtmacs.qte_global as qte_global

from PyQt4 import QtCore, QtGui
from qtmacs.base_macro import QtmacsMacro

# Shorthands.
QtmacsUndoCommand = qtmacs.undo_stack.QtmacsUndoCommand
QtmacsUndoStack = qtmacs.undo_stack.QtmacsUndoStack
QtmacsTextEdit = qtmacs.extensions.qtmacstextedit_widget.QtmacsTextEdit
type_check = qtmacs.type_check.type_check


# ------------------------------------------------------------
#                   Define all the macros
# ------------------------------------------------------------
class SelfInsert(QtmacsMacro):
    """
    Insert the last character from ``last_key_sequence`` defined in
    the global name space.

    The ``last_key_sequence`` variable is overwritten/updated every
    time the event handler in Qtmacs receives a new keyboard event.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QTextEdit``, ``QtmacsTextEdit``

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature(('QTextEdit', 'QtmacsTextEdit'))

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


class Undo(QtmacsMacro):
    """
    Trigger the ``undo`` function of the active widget.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QTextEdit``, ``QtmacsTextEdit``

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature(('QTextEdit', 'QtmacsTextEdit'))

    def qteRun(self):
        self.qteWidget.undo()


class UndoDelCharBackward(QtmacsUndoCommand):
    """
    Implement del-char-backwards and its inverse.

    This undo-object can undo any text- and HTML objects (eg. images).

    |Args|

    * ``qteWidget`` (**QWidget**): the widget to use.

    """

    @type_check
    def __init__(self, qteWidget):
        super().__init__()
        self.qteWidget = qteWidget
        self.cursorPos0 = self.selText = self.selPos = None
        self.removedChar = None

    def commit(self):
        """
        Insert the text at the current cursor position.
        """

        tc = self.qteWidget.textCursor()

        # If this is the first ever call to this undo/redo element then
        # backup the current cursor position and the selected text (may be
        # none). This information will be required for the redo operation
        # to position the cursor (and selected text) where it was at the
        # very first call.
        if self.cursorPos0 is None:
            self.cursorPos0 = tc.position()
            self.selText = tc.selection().toHtml()
            self.selStart = tc.selectionStart()
            self.selEnd = tc.selectionEnd()
        else:
            tc.setPosition(self.cursorPos0, QtGui.QTextCursor.MoveAnchor)

        # Remove the originally selected text (may be none).
        tc.setPosition(self.selStart, QtGui.QTextCursor.MoveAnchor)
        tc.setPosition(self.selEnd, QtGui.QTextCursor.KeepAnchor)
        tc.removeSelectedText()

        # Move to the start of the (just deleted) text block and insert
        # the characters there.
        if len(self.selText) > 0:
            pos = self.selStart
        else:
            pos = tc.position()
        tc.setPosition(pos)

        # Backup the cursor position before and after the deletion.
        self.cursorPos1 = tc.position()
        self.cursorPos2 = self.cursorPos1 - 1

        # Mark the area in between the two cursor positions, backup
        # the selected content, and remove it.
        tc.setPosition(self.cursorPos1, QtGui.QTextCursor.MoveAnchor)
        tc.setPosition(self.cursorPos2, QtGui.QTextCursor.KeepAnchor)
        self.removedChar = tc.selection().toHtml()
        tc.removeSelectedText()

        # Place the cursor at the new position.
        tc.setPosition(self.cursorPos2, QtGui.QTextCursor.KeepAnchor)

        self.qteWidget.setTextCursor(tc)

    def reverseCommit(self):
        """
        Remove the inserted character(s).
        """

        tc = self.qteWidget.textCursor()

        # Move the cursor to the point after the deletion, re-insert the
        # deleted characters, and move the cursor to the point before
        # the deletion occurred.
        tc.setPosition(self.cursorPos2, QtGui.QTextCursor.MoveAnchor)
        tc.insertHtml(self.removedChar)
        tc.setPosition(self.cursorPos1, QtGui.QTextCursor.KeepAnchor)

        # Add the previously selected text (if there was any). Note that the
        # text will not be 'selected' (ie. highlighted) this time.
        if len(self.selText) > 0:
            tc.setPosition(self.selStart)
            tc.insertHtml(self.selText)


class DelCharBackward(QtmacsMacro):
    """
    Delete character to the left of the cursor.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QTextEdit``, ``QtmacsTextEdit``

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature(('QTextEdit', 'QtmacsTextEdit'))

    def qteRun(self):
        if type(self.qteWidget) == QtmacsTextEdit:
            undoObj = UndoDelCharBackward(self.qteWidget)
            self.qteWidget.qteUndoStack.push(undoObj)
        else:
            self.qteWidget.textCursor().deletePreviousChar()


class UndoKillLine(QtmacsUndoCommand):
    """
    Implement kill-line and its inverse.

    This undo-object covers both text- and HTML objects (eg. images).

    |Args|

    * ``qteWidget`` (**QWidget**): the widget to use.

    """

    def __init__(self, qteWidget):
        super().__init__()
        self.qteWidget = qteWidget
        self.cursorPos0 = None

    def commit(self):
        """
        Delete the rest of the line.
        """

        # Get the text cursor for the current document and unselect everything.
        tc = self.qteWidget.textCursor()
        tc.clearSelection()

        # If this is the first ever call to this undo/redo element then
        # backup the current cursor position and the selected text (may be
        # none). This information will be required for the redo operation
        # to position the cursor (and selected text) where it was at the
        # very first call.
        if self.cursorPos0 is None:
            self.cursorPos0 = tc.position()

        # Ensure nothing is selected.
        tc.setPosition(self.cursorPos0, QtGui.QTextCursor.MoveAnchor)

        # Mark the rest of the line, store its content in this very object
        # and the global kill-list, and remove it.
        tc.movePosition(QtGui.QTextCursor.EndOfLine,
                        QtGui.QTextCursor.KeepAnchor)
        self.cursorPos1 = tc.selectionEnd()
        self.killedText = tc.selection().toHtml()
        data = qtmacs.kill_list.KillListElement(
            tc.selection().toPlainText(),
            tc.selection().toHtml(),
            'QtmacsTextEdit-Html')
        qte_global.kill_list.append(data)
        tc.removeSelectedText()

        # Apply the changes.
        self.qteWidget.setTextCursor(tc)

    def reverseCommit(self):
        """
        Re-insert the previously deleted line.
        """

        # Get the text cursor for the current document.
        tc = self.qteWidget.textCursor()

        # Re-insert the deleted text at the correct position.
        tc.setPosition(self.cursorPos0)
        tc.insertHtml(self.killedText)

        # Apply the changes.
        self.qteWidget.setTextCursor(tc)


class KillLine(QtmacsMacro):
    """
    Kill to the end of the line and place the content into the kill-list.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QTextEdit``, ``QtmacsTextEdit``

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature(('QTextEdit', 'QtmacsTextEdit'))

    def qteRun(self):
        if type(self.qteWidget) == QtmacsTextEdit:
            undoObj = UndoKillLine(self.qteWidget)
            self.qteWidget.qteUndoStack.push(undoObj)
        else:
            self.qteWidget.textCursor().deletePreviousChar()


class UndoYank(QtmacsUndoCommand):
    """
    Implement yank and its inverse.

    This undo-object covers both text- and HTML objects (eg. images).

    |Args|

    * ``qteWidget`` (**QWidget**): the widget to use.
    * ``yankText`` (**str**): text to insert (can be plain text or Html).
    * ``textType`` (**bool**): whether or not ``yankText`` is plain text
       or not.

    """

    @type_check
    def __init__(self, qteWidget, yankText: str, textType: bool):
        super().__init__()
        self.qteWidget = qteWidget
        self.textType = textType
        self.yankText = yankText
        self.cursorPos0 = None

    def commit(self):
        """
        Delete the rest of the line.
        """

        # Get the text cursor for the current document and unselect
        # everything.
        tc = self.qteWidget.textCursor()
        tc.clearSelection()

        # If this is the first ever call to this undo/redo element then
        # backup the current cursor position and the selected text (may be
        # none). This information will be required for the redo operation
        # to position the cursor (and selected text) where it was at the
        # very first call.
        if self.cursorPos0 is None:
            self.cursorPos0 = tc.position()
        else:
            tc.setPosition(self.cursorPos0, QtGui.QTextCursor.MoveAnchor)

        # Insert the element and keep track of how much the cursor has
        # moved. This is trivial to determine automatically if
        # `yankText` is pure text, but if it is HTML code then it is
        # safer to rely on Qt's builtin ``position`` method.
        if self.textType:
            tc.insertText(self.yankText)
        else:
            tc.insertHtml(self.yankText)
        self.cursorPos1 = tc.position()

        # Apply the changes.
        self.qteWidget.setTextCursor(tc)

    def reverseCommit(self):
        """
        Re-insert the previously removed character(s).
        """
        # Get the text cursor for the current document.
        tc = self.qteWidget.textCursor()

        # Mark the previously inserted text and remove it.
        tc.setPosition(self.cursorPos0, QtGui.QTextCursor.MoveAnchor)
        tc.setPosition(self.cursorPos1, QtGui.QTextCursor.KeepAnchor)
        tc.removeSelectedText()
        tc.setPosition(self.cursorPos0, QtGui.QTextCursor.MoveAnchor)

        # Apply the changes.
        self.qteWidget.setTextCursor(tc)


class Yank(QtmacsMacro):
    """
    Re-insert the last killed element.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QtmacsTextEdit``

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature(('QTextEdit', 'QtmacsTextEdit'))

    def qteRun(self):
        # Do nothing if the kill-list is empty.
        if len(qte_global.kill_list) == 0:
            return

        # Fetch the last element in the kill-list. Then construct a
        # ``UndoYank`` object that, depending on the type of the last
        # element, inserts either a text string or a Html string.
        el = qte_global.kill_list[-1]
        if el.dataType() == "QtmacsTextEdit-Html":
            undoObj = UndoYank(self.qteWidget, el.dataCustom(), False)
        else:
            undoObj = UndoYank(self.qteWidget, el.dataText(), True)

        # Push the undo-element onto the undo-stack to put the changes
        # into effect.
        self.qteWidget.qteUndoStack.push(undoObj)

        # Trigger the 'yank-qtmacs_text_edit' hook (intercepted by yank-pop).
        self.qteMain.qteRunHook('yank-qtmacs_text_edit')


class YankPop(QtmacsMacro):
    """
    Replace the just yanked element with the previous one in the
    kill-list. This macro can handle plain text and Html.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QtmacsTextEdit``

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature(('QTextEdit', 'QtmacsTextEdit'))

        self.killListIdx = -1
        self.qteMain.qteConnectHook('yank-qtmacs_text_edit', self.enableHook)

    def qteRun(self):
        # Do nothing if the kill-list contains no earlier element.
        if self.killListIdx < 0:
            return

        # Remove the last yanked text along with the corresponding
        # undo object.
        undoObj = self.qteWidget.qteUndoStack.pop()
        undoObj.reverseCommit()

        # Retrieve the element to yank from the kill-list and insert
        # it by creating another UndoYank object. Note that there is
        # no UndoPopYank object!
        el = qte_global.kill_list[self.killListIdx]
        if el.dataType() == "QtmacsTextEdit-Html":
            undoObj = UndoYank(self.qteWidget, el.dataCustom(), False)
        else:
            undoObj = UndoYank(self.qteWidget, el.dataText(), True)

        self.qteWidget.qteUndoStack.push(undoObj)

        # Decrement the kill-list index. The effect is that at the
        # next invokation an earlier element in the kill-list will
        # be chosen.
        self.killListIdx -= 1

    def disableHook(self, msgObj):
        """
        Disable yank-pop.

        The ``enableHook`` method (see below) connects this method
        to the ``qtesigKeyseqComplete`` signal to catch
        consecutive calls to this ``yank-pop`` macro. Once the user
        issues a keysequence for any other macro but this one, the
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

        This method is connected to the 'yank-qtmacs_text_edit' hook
        (triggered by the yank macro) to ensure that yank-pop only
        gets activated afterwards.
        """
        self.killListIdx = len(qte_global.kill_list) - 2
        self.qteMain.qtesigKeyseqComplete.connect(self.disableHook)


class OpenLine(QtmacsMacro):
    """
    Open a new line (ie. insert a new-line at the current cursor position).

    |Signature|

    * *applet*: '*'
    * *widget*: ``QTextEdit``, ``QtmacsTextEdit``

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature(('QTextEdit', 'QtmacsTextEdit'))

    def qteRun(self):
        # Remember the current cursor position.
        tc = self.qteWidget.textCursor()
        pos = tc.position()

        # Construct a new-line key event and pass it through the keypressed
        # method which knows how to undo it if necessary.
        modQt, keyQt = qte_global.Qt_key_map['1']
        key_event = QtGui.QKeyEvent(QtCore.QEvent.KeyPress, keyQt, modQt, '\n')
        self.qteWidget.keyPressEvent(key_event)

        # Now that the new line was opened, return the cursor to the
        # original position.
        tc.setPosition(pos)
        self.qteWidget.setTextCursor(tc)


class ForwardChar(QtmacsMacro):
    """
    Move cursor one character to the right.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QTextEdit``, ``QtmacsTextEdit``

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature(('QTextEdit', 'QtmacsTextEdit'))

    def qteRun(self):
        tc = self.qteWidget.textCursor()
        tc.movePosition(QtGui.QTextCursor.NextCharacter)
        self.qteWidget.setTextCursor(tc)


class BackwardChar(QtmacsMacro):
    """
    Move cursor one character to the left.
    |Signature|

    * *applet*: '*'
    * *widget*: ``QTextEdit``, ``QtmacsTextEdit``

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature(('QTextEdit', 'QtmacsTextEdit'))

    def qteRun(self):
        tc = self.qteWidget.textCursor()
        tc.movePosition(QtGui.QTextCursor.PreviousCharacter)
        self.qteWidget.setTextCursor(tc)


class ForwardWord(QtmacsMacro):
    """
    Move cursor to beginning of next word.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QTextEdit``, ``QtmacsTextEdit``

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature(('QTextEdit', 'QtmacsTextEdit'))

    def qteRun(self):
        tc = self.qteWidget.textCursor()
        tc.movePosition(QtGui.QTextCursor.NextWord)
        self.qteWidget.setTextCursor(tc)


class BackwardWord(QtmacsMacro):
    """
    Move cursor to beginning of previous word.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QTextEdit``, ``QtmacsTextEdit``

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature(('QTextEdit', 'QtmacsTextEdit'))

    def qteRun(self):
        tc = self.qteWidget.textCursor()
        tc.movePosition(QtGui.QTextCursor.PreviousWord)
        self.qteWidget.setTextCursor(tc)


class MoveStartOfLine(QtmacsMacro):
    """
    Move cursor to the beginning of the line.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QTextEdit``, ``QtmacsTextEdit``

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature(('QTextEdit', 'QtmacsTextEdit'))

    def qteRun(self):
        tc = self.qteWidget.textCursor()
        tc.movePosition(QtGui.QTextCursor.StartOfLine)
        self.qteWidget.setTextCursor(tc)


class MoveEndOfLine(QtmacsMacro):
    """
    Move cursor to the end of the line.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QTextEdit``, ``QtmacsTextEdit``

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature(('QTextEdit', 'QtmacsTextEdit'))

    def qteRun(self):
        tc = self.qteWidget.textCursor()
        tc.movePosition(QtGui.QTextCursor.EndOfLine)
        self.qteWidget.setTextCursor(tc)


class NextLine(QtmacsMacro):
    """
    Move cursor to next line.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QTextEdit``, ``QtmacsTextEdit``

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature(('QTextEdit', 'QtmacsTextEdit'))

    def qteRun(self):
        tc = self.qteWidget.textCursor()
        tc.movePosition(QtGui.QTextCursor.Down)
        self.qteWidget.setTextCursor(tc)


class PreviousLine(QtmacsMacro):
    """
    Move cursor to previous line.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QTextEdit``, ``QtmacsTextEdit``

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature(('QTextEdit', 'QtmacsTextEdit'))

    def qteRun(self):
        tc = self.qteWidget.textCursor()
        tc.movePosition(QtGui.QTextCursor.Up)
        self.qteWidget.setTextCursor(tc)


class EndOfBuffer(QtmacsMacro):
    """
    Move cursor to the very end of the ``QTextEdit``.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QTextEdit``, ``QtmacsTextEdit``

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature(('QTextEdit', 'QtmacsTextEdit'))

    def qteRun(self):
        tc = self.qteWidget.textCursor()
        tc.movePosition(QtGui.QTextCursor.End)
        self.qteWidget.setTextCursor(tc)


class BeginningOfBuffer(QtmacsMacro):
    """
    Move cursor to the very beginning of the ``QTextEdit``.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QTextEdit``, ``QtmacsTextEdit``
    * *widget*: '*'

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature(('QTextEdit', 'QtmacsTextEdit'))

    def qteRun(self):
        tc = self.qteWidget.textCursor()
        tc.movePosition(QtGui.QTextCursor.Start)
        self.qteWidget.setTextCursor(tc)


class ScrollDown(QtmacsMacro):
    """
    Scroll up by approximately as much as is currently visible.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QTextEdit``, ``QtmacsTextEdit``

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature(('QTextEdit', 'QtmacsTextEdit'))

    def qteRun(self):
        bar = self.qteWidget.verticalScrollBar()
        tot_height = self.qteWidget.maximumViewportSize().height()
        new_value = bar.value() + int(0.9 * tot_height)
        bar.setValue(new_value)


class ScrollUp(QtmacsMacro):
    """
    Scroll down by approximately as much as is currently visible.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QTextEdit``, ``QtmacsTextEdit``

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature(('QTextEdit', 'QtmacsTextEdit'))

    def qteRun(self):
        bar = self.qteWidget.verticalScrollBar()
        tot_height = self.qteWidget.maximumViewportSize().height()
        new_value = bar.value() - int(0.9 * tot_height)
        bar.setValue(new_value)


class StrikeOutNext(QtmacsMacro):
    """
    Strike out the character to the right of the cursor.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QTextEdit``, ``QtmacsTextEdit``

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature(('QTextEdit', 'QtmacsTextEdit'))

    def qteRun(self):
        # Get the text cursor and character format and enable the
        # strikeout feature.
        tc = self.qteWidget.textCursor()
        cf = tc.charFormat()
        cf.setFontStrikeOut(True)

        # Select next character by moving the cursor and keeping the
        # anchor.
        tc.movePosition(QtGui.QTextCursor.NextCharacter,
                        QtGui.QTextCursor.KeepAnchor)

        # Apply the strikeout format to the just selected character.
        tc.setCharFormat(cf)

        # Clear the selection again.
        tc.clearSelection()


class ToggleStrikeOut(QtmacsMacro):
    """
    Toggle the strikeout formatting for the next character.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QTextEdit``, ``QtmacsTextEdit``

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature(('QTextEdit', 'QtmacsTextEdit'))

    def qteRun(self):
        # Get the text cursor and character format.
        tc = self.qteWidget.textCursor()
        cf = tc.charFormat()

        # Mark the next character.
        tc.movePosition(QtGui.QTextCursor.NextCharacter,
                        QtGui.QTextCursor.KeepAnchor)

        # Invert the strike-out format of the next character.
        if tc.charFormat().fontStrikeOut():
            # Already struck out: make it normal again.
            cf.setFontStrikeOut(False)
            tc.setCharFormat(cf)
        else:
            # Normal character: strike it out.
            cf.setFontStrikeOut(True)
            tc.setCharFormat(cf)

        # Move the cursor back to the original position thereby also
        # removing the anchor.
        tc.movePosition(QtGui.QTextCursor.PreviousCharacter,
                        QtGui.QTextCursor.KeepAnchor)


class BracketMatching(QtmacsMacro):
    """
    Highlight matching parenthesis.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QTextEdit``, ``QtmacsTextEdit``

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature(('QTextEdit', 'QtmacsTextEdit'))
        self.charToHighlight = ('(', ')')

    def qteRun(self):
        class BracketMatchingData:
            """
            Widget specific admin information for the bracket matching macro.
            """
            def __init__(self):
                self.isEnabled = False
                self.matchingPositions = None
                self.oldCharFormats = None

        # Retrieve the macro specific data structure from the sender applet.
        data = self.qteMacroData()
        if not data:
            data = BracketMatchingData()

        if data.isEnabled:
            self.qteWidget.cursorPositionChanged.disconnect(
                self.cursorPositionChangedEvent)
            data.isEnabled = False
            self.qteMain.qteStatus('Bracket Matching Disabled')
        else:
            self.qteWidget.cursorPositionChanged.connect(
                self.cursorPositionChangedEvent)
            data.isEnabled = True
            self.qteMain.qteStatus('Bracket Matching Enabled')

        self.qteSaveMacroData(data)

    def cursorPositionChangedEvent(self):
        """
        Update the highlighting.

        This is an overloaded version of the native Qt slot of
        ``QTextEdit``.

        In this class, the purpose of this slot is to check if the
        character to the right of the cursor needs highlighting,
        assuming there is a second character to pair with it.

        |Args|

        * **None**

        |Returns|

        * **None**

        |Raises|

        * **None**
        """

        # Determine the sender and cursor position.
        qteWidget = self.sender()
        tc = qteWidget.textCursor()
        origin = tc.position()

        # Remove all the highlighting. Since this will move the
        # cursor, first disconnect this very routine to avoid an
        # infinite recursion.
        qteWidget.cursorPositionChanged.disconnect(
            self.cursorPositionChangedEvent)
        self.qteRemoveHighlighting(qteWidget)
        qteWidget.cursorPositionChanged.connect(
            self.cursorPositionChangedEvent)

        # If we are beyond the last character (for instance because
        # the cursor was explicitly moved to the end of the buffer)
        # then there is no character to the right and will result in
        # an error when trying to fetch it.
        if origin >= len(qteWidget.toPlainText()):
            return
        else:
            # It is save to retrieve the character to the right of the
            # cursor.
            char = qteWidget.toPlainText()[origin]

        # Return if the character is not in the matching list.
        if char not in self.charToHighlight:
            return

        # Disconnect the 'cursorPositionChanged' signal from this
        # function because it will make changes to the cursor position
        # and would therefore immediately trigger itself, resulting in
        # an infinite recursion.
        qteWidget.cursorPositionChanged.disconnect(
            self.cursorPositionChangedEvent)

        # If we got until here "char" must be one of the two
        # characters to highlight.
        if char == self.charToHighlight[0]:
            start = origin
            # Found the first character, so now look for the second
            # one. If this second character does not exist the
            # function returns '-1' which is safe because the
            # ``self.highlightCharacter`` method can deal with this.
            stop = qteWidget.toPlainText().find(self.charToHighlight[1],
                                                start + 1)
        else:
            # Found the second character so the start index is indeed
            # the stop index.
            stop = origin

            # Search for the preceeding first character.
            start = qteWidget.toPlainText().rfind(self.charToHighlight[0],
                                                  0, stop)

        # Highlight the characters.
        oldCharFormats = self.highlightCharacters(qteWidget, (start, stop),
                                                  QtCore.Qt.blue, 100)

        # Store the positions of the changed character in the
        # macroData structure of this widget.
        data = self.qteMacroData(qteWidget)
        data.matchingPositions = (start, stop)
        data.oldCharFormats = oldCharFormats
        self.qteSaveMacroData(data, qteWidget)

        # Reconnect the 'cursorPositionChanged' signal.
        qteWidget.cursorPositionChanged.connect(
            self.cursorPositionChangedEvent)

    def qteRemoveHighlighting(self, widgetObj):
        """
        Remove the highlighting from previously highlighted characters.

        The method access instance variables to determine which
        characters are currently highlighted and have to be converted
        to non-highlighted ones.

        |Args|

        * ``widgetObj`` (**QWidget**): the ``QTextEdit`` to use.

        |Returns|

        * **None**

        |Raises|

        * **None**
        """

        # Retrieve the widget specific macro data.
        data = self.qteMacroData(widgetObj)
        if not data:
            return

        # If the data structure is empty then no previously
        # highlighted characters exist in this particular widget, so
        # do nothing.
        if not data.matchingPositions:
            return

        # Restore the original character formats, ie. undo the
        # highlighting changes.
        self.highlightCharacters(widgetObj, data.matchingPositions,
                                 QtCore.Qt.black, 50, data.oldCharFormats)

        # Clear the data structure to indicate that no further
        # highlighted characters exist in this particular widget.
        data.matchingPositions = None
        data.oldCharFormats = None
        self.qteSaveMacroData(data, widgetObj)

    def highlightCharacters(self, widgetObj, setPos, colorCode,
                            fontWeight, charFormat=None):
        """
        Change the character format of one or more characters.

        If ``charFormat`` is **None** then only the color and font
        weight of the characters are changed to ``colorCode`` and
        ``fontWeight``, respectively.

        |Args|

        * ``widgetObj`` (**QWidget**): the ``QTextEdit`` holding
          the characters.
        * ``setPos`` (**tuple** of **int**): character positions
          inside the widget.
        * ``colorCode`` (**QColor**): eg. ``QtCore.Qt.blue``
        * ``fontWeight`` (**int**): font weight.
        * ``charFormat`` (**QTextCharFormat**): the character
          format to apply (see Qt documentation for details.)

        |Returns|

        * **list**: the original character format of the replaced
          characters. This list has the same length as ``setPos``.

        |Raises|

        * **None**
        """

        # Get the text cursor and character format.
        textCursor = widgetObj.textCursor()
        oldPos = textCursor.position()
        retVal = []

        # Change the character formats of all the characters placed at
        # the positions ``setPos``.
        for ii, pos in enumerate(setPos):
            # Extract the position of the character to modify.
            pos = setPos[ii]

            # Ignore invalid positions. This can happen if the second
            # character does not exist and the find-functions in the
            # ``cursorPositionChangedEvent`` method returned
            # '-1'. Also, store **None** as the format for this
            # non-existent character.
            if pos < 0:
                retVal.append(None)
                continue

            # Move the text cursor to the specified character position
            # and store its original character format (necessary to
            # "undo" the highlighting once the cursor was moved away
            # again).
            textCursor.setPosition(pos)
            retVal.append(textCursor.charFormat())

            # Change the character format. Either use the supplied
            # one, or use a generic one.
            if charFormat:
                # Use a specific character format (usually used to
                # undo the changes a previous call to
                # 'highlightCharacters' has made).
                fmt = charFormat[ii]
            else:
                # Modify the color and weight of the current character format.
                fmt = textCursor.charFormat()

                # Get the brush and specify its foreground color and
                # style. In order to see the characters it is
                # necessary to explicitly specify a solidPattern style
                # but I have no idea why.
                myBrush = fmt.foreground()
                myBrush.setColor(colorCode)
                myBrush.setStyle(QtCore.Qt.SolidPattern)
                fmt.setForeground(myBrush)
                fmt.setFontWeight(fontWeight)

            # Select the character and apply the selected format.
            textCursor.movePosition(QtGui.QTextCursor.NextCharacter,
                                    QtGui.QTextCursor.KeepAnchor)
            textCursor.setCharFormat(fmt)

        # Apply the textcursor to the current element.
        textCursor.setPosition(oldPos)
        widgetObj.setTextCursor(textCursor)
        return retVal


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
    qteMain.qteBindKeyWidget('<return>', 'self-insert', widgetObj)
    qteMain.qteBindKeyWidget('<enter>', 'self-insert', widgetObj)

    # ------------------------------------------------------------
    #  Install macros and key-bindings for all other macros.
    # ------------------------------------------------------------

    # For readability purposes, compile a list where each entry
    # contains the macro name, macro class, and key binding associated
    # with this macro.
    macro_list = ((DelCharBackward, '<backspace>'),
                  (ForwardChar, '<ctrl>+f'),
                  (ForwardWord, '<alt>+f'),
                  (BackwardChar, '<ctrl>+b'),
                  (BackwardWord, '<alt>+b'),
                  (MoveStartOfLine, '<ctrl>+a'),
                  (MoveEndOfLine, '<ctrl>+e'),
                  (NextLine, '<ctrl>+n'),
                  (PreviousLine, '<ctrl>+p'),
                  (EndOfBuffer, '<alt>+>'),
                  (BeginningOfBuffer, '<alt>+<'),
                  (ToggleStrikeOut, None),
                  (StrikeOutNext, None),
                  (BracketMatching, '<ctrl>+m'),
                  (OpenLine, '<ctrl>+o'),
                  (Undo, '<ctrl>+/'),
                  (ScrollDown, '<ctrl>+v'),
                  (ScrollUp, '<alt>+v'),
                  (KillLine, '<ctrl>+k'),
                  (Yank, '<ctrl>+y'),
                  (YankPop, '<alt>+y'),
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

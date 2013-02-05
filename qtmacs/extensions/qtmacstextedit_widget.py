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
A drop-in replacement for ``QTextEdit`` with a more Emacs like undo
behaviour.

It is safe to use::

    from qtmacstextedit_widget import *

Here is an example::

    from PyQt4 import QtCore, QtGui
    from qtmacs.base_applet import QtmacsApplet
    from qtmacs.extensions.qtmacstextedit_widget import QtmacsTextEdit

    # Get a reference to the main instance of Qtmacs.
    import qtmacs.qte_global as qte_global
    qteMain = qte_global.qteMain


    class TestQtmacsTextEdit(QtmacsApplet):
        \"\"\"
        Demonstrate the use of ``QtmacsTextEdit`` in an applet.
        \"\"\"
        def __init__(self, appletID):
            # Initialise the base class.
            super().__init__(appletID)

            # Add a QtmacsTextEdit widget to the applet.
            self.qteText = self.qteAddWidget(QtmacsTextEdit(self))


    qteMain.qteRegisterApplet(TestQtmacsTextEdit)

Put this into a file (eg. `demo.py`), run

.. code-block:: bash

   ./qtmacs --load demo.py

instantiate the applet with ``<ctrl>+x <ctrl>+a``, and type
'TextQtmacsTextEdit'.

"""

import qtmacs.type_check
import qtmacs.undo_stack
from PyQt4 import QtCore, QtGui

# Shorthands
type_check = qtmacs.type_check.type_check
QtmacsUndoCommand = qtmacs.undo_stack.QtmacsUndoCommand
QtmacsUndoStack = qtmacs.undo_stack.QtmacsUndoStack


class UndoGenericQtmacsTextEdit(QtmacsUndoCommand):
    """
    Generic undo-object to revert an arbitrary change in the document.

    This undo command takes a snapshot of the current state and
    requires another snapshot from before the changes were made.

    Example::

        # Backup the current state of the document for the undo
        # object later.
        textBefore = self.qteWidget.toHtml()

        # ... arbitrary changes to the text in self.qteWidget.

        # Create the generic undo object.
        undoObj = UndoGenericQtmacsTextEdit(self.qteWidget, textBefore)
        self.qteWidget.qteUndoStack.push(undoObj)

    """
    @type_check
    def __init__(self, qteWidget, before):
        super().__init__()
        self.qteWidget = qteWidget
        self.before = before
        self.after = None

    def placeCursor(self, pos):
        """
        Try to place the cursor in ``line`` at ``col`` if possible.
        If this is not possible, then place it at the end.
        """
        if pos > len(self.qteWidget.toPlainText()):
            pos = len(self.qteWidget.toPlainText())

        tc = self.qteWidget.textCursor()
        tc.setPosition(pos)
        self.qteWidget.setTextCursor(tc)

    def commit(self):
        """
        Put the document into the new state.
        """
        if self.after is None:
            # If this is the first 'commit' call then do not make
            # any changes but store the current document state.
            self.after = self.qteWidget.toHtml()
        else:
            # Put the document into the edited state.
            pos = self.qteWidget.textCursor().position()
            self.qteWidget.setHtml(self.after)
            self.placeCursor(pos)

    def reverseCommit(self):
        """
        Reverse the document to the original state.
        """
        print(self.after == self.before)
        pos = self.qteWidget.textCursor().position()
        self.qteWidget.setHtml(self.before)
        self.placeCursor(pos)


class UndoSelfInsert(QtmacsUndoCommand):
    """
    Implement the self-insert and its reverse.

    |Args|

    * ``qteWidget`` (**QWidget**): the widget to use.
    * ``text`` (**str**): text/character to insert.

    """

    def __init__(self, qteWidget, text):
        super().__init__()
        self.text = text
        self.qteWidget = qteWidget
        self.cursorPos0 = self.selText = self.selPos = None

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

        # Backup the cursor position before the insertion operation,
        # insert the new character(s), move the cursor forward, and
        # backup the new cursor position as well.
        self.cursorPos1 = tc.position()
        tc.insertText(self.text)
        self.cursorPos2 = tc.position()

        self.qteWidget.setTextCursor(tc)

    def reverseCommit(self):
        """
        Remove the inserted character(s).
        """

        tc = self.qteWidget.textCursor()

        # Select the area from before the insertion to after the insertion,
        # and remove it.
        tc.setPosition(self.cursorPos1, QtGui.QTextCursor.MoveAnchor)
        tc.setPosition(self.cursorPos2, QtGui.QTextCursor.KeepAnchor)
        tc.removeSelectedText()

        # Add the previously selected text (if there was any). Note that the
        # text will not be 'selected' (ie. highlighted) this time.
        if len(self.selText) > 0:
            tc.setPosition(self.selStart)
            tc.insertHtml(self.selText)


class UndoPaste(QtmacsUndoCommand):
    """
    Implement pasting and its reverse.

    This command can paste both text and images from the clipboard.

    |Args|

    * ``qteWidget`` (**QWidget**): the widget to use.
    * ``data`` (**QMimeData**): MIME object.
    * ``pasteCnt`` (**int**): used to uniquely enumerate the document resource
        when inserting an image.

    """

    def __init__(self, qteWidget, data, pasteCnt):
        super().__init__()
        self.qteWidget = qteWidget
        self.pasteCnt = pasteCnt

        # If an image is present, then the date is an image, otherwise
        # it is text.
        self.isImage = data.hasImage()
        if self.isImage:
            self.data = QtGui.QImage(data.imageData())
        else:
            self.data = data.text()

    def commit(self):
        """
        Insert the text at the current cursor position.
        """

        # Backup and remove the currently selected text (may be none).
        tc = self.qteWidget.textCursor()
        self.selText = tc.selection().toHtml()
        self.selStart = tc.selectionStart()
        self.selEnd = tc.selectionEnd()
        tc.removeSelectedText()

        # Move to the start of the (just deleted) text block and insert
        # the characters there.
        tc.setPosition(self.selStart)

        # If the MIME data contained an image then create a new HTML
        # resource for it and insert it with the HTML syntax for adding
        # an image. On the other hand, if the resource was simply a string,
        # then just add it.
        if self.isImage:
            imgName = "pastedImage_{}".format(str(self.pasteCnt))
            document = self.qteWidget.document()
            document.addResource(QtGui.QTextDocument.ImageResource,
                                 QtCore.QUrl(imgName), self.data)
            self.qteWidget.setDocument(document)
            tc.insertHtml('<img src={}>'.format(imgName))
        else:
            tc.insertText(self.data)

        # Update the text cursor in the document.
        self.qteWidget.setTextCursor(tc)

    def reverseCommit(self):
        """
        Remove the inserted character(s).
        """

        # Move the cursor to the right of the text to delete.
        tc = self.qteWidget.textCursor()

        # Delete as many characters as necessary. For an image that would
        # be exactly 1 even though the HTML code to embed that image is usually
        # longer. For text, it would be as many characters as the pasted text
        # was long.
        if self.isImage:
            dataLen = 1
        else:
            dataLen = len(self.data)

        tc.setPosition(self.selStart + dataLen, QtGui.QTextCursor.MoveAnchor)
        for ii in range(dataLen):
            tc.deletePreviousChar()

        # Add the previously selected text (this may be none).
        tc.insertHtml(self.selText)
        self.qteWidget.setTextCursor(tc)


class QtmacsTextEdit(QtGui.QTextEdit):
    """
    A drop-in replacement for ``QTextEdit`` with Emacs like undo behaviour.

    Under the hood this class has a ``qteUndoStack`` attribute (a
    ``QtmacsUndoStack`` instance) and overloaded ``undo``, ``redo``,
    ``insertFromMimeData``, and ``keyPressEvent`` methods to
    facilitate an Emacs like undo behaviour. Note that as a
    consequence, the ``redo`` method now does nothing.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Instantiate an undo stack for this widget.
        self.qteUndoStack = QtmacsUndoStack()

        # Count the number of pasted objects. This is necessary to enumerate
        # the images pasted into the document in order to give them unique
        # names.
        self.pasteCnt = 0

    def insertFromMimeData(self, data):
        """
        Paste the MIME data at the current cursor position.

        This method also adds another undo-object to the undo-stack.
        """
        undoObj = UndoPaste(self, data, self.pasteCnt)
        self.pasteCnt += 1
        self.qteUndoStack.push(undoObj)

    def keyPressEvent(self, keyEvent):
        """
        Insert the character at the current cursor position.

        This method also adds another undo-object to the undo-stack.
        """
        undoObj = UndoSelfInsert(self, keyEvent.text())
        self.qteUndoStack.push(undoObj)

    def undo(self):
        """
        Undo the last change.
        """
        self.qteUndoStack.undo()

    def redo(self):
        """
        This method does nothing anymore.
        """
        pass

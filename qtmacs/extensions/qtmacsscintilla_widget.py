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
A drop-in replacement for ``QSciScintilla`` with a more Emacs like undo
behaviour.

It is safe to use::

    from qtmacs_scintilla import *

Here is an example::

    from PyQt4 import QtCore, QtGui
    from qtmacs.base_applet import QtmacsApplet
    from qtmacs.extensions.qtmacsscintilla_widget import QtmacsScintilla

    # Get a reference to the main instance of Qtmacs.
    import qtmacs.qte_global as qte_global
    qteMain = qte_global.qteMain


    class TestQtmacsScintilla(QtmacsApplet):
        \"\"\"
        Demonstrate the use of ``QtmacsScintilla`` in an applet.
        \"\"\"
        def __init__(self, appletID):
            # Initialise the base class.
            super().__init__(appletID)

            # Add a QtmacsScintilla widget to the applet.
            self.qteText = self.qteAddWidget(QtmacsScintilla(self))


    qteMain.qteRegisterApplet(TestQtmacsScintilla)

Put this into a file (eg. `demo.py`), run

.. code-block:: bash

   ./qtmacs --load demo.py

instantiate the applet with ``<ctrl>+x <ctrl>+a``, and type
'TextQtmacsScintilla'.
"""

import qtmacs.kill_list
import qtmacs.type_check
import qtmacs.undo_stack
import qtmacs.qte_global as qte_global
from PyQt4 import QtCore, QtGui, Qsci

# Shorthands:
type_check = qtmacs.type_check.type_check
KillListElement = qtmacs.kill_list.KillListElement
QtmacsUndoStack = qtmacs.undo_stack.QtmacsUndoStack
QtmacsUndoCommand = qtmacs.undo_stack.QtmacsUndoCommand

# Global variables:
qteMain = qte_global.qteMain


class UndoRemoveSelectedText(QtmacsUndoCommand):
    """
    Implement ``removeSelectedText`` and its undo operation.

    This undo object removes the selected text and places the
    content into the kill list. If no text is selected then
    nothing happens.

    |Args|

    * ``qteWidget`` (**QWidget**): the widget to use.

    |Raises|

    * **QtmacsArgumentError** if at least one argument has an invalid type.
    """

    @type_check
    def __init__(self, qteWidget):
        super().__init__()
        self.qteWidget = qteWidget
        self.baseClass = super(type(qteWidget), qteWidget)
        self.removedText = None
        self.selectionPos = None

        # Determine if the widget has a selection.
        if qteWidget.hasSelectedText():
            self.selectionPos = qteWidget.getSelection()
        else:
            return

        # Backup the text and style.
        text, self.style = qteWidget.SCIGetStyledText(self.selectionPos)
        self.removedText = text.decode('utf-8')

    def commit(self):
        # Do nothing if no selection was available upon construction.
        if self.selectionPos is None:
            return

        # Remove the selection.
        self.qteWidget.setSelection(*self.selectionPos)
        self.baseClass.removeSelectedText()

        # Add the just killed text to the kill-list.
        data = KillListElement(self.removedText, None, 'QtmacsScintilla-Text')
        qte_global.kill_list.append(data)

    def reverseCommit(self):
        """
        Reinsert the killed word.
        """

        # Do nothing if no selection was available upon construction.
        if self.selectionPos is None:
            return

        # Insert the text at the specified position.
        line, col = self.selectionPos[:2]
        self.baseClass.insertAt(self.removedText, line, col)

        # Add the styling information.
        self.qteWidget.SCISetStylingEx(line, col, self.style)

        # Place the cursor at the end of the selection.
        line, col = self.selectionPos[2:]
        self.qteWidget.setCursorPosition(line, col)


class UndoReplaceSelectedText(QtmacsUndoCommand):
    """
    Implement ``replaceSelectedText`` and its undo operation.

    This undo object replaces the selected text with the specified
    one. If no text is selected then nothing happens.

    |Args|

    * ``qteWidget`` (**QWidget**): the widget to use.
    * ``text`` (**str**): text to replace the selection.

    |Raises|

    * **QtmacsArgumentError** if at least one argument has an invalid type.
    """

    @type_check
    def __init__(self, qteWidget, text):
        super().__init__()
        self.qteWidget = qteWidget
        self.baseClass = super(type(qteWidget), qteWidget)
        self.selectionPosOld = None
        self.selectionPosNew = None
        self.oldText = None
        self.newText = text

        # Update the selection position only if the widget has
        # one. If not, then ``commit`` and ``reverseCommit``
        # will both do nothing.
        if qteWidget.hasSelectedText():
            self.selectionPosOld = qteWidget.getSelection()

    def commit(self):
        if self.selectionPosOld is None:
            return

        # Shorthand.
        wid = self.qteWidget

        # Backup the text and style.
        text, self.oldStyle = wid.SCIGetStyledText(self.selectionPosOld)
        self.oldText = text.decode('utf-8')

        # Replace the selected text with the new one.
        self.baseClass.replaceSelectedText(self.newText)

        # Determine and backup the region occupied by the new text.
        start = self.selectionPosOld[:2]
        pos = wid.positionFromLineIndex(*start)
        pos += len(self.newText)
        stop = wid.lineIndexFromPosition(pos)
        self.selectionPosNew = (start[0], start[1], stop[0], stop[1])
        wid.setCursorPosition(*stop)

    def reverseCommit(self):
        """
        Reinsert the killed word.
        """
        if self.selectionPosOld is None:
            return

        # Shorthand.
        wid = self.qteWidget

        # Select, backup, and delete the selection.
        wid.setSelection(*self.selectionPosNew)
        self.baseClass.replaceSelectedText(self.oldText)

        # Add the styling information.
        line, col = self.selectionPosNew[0:2]
        wid.SCISetStylingEx(line, col, self.oldStyle)
        wid.setCursorPosition(line, col)


class UndoInsertAt(QtmacsUndoCommand):
    """
    Implement ``insertAt`` and its undo operation.

    This undo object inserts the specified text at the specified
    position. Selected text is ignored, and selections are always
    cleared.

    |Args|

    * ``qteWidget`` (**QWidget**): the widget to use.
    * ``text`` (**str**): text to insert at the specified position.
    * ``line`` (**int**): line number.
    * ``col`` (**int**): column number.

    |Raises|

    * **QtmacsArgumentError** if at least one argument has an invalid type.
    """

    @type_check
    def __init__(self, qteWidget, text, line, col):
        super().__init__()
        self.qteWidget = qteWidget
        self.baseClass = super(type(qteWidget), qteWidget)
        self.insertedText = text
        self.line = line
        self.col = col
        self.selectionPos = None

    def commit(self):
        # Ensure that the cursor position is valid.
        if not self.qteWidget.isPositionValid(self.line, self.col):
            msg = ('Cannot redo "insertAt" operation because the cursor '
                   'position is invalid. The document is possibly in '
                   'an inconsistent state. Please save and re-open.')
            qteMain.qteLogger.critical(msg)
            return

        self.baseClass.insertAt(self.insertedText, self.line, self.col)

        # Determine and backup the region occupied by the just
        # inserted text to facilitate redo (ie. removing the text).
        pos = self.qteWidget.positionFromLineIndex(self.line, self.col)
        pos += len(self.insertedText)
        line, col = self.qteWidget.lineIndexFromPosition(pos)
        self.selectionPos = (self.line, self.col, line, col)
        self.qteWidget.setCursorPosition(line, col)

    def reverseCommit(self):
        """
        Reinsert the killed word.
        """
        # Ensure that the cursor position is valid.
        if not self.qteWidget.isSelectionPositionValid(self.selectionPos):
            msg = ('Cannot undo "insert" operation because the selection'
                   'position is invalid. The document is possibly in '
                   'an inconsistent state. Please save and re-open.')
            qteMain.qteLogger.critical(msg)
            return

        # Select and delete the inserted text.
        self.qteWidget.setSelection(*self.selectionPos)
        self.baseClass.removeSelectedText()
        line, col = self.selectionPos[0:2]
        self.qteWidget.setCursorPosition(line, col)


class UndoInsert(QtmacsUndoCommand):
    """
    Implement ``insert`` and its undo operation.

    This undo object inserts the specified text at the current cursor
    position. Selected text is ignored, and selections are always
    cleared.

    |Args|

    * ``qteWidget`` (**QWidget**): the widget to use.
    * ``text`` (**str**): text to insert at the current position.

    |Raises|

    * **QtmacsArgumentError** if at least one argument has an invalid type.
    """

    @type_check
    def __init__(self, qteWidget, text):
        super().__init__()
        self.qteWidget = qteWidget
        self.baseClass = super(type(qteWidget), qteWidget)
        self.insertedText = text
        self.cursorPosition = qteWidget.getCursorPosition()
        self.selectionPos = None

    def commit(self):
        # Ensure that the cursor position is valid.
        if not self.qteWidget.isPositionValid(*self.cursorPosition):
            msg = ('Cannot redo "insert" operation because the cursor '
                   'position is invalid. The document is possibly in '
                   'an inconsistent state. Please save and re-open.')
            qteMain.qteLogger.critical(msg)
            return

        self.qteWidget.setCursorPosition(*self.cursorPosition)
        self.baseClass.insert(self.insertedText)

        # Determine and backup the region where the text was inserted.
        pos = self.qteWidget.positionFromLineIndex(*self.cursorPosition)
        pos += len(self.insertedText)
        line, col = self.qteWidget.lineIndexFromPosition(pos)
        self.selectionPos = (self.cursorPosition[0],
                             self.cursorPosition[1],
                             line, col)
        self.qteWidget.setCursorPosition(line, col)

    def reverseCommit(self):
        """
        Reinsert the killed word.
        """
        # Ensure that the cursor position is valid.
        if not self.qteWidget.isSelectionPositionValid(self.selectionPos):
            msg = ('Cannot undo "insert" operation because the selection'
                   'position is invalid. The document is possibly in '
                   'an inconsistent state. Please save and re-open.')
            qteMain.qteLogger.critical(msg)
            return

        # Select and delete the inserted text.
        self.qteWidget.setSelection(*self.selectionPos)
        self.baseClass.removeSelectedText()
        line, col = self.selectionPos[:2]
        self.qteWidget.setCursorPosition(line, col)


class UndoSetText(QtmacsUndoCommand):
    """
    Implement ``setText`` and its undo operation.

    This undo object removes all the text from the widget
    and replaces it with a new text.

    |Args|

    * ``qteWidget`` (**QWidget**): the widget to use.
    * ``newText`` (**str**): the new text.

    |Raises|

    * **QtmacsArgumentError** if at least one argument has an invalid type.
    """
    @type_check
    def __init__(self, qteWidget, newText):
        super().__init__()
        self.qteWidget = qteWidget
        self.baseClass = super(type(qteWidget), qteWidget)
        self.newText = newText

        # Backup the text and style.
        line, col = self.qteWidget.getNumLinesAndColumns()
        text, self.style = self.qteWidget.SCIGetStyledText((0, 0, line, col))
        self.oldText = text.decode('utf-8')

    def commit(self):
        """
        Replace the current widget content with the new text.
        """
        self.baseClass.setText(self.newText)

    def reverseCommit(self):
        """
        Replace the current widget content with the original text.
        Note that the original text has styling information available,
        whereas the new text does not.
        """
        self.baseClass.setText(self.oldText)
        self.qteWidget.SCISetStylingEx(0, 0, self.style)


class UndoGenericQtmacsScintilla(QtmacsUndoCommand):
    """
    Generic undo-object to revert an arbitrary change in the document.

    This undo command takes snapshot of the current document state
    (including style) at instantiation, and a second snapshot at
    the time it is pushed onto the stack.

    Example::

        # Instantiate the undo object to get a snapshot.
        undoObj = UndoGenericQtmacsScintilla(self.qteWidget)

        # ... arbitrary changes to the text in self.qteWidget.

        # Push the undo object to automatically generate another
        # snapshot.
        self.qteWidget.qteUndoStack.push(undoObj)

    |Args|

    * ``qteWidget`` (**QWidget**): the widget to use.

    |Raises|

    * **QtmacsArgumentError** if at least one argument has an invalid type.
    """
    @type_check
    def __init__(self, qteWidget):
        super().__init__()
        self.qteWidget = qteWidget
        self.baseClass = super(type(qteWidget), qteWidget)
        self.textAfter = None

        # Backup the current document (including style).
        line, col = self.qteWidget.getNumLinesAndColumns()
        text, style = self.qteWidget.SCIGetStyledText((0, 0, line, col))
        self.styleBefore = style
        self.textBefore = text.decode('utf-8')
        self.origPosition = self.qteWidget.getCursorPosition()

    def placeCursor(self, line, col):
        """
        Try to place the cursor in ``line`` at ``col`` if possible,
        otherwise place it at the end.
        """
        num_lines, num_col = self.qteWidget.getNumLinesAndColumns()

        # Place the cursor at the specified position if possible.
        if line >= num_lines:
            line, col = num_lines, num_col
        else:
            text = self.qteWidget.text(line)
            if col >= len(text):
                col = len(text) - 1

        self.qteWidget.setCursorPosition(line, col)

    def commit(self):
        """
        Put the document into the new state.
        """
        if self.textAfter is None:
            # If this is the first 'commit' call then do not make
            # any changes but store the current document state
            # and its style.
            line, col = self.qteWidget.getNumLinesAndColumns()
            text, style = self.qteWidget.SCIGetStyledText((0, 0, line, col))
            self.styleAfter = style
            self.textAfter = text.decode('utf-8')
        else:
            # Put the document into the 'after' state.
            self.baseClass.setText(self.textAfter)
            self.qteWidget.SCISetStylingEx(0, 0, self.styleAfter)
        self.placeCursor(*self.origPosition)

    def reverseCommit(self):
        """
        Put the document into the 'before' state.
        """
        # Put the document into the 'before' state.
        self.baseClass.setText(self.textBefore)
        self.qteWidget.SCISetStylingEx(0, 0, self.styleBefore)


class QtmacsScintilla(Qsci.QsciScintilla):
    """
    A drop-in replacement for ``QsciScintilla`` with Emacs like undo behaviour.

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

        # Make all styles have a mono space font. This being hardcoded
        # is somewhat of a hack but sufficient for now.
        self.setMonospace()

        # Position of last set marker (line- and column number).
        self.qteMarkers = {}

    @type_check
    def qteSetMark(self, markerID=0, line: int=None, col: int=None):
        """
        Define/overwrite the line- and column index of marker ``markerID``.

        The default marker has ``markerID=0`` by convention.

        If ``line`` and/or ``col`` are not provided they are substituted
        with the values of the current cursor position.

        ..note: ``line`` and ``col`` are not range checked. They can therefore
                take on arbitrary values (even negative ones) that do not
                denote a valid position in the document.

        |Args|

        * ``markerID`` (**object**): arbitrary Python object that is
          internally used as a dictionary.
        * ``line`` (**int**): an integer specifying the line
          number of the marker.
        * ``col`` (**int**): an integer specifying the column
          number of the marker.

        |Returns|

        * **None**

        |Raises|

        * **None**
        """

        # Query the line- and column number unless provided.
        if (line is None) and (col is None):
            line, col = self.getCursorPosition()
        elif line is None:
            line, _ = self.getCursorPosition()
        elif col is None:
            _, col = self.getCursorPosition()
        else:
            pass

        self.qteMarkers[markerID] = (line, col)
        return (line, col)

    @type_check
    def qteGetMark(self, markerID=0):
        """
        Retrieve the line- and column number of mark with ID ``markerID``.

        The method returns a tuple containing the line- and column number
        of the marker, or **None** if no marker with ``markerID`` exists.

        The default marker has ``markerID=0`` by convention.

        |Args|

        * ``markerID`` (**object**): arbitrary Python object that is
          internally used as a dictionary.

        |Returns|

        * **tuple**: line- and column number of the mark, or **None** if
          ``markerID`` is invalid.

        |Raises|

        * **None**
        """
        if markerID not in self.qteMarkers:
            return None
        else:
            return self.qteMarkers[markerID]

    def fromMimeData(self, data):
        """
        Paste the clipboard data at the current cursor position.

        This method also adds another undo-object to the undo-stack.

        ..note: This method forcefully interrupts the ``QsciInternal``
                pasting mechnism by returning an empty MIME data element.
                This is not an elegant implementation, but the best I
                could come up with at the moment.

        """
        # Only insert the element if it is available in plain text.
        if data.hasText():
            self.insert(data.text())

        # Tell the underlying QsciScintilla object that the MIME data
        # object was indeed empty.
        return (QtCore.QByteArray(), False)

    def getNumLinesAndColumns(self):
        """
        Return the number of lines, and columns in the last line.

        |Args|

        * **None**

        |Returns|

        **tuple**: (number of lines, number of columns in last line)

        |Raises|

        * **None**
        """
        num_char_tot = len(self.text())
        return self.lineIndexFromPosition(num_char_tot)

    @type_check
    def isPositionValid(self, line: int, column: int):
        """
        Return **True** if ``line`` and ``column`` denote a valid
        position.

        |Args|

        * ``line`` (**int**): line number
        * ``column`` (**int**): column in line ``line``

        |Returns|

        **bool**: **True** if ``line`` and ``column`` specify a
          valid point in the document, **False** otherwise.

        |Raises|

        * **None**
        """
        if (line < 0) or (column < 0):
            return False

        last_line, last_col = self.getNumLinesAndColumns()
        if line > last_line:
            return False

        if column <= len(self.text(line)):
            return True
        else:
            return False

    @type_check
    def isSelectionPositionValid(self, selPos: tuple):
        """
        Return **True** if the start- and end position denote valid
        positions within the document.

        |Args|

        * ``selPos`` (**tuple**): tuple with four integers.

        |Returns|

        **bool**: **True** if the positions are valid; **False** otherwise.

        |Raises|

        * **None**
        """
        if selPos is None:
            return False
        if len(selPos) != 4:
            return False
        check1 = self.isPositionValid(*selPos[:2])
        check2 = self.isPositionValid(*selPos[2:])
        if check1 and check2:
            return True
        else:
            return False

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

    @type_check
    def keyPressEvent(self, keyEvent: QtGui.QKeyEvent):
        """
        Undo safe wrapper for the native ``keyPressEvent`` method.

        |Args|

        * ``keyEvent`` (**QKeyEvent**): the key event to process.

        |Returns|

        **None**

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        undoObj = UndoInsert(self, keyEvent.text())
        self.qteUndoStack.push(undoObj)

    @type_check
    def removeSelectedText(self):
        """
        Undo safe wrapper for the native ``removeSelectedText`` method.

        |Args|

        * **None**

        |Returns|

        **None**

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        undoObj = UndoRemoveSelectedText(self)
        self.qteUndoStack.push(undoObj)

    @type_check
    def replaceSelectedText(self, text: str):
        """
        Undo safe wrapper for the native ``replaceSelectedText`` method.

        |Args|

        * ``text`` (**str**): text to replace the current selection.

        |Returns|

        **None**

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        undoObj = UndoReplaceSelectedText(self, text)
        self.qteUndoStack.push(undoObj)

    @type_check
    def insert(self, text: str):
        """
        Undo safe wrapper for the native ``insert`` method.

        |Args|

        * ``text`` (**str**): text to insert at the current position.

        |Returns|

        **None**

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        undoObj = UndoInsert(self, text)
        self.qteUndoStack.push(undoObj)

    @type_check
    def insertAt(self, text: str, line: int, col: int):
        """
        Undo safe wrapper for the native ``insertAt`` method.

        |Args|

        * ``text`` (**str**): text to insert at the specified position.
        * ``line`` (**int**): line number.
        * ``col`` (**int**): column number.

        |Returns|

        **None**

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        undoObj = UndoInsertAt(self, text, line, col)
        self.qteUndoStack.push(undoObj)

    @type_check
    def append(self, text: str):
        """
        Undo safe wrapper for the native ``append`` method.

        |Args|

        * ``text`` (**str**): text to insert at the specified position.

        |Returns|

        **None**

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        pos = self.getCursorPosition()
        line, col = self.getNumLinesAndColumns()
        undoObj = UndoInsertAt(self, text, line, col)
        self.qteUndoStack.push(undoObj)
        self.setCursorPosition(*pos)

    @type_check
    def setText(self, text: str):
        """
        Undo safe wrapper for the native ``setText`` method.

        |Args|

        * ``text`` (**str**): text to insert at the specified position.

        |Returns|

        **None**

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        undoObj = UndoSetText(self, text)
        self.qteUndoStack.push(undoObj)

    @type_check
    def SCIGetStyledText(self, selectionPos: tuple):
        """
        Pythonic wrapper for the SCI_GETSTYLEDTEXT command.

        For example, to get the raw text and styling bits
        for the first five characters in the widget use::

            text, style = SCIGetStyledText((0, 0, 0, 5))
            print(text.decode('utf-8'))

        |Args|

        * ``selectionPos`` (**tuple**): selection position in the
          form of (start_line, start_col, end_line, end_col).

        |Returns|

        **tuple** of two ``bytearrays``. The first contains the
          the character bytes and the second the Scintilla styling
          information.

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """

        # Sanity check.
        if not self.isSelectionPositionValid(selectionPos):
            return None

        # Convert the start- and end point of the selection into
        # stream offsets. Ensure that start comes before end.
        start = self.positionFromLineIndex(*selectionPos[:2])
        end = self.positionFromLineIndex(*selectionPos[2:])
        if start > end:
            start, end = end, start

        # Allocate a large enough buffer.
        bufSize = 2 * (end - start) + 2
        buf = bytearray(bufSize)

        # Fetch the text- and styling information.
        numRet = self.SendScintilla(self.SCI_GETSTYLEDTEXT, start, end, buf)

        # The last two bytes are always Zero according to the
        # Scintilla documentation, so remove them.
        buf = buf[:-2]

        # Double check that we did not receive more bytes than the buffer
        # was long.
        if numRet > bufSize:
            qteMain.qteLogger.error('SCI_GETSTYLEDTEX function returned more'
                                    ' bytes than expected.')
        text = buf[0::2]
        style = buf[1::2]
        return (text, style)

    @type_check
    def SCISetStyling(self, line: int, col: int,
                      numChar: int, style: bytearray):
        """
        Pythonic wrapper for the SCI_SETSTYLINGEX command.

        For example, the following code applies style #3
        to the first fivie characters in the second line
        of the widget:

            SCISetStyling((0, 1), 5, 3)

        |Args|

        * ``line`` (**int**): line number where to start styling.
        * ``col`` (**int**): column number where to start styling.
        * ``numChar`` (**int**): number of characters to style.
        * ``style`` (**int**): Scintilla style number.

        |Returns|

        **None**

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        if not self.isPositionValid(line, col):
            return

        pos = self.positionFromLineIndex(line, col)
        self.SendScintilla(self.SCI_STARTSTYLING, pos, 0xFF)
        self.SendScintilla(self.SCI_SETSTYLING, numChar, style)

    @type_check
    def SCISetStylingEx(self, line: int, col: int, style: bytearray):
        """
        Pythonic wrapper for the SCI_SETSTYLINGEX command.

        For example, the following code will fetch the
        styling for the first five characters applies
        it verbatim to the next five characters.

            text, style = SCIGetStyledText((0, 0, 0, 5))
            SCISetStylingEx((0, 5), style)

        |Args|

        * ``line`` (**int**): line number where to start styling.
        * ``col`` (**int**): column number where to start styling.
        * ``style`` (**bytearray**): Scintilla style bits.

        |Returns|

        **None**

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        if not self.isPositionValid(line, col):
            return

        pos = self.positionFromLineIndex(line, col)
        self.SendScintilla(self.SCI_STARTSTYLING, pos, 0xFF)
        self.SendScintilla(self.SCI_SETSTYLINGEX, len(style), style)

    def qteSetLexer(self, lexer):
        """
        Specify the lexer to use.

        The only difference between this method and the native
        ``setLexer`` method is that expects ``lexer`` to be class, not
        an instance. Another feature is that this method knows which
        ``lexer`` class was installed last, and this information can
        be retrieved with ``qteLexer`` again.

        |Args|

        * ``lexer`` (**QsciLexer**): lexer class (*not* instance).

        |Returns|

        **None**

        |Raises|

        * **QtmacsOtherError** if lexer is not a class.
        """
        if (lexer is not None) and (not issubclass(lexer, Qsci.QsciLexer)):
            QtmacsOtherError('lexer must be a class object and derived from'
                             ' <b>QsciLexer</b>')
            return

        # Install and backup the lexer class.
        self.qteLastLexer = lexer
        if lexer is None:
            self.setLexer(None)
        else:
            self.setLexer(lexer())

        # Make all fonts in the style mono space.
        self.setMonospace()

    def qteLexer(self):
        """
        Return the class name of the last installed lexer object.

        This method works in conjunction with ``qteSetLexer`` because
        the native ``lexer`` method does not appear to work (it never
        returns a lexer).

        |Args|

        * **None**

        |Returns|

        **None**

        |Raises|

        * **None**
        """
        return self.qteLastLexer

    def setMonospace(self):
        """
        Fix the fonts of the first 32 styles to a mono space one.

        |Args|

        * **None**

        |Returns|

        **None**

        |Raises|

        * **None**
        """
        font = bytes('courier new', 'utf-8')
        for ii in range(32):
            self.SendScintilla(self.SCI_STYLESETFONT, ii, font)

    @type_check
    def setModified(self, isModified: bool):
        """
        Set the modified state to ``isModified``.

        From a programmer's perspective this method does the same as
        the native ``QsciScintilla`` method but also ensures that the
        undo framework knows when the document state was changed.

        |Args|

        * ``isModified`` (**bool**): whether or not the document is considered
          unmodified.

        |Returns|

        **None**

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        if not isModified:
            self.qteUndoStack.saveState()
        super().setModified(isModified)

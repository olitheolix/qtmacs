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
An Undo framework to replace the Qt native implementation in applets.

The main difference to Qt's one is that an undo operations does not
remove elements from the stack but rather adds the inverse operation
to the stack (like in GIT). This facilitates an Emacs like undo
behaviour where undone operations can themselves be undone again,
which makes a dedicated `redo` option superfluous.

It is safe to use::

    from undo_stack import *

Here is a (pseudo) example where a macro (called ``FooMacro``)
uses the ``UndoFoo`` command to implement the actual `foo` action::

    class UndoFoo(QtmacsUndoCommand):
        \"\"\"
        Demonstrate how to implement a reversible `foo` command
        with the help of ``QtmacsUndoCommand`` class.
        \"\"\"

        def __init__(self, arg1, arg2):
            \"\"\"
            To execute the ``foo`` operation this object (and thus this
            constructor) will almost certainly want to know the widget,
            among other information, eg. the character to insert if this
            is an undo object for the self-insert widget.
            \"\"\"

            # -- your code goes here --
            pass

        def reverseCommit(self):
            \"\"\"
            Implement the ``foo`` action and make sure to store all
            information necessary to *exactly* reverse the operation.
            \"\"\"

            # -- your code goes here --
            pass

        def commit(self):
            \"\"\"
            Implement the steps that *exactly* reverse the ``foo`` operation
            implemented in ``reverseCommit``.
            \"\"\"

            # -- your code goes here --
            pass

    class FooMacro(QtmacsMacro):
        \"\"\"
        Apply foo with the help of an ``QtmacsUndoCommand`` object.
        \"\"\"

        def __init__(self):
            super().__init__()
            self.qteSetAppletSignature('*')
            self.qteSetWidgetSignature(('QTextEdit', 'QtmacsTextEdit'))

        def qteRun(self):
            # Instantiate an undo-object that can implement (and reverse)
            # the foo operation.
            undoObj = UndoFoo(self, self.qteWidget, arg2, arg3, ...)

            # Push this undo object onto the stack (this will automatically
            # trigger the ``commit`` method of that object).
            self.qteUndoStack.push(undoObj)

Once the ``undoObj`` was added to the stack via ``qteUndoStack`` the
``undo`` method of the widget takes care of everything else related to
doing and undoing.
"""

import inspect
import qtmacs.auxiliary
import qtmacs.type_check

from PyQt4 import QtCore, QtGui
from qtmacs.exceptions import *

# Shorthands
type_check = qtmacs.type_check.type_check
QtmacsMessage = qtmacs.auxiliary.QtmacsMessage


class QtmacsUndoCommand(object):
    """
    Container to specify a command and how to undo it.

    If ``undoObj`` is a ``QtmacsUndoCommand`` itself then return
    a copy of it.

    |Args|

    * ``undoObj`` (**QtmacsUndoCommand**): object to copy.

    |Raises|

    * **QtmacsArgumentError** if at least one argument has an invalid type.
    """
    def __init__(self, undoObj=None):
        # Check type of input arguments.
        if not isinstance(undoObj, QtmacsUndoCommand) and undoObj is not None:
            raise QtmacsArgumentError('undoObj', 'QtmacsUndoCommand',
                                      inspect.stack()[0][3])

        if undoObj:
            self.nextIsRedo = undoObj.nextIsRedo
            self.commit = undoObj.commit
            self.reverseCommit = undoObj.reverseCommit
        else:
            self.nextIsRedo = True

    def commit(self):
        """
        Implement the desired action.

        |Args|

        * **None**

        |Returns|

        * **None**

        |Raises|

        * **None**
        """
        pass

    def reverseCommit(self):
        """
        Implement the inverse of the action from ``commit``.

        |Args|

        * **None**

        |Returns|

        * **None**

        |Raises|

        * **None**
        """
        pass


class QtmacsUndoStack(QtCore.QObject):
    """
    Implement an Undo stack.

    The class provides two methods: ``push`` and ``undo``. The first
    takes a ``QtmacsUndoCommand`` object, adds it to the stack, and
    runs its ``commit`` method. The second method does not take any
    arguments and will push the corresponding inverse action
    (ie. ``reverseCommit`` method) onto the stack.

    ..note: the class keeps track of consecutive ``undo`` calls and
            will to push the correct undo action onto the stack.

    The class also features the ``qtesigSavedState`` signal which
    is triggered whenever the undo actions lead back to the last
    saved state, at least theoretically (see the documentation of
    the ``undo`` method for further details).
    """

    qtesigSavedState = QtCore.pyqtSignal(QtmacsMessage)

    def __init__(self):
        # Call super class constructor.
        super().__init__()

        # The stack is a simple list.
        self._qteStack = []

        # Point to last undo action, or ``None`` if the last action
        # was not one.
        self._qteIndex = 0
        self._wasUndo = False

        # Index of last undo element where the modified state of
        # the document was set to "unmodified" (see ``setModified`` method).
        self._qteLastSavedUndoIndex = 0

    @type_check
    def _push(self, undoObj: QtmacsUndoCommand):
        """
        The actual method that adds the command object onto the stack.

        This method also toggles the ``nextIsRedo`` flag in the
        command object and, depending on its value, executes either
        the ``commit`` or ``reverseCommit`` method of the object. This
        distinction is invisible to the user but if the method is
        passed a copy of an older ``undoObj`` already on the stack
        (typically the case when called from ``undo``) then it will
        call the inverse command (ie a ``commit`` when the previous
        call was a ``reverseCommit`` and vice versa). In this manner,
        the undo history will contain just another command object
        which happens to undo a previous one, irrespective of whether
        the previous one was already the undoing of an even earlier
        one.
        """
        self._qteStack.append(undoObj)
        if undoObj.nextIsRedo:
            undoObj.commit()
        else:
            undoObj.reverseCommit()
        undoObj.nextIsRedo = not undoObj.nextIsRedo

    def push(self, undoObj):
        """
        Add ``undoObj`` command to stack and run its ``commit`` method.

        |Args|

        * ``undoObj`` (**QtmacsUndoCommand**): the new command object.

        |Returns|

        * **None**

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        # Check type of input arguments.
        if not isinstance(undoObj, QtmacsUndoCommand):
            raise QtmacsArgumentError('undoObj', 'QtmacsUndoCommand',
                                      inspect.stack()[0][3])

        # Flag that the last action was not an undo action and push
        # the command to the stack.
        self._wasUndo = False
        self._push(undoObj)

    def pop(self):
        """
        Pop the last undo command from the stack.

        Unlike the ``undo`` method, ``pop` does not undo any changes, (ie.
        call methods in the ``QtmacsUndoCommand`` object) and literally
        removes the ``QtmacsUndoCommand`` from the stack. The consequence
        is that the so removed ``QtmacsUndoCommand`` cannot be undone again.

        There should be hardly a need to call this method except in special
        cases. One such case is the ``yank-pop`` macro which replaces the
        last yanked text with another one.
        """
        return self._qteStack.pop()

    def reset(self):
        """
        Remove all undo objects - permanently.

        This operation cannot be undone.
        """
        self._qteStack = []
        self._qteIndex = 0

    def undo(self):
        """
        Undo the last command by adding its inverse action to the stack.

        This method automatically takes care of applying the correct
        inverse action when it is called consecutively (ie. without a
        calling ``push`` in between).

        The ``qtesigSavedState`` signal is triggered whenever enough undo
        operations have been performed to put the document back into the
        last saved state.

        ..warning: The ``qtesigSaveState`` is triggered whenever the
          logic of the undo operations **should** have led back to
          that state, but since the ``UndoStack`` only stacks and
          ``QtmacsUndoCommand`` objects it may well be the document is
          **not** in the last saved state, eg. because not all
          modifications were protected by undo objects, or because the
          ``QtmacsUndoCommand`` objects have a bug. It is therefore
          advisable to check in the calling class if the content is
          indeed identical by comparing it with a temporarily stored
          copy.

        |Args|

        * **None**

        |Signals|

        * ``qtesigSavedState``: the document is the last saved state.

        |Returns|

        * **None**

        |Raises|

        * **None**
        """
        # If it is the first call to this method after a ``push`` then
        # reset ``qteIndex`` to the last element, otherwise just
        # decrease it.
        if not self._wasUndo:
            self._qteIndex = len(self._qteStack)
        else:
            self._qteIndex -= 1

        # Flag that the last action was an `undo` operation.
        self._wasUndo = True
        if self._qteIndex <= 0:
            return

        # Make a copy of the command and push it to the stack.
        undoObj = self._qteStack[self._qteIndex - 1]
        undoObj = QtmacsUndoCommand(undoObj)
        self._push(undoObj)

        # If the just pushed undo object restored the last saved state
        # then trigger the ``qtesigSavedState`` signal and set the
        # _qteLastSaveUndoIndex variable again. This is necessary
        # because an undo command will not *remove* any elements from
        # the undo stack but *add* the inverse operation to the
        # stack. Therefore, when enough undo operations have been
        # performed to reach the last saved state that means that the
        # last addition to the stack is now implicitly the new last
        # save point.
        if (self._qteIndex - 1) == self._qteLastSavedUndoIndex:
            self.qtesigSavedState.emit(QtmacsMessage())
            self.saveState()

    def saveState(self):
        """
        Treat the current state as the last unmodified one.

        |Args|

        * **None**

        |Returns|

        * **None**

        |Raises|

        * **None**
        """
        self._qteLastSavedUndoIndex = len(self._qteStack)

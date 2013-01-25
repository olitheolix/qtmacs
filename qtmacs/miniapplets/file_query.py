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
Mini applet template for file queries.

The user needs to overload the ``inputCompleted`` method to implement
the desired action on the chosen file name. Furthermore, the user
*may* overload the ``generateCompletions`` method to tailor the
default completions even further (eg. consider only 'pdf' files).

By default, entries can be auto completed with <tab> from the list of
possible file name completions, but also allows other names not on the
list. The class also features a history that can be traversed with
<alt>+n and <alt>+p.

The code below demonstrates how to use this class and will display the
input in the status applet once the user hits enter. Put this in your
configuration file, start Qtmacs, press `<alt>+x`, type
`ExampleQuery`, and try it out::

    class ExampleQuery(QtmacsMacro):
        \"\"\"
        Use the mini applet to query a file name.

        |Signature|

        * *applet*: '*'
        * *widget*: '*'

        \"\"\"
        class Query(qtmacs.miniapplets.file_query.MiniAppletFindFile):
            \"\"\"
            Query the name of a file (always starts in the current directory).
            \"\"\"
            def generateCompletions(self, completions):
                # Retain only those files that contain an 'e'.
                return [_ for _ in completions if 'e' in _]

            def inputCompleted(self, userInput):
                # Display the user input in the status applet.
                self.qteMain.qteStatus('Selected file: ' + userInput);

        def __init__(self):
            super().__init__()
            self.qteSetAppletSignature('*')
            self.qteSetWidgetSignature('*')

        def qteRun(self):
            # Instantiate the file name query.
            query = self.Query(self.qteApplet, self.qteWidget)

            # Install the query object as the mini applet and return
            # control to the event loop.
            self.qteMain.qteAddMiniApplet(query)

    # Register the macro with Qtmacs.
    qteRegisterMacro(ExampleQuery)

..note: the implementation of this query is very similar to the one in
        base_query.py. The reason why this one does not inhert it is
        because the history feature needs to manipulate a global module
        variable.

It is safe to use::

    from file_query import *

"""
import os
import qtmacs.type_check
import qtmacs.miniapplets.base_query as base_query

from PyQt4 import QtCore, QtGui
from qtmacs.base_macro import QtmacsMacro
from qtmacs.base_applet import QtmacsApplet

# Shorthands
type_check = qtmacs.type_check.type_check

# Global variables used by the macros to query and update the
# history. Macros using the ``MiniAppletBaseQuery`` class must
# point ``qteQueryHistory`` to the history (a Python list) they would
# like to use.
qteQueryHistory = []
qteHistIdx = None


class AutocompleteInput(base_query.AutocompleteInput):
    """
    Display all possible file completions in a dedicated applet.

    Create (or reuse) the applet with ID '\*\*Completions\*\*' to
    display all possible completions for the partially entered file
    name.

    |Signature|

    * *applet*: 'MiniApplet'
    * *widget*: ``QTextEdit``

    """
    def qteRun(self):
        # Fetch the text typed into the mini applet by the user
        # and extract purely the path name.
        userInput = self.qteWidget.toPlainText()
        path = os.path.split(userInput)
        path = path[0]

        # If the path is empty replace it with the root path.
        if len(path) == 0:
            path = '/'

        # Get a handle to the current directory and extract all files
        # and directories in it.
        curDir = QtCore.QDir(path)
        curDir.setFilter(QtCore.QDir.AllEntries | QtCore.QDir.NoDot)
        curDir.setSorting(QtCore.QDir.Name | QtCore.QDir.DirsFirst)
        curDir = curDir.entryInfoList()

        # Convert the list of QFileEntry obejects to strings denoting
        # the absolute file names (ie. path + fileName,
        # eg. /foo/bar.txt). Also, remove those entries that do not
        # contain the user input as a sub-string.
        completions = []
        for ii in curDir:
            name = ii.absoluteFilePath()
            if userInput not in name:
                continue

            if ii.isDir():
                completions.append(name + '/')
            else:
                completions.append(name)

        # Call the generateCompletions method from the
        # ``MiniAppletBaseQuery`` class (the programmer has to
        # overload it).
        completions = self.qteApplet.generateCompletions(completions)

        # Keep only those entries which contain the user input as a
        # sub-string.
        if isinstance(completions, list) or isinstance(completions, tuple):
            completions = [_ for _ in completions if userInput in _]
        else:
            completions = None

        # Auto-complete as much as possible by displaying the largest
        # common prefix of all possible completions. If no such prefix
        # exists, then do nothing as otherwise the entry field would
        # be wiped clean.
        pre = os.path.commonprefix(completions)
        if len(pre) > 0:
            self.qteWidget.setPlainText(pre)
            tc = self.qteWidget.textCursor()
            tc.movePosition(QtGui.QTextCursor.EndOfLine)
            self.qteWidget.setTextCursor(tc)

        # If something could be completed do not proceed to
        # show a list of possible completions but return now.
        if len(pre) > len(userInput):
            return

        # If the completion is not unique then list all options,
        # otherwise close the completions applet altogether.
        if (completions is not None) and (len(completions) > 1):
            # Get a handle to the completions buffer or create a new
            # one if none exists yet.
            app = self.qteMain.qteGetAppletHandle(self.completionsAppID)
            if app is None:
                app = self.qteMain.qteNewApplet('RichEditor',
                                                self.completionsAppID)
            self.qteMain.qteSplitApplet(app)

            # Clear the buffer and list the possible completions.
            app.qteText.clear()
            for _ in completions:
                app.qteText.append(_)
        else:
            self.qteMain.qteKillApplet(self.completionsAppID)


class QueryInput(QtmacsMacro):
    """
    Close the mini applet and process the user input.

    This macro executes when the user hits <enter> to finalise the
    input. The mini applet is closed and the extracted string passed
    to the (overloaded) ``inputCompleted`` method in the
    ``MiniAppletBaseQuery`` object.

    |Signature|

    * *applet*: 'MiniApplet'
    * *widget*: ``QTextEdit``

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('MiniApplet')
        self.qteSetWidgetSignature('QTextEdit')

        # ID of the completions buffer. Note that this name is
        # implicitly agreed upon between this macro and the
        # AutocompleteInput macro. Therefore, ensure to change the
        # name in both locations if so desired.
        self.completionsAppID = '__Buffer Completions__'

    def qteRun(self):
        # Fetch the final user input.
        userInput = self.qteWidget.toPlainText()

        # If a history list was supplied to ``MiniAppletBaseQuery``
        # then add the latest entry.
        global qteQueryHistory, qteHistIdx
        if isinstance(qteQueryHistory, list):
            qteQueryHistory.append(userInput)
            qteHistIdx = len(qteQueryHistory)

        # Process the user input in the main object and close the mini
        # applet.
        self.qteApplet.inputCompleted(userInput)

        # Kill the completions buffer and mini applet. The methods are
        # smart enough to do nothing if one or the other (or both)
        # do not exist anymore.
        self.qteMain.qteRemoveAppletFromLayout(self.completionsAppID)
        self.qteMain.qteKillApplet(self.completionsAppID)
        self.qteMain.qteKillMiniApplet()


class NextInHistory(QtmacsMacro):
    """
    Yield the next-older entry in the history and display it in the
    mini applet.

    This macro will do nothing if ``MiniAppletBaseQuery`` (or the
    derived class) was not instantiated with a valid Python list as
    the history.

    |Signature|

    * *applet*: 'MiniApplet'
    * *widget*: ``QTextEdit``

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('MiniApplet')
        self.qteSetWidgetSignature('QTextEdit')

    def qteRun(self):
        # Return immediately if no history list exists.
        global qteQueryHistory, qteHistIdx
        if not isinstance(qteQueryHistory, list):
            return

        # If no newer element is available then do nothing.
        if qteHistIdx >= len(qteQueryHistory) - 1:
            return

        # Increment the counter to point to the next element in the history
        # and overwrite the entire content of the QTextEdit with the item from
        # the history list.
        qteHistIdx += 1
        msg = qteQueryHistory[qteHistIdx]
        self.qteWidget.setPlainText(msg)
        tc = self.qteWidget.textCursor()
        tc.movePosition(QtGui.QTextCursor.EndOfLine)
        self.qteWidget.setTextCursor(tc)


class BackInHistory(QtmacsMacro):
    """
    Yield the next-newer entry in the history and display it in the
    mini applet.

    This macro will do nothing if ``MiniAppletBaseQuery`` (or the
    derived class) was not instantiated with a valid Python list as
    the history.

    |Signature|

    * *applet*: 'MiniApplet'
    * *widget*: ``QTextEdit``

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('MiniApplet')
        self.qteSetWidgetSignature('QTextEdit')

    def qteRun(self):
        # Return immediately if no history list exists.
        global qteQueryHistory, qteHistIdx
        if not isinstance(qteQueryHistory, list):
            return

        # If no older element is available then do nothing.
        if qteHistIdx == 0:
            return

        # Decrement the counter to point to the previous element in
        # the history and overwrite the entire content of the
        # QTextEdit with the item from the history list.
        qteHistIdx -= 1
        msg = qteQueryHistory[qteHistIdx]
        self.qteWidget.setPlainText(msg)
        tc = self.qteWidget.textCursor()
        tc.movePosition(QtGui.QTextCursor.EndOfLine)
        self.qteWidget.setTextCursor(tc)


class MiniAppletFindFile(QtmacsApplet):
    """
    Customisable auto completion mini applet.

    This class facilitates an easy way to implement a custom mini
    applet query complete with auto-completion and history feature. To
    use this class, derive a new object from it where the virtual
    ``generateCompletions`` and ``inputCompleted`` methods are
    overloaded with with the desired functionality. The first method
    provides a way to adapt the possible completions based on what the
    user has entered so far, whereas the second method is called once
    the user has finished the entry (ie. hit <enter>) and must
    implement the logic to act upon this input. See the module
    documentation for an example.

    The ``history`` argument must be a list and will be dynamically
    extended at run-time with the user entries. It is thus a good idea
    to keep a reference to it alive in the calling macro in order to
    preserve it between calls.

    The ``applet`` and ``widget`` parameter are (almost) certainly the
    respective ``self.qteApplet`` and ``self.qteWidget`` attributes of
    the macro that instantiates this class. These pointers are
    necessary because the ``generateCompletions`` and ``inputCompleted``
    methods (ie. the ones to overload) are likely in need of these to
    implement the desired behaviour inside the applet and widget.

    The ``appletID`` is an arbitrary string to uniquely identify the
    mini-applet. This is the same as for any other ``QtmacsApplet``
    but Has hardly any practical use for mini-applet and should
    probably be left blank. In that case, Qtmacs will automatically
    assign a unique name of the form '__DefaultQuery#{number}__'.

    |Args|

    * ``applet`` (**QtmacsApplet**): reference to calling applet
      (typically ``self.qteApplet``).
    * ``widget`` (**QWidget**): reference to calling widget
      (typically ``self.qteWidget``).
    * ``appletID`` (**str**): unique name of mini applet.
    """
    @type_check
    def __init__(self, applet: QtmacsApplet, widget: QtGui.QWidget,
                 history: list=None, appletID: str=None):

        # Automatically determine a unique applet ID if none was provided.
        if appletID is None:
            cnt = 0
            while True:
                appletID = '__DefaultQuery#{}__'.format(cnt)
                if not applet.qteMain.qteGetAppletHandle(appletID):
                    break
                else:
                    cnt += 1

        # Initialise the base classes and define the applet signature
        # (all the macros defined earlier must use this applet signature).
        super().__init__(appletID)
        self.qteSetAppletSignature('MiniApplet')

        # Point the global variables to the user supplied history, or
        # **None** if it is missing.
        global qteQueryHistory, qteHistIdx
        if isinstance(history, list):
            qteQueryHistory = history
            qteHistIdx = len(qteQueryHistory)
        else:
            qteQueryHistory = qteHistIdx = None

        # Make sure the mini applet is only as high as it has to be,
        # otherwise the Qt layout engine is likely to allocate it half
        # the vertical space (ugly!).
        fm = self.fontMetrics().size(0, 'X')
        self.setMaximumHeight(2.5 * fm.height())

        # Keep a reference to the calling applet and widget.
        self.qteWidget = widget
        self.qteApplet = applet

        # Line up a QLabel for the "Find file" prefix string, and a
        # QTextEdit (pure text only) for the user input.
        self.qteTextPrefix = self.qteAddWidget(QtGui.QLabel(self),
                                               isFocusable=False)
        self.qteTextPrefix.setText('Find file:')
        self.qteText = self.qteAddWidget(QtGui.QTextEdit(self))
        self.qteText.setAcceptRichText(False)

        curDir = QtCore.QDir().current()
        self.qteText.append(curDir.absolutePath() + '/')

        # At this point, the QTextEdit used in the mini applet as a
        # text entry field is already endowed will all the usual
        # macros and key-bindings for a QTextEdit (the qteAddWidget
        # method took care of that). However, to be useful in a mini
        # applet context the <tab> key should trigger auto-completion
        # instead of literally inserting a <tab>, and the <enter> key
        # should close the mini applet and process its input, instead
        # of inserting a newline. Similarly, <ctrl>-p and <ctrl>-n
        # should go back and forth in the history. Therefore, replace
        # the default macros for these keys with dedicated macros that
        # enact the just behaviour for the QTextEdit in the mini
        # applet.

        # Auto-completion.
        p = QtCore.Qt
        n = self.qteMain.qteRegisterMacro(AutocompleteInput, replaceMacro=True)
        self.qteMain.qteBindKeyWidget('<Tab>', n, self.qteText)

        # Process final user input.
        n = self.qteMain.qteRegisterMacro(QueryInput, replaceMacro=True)
        self.qteMain.qteBindKeyWidget('<Enter>', n, self.qteText)
        self.qteMain.qteBindKeyWidget('<Return>', n, self.qteText)

        # Bring up next element in the history.
        n = self.qteMain.qteRegisterMacro(NextInHistory, replaceMacro=True)
        self.qteMain.qteBindKeyWidget('<Alt>+n', n, self.qteText)

        # Bring up previous element in the history.
        n = self.qteMain.qteRegisterMacro(BackInHistory, replaceMacro=True)
        self.qteMain.qteBindKeyWidget('<Alt>+p', n, self.qteText)

    def generateCompletions(self, completions):
        """
        Generate the possible list of completions.

        The ``completions`` list contains all possible file- and directory
        completions as strings (directories have a traling '/').

        |Args|

        * ``completions`` (**list**): list of strings. Each entry denotes one
          possible completions.

        |Returns|

        * **tuple, list**: a tuple/list of strings.

        |Raises|

        * **None**

        """
        return completions

    def inputCompleted(self, userInput):
        """
        Virtual: must be overloaded to implement specific action when
        the user hits <enter>.

        |Args|

        * ``userInput`` (**str**): the content of the ``QTextEdit`` when
          the user hit <enter>.

        |Returns|

        * **None**

        |Raises|

        * **None**

        """
        pass

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
A QScintilla demo for editing source code. This applet is part of PyQt
but my not have been installed automatically with the rest of PyQt.

As with every applet, do not use::

    from qtmacs.applets.scieditor import SciEditor

Usage example (put this in a file and provide that as command line
argument to Qtmacs)::

    import qtmacs.applets.scieditor as scieditor

    app_name = qteMain.qteRegisterApplet(scieditor.SciEditor)
    app_obj = qteMain.qteNewApplet(app_name)
    qteMain.qteMakeAppletActive(app_obj1)

To learn more about the properties please visit
http://pygtksci.sourceforge.net/reference/margin.html

As with every applet, do **not** use::

    from qtmacs.applets.scieditor import SciEditor

"""

import qtmacs.type_check
import qtmacs.qte_global as qte_global

from PyQt4 import QtCore, Qsci, QtGui
from qtmacs.base_macro import QtmacsMacro
from qtmacs.base_applet import QtmacsApplet
from qtmacs.extensions.qtmacsscintilla_widget import QtmacsScintilla
from qtmacs.auxiliary import QtmacsModeBar

# Import all the lexers currently supported by QScintilla as listed on
# www.riverbankcomputing.co.uk/static/Docs/QScintilla2/classQsciLexer.html
from PyQt4.Qsci import QsciLexerBash, QsciLexerBatch, QsciLexerCMake
from PyQt4.Qsci import QsciLexerCPP, QsciLexerCSS, QsciLexerCustom
from PyQt4.Qsci import QsciLexerD, QsciLexerDiff, QsciLexerFortran77
from PyQt4.Qsci import QsciLexerHTML, QsciLexerLua, QsciLexerMakefile
from PyQt4.Qsci import QsciLexerMatlab, QsciLexerPascal, QsciLexerPerl
from PyQt4.Qsci import QsciLexerPostScript, QsciLexerPOV, QsciLexerProperties
from PyQt4.Qsci import QsciLexerPython, QsciLexerRuby, QsciLexerSpice
from PyQt4.Qsci import QsciLexerSQL, QsciLexerTCL, QsciLexerTeX
from PyQt4.Qsci import QsciLexerVerilog, QsciLexerVHDL, QsciLexerYAML

# Shorthands:
type_check = qtmacs.type_check.type_check


class CustomLexer(Qsci.QsciLexerPython):
    """
    Simple demonstration of how to change the colors for
    particular style elements in Python code. For a full
    list of available styles see
    http://www.riverbankcomputing.co.uk/static/Docs/QScintilla2/
    classQsciLexerPython.html#a7ada96b405219532d482cf5a1b610f4a
    """
    def defaultColor(self, style):
        if style == 0:
            return QtGui.QColor('#000000')
        elif style == 1:
            return QtGui.QColor('#C0C0C0')
        elif style == 2:
            return QtGui.QColor('#0000CC')
        elif style == 3:
            return QtGui.QColor('#CC0000')
        elif style == 4:
            return QtGui.QColor('#00CC00')
        return Qsci.QsciLexerCustom.defaultColor(self, style)


# A dictionary to specify which lexer goes with which file type.
lexer_type = {'py': QsciLexerPython,
              'sh': QsciLexerBash,
              'tex': QsciLexerTeX,
              'cpp': QsciLexerCPP,
              }


class SciEditor(QtmacsApplet):
    def __init__(self, appletID):
        # Initialise the base classes.
        super().__init__(appletID)

        # Instantiate and register a Scintilla widget.
        self.qteScintilla = self.qteAddWidget(QtmacsScintilla(self))

        # Add all the fields necessar in the mode bar.
        self._qteModeBar = QtmacsModeBar()
        self._qteModeBar.qteAddMode('EOL', 'U')
        self._qteModeBar.qteAddMode('READONLY', 'R')
        self._qteModeBar.qteAddMode('MODIFIED', '-')
        self._qteModeBar.qteAddMode('APPLETID', self.qteAppletID())
        self._qteModeBar.qteAddMode('POSITION', '(0,0)')
        self._qteModeBar.qteAddMode('OTHER', None)

        # Arrange the Scintilla editor widget and the mode bar in a layout.
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.qteScintilla)
        vbox.addWidget(self._qteModeBar)
        self.setLayout(vbox)

        # Intercept the position-changed signals.
        self.qteScintilla.cursorPositionChanged.connect(
            self.qteCursorPosChanged)

        # Intercept the modification changed signal.
        self.qteScintilla.modificationChanged.connect(
            self.qteModificationChanged)

        # Intercept the qtesigSaveState signal to know when
        # the document is in its last saved state again.
        self.qteScintilla.qteUndoStack.qtesigSavedState.connect(
            self.qteSavedState)

        # Query the end-of-line (EOL) mode and enforce it throughout
        # the document.
        eolmode = self.qteScintilla.eolMode()
        self.qteScintilla.setEolMode(eolmode)

        # Report the used EOL mode in the status buffer.
        if eolmode == QtmacsScintilla.EolUnix:
            self.qteMain.qteStatus('Using Unix EOL mode')
            self._qteModeBar.qteChangeModeValue('EOL', 'Unix')
        elif eolmode == QtmacsScintilla.EolWindows:
            self.qteMain.qteStatus('Using Windows EOL mode')
            self._qteModeBar.qteChangeModeValue('EOL', 'Dos')
        elif eolmode == QtmacsScintilla.EolMac:
            self.qteMain.qteStatus('Using Mac EOL mode')
            self._qteModeBar.qteChangeModeValue('EOL', 'Mac')
        else:
            self.qteMain.qteStatus('Unknown EOL mode')
            self._qteModeBar.qteChangeModeValue('EOL', 'Unknown')

        # Initialise the file handle and file name.
        self.file = self.fileName = None

        # Load the file with name 'appletID'.
        self.loadFile(appletID)

        # Extract the file extension.
        idx = appletID.rfind('.')
        if idx >= 0:
            ext = appletID[idx + 1:]
        else:
            ext = None

        # Prevent Scintilla from auto-indenting when asked to
        # add a new line. This is necessary because the new-line
        # macro takes care of the indentation in order to keep
        # the undo history consistent.
        self.qteScintilla.setAutoIndent(False)

        # Change indentation width and ensure that indents are actual
        # whitespaces, not tabs.
        self.qteScintilla.setTabWidth(4)
        self.qteScintilla.setIndentationsUseTabs(False)

        # Try to find a lexer for the file type to enable syntax
        # highlighting and folding. If no appropriate lexer exists,
        # then treat the file as pure text.
        if ext in lexer_type:
            self.qteScintilla.qteSetLexer(lexer_type[ext])
            self.qteScintilla.setFolding(Qsci.QsciScintilla.BoxedTreeFoldStyle)
        else:
            # Disable margin #1 which is (by default) the symbol margin for
            # eg. folding.
            self.qteScintilla.setMarginWidth(1, 0)

        # Increase all fonts by a factor of two for readability.
        self.qteScintilla.zoomTo(2)

        # Declare the content pristine.
        self.qteScintilla.setModified(False)

    @classmethod
    def __qteRegisterAppletInit__(cls):
        """
        Assciate various file types with this applet so that the
        find-file macro will instantiate us automatically for
        any of them.
        """
        tmp = qte_global.findFile_types
        tmp.insert(0, ('.*\.txt$', cls.__name__))
        tmp.insert(0, ('.*\.py$', cls.__name__))
        tmp.insert(0, ('.*\.sh$', cls.__name__))
        tmp.insert(0, ('.*\.tex$', cls.__name__))
        tmp.insert(0, ('.*\.cpp$', cls.__name__))

    def qteCursorPosChanged(self, line, col):
        # Update the line- and column number in the mode bar.
        msg = '({},{})'.format(line, col)
        self._qteModeBar.qteChangeModeValue('POSITION', msg)

    def qteModificationChanged(self, mod):
        """
        Update the modification status in the mode bar.

        This slot is Connected to the ``modificationChanged`` signal
        from the ``QtmacsScintilla`` widget.
        """
        if mod:
            s = '*'
        else:
            s = '-'
        self._qteModeBar.qteChangeModeValue('MODIFIED', s)

    def qteSavedState(self, msg):
        """
        Set the modified state to 'Saved'.

        This slot is connected to the ``qtesigSavedState`` signal
        from the ``QtmacsUndoStack`` class. It calls the
        ``setModified`` method of the ``QtmacsScintilla`` widget
        which, in turn, triggers the ``qteModificationChanged``
        slot to ensure the mode bar status is updated accordingly.
        """
        self.qteScintilla.setModified(False)

    def loadFile(self, fileName):
        """
        Display the file ``fileName``.
        """

        self.fileName = fileName
        # Assign QFile object with the current name.
        self.file = QtCore.QFile(fileName)
        if self.file.exists():
            # Load the file into the widget and reset the undo stack
            # to delete the undo object create by the setText method.
            # Without it, an undo operation would delete the content
            # of the widget which is intuitive.
            self.qteScintilla.setText(open(fileName).read())
            self.qteScintilla.qteUndoStack.reset()
        else:
            msg = "File <b>{}</b> does not exist".format(self.qteAppletID())
            self.qteLogger.info(msg)

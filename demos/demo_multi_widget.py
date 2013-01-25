# Copyright 2012-2013, Oliver Nagy <qtmacsdev@gmail.com>
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
A demo to show multiple widgets and a ``QPushButton`` in an applet.

As with every applet, do not use::

    from demo_multi_widget import DemoMultiWidget

"""
import qtmacs.qte_global as qte_global

from PyQt4 import QtCore, QtGui, QtWebKit
from qtmacs.base_applet import QtmacsApplet
from qtmacs.base_macro import QtmacsMacro


class DemoMultiWidget(QtmacsApplet):
    """
    An applet with multiple widgets of different types. It contains a
    conventional QLineEdit, a second QLineEdit with a custom widget
    signature name, a static label (cannot receive focus), and a
    QPushButton which behaves like in normal Qt applications and has a
    connected 'clicked' signal.
    """
    def __init__(self, appletID):
        # Initialise the base class.
        super().__init__(appletID)

        # Add a (non focusable) label, two line edits, and a push button.
        self.qteLabel = self.qteAddWidget(QtGui.QLabel(self),
                                          isFocusable=False)
        self.qteLine1 = self.qteAddWidget(QtGui.QLineEdit(self))
        self.qteLine2 = self.qteAddWidget(QtGui.QLineEdit(self),
                                          widgetSignature='custom')
        self.qtePB = self.qteAddWidget(QtGui.QPushButton(self))

        # Set the labels.
        self.qteLabel.setText('Label')
        self.qtePB.setText('Hit me')

        # Connect the clicked signal to a slot like in any PyQt4 program.
        self.qtePB.clicked.connect(self.myClickedSlot)

        # Register and bind the DemoMacroClick macro to the <space>
        # key to ensure that every button inside this applet is
        # clickable without a mouse.
        name = self.qteMain.qteRegisterMacro(DemoMacroClick)
        self.qteMain.qteBindKeyApplet('<space>', name, self)

        # Bind a test macro to the custom QLineEdit and associate the 'e' key.
        name = self.qteMain.qteRegisterMacro(DemoMacroMulti1)
        self.qteMain.qteBindKeyWidget('e', name, self.qteLine2)

        # Bind a test macro to the custom QLineEdit and associate the 'n' key.
        name = self.qteMain.qteRegisterMacro(DemoMacroMulti2)
        self.qteMain.qteBindKeyApplet('n', name, self)

    def myClickedSlot(self):
        self.qteLine2.setText('Hello')

        if self.qteLine1.isVisible():
            self.qteLine1.hide()
        else:
            self.qteLine1.show()

        # remove a keybinding
        #self.qteMain.qteUnbindKeyApplet(self, 'n')
        #self.qteMain.qteUnbindAllFromApplet(self)
        #self.qteMain.qteUnbindAllFromWidgetObject(self.qteLine2)
        #self.qteMain.qteUnbindKeyFromWidgetObject('n', self.qteLine1)


class DemoMacroMulti1(QtmacsMacro):
    """
    Insert the typed key, followed by a '|' character, into a QLineEdit.

    |Signature|

    * *applet*: 'DemoMultiWidget'
    * *widget*: 'custom'
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('DemoMultiWidget')
        self.qteSetWidgetSignature('custom')

    def qteRun(self):
        key = qte_global.last_key_sequence.toQKeyEventList()[-1]
        self.qteWidget.insert(key.text() + '|')


class DemoMacroMulti2(QtmacsMacro):
    """
    Insert the typed key, followed by a '$' character, into a QLineEdit.

    |Signature|

    * *applet*: 'DemoMultiWidget'
    * *widget*: 'custom'
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('DemoMultiWidget')
        self.qteSetWidgetSignature('custom')

    def qteRun(self):
        key = qte_global.last_key_sequence.toQKeyEventList()[-1]
        self.qteWidget.insert(key.text() + '$')


class DemoMacroClick(QtmacsMacro):
    """
    Pass the last key on to the widget.

    |Signature|

    * *applet*: 'DemoMultiWidget'
    * *widget*: 'QPushButton'
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('DemoMultiWidget')
        self.qteSetWidgetSignature('QPushButton')

    def qteRun(self):
        key = qte_global.last_key_sequence.toQKeyEventList()[-1]
        self.qteWidget.keyPressEvent(key)

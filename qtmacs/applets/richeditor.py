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
A simple text editor based on ``QtmacsTextEdit``.

If the ``appletID`` is '**Startup Screen**' then the applet displays a
GNU head (from http://www.gnu.org/graphics/bahlon/) and the GPL,
otherwise the file with name ``appletID``, or an empty buffer if this
file does not exist.

As with every applet, do **not** use::

    from qtmacs.applets.richeditor import RichEditor

"""

import os
import qtmacs.base_applet
import qtmacs.extensions.qtmacstextedit_widget
from PyQt4 import QtCore, QtGui

# Shorthands
QtmacsTextEdit = qtmacs.extensions.qtmacstextedit_widget.QtmacsTextEdit


class RichEditor(qtmacs.base_applet.QtmacsApplet):
    """
    Standard text editing class based on ``QtmacsTextEdit``.

    |Args|

    * ``appletID`` (**str**): unique ID used by ``QtmacsMain`` to
      distinguish applets.

    """
    def __init__(self, appletID):
        # Initialise the base class.
        super().__init__(appletID)

        # Add a QtmacsTextEdit widget to the applet.
        self.qteText = self.qteAddWidget(QtmacsTextEdit(self))

        # Initialise the file handle and file name.
        self.file = self.fileName = None

        # The startup screen is special.
        if appletID == '**Startup Screen**':
            self.displayStartupScreen()
        else:
            self.loadFile(appletID)

    def loadFile(self, fileName):
        """
        Display the file associated with the appletID.
        """

        # Assign QFile object with the current name.
        self.file = QtCore.QFile(fileName)
        if self.file.exists():
            self.qteText.append(open(fileName).read())
        else:
            msg = "File <b>{}</b> does not exist".format(self.qteAppletID())
            self.qteLogger.info(msg)

    def displayStartupScreen(self):
        """
        Display the Qtmacs logo (Max) together with the GPL.
        """
        # Determine the path of the Qtmacs application because this is
        # also where the image file is located.
        path, _ = os.path.split(qtmacs.qtmacsmain.__file__)

        # Load the image and insert it at the current position.
        img = QtGui.QImage(path + '/misc/Max.png')
        tc = self.qteText.textCursor()
        tc.insertImage(img)
        self.qteText.setTextCursor(tc)

        # Display the GPL text.
        gpl_text = open(path + '/misc/gpl.txt').readlines()
        gpl_text = ''.join(gpl_text)
        self.qteText.append('\n\n' + gpl_text)

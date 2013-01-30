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
A demo for displaying PDF files.

This demo depends on a working popplerqt4 installation
(http://code.google.com/p/python-poppler-qt4/).

As with every applet, do **not** use::

    from qtmacs.applets.pdf_reader import PDFReader

"""

import popplerqt4
import qtmacs.qte_global as qte_global

from PyQt4 import QtCore, QtGui, QtWebKit
from qtmacs.base_applet import QtmacsApplet
from qtmacs.base_macro import QtmacsMacro


class PDFReader(QtmacsApplet):
    """
    Display the first page of a PDF file using Python-Poppler library.
    """
    def __init__(self, appletID):
        # Initialise the base classes.
        super().__init__(appletID)

        # Initialise the file handle and file name.
        self.file = self.fileName = None

        # Add the QScrollArea that will display the PDF file.
        self.qteScroll = self.qteAddWidget(QtGui.QScrollArea())

        # Put it all into a layout as Qtmacs will otherwise try to
        # arrange it automatically, which is generally a bad idea when
        # more than one widget is involved.
        hbox = QtGui.QHBoxLayout(self)
        hbox.addWidget(self.qteScroll)
        self.setLayout(hbox)

        # Connect two macros to the scroll area, one for scrolling
        # down, one for scrolling up.
        down = self.qteMain.qteRegisterMacro(ScrollDown)
        up = self.qteMain.qteRegisterMacro(ScrollUp)
        self.qteMain.qteBindKeyWidget('<ctrl>+v', down, self.qteScroll)
        self.qteMain.qteBindKeyWidget('<alt>+v', up, self.qteScroll)

        # If the appletID does not denote a PDF file then open the
        # demo file. Otherwise, open the requested file.
        if appletID[-3:] == 'pdf':
            self.loadFile(appletID)
        else:
            self.loadFile('pyqt-whitepaper-a4.pdf')

    @classmethod
    def __qteRegisterAppletInit__(cls):
        """
        Assciate PDF files with this applet so that the find-file
        macro will instantiate us automatically.
        """
        tmp = qte_global.findFile_types
        tmp.insert(0, ('.*\.pdf$', cls.__name__))

    def loadFile(self, fileName):
        """
        Load and display the PDF file specified by ``fileName``.
        """

        # Test if the file exists.
        if not QtCore.QFile(fileName).exists():
            msg = "File <b>{}</b> does not exist".format(self.qteAppletID())
            self.qteLogger.info(msg)
            self.fileName = None
            return

        # Store the file name and load the PDF document with the
        # Poppler library.
        self.fileName = fileName
        doc = popplerqt4.Poppler.Document.load(fileName)

        # Enable antialiasing to improve the readability of the fonts.
        doc.setRenderHint(popplerqt4.Poppler.Document.Antialiasing)
        doc.setRenderHint(popplerqt4.Poppler.Document.TextAntialiasing)

        # Convert each page to an image, then install that image as the
        # pixmap of a QLabel, and finally insert that QLabel into a
        # vertical layout.
        hbox = QtGui.QVBoxLayout()
        for ii in range(doc.numPages()):
            pdf_img = doc.page(ii).renderToImage()
            pdf_label = self.qteAddWidget(QtGui.QLabel())
            pdf_label.setPixmap(QtGui.QPixmap.fromImage(pdf_img))
            hbox.addWidget(pdf_label)

        # Use an auxiliary widget to hold that layout and then place
        # that auxiliary widget into a QScrollView. The auxiliary
        # widget is necessary because QScrollArea can only display a
        # single widget at once.
        tmp = self.qteAddWidget(QtGui.QWidget(self))
        tmp.setLayout(hbox)
        self.qteScroll.setWidget(tmp)


class ScrollDown(QtmacsMacro):
    """
    Scroll down by approximately as much as is currently visible.
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('PDFReader')
        self.qteSetWidgetSignature('QScrollArea')

    def qteRun(self):
        bar = self.qteWidget.verticalScrollBar()
        tot_height = self.qteWidget.maximumViewportSize().height()
        new_value = bar.value() + int(0.95 * tot_height)
        bar.setValue(new_value)


class ScrollUp(QtmacsMacro):
    """
    Scroll up by approximately as much as is currently visible.
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('PDFReader')
        self.qteSetWidgetSignature('QScrollArea')

    def qteRun(self):
        bar = self.qteWidget.verticalScrollBar()
        tot_height = self.qteWidget.maximumViewportSize().height()
        new_value = bar.value() - int(0.95 * tot_height)
        bar.setValue(new_value)

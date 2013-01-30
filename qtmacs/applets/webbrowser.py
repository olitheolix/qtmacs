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
A demo for displaying web pages.

As with every applet, do **not** use::

    from qtmacs.applets.webbrowser import WebBrowser

"""
import qtmacs.qte_global as qte_global

from PyQt4 import QtCore, QtGui, QtWebKit
from qtmacs.base_applet import QtmacsApplet
from qtmacs.base_macro import QtmacsMacro


class WebBrowser(QtmacsApplet):
    """
    A Web Browser Demo.
    """
    def __init__(self, appletID):
        # Initialise the base class.
        super().__init__(appletID)

        # Add a webView element and point it to an initial location.
        self.qteWeb = self.qteAddWidget(QtWebKit.QWebView(self))

        # Register and bind the macros.
        name = self.qteMain.qteRegisterMacro(ScrollDown)
        self.qteMain.qteBindKeyWidget('<ctrl>+n', name, self.qteWeb)
        name = self.qteMain.qteRegisterMacro(ScrollUp)
        self.qteMain.qteBindKeyWidget('<ctrl>+p', name, self.qteWeb)

        # Bind the standard alphanumerical keys.
        alpha_keys = 'abcdefghijklmnopqrstuvwxyz'
        alpha_keys += alpha_keys.upper() + '0123456789'
        name = self.qteMain.qteRegisterMacro(SelfInsert)
        for ch in alpha_keys:
            self.qteMain.qteBindKeyWidget(ch, name, self.qteWeb)

        # Also bind the <space>, <enter>, and <backspace> key.
        self.qteMain.qteBindKeyWidget('<space>', name, self.qteWeb)
        self.qteMain.qteBindKeyWidget('<return>', name, self.qteWeb)
        self.qteMain.qteBindKeyWidget('<backspace>', name, self.qteWeb)

        # Register and bind macro to move the cursor to the left and right.
        name = self.qteMain.qteRegisterMacro(BackwardChar)
        self.qteMain.qteBindKeyWidget('<ctrl>+b', name, self.qteWeb)
        name = self.qteMain.qteRegisterMacro(ForwardChar)
        self.qteMain.qteBindKeyWidget('<ctrl>+f', name, self.qteWeb)

        # If appletID starts with 'http' then interpret it as an URL,
        # otherwise load a default page.
        if appletID[:4] == 'http':
            self.loadFile(appletID)
        else:
            self.loadFile('http://www.google.com.au')

    @classmethod
    def __qteRegisterAppletInit__(cls):
        """
        Update the 'findFile_types' variable so that the find-file
        macro will open all files that start with 'http://' with this
        class.
        """
        tmp = qte_global.findFile_types
        tmp.insert(0, ('http://.*$', cls.__name__))

    def loadFile(self, fileName):
        """
        Load the URL ``fileName``.
        """
        self.fileName = fileName
        self.qteWeb.load(QtCore.QUrl(fileName))


class ScrollDown(QtmacsMacro):
    """
    Move the web page down by 25% of its visible size.
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('WebBrowser')
        self.qteSetWidgetSignature('QWebView')

    def qteRun(self):
        # Compute 25% of the currently visible web-page height (in pixels).
        size = self.qteWidget.page().viewportSize()
        inc = int(size.height() * 0.25)

        # Move the web page ``inc`` pixels up.
        self.qteWidget.page().mainFrame().scroll(0, +inc)


class ScrollUp(QtmacsMacro):
    """
    Move the web page up by 25% of its visible size.
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('WebBrowser')
        self.qteSetWidgetSignature('QWebView')

    def qteRun(self):
        # Compute 25% of the currently visible web-page height (in pixels).
        size = self.qteWidget.page().viewportSize()
        inc = int(size.height() * 0.25)

        # Move the web page ``inc`` pixels up.
        self.qteWidget.page().mainFrame().scroll(0, -inc)


class SelfInsert(QtmacsMacro):
    """
    Insert a character into the active element.
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('WebBrowser')
        self.qteSetWidgetSignature('QWebView')

    def qteRun(self):
        last_key = qte_global.last_key_sequence.toQKeyEventList()[-1]
        self.qteWidget.keyPressEvent(last_key)


class BackwardChar(QtmacsMacro):
    """
    Move the caret one character back.
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('WebBrowser')
        self.qteSetWidgetSignature('QWebView')

    def qteRun(self):
        self.qteWidget.triggerPageAction(QtWebKit.QWebPage.MoveToPreviousChar)


class ForwardChar(QtmacsMacro):
    """
    Move the caret one character forward.
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('WebBrowser')
        self.qteSetWidgetSignature('QWebView')

    def qteRun(self):
        self.qteWidget.triggerPageAction(QtWebKit.QWebPage.MoveToNextChar)


class ShowActiveElement(QtmacsMacro):
    """
    Find the active web element and display its attributes.
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('WebBrowser')
        self.qteSetWidgetSignature('QWebView')

    def qteRun(self):
        frame = self.qteWidget.page().currentFrame()
        for element in frame.documentElement().findAll('*'):
            if element.hasFocus():
                print('The active element has the following attributes: ')
                for attr in element.attributeNames():
                    print('  ' + attr + ': ', element.attribute(attr))

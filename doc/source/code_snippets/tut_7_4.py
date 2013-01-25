import qtmacs.qte_global as qte_global

from PyQt4 import QtCore, QtGui, QtWebKit
from qtmacs.base_applet import QtmacsApplet
from qtmacs.base_macro import QtmacsMacro

# Get a reference to the main instance of Qtmacs.
qteMain = qte_global.qteMain


class DemoWeb(QtmacsApplet):
    """
    A Web Browser Demo.
    """
    def __init__(self, appletID):
        # Initialise the base class.
        super().__init__(appletID)

        # Add a webView element and point it to an initial location.
        self.qteWeb = self.qteAddWidget(QtWebKit.QWebView(self))
        self.qteWeb.load(QtCore.QUrl('http://www.google.com.au'))

        # Register and bind the macros.
        name = self.qteMain.qteRegisterMacro(ScrollDown)
        self.qteMain.qteBindKeyWidget('<ctrl>+n', name, self.qteWeb)
        name = self.qteMain.qteRegisterMacro(ScrollUp)
        self.qteMain.qteBindKeyWidget('<ctrl>+p', name, self.qteWeb)

        # Bind it the standard alphanumerical keys.
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


class ScrollDown(QtmacsMacro):
    """
    Move the web page down by 25% of its visible size.
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('DemoWeb')
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
        self.qteSetAppletSignature('DemoWeb')
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
        self.qteSetAppletSignature('DemoWeb')
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
        self.qteSetAppletSignature('DemoWeb')
        self.qteSetWidgetSignature('QWebView')

    def qteRun(self):
        self.qteWidget.triggerPageAction(QtWebKit.QWebPage.MoveToPreviousChar)


class ForwardChar(QtmacsMacro):
    """
    Move the caret one character forward.
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('DemoWeb')
        self.qteSetWidgetSignature('QWebView')

    def qteRun(self):
        self.qteWidget.triggerPageAction(QtWebKit.QWebPage.MoveToNextChar)


# Register the applet and create an instance thereof.
app_name = qteMain.qteRegisterApplet(DemoWeb)
app_obj = qteMain.qteNewApplet(app_name)
qteMain.qteMakeAppletActive(app_obj)

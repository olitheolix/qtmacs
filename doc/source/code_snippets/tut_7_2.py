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


# Register the applet and create an instance thereof.
app_name = qteMain.qteRegisterApplet(DemoWeb)
app_obj = qteMain.qteNewApplet(app_name)
qteMain.qteMakeAppletActive(app_obj)

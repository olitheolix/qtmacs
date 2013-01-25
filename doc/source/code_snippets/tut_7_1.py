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

# Register the applet and create an instance thereof.
app_name = qteMain.qteRegisterApplet(DemoWeb)
app_obj = qteMain.qteNewApplet(app_name)
qteMain.qteMakeAppletActive(app_obj)

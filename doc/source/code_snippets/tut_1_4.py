"""
Tutorial 1: a "Hello world" applet.
"""

# Import the module with the global variables and the macro base class.
import qtmacs.qte_global as qte_global
from qtmacs.base_applet import QtmacsApplet
from PyQt4 import QtGui

# Get a reference to the main instance of Qtmacs.
qteMain = qte_global.qteMain


class HelloWorldApp(QtmacsApplet):
    """
    A 'Hello world' applet.
    """
    def __init__(self, appletID):
        # Initialise the base class.
        super().__init__(appletID)

        # Instantiate a QLabel.
        self.qteLabel = QtGui.QLabel('Hello world.', parent=self)


# Register the applet with Qtmacs.
qteMain.qteRegisterApplet(HelloWorldApp)

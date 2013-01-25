"""
Tutorial 1: a "Hello world" applet.
"""

# Import the module with the global variables and the macro base class.
import qtmacs.qte_global as qte_global
from qtmacs.base_applet import QtmacsApplet

# Get a reference to the main instance of Qtmacs.
qteMain = qte_global.qteMain


class HelloWorldApp(QtmacsApplet):
    """
    An empty applet.
    """
    pass


# Register the applet with Qtmacs.
qteMain.qteRegisterApplet(HelloWorldApp)

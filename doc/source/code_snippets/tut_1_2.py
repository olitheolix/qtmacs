"""
Tutorial 1: a "Hello world" macro.
"""

# Import the module with the global variables and the macro base class.
import qtmacs.qte_global as qte_global
from qtmacs.base_macro import QtmacsMacro

# Get a reference to the main instance of Qtmacs.
qteMain = qte_global.qteMain


class HelloWorld(QtmacsMacro):
    """
    Displays 'Hello world.' in the status applet.

    |Signature|

    * *applet*: '*'
    * *widget*: '*'
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('*')

    def qteRun(self):
        self.qteMain.qteStatus('Hello world.')


# Register the macro with Qtmacs.
macro_name = qteMain.qteRegisterMacro(HelloWorld)
qteMain.qteBindKeyGlobal('<ctrl>+d h', macro_name)

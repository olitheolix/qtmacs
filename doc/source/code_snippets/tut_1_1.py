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
    Prints 'Hello world.' to the console.

    |Signature|

    * *applet*: '*'
    * *widget*: '*'
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('*')

    def qteRun(self):
        print('Hello world.')


# Register the macro with Qtmacs.
macro_name = qteMain.qteRegisterMacro(HelloWorld)

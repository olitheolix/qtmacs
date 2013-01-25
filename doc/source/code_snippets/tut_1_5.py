"""
Tutorial 1: a "Hello world" macro and applet.
"""

# Import the module with the global variables and the macro base class.
import qtmacs.qte_global as qte_global
from qtmacs.base_macro import QtmacsMacro
from qtmacs.base_applet import QtmacsApplet
from PyQt4 import QtGui

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
        print(self.qteApplet._qteActiveWidget)


# Register the macro with Qtmacs.
macro_name = qteMain.qteRegisterMacro(HelloWorld)
qteMain.qteBindKeyGlobal('<ctrl>+d h', macro_name)


class HelloWorldApp(QtmacsApplet):
    """
    A 'Hello world' applet.
    """
    def __init__(self, appletID):
        # Initialise the base class.
        super().__init__(appletID)

        # Create some Qt widgets for demonstration purposes.
        self.qteLabel = QtGui.QLabel('Hello world.', parent=self)
        self.qteTextEdit = QtGui.QLineEdit('TextEdit', parent=self)
        self.qteSpinBox = QtGui.QSpinBox(self)
        self.qteSlider = QtGui.QSlider(self)
        self.qteDial = QtGui.QDial(self)

        # Place the widgets in a layout.
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.qteLabel)
        layout.addWidget(self.qteTextEdit)
        layout.addWidget(self.qteSpinBox)
        layout_tmp = QtGui.QHBoxLayout()
        layout_tmp.addWidget(self.qteSlider)
        layout_tmp.addWidget(self.qteDial)
        layout.addLayout(layout_tmp)
        self.setLayout(layout)


# Register the applet with Qtmacs, create an instance of it, and display it.
app_name = qteMain.qteRegisterApplet(HelloWorldApp)
app_obj = qteMain.qteNewApplet(app_name)
qteMain.qteMakeAppletActive(app_obj)

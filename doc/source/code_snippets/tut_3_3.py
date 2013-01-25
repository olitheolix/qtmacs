"""
Tutorial 3: Applet- and macro signatures.
"""

# Import the module with the global variables and the macro base class.
import qtmacs.qte_global as qte_global
from qtmacs.base_macro import QtmacsMacro
from qtmacs.base_applet import QtmacsApplet
from PyQt4 import QtGui

# Get a reference to the main instance of Qtmacs.
qteMain = qte_global.qteMain


class TutorialMulti(QtmacsApplet):
    """
    An applet with multiple widgets.
    """
    def __init__(self, appletID):
        # Initialise the base class.
        super().__init__(appletID)

        # Instantiate three QLineEdit objects.
        line1 = QtGui.QLineEdit(self)
        line2 = QtGui.QLineEdit(self)
        line3 = QtGui.QLineEdit(self)

        # Register them with Qtmacs.
        self.qteLine1 = self.qteAddWidget(line1)
        self.qteLine2 = self.qteAddWidget(line2, autoBind=False)
        self.qteLine3 = self.qteAddWidget(line3, widgetSignature='custom')

        # Register the macro and bind it to the 'e' key for all
        # widgets currently registered in this class.
        name = self.qteMain.qteRegisterMacro(DemoMacroLineEdit)
        self.qteMain.qteBindKeyApplet('e', name, self)


class DemoMacroLineEdit(QtmacsMacro):
    """
    Insert the typed key, followed by a '|' character, into a QLineEdit.

    |Signature|

    * *applet*: '*'
    * *widget*: 'QLineEdit'
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QLineEdit')

    def qteRun(self):
        self.qteWidget.insert('|LineEdit|')


# Register the applet with Qtmacs and create an instance of it.
app_name = qteMain.qteRegisterApplet(TutorialMulti)
app_obj = qteMain.qteNewApplet(app_name)

# Make the applet active.
qteMain.qteMakeAppletActive(app_obj)

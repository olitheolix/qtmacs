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

        # Instantiate and register two push buttons.
        self.qtePBLocal = self.qteAddWidget(QtGui.QPushButton(self))
        self.qtePBGlobal = self.qteAddWidget(QtGui.QPushButton(self))
        self.qtePBLocal.setText('Local')
        self.qtePBGlobal.setText('Global')

        # Register the macro and connect the ``clicked`` signals of
        # the push buttons.
        self.macroName = qteMain.qteRegisterMacro(DemoMacroLineEdit)
        self.qtePBGlobal.clicked.connect(self.clickedGlobal)
        self.qtePBLocal.clicked.connect(self.clickedLocal)

        # Register DemoClickTheButton and bind it to <space>.
        name = qteMain.qteRegisterMacro(DemoClickTheButton)
        self.qteMain.qteBindKeyApplet('<space>', name, self)

    def clickedGlobal(self):
        qteMain.qteBindKeyGlobal('e', self.macroName)

    def clickedLocal(self):
        qteMain.qteBindKeyApplet('e', self.macroName, self)


class DemoMacroLineEdit(QtmacsMacro):
    """
    Insert the typed key, followed by a '|' character, into a QLineEdit.

    | Signature |

    * *applet*: '*'
    * *widget*: 'QLineEdit'
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QLineEdit')

    def qteRun(self):
        self.qteWidget.insert('|LineEdit|')


class DemoClickTheButton(QtmacsMacro):
    """
    Pass the last key on to the Qt native ``keyPressEvent`` method of
    the active widget.

    |Signature|

    * *applet*: 'DemoMultiWidget'
    * *widget*: 'QPushButton'
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QPushButton')

    def qteRun(self):
        self.qteWidget.animateClick()


# Register the applet with Qtmacs and create an instance of it.
app_name = qteMain.qteRegisterApplet(TutorialMulti)
app_obj1 = qteMain.qteNewApplet(app_name)
app_obj2 = qteMain.qteNewApplet(app_name)

# Make the applet active, split its layout, and show the second
# applet in the other half.
qteMain.qteMakeAppletActive(app_obj1)
qteMain.qteSplitApplet(app_obj2)

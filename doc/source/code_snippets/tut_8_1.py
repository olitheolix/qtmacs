"""
Tutorial 8: an applet with a ``QLineEdit`` that displays its content
            in the status applet whenever the user hits <enter>.
"""

# Import the module with the global variables and the macro base
# class.
import qtmacs.qte_global as qte_global
from qtmacs.base_macro import QtmacsMacro
from qtmacs.base_applet import QtmacsApplet
from PyQt4 import QtGui

# Get a reference to the main instance of Qtmacs.
qteMain = qte_global.qteMain


class TutorialMiniApplet(QtmacsApplet):
    """
    An applet with a ``QLineEdit``.
    """
    def __init__(self, appletID):
        # Initialise the base class.
        super().__init__(appletID)

        # Add a QLineEdit widget to the applet.
        self.qteText = self.qteAddWidget(QtGui.QLineEdit(self))

        # Register our macro and let it handle the <return> key for
        # the QTextEdit widget.
        name = qteMain.qteRegisterMacro(InputComplete)
        qteMain.qteBindKeyWidget('<return>', name, self.qteText)


class InputComplete(QtmacsMacro):
    """
    Read the content from the ``QLineEdit`` and display it in the
    status applet.

    |Signature|

    * *applet*: 'TutorialMiniApplet'
    * *widget*: 'QLineEdit'

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('TutorialMiniApplet')
        self.qteSetWidgetSignature('QLineEdit')

    def qteRun(self):
        content = self.qteWidget.text()
        self.qteMain.qteStatus(content)


# Register the applet with Qtmacs, create an instance of it, and
# display it.
app_name = qteMain.qteRegisterApplet(TutorialMiniApplet)
app_obj = qteMain.qteNewApplet(app_name)
qteMain.qteMakeAppletActive(app_obj)

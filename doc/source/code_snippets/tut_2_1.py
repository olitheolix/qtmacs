"""
Tutorial 2: an editor component -- Qtmacs style.
"""

# Import the module with the global variables and the macro base
# class.
import qtmacs.qte_global as qte_global
from qtmacs.base_macro import QtmacsMacro
from qtmacs.base_applet import QtmacsApplet
from PyQt4 import QtGui

# Get a reference to the main instance of Qtmacs.
qteMain = qte_global.qteMain


class TutorialTextEdit(QtmacsApplet):
    """
    A simple text editor.
    """
    def __init__(self, appletID):
        # Initialise the base class.
        super().__init__(appletID)

        # Add a QTextEdit widget to the applet.
        self.qteText = self.qteAddWidget(QtGui.QTextEdit(self), autoBind=False)
        self.qteText.append('Tutorial 2: a macro driven text editor.')


# Register the applet with Qtmacs, create an instance of it, and
# display it.
app_name = qteMain.qteRegisterApplet(TutorialTextEdit)
app_obj = qteMain.qteNewApplet(app_name)
qteMain.qteMakeAppletActive(app_obj)

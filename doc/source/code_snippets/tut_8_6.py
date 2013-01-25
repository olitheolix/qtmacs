"""
Tutorial 8: an applet with a ``QLineEdit`` that displays its content
            in the status applet whenever the user hits <enter>.
"""

# Import the default query object.
import qtmacs.miniapplets.base_query as base_query

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


class Query(base_query.MiniAppletBaseQuery):
    """
    Demonstrate the use of ``MiniAppletBaseQuery``.
    """
    def generateCompletions(self, userInput):
        """
        This method is called whenever the user hits <tab>. The
        ``userInput`` argument is the currently entered text.
        """
        return ['Option 1', 'Option 2', 'Option 3', 'Yes', 'No']

    def inputCompleted(self, userInput):
        """
        This method is called whenever the user hits <enter>. The
        ``userInput`` argument is the currently entered text.
        """
        self.qteMain.qteStatus(userInput)


class SpawnTutorialMiniApplet(QtmacsMacro):
    """
    Register- and instantiate ``TutorialMiniApplet``.

    |Signature|

    * *applet*: '*'
    * *widget*: '*'

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('*')
        self.qteQueryHistory = ['Item 1', 'foo', 'bar']

    def qteRun(self):
        # Instantiate the query object and install it as the mini applet.
        query = Query(self.qteApplet, self.qteWidget, prefix='Tutorial Query',
                      history=self.qteQueryHistory)
        self.qteMain.qteAddMiniApplet(query)


# Register ``SpawnTutorialMiniApplet`` and bind it to a key.
name = qteMain.qteRegisterMacro(SpawnTutorialMiniApplet)
qteMain.qteBindKeyGlobal('<ctrl>+x q', name)

import qtmacs.qte_global as qte_global
from qtmacs.base_applet import QtmacsApplet
from qtmacs.base_macro import QtmacsMacro
from PyQt4.Qsci import QsciScintilla, QsciScintillaBase, QsciLexerPython

# Get a reference to the main instance of Qtmacs.
qteMain = qte_global.qteMain


class Scintilla(QtmacsApplet):
    def __init__(self, appletID):
        # Initialise the base classes.
        super().__init__(appletID)

        # Instantiate and register a Scintilla widget.
        self.qteScintilla = self.qteAddWidget(QsciScintilla(self))

        # Load this very file and display it inside the Scintilla widget.
        tmp = ''.join(open(__file__).readlines())
        self.qteScintilla.setText(tmp)

        # Change the lexer to Python to activate syntax highlighting,
        # and enable code folding.
        self.qteScintilla.setLexer(QsciLexerPython())
        self.qteScintilla.setFolding(QsciScintilla.BoxedTreeFoldStyle)

        # Register the self-insert macro.
        name = self.qteMain.qteRegisterMacro(SelfInsert)

        # Bind it the standard alphanumerical keys.
        alpha_keys = 'abcdefghijklmnopqrstuvwxyz'
        alpha_keys += alpha_keys.upper() + '0123456789'
        for ch in alpha_keys:
            self.qteMain.qteBindKeyWidget(ch, name, self.qteScintilla)


class SelfInsert(QtmacsMacro):
    """
    Insert the last typed character.

    The ``last_key_sequence`` variable is overwritten/updated every
    time the event handler in Qtmacs receives a new keyboard event.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QsciScintilla``

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QsciScintilla')

    def qteRun(self):
        # Extract the last QKeyEvent from the keyboard sequence (there
        # should only be one anyway, but just to be sure). Then
        # extract the human readable text this key represents.
        keys = qte_global.last_key_sequence.toQKeyEventList()[-1]
        ch = keys.text()

        # Determine the current cursor position inside the Scintilla
        # widget (it is organised in lines and columns, not as a stream
        # like eg. QTextEdit), insert the character, and manually move
        # the caret forward.
        line, idx = self.qteWidget.getCursorPosition()
        self.qteWidget.insertAt(ch, line, idx)
        self.qteWidget.setCursorPosition(line, idx + 1)


# Register the applet and create an instance thereof.
app_name = qteMain.qteRegisterApplet(Scintilla)
app_obj = qteMain.qteNewApplet(app_name)
qteMain.qteMakeAppletActive(app_obj)

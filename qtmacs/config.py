"""
Global configuration file loaded from the constructor of ``QtmacsMain``.
"""
# Get a reference to the main instance of Qtmacs.
import qtmacs.qte_global as qte_global
qteMain = qte_global.qteMain

# Register the RichEditor applet.
try:
    import qtmacs.applets.richeditor
    qteMain.qteRegisterApplet(qtmacs.applets.richeditor.RichEditor)
except ImportError:
    qteMain.qteLogger.info('RichEditor applet not loaded.')

errMsg = '<b>{}</b> applet not loaded.'

# Register the SciEditor applet.
try:
    import qtmacs.applets.scieditor
    qteMain.qteRegisterApplet(qtmacs.applets.scieditor.SciEditor)
except ImportError:
    msg = errMsg.format('SciEditor')
    msg += ' Are you missing PyQt4.Qsci?'
    qteMain.qteLogger.info(msg)

# Register the WebBrowser applet.
try:
    import qtmacs.applets.webbrowser
    qteMain.qteRegisterApplet(qtmacs.applets.webbrowser.WebBrowser)
except ImportError:
    msg = errMsg.format('WebBrowser')
    qteMain.qteLogger.info(msg)

# Register the PDFReaderapplet. If this fails then most likely
# because the Python bindings for Poppler could not be found.
try:
    import qtmacs.applets.pdf_reader
    qteMain.qteRegisterApplet(qtmacs.applets.pdf_reader.PDFReader)
except ImportError:
    msg = errMsg.format('PDFReader')
    msg += ' Are you missing the Python-Poppler bindings?.'
    qteMain.qteLogger.info(msg)

# Register the Bash applet. This may fail for various reasons,
# most notably on systems without a Bash (eg. Windows) or when
# the pexpect-u module is not installed.
try:
    import qtmacs.applets.bash
    qteMain.qteRegisterApplet(qtmacs.applets.bash.Bash)
except ImportError:
    msg = errMsg.format('Bash')
    qteMain.qteLogger.info(msg)

# Instantiate the WebBrowser applet and point it to the
# documentation.
url = 'http://qtmacsdev.github.com/qtmacs/titlepage.html'
appObj = qteMain.qteNewApplet('WebBrowser', url)
if appObj is not None:
    qteMain.qteMakeAppletActive(appObj)

# Instantiate the RichEditor applet with the special ID
# **Startup Screen** to display Max (the Qtmacs logo)
# and the GPL text.
appObj = qteMain.qteNewApplet('RichEditor', '**Startup Screen**')
if appObj is not None:
    qteMain.qteMakeAppletActive(appObj)

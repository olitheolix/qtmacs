"""
Global configuration file loaded from the constructor of ``QtmacsMain``.
"""
# Get a reference to the main instance of Qtmacs.
import qtmacs.qte_global as qte_global
qteMain = qte_global.qteMain

# Register the RichEditor applet.
import qtmacs.applets.richeditor
qteMain.qteRegisterApplet(qtmacs.applets.richeditor.RichEditor)

# Register the SciEditor applet.
import qtmacs.applets.scieditor
qteMain.qteRegisterApplet(qtmacs.applets.scieditor.SciEditor)

# Register the Bash applet. This may fail for various reasons,
# most notably on systems without a Bash (eg. Windows) or when
# the pexpect-u module is not installed.
try:
    import qtmacs.applets.bash
    qteMain.qteRegisterApplet(qtmacs.applets.bash.Bash)
except ImportError:
    qteMain.qteLogger.info('Bash applet could not be loaded.')

# Instantiate the RichEditor applet with the special ID
# **Startup Screen** to display Max (the Qtmacs logo)
# and the GPL text.
appObj = qteMain.qteNewApplet('RichEditor', '**Startup Screen**')
if appObj is not None:
    qteMain.qteMakeAppletActive(appObj)

"""
Register all demos with Qtmacs.
"""
import sys

# Add the parent directory with the Qtmacs package to the path.
sys.path.insert(0, '../')
import qtmacs.qte_global as qte_global
from qtmacs.base_macro import QtmacsMacro

# Get a reference to the main instance of Qtmacs.
qteMain = qte_global.qteMain

# Load all the demo applets and register them with Qtmacs. Note: do
# NOT use the 'from foo import bar' syntax because the module in which
# the applets live are also their own dedicated name spaces shared
# amongst all their instances.
sys.path.insert(0, '../demos/')
import demo_empty
import demo_multi_widget
import demo_web
import demo_thread

qteMain.qteRegisterApplet(demo_empty.DemoEmpty)
qteMain.qteRegisterApplet(demo_multi_widget.DemoMultiWidget)
qteMain.qteRegisterApplet(demo_web.DemoWeb)
qteMain.qteRegisterApplet(demo_thread.DemoThread)

# Try to register the PDF viewer. This will fail if the poppler
# library is not installed.
try:
    import demo_pdf
    qteMain.qteRegisterApplet(demo_pdf.DemoPDF)
except ImportError:
    msg = 'python-Poppler library not found. PDF demo will not work'
    qteMain.qteLogger.warning(msg)

#!/usr/bin/python3

import sys
from PyQt4 import QtGui

sys.path.insert(0, '../')
import qtmacs.qtmacsmain

# Add the "./demos' directory to the search path in order to import
# 'demo_multi_widget'.
sys.path.insert(0, '../demos/')
import demo_multi_widget


class DemoApp(QtGui.QWidget):
    """
    Demonstrate how to embed Qtmacs into a Qt application.

    In this case, the application consists of a standard QTextEdit-
    and Qtmacs widget side by side.
    """
    def __init__(self, parent=None):
        super().__init__(parent=parent)

        # Instantiate a QTextEdit widget.
        self.textEdit = QtGui.QTextEdit(self)

        # Instantiate a Qtmacs widget.
        self.qtmacs = qtmacs.qtmacsmain.QtmacsMain(parent=self)
        app = self.qtmacs.qteNewApplet('RichEditor', 'config')
        self.qtmacs.qteMakeAppletActive(app)

        # Load and show the multi widget demo from the './demos' directory.
        name = self.qtmacs.qteRegisterApplet(demo_multi_widget.DemoMultiWidget)
        wid = self.qtmacs.qteNewApplet(name, 'Multi Widget')
        if wid:
            self.qtmacs.qteMakeAppletActive(wid)

        # Place both widgets into a layout.
        appLayout = QtGui.QHBoxLayout()
        appLayout.addWidget(self.textEdit)
        appLayout.addWidget(self.qtmacs.qteNextWindow())
        self.setLayout(appLayout)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    demo = DemoApp()
    demo.show()
    sys.exit(app.exec_())

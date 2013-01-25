import popplerqt4
import qtmacs.qte_global as qte_global

from PyQt4 import QtCore, QtGui, QtWebKit
from qtmacs.base_applet import QtmacsApplet
from qtmacs.base_macro import QtmacsMacro

# Get a reference to the main instance of Qtmacs.
qteMain = qte_global.qteMain


class DemoPDF(QtmacsApplet):
    """
    Display the first page of a PDF file using Python-Poppler library.
    """
    def __init__(self, appletID):
        # Initialise the base classes.
        super().__init__(appletID)

        # Load the PDF document with the Poppler library.
        doc = popplerqt4.Poppler.Document.load('demos/pyqt-whitepaper-a4.pdf')

        # Enable antialiasing to improve the readability of the fonts.
        doc.setRenderHint(popplerqt4.Poppler.Document.Antialiasing)
        doc.setRenderHint(popplerqt4.Poppler.Document.TextAntialiasing)

        # Convert the first page to an image and install it as the
        # pixmap of a QLabel.
        pdf_img = doc.page(0).renderToImage()
        pdf_label = self.qteAddWidget(QtGui.QLabel())
        pdf_label.setPixmap(QtGui.QPixmap.fromImage(pdf_img))

        # Add a QScrollArea and place the pdf_label inside.
        self.qteScroll = self.qteAddWidget(QtGui.QScrollArea())
        self.qteScroll.setWidget(pdf_label)

        # Put it all into a layout as Qtmacs will otherwise try to
        # arrange it automatically, which is generally a bad idea when
        # more than one widget is involved.
        hbox = QtGui.QHBoxLayout(self)
        hbox.addWidget(self.qteScroll)
        self.setLayout(hbox)


# Register the applet and create an instance thereof.
app_name = qteMain.qteRegisterApplet(DemoPDF)
app_obj = qteMain.qteNewApplet(app_name)
qteMain.qteMakeAppletActive(app_obj)

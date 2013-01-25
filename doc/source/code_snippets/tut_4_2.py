# Import the module with the global variables and the macro base class.
import qtmacs.qte_global as qte_global
from PyQt4 import QtCore, QtGui, QtWebKit
from qtmacs.base_applet import QtmacsApplet

# Get a reference to the main instance of Qtmacs.
qteMain = qte_global.qteMain


class Worker(QtCore.QObject):
    """
    Use blocking sleep-calls to periodically emit a signal.

    This thread uses blocking sleep-calls to simulate time consuming
    operations that will block the GUI when run in the main thread.
    """
    sigStartWork = QtCore.pyqtSignal()
    sigUpdate = QtCore.pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.sigStartWork.connect(self.work)

    # Explicitly mark the method as a Qt slot to ensure signals are
    # delivered correctly across threads.
    @QtCore.pyqtSlot()
    def work(self):
        """
        Use a blocking <sleep> call to periodically trigger a signal.
        """
        import time
        for val in range(200):
            time.sleep(0.1)
            self.sigUpdate.emit(val + 1)


class DemoThread(QtmacsApplet):
    """
    Demonstrate threading and a non-blocking GUI.
    """

    def __init__(self, appletID):
        # Initialise the base class.
        super().__init__(appletID)

        # Add a progress-bar element to the applet and register it with Qtmacs.
        self.qteProgBar = self.qteAddWidget(QtGui.QProgressBar(self))
        self.qteProgBar.setMinimum(0)
        self.qteProgBar.setMaximum(200)

        # Instantiate the worker object and connect the trigger signal to the
        # "setValue" slot of the progress bar.
        self.worker = Worker()
        self.worker.sigUpdate.connect(self.qteProgBar.setValue)

        # Create a Qt thread, move the worker into the thread, and
        # start the thread.
        self.thread = QtCore.QThread()
        self.worker.moveToThread(self.thread)
        self.thread.start()

        # Start the work in the worker thread.
        self.worker.sigStartWork.emit()


# Register the applet and create an instance thereof.
app_name = qteMain.qteRegisterApplet(DemoThread)
app_obj = qteMain.qteNewApplet(app_name)
qteMain.qteMakeAppletActive(app_obj)

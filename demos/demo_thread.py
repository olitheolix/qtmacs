# Copyright 2012, Oliver Nagy <qtmacsdev@gmail.com>
#
# This file is part of Qtmacs.
#
# Qtmacs is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Qtmacs is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Qtmacs. If not, see <http://www.gnu.org/licenses/>.

"""
A demo with ``QThreads``.

As with every applet, do not use::

    from demo_thread import DemoThread

"""

from PyQt4 import QtCore, QtGui, QtWebKit
from qtmacs.base_applet import QtmacsApplet


class Worker(QtCore.QObject):
    """
    Use blocking sleep-calls to periodically emit a signal.

    This thread uses blocking sleep-calls to simulate time consuming
    operations that will block the GUI when run in the main thread.
    """
    sig_start_work = QtCore.pyqtSignal()
    sig_update = QtCore.pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.sig_start_work.connect(self.work)

    # Explicitly mark the method as a Qt slot to ensure signals are
    # delivered correctly across threads.
    @QtCore.pyqtSlot()
    def work(self):
        """
        Use a blocking <sleep> call to periodically trigger a signal.
        """
        import time
        for val in range(100):
            time.sleep(0.1)
            self.sig_update.emit(val + 1)


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
        self.qteProgBar.setMaximum(100)

        # Instantiate the worker object and connect the trigger signal to the
        # "setValue" slot of the progress bar.
        self.worker = Worker()
        self.worker.sig_update.connect(self.qteProgBar.setValue)

        # Create a Qt thread, move the worker into the thread, and
        # start the thread.
        self.thread = QtCore.QThread()
        self.worker.moveToThread(self.thread)
        self.thread.start()

        # Start the work in the worker thread.
        self.worker.sig_start_work.emit()

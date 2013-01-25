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
Simple mini applet to display status messages.

It connects to the ``qteStatus`` signal and displays all messages dispatched
with ``qteStatus``. Furthermore, it connects to some signals from the event
filter to display partially completed key sequences and abort signals.

.. note: This is (one of the few) modules that Qtmacs automatically registers
   and instantiates at startup.

As with every applet, do **not** use::

    from qtmacs.applets.statusbar import StatusBar

"""

import qtmacs.base_applet
from PyQt4 import QtCore, QtGui


class StatusBar(qtmacs.base_applet.QtmacsApplet):
    """
    A simple status applet.

    It displays:

    1. status messages distributed via the ``qteStatus``,
    2. partially completed key sequences.

    |Args|

    * ``appletID`` (**str**): unique ID used by ``QtmacsMain``
      to distinguish applets.

    """
    def __init__(self, appletID):
        super().__init__(appletID)

        # Limit the height of the mini applet to avoid an ugly layout.
        height = self.fontMetrics().height()
        self.setMaximumHeight(2 * height)

        # Create a display label, put it into a layout to ensure that
        # it uses all the horizontal space available, and install it
        # as the applet layout.
        self.qteLabel = self.qteAddWidget(QtGui.QLabel(self))
        appLayout = QtGui.QHBoxLayout()
        appLayout.addWidget(self.qteLabel)
        self.setLayout(appLayout)

        # Intercept abort, invalid, partially complete, and fully
        # complete key sequences.
        self.qteMain.qtesigAbort.connect(self.clear)
        self.qteMain.qtesigKeyseqComplete.connect(self.clear)
        self.qteMain.qtesigKeyseqInvalid.connect(self.clear)
        self.qteMain.qtesigKeyseqPartial.connect(self.displayKeySlot)

        # Connect to the status message hook.
        self.qteMain.qteConnectHook('qteStatus', self.displayStatusMessage)

    def displayStatusMessage(self, msgObj):
        """
        Display the last status message and partially completed key sequences.

        |Args|

        * ``msgObj`` (**QtmacsMessage**): the data supplied by the hook.

        |Returns|

        * **None**

        |Raises|

        * **None**
        """

        # Ensure the message ends with a newline character.
        msg = msgObj.data
        if not msg.endswith('\n'):
            msg = msg + '\n'

        # Display the message in the status field.
        self.qteLabel.setText(msg)

    def displayKeySlot(self, msgObj):
        """
        Display the currently entered key sequence in the status bar.

        The ``data.data`` attribute is expected to be a
        ``QKeysequence`` instance.

        This method a slot for ``qtesigKeyseqPartial``.

        |Args|

        * ``data`` (**QtmacsMessage**): supplied by the signal.

        |Returns|

        * **None**

        |Raises|

        * **None**
        """
        self.qteLabel.setText(msgObj.data.toString())

    def clear(self, msgObj):
        self.qteLabel.setText('')

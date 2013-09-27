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
An applet with an interactive Bash.

This applet requires the `Bash` program and the ``QBash`` widget
(https://github.com/qtmacsdev/qbash). The former should be available on any
Unix-like system, whereas the latter must be either in the Python search path,
or copied to the `qtmacsroot/modules` directory. For instance, to get both
Qtmacs and QBash:

.. code-block:: bash

   git clone https://github.com/qtmacsdev/qtmacs qtmacsroot
   cd qtmacsroot/modules
   git clone https://github.com/qtmacsdev/qbash

As with every applet, do **not** use::

    from qtmacs.applets.bash import Bash

"""
import qbash.qbash
import qtmacs.auxiliary
import qtmacs.type_check
import qtmacs.qte_global as qte_global

from qtmacs.base_macro import QtmacsMacro
from qtmacs.base_applet import QtmacsApplet

#Shorthands:
type_check = qtmacs.type_check.type_check
QtmacsMessage = qtmacs.auxiliary.QtmacsMessage


class QtmacsBash(qbash.qbash.QBash):
    """
    Bash applet.

    This is basically the QBash applet with a few tweaks to run inside Qtmacs.
    """
    def shellTerminated(self):
        """
        Do nothing when the shell terminates.

        The original method would close the widget and/or terminate the program
        - this is unacceptable for an applet.
        """
        pass


class Bash(QtmacsApplet):
    """
    Demonstrate Bash applet.
    """
    def __init__(self, appletID):
        super().__init__(appletID)

        # Add the shell widget.
        self.qteBash = self.qteAddWidget(QtmacsBash(self), autoBind=False)

        # Register the SendCharacter macro. It will forward the keys
        # to the ``sendShell`` method of this class, which, in turn, will
        # forward it to QBash, which will convert it to an ASCII sequence and
        # before writing it to stdin of the Bash process.
        macroName = self.qteMain.qteRegisterMacro(SendCharacter)

        # Bind alphanumerical keys.
        for key in ('abcdefghijklmnopqrstuvwxyz'
                    'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
                    '[],=-.;/`&^~*@|#(){}$><%+?"_!'
                    "'\\"):
            self.qteMain.qteBindKeyWidget(key, macroName, self.qteBash)

        # Bind important not-alphanumerical keys.
        for key in ('<space>', '<colon>', '<return>', '<tab>',
                    '<backspace>', '<ctrl>+p', '<ctrl>+n', '<ctrl>+c',
                    '<ctrl>+b', '<ctrl>+f', '<ctrl>+d', '<ctrl>+o'):
            self.qteMain.qteBindKeyWidget(key, macroName, self.qteBash)

    def sendShell(self, keyEvent):
        """
        Send ``keyEvent`` to ``QBash``.

        The ``keyPressEvent`` method of ``QBash`` will converted ``keyEvent``
        into the correct ANSII code for the used terminal and send it to the
        Bash process.
        """
        self.qteBash.keyPressEvent(keyEvent)


class SendCharacter(QtmacsMacro):
    """
    Send the last typed character to Bash applet for processing.

    |Signature|

    * *applet*: 'Bash'
    * *widget*: '*'

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('Bash')
        self.qteSetWidgetSignature('*')

    def qteRun(self):
        # Extract the list of QKeyEvents that triggered this very
        # macro from the global variable ``last_key_sequence``. This
        # returns a list.
        keys = qte_global.last_key_sequence.toQKeyEventList()

        # The list should contain only one element for single keys but
        # to be sure pick only the last one. This will return a
        # Qt-native QKeyEvent object.
        self.qteApplet.sendShell(keys[-1])

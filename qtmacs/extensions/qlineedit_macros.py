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
Default macros and key bindings for ``QLineEdit``.

The ``qteAddWidget`` method of ``QtmacsApplet`` uses this file to
endow ``QLineEdit`` widgets with their default macros and
keybindings. The entry point to this module is the function
``install_macros_and_bindings``.

.. note: Macros are only registered if they do not yet exist. However,
   if a macro with the same name already does exists, then it is *not*
   replaced.

"""

import qtmacs.qte_global as qte_global

from PyQt4 import QtCore, QtGui
from qtmacs.base_macro import QtmacsMacro


# ------------------------------------------------------------
#                     Define all the macros
# ------------------------------------------------------------
class SelfInsert(QtmacsMacro):
    """
    Insert the last character from ``last_key_sequence`` defined in
    the globla name space.

    The ``last_key_sequence`` variable is overwritten/updated every
    time the event handler in Qtmacs receives a new keyboard event.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QLineEdit``

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QLineEdit')

    def qteRun(self):
        # Extract the last QKeyEvent from the keyboard sequence (there
        # should only be one anyway, but just to be sure). Then
        # extract the human readable text this key represents and
        # insert it into the QLineEdit or QTextEdit.
        keys = qte_global.last_key_sequence.toQKeyEventList()[-1]
        ch = keys.text()
        self.qteWidget.insert(ch)


class DelCharBackward(QtmacsMacro):
    """
    Delete character the left of the cursor.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QLineEdit``

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QLineEdit')

    def qteRun(self):
        self.qteWidget.backspace()


class ForwardChar(QtmacsMacro):
    """
    Mover cursor one character to the right.

    |Signature|

    * *applet*: '*'
    * *widget*: ``QLineEdit``

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QLineEdit')

    def qteRun(self):
        self.qteWidget.cursorForward(False, 1)


class BackwardChar(QtmacsMacro):
    """
    Move cursor one character to the left.
    |Signature|

    * *applet*: '*'
    * *widget*: ``QLineEdit``

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('QLineEdit')

    def qteRun(self):
        self.qteWidget.cursorBackward(False, 1)


# ------------------------------------------------------------
#                 Assign the default key bindings
# ------------------------------------------------------------

def install_macros_and_bindings(widgetObj):
    qteMain = qte_global.qteMain

    # ------------------------------------------------------------
    #  Install macros for alphanumeric characters. Note that all
    #  these characters are processed by the self-insert macro.
    # ------------------------------------------------------------

    # All alphanumerical characters are processed by the same macro,
    # namely 'self-insert'. Therefore, specify all alphanumerical
    # macros in a string and then install them in a loop. This is more
    # readable and flexibile than writing three dozen bind commands.
    char_list = "abcdefghijklmnopqrstuvwxyz"
    char_list += char_list.upper()
    char_list += "0123456789"
    char_list += "'\\[],=-.;/`&^~*!|#(){}$<>%+?_"

    # Register the macro if it is not already.
    if not qteMain.qteIsMacroRegistered('self-insert', widgetObj):
        qteMain.qteRegisterMacro(SelfInsert, True, 'self-insert')

    # Install the self-insert macro for every character in the char_list.
    for char in char_list:
        qteMain.qteBindKeyWidget(char, 'self-insert', widgetObj)

    # Install the self-insert macro for some additional keys that
    # cannot easily be added to char_list.
    qteMain.qteBindKeyWidget('"', 'self-insert', widgetObj)
    qteMain.qteBindKeyWidget('<space>', 'self-insert', widgetObj)
    qteMain.qteBindKeyWidget('<colon>', 'self-insert', widgetObj)
    qteMain.qteBindKeyWidget('<return>', 'self-insert', widgetObj)
    qteMain.qteBindKeyWidget('<enter>', 'self-insert', widgetObj)

    # ------------------------------------------------------------
    #   Install macros and keybindings for all other macros.
    # ------------------------------------------------------------

    # For readability purposes, compile a list where each entry
    # contains the macro name, macro class, and key binding associated
    # with this macro.
    macro_list = ((DelCharBackward, '<backspace>'),
                  (ForwardChar, '<ctrl>+f'),
                  (BackwardChar, '<ctrl>+b'),
                  )

    # Iterate over the list of macros and their keybinding and
    # register them if they are not already.
    for macroCls, keysequence in macro_list:
        # Get the macro name.
        macroName = qteMain.qteMacroNameMangling(macroCls)

        # Register the macro if it has not been already.
        if not qteMain.qteIsMacroRegistered(macroName, widgetObj):
            qteMain.qteRegisterMacro(macroCls, True, macroName)

        # Assign the macro a keyboard shortcut if one is available.
        if keysequence is not None:
            qteMain.qteBindKeyWidget(keysequence, macroName, widgetObj)

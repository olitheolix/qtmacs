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
All platform dependent initialisations go here.

The main entry point to this module is the ``setup`` function which
triggers all the necessary platform specific initialisations. The
results therefore are usually stored as global variables in the
``qtmacs.qte_global`` module.

.. note:: this file is incomplete and has only been tested on the
   author's computer. In particular, the modifier key map is probably
   different for Mac computer, and not all keys available on a
   standard US keyboard are currently defined.
"""

import qtmacs.qte_global as qte_global
from PyQt4 import QtCore

# Default keymap.
default_qt_keymap = {
    '0': (QtCore.Qt.NoModifier, QtCore.Qt.Key_0),
    '1': (QtCore.Qt.NoModifier, QtCore.Qt.Key_1),
    '2': (QtCore.Qt.NoModifier, QtCore.Qt.Key_2),
    '3': (QtCore.Qt.NoModifier, QtCore.Qt.Key_3),
    '4': (QtCore.Qt.NoModifier, QtCore.Qt.Key_4),
    '5': (QtCore.Qt.NoModifier, QtCore.Qt.Key_5),
    '6': (QtCore.Qt.NoModifier, QtCore.Qt.Key_6),
    '7': (QtCore.Qt.NoModifier, QtCore.Qt.Key_7),
    '8': (QtCore.Qt.NoModifier, QtCore.Qt.Key_8),
    '9': (QtCore.Qt.NoModifier, QtCore.Qt.Key_9),
    'a': (QtCore.Qt.NoModifier, QtCore.Qt.Key_A),
    'A': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_A),
    'b': (QtCore.Qt.NoModifier, QtCore.Qt.Key_B),
    'B': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_B),
    'c': (QtCore.Qt.NoModifier, QtCore.Qt.Key_C),
    'C': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_C),
    'd': (QtCore.Qt.NoModifier, QtCore.Qt.Key_D),
    'D': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_D),
    'e': (QtCore.Qt.NoModifier, QtCore.Qt.Key_E),
    'E': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_E),
    'f': (QtCore.Qt.NoModifier, QtCore.Qt.Key_F),
    'F': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_F),
    'g': (QtCore.Qt.NoModifier, QtCore.Qt.Key_G),
    'G': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_G),
    'h': (QtCore.Qt.NoModifier, QtCore.Qt.Key_H),
    'H': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_H),
    'i': (QtCore.Qt.NoModifier, QtCore.Qt.Key_I),
    'I': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_I),
    'j': (QtCore.Qt.NoModifier, QtCore.Qt.Key_J),
    'J': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_J),
    'k': (QtCore.Qt.NoModifier, QtCore.Qt.Key_K),
    'K': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_K),
    'l': (QtCore.Qt.NoModifier, QtCore.Qt.Key_L),
    'L': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_L),
    'm': (QtCore.Qt.NoModifier, QtCore.Qt.Key_M),
    'M': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_M),
    'n': (QtCore.Qt.NoModifier, QtCore.Qt.Key_N),
    'N': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_N),
    'o': (QtCore.Qt.NoModifier, QtCore.Qt.Key_O),
    'O': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_O),
    'p': (QtCore.Qt.NoModifier, QtCore.Qt.Key_P),
    'P': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_P),
    'q': (QtCore.Qt.NoModifier, QtCore.Qt.Key_Q),
    'Q': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_Q),
    'r': (QtCore.Qt.NoModifier, QtCore.Qt.Key_R),
    'R': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_R),
    's': (QtCore.Qt.NoModifier, QtCore.Qt.Key_S),
    'S': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_S),
    't': (QtCore.Qt.NoModifier, QtCore.Qt.Key_T),
    'T': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_T),
    'u': (QtCore.Qt.NoModifier, QtCore.Qt.Key_U),
    'U': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_U),
    'v': (QtCore.Qt.NoModifier, QtCore.Qt.Key_V),
    'V': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_V),
    'w': (QtCore.Qt.NoModifier, QtCore.Qt.Key_W),
    'W': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_W),
    'x': (QtCore.Qt.NoModifier, QtCore.Qt.Key_X),
    'X': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_X),
    'y': (QtCore.Qt.NoModifier, QtCore.Qt.Key_Y),
    'Y': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_Y),
    'z': (QtCore.Qt.NoModifier, QtCore.Qt.Key_Z),
    'Z': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_Z),
    '<RETURN>': (QtCore.Qt.NoModifier, QtCore.Qt.Key_Return),
    '<ENTER>': (QtCore.Qt.NoModifier, QtCore.Qt.Key_Enter),
    '<TAB>': (QtCore.Qt.NoModifier, QtCore.Qt.Key_Tab),
    "'": (QtCore.Qt.NoModifier, QtCore.Qt.Key_Apostrophe),
    '\\': (QtCore.Qt.NoModifier, QtCore.Qt.Key_Backslash),
    '[': (QtCore.Qt.NoModifier, QtCore.Qt.Key_BracketLeft),
    ']': (QtCore.Qt.NoModifier, QtCore.Qt.Key_BracketRight),
    ',': (QtCore.Qt.NoModifier, QtCore.Qt.Key_Comma),
    '=': (QtCore.Qt.NoModifier, QtCore.Qt.Key_Equal),
    '-': (QtCore.Qt.NoModifier, QtCore.Qt.Key_Minus),
    '.': (QtCore.Qt.NoModifier, QtCore.Qt.Key_Period),
    ';': (QtCore.Qt.NoModifier, QtCore.Qt.Key_Semicolon),
    '/': (QtCore.Qt.NoModifier, QtCore.Qt.Key_Slash),
    '<SPACE>': (QtCore.Qt.NoModifier, QtCore.Qt.Key_Space),
    '`': (QtCore.Qt.NoModifier, QtCore.Qt.Key_QuoteLeft),
    '&': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_Ampersand),
    '^': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_AsciiCircum),
    '~': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_AsciiTilde),
    '*': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_Asterisk),
    '@': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_At),
    '|': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_Bar),
    '#': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_NumberSign),
    '(': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_ParenLeft),
    ')': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_ParenRight),
    '{': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_BraceLeft),
    '}': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_BraceRight),
    '<COLON>': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_Colon),
    '$': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_Dollar),
    '>': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_Greater),
    '<': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_Less),
    '%': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_Percent),
    '+': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_Plus),
    '?': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_Question),
    '"': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_QuoteDbl),
    '_': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_Underscore),
    '!': (QtCore.Qt.ShiftModifier, QtCore.Qt.Key_Exclam),
    '<BACKSPACE>': (QtCore.Qt.NoModifier, QtCore.Qt.Key_Backspace),
    '<F1>': (QtCore.Qt.NoModifier, QtCore.Qt.Key_F1),
    '<F2>': (QtCore.Qt.NoModifier, QtCore.Qt.Key_F2),
    '<F3>': (QtCore.Qt.NoModifier, QtCore.Qt.Key_F3),
    '<F4>': (QtCore.Qt.NoModifier, QtCore.Qt.Key_F4),
    '<F5>': (QtCore.Qt.NoModifier, QtCore.Qt.Key_F5),
    '<F6>': (QtCore.Qt.NoModifier, QtCore.Qt.Key_F6),
    '<F7>': (QtCore.Qt.NoModifier, QtCore.Qt.Key_F7),
    '<F8>': (QtCore.Qt.NoModifier, QtCore.Qt.Key_F8),
    '<F9>': (QtCore.Qt.NoModifier, QtCore.Qt.Key_F9),
    '<F10>': (QtCore.Qt.NoModifier, QtCore.Qt.Key_F10),
    '<F11>': (QtCore.Qt.NoModifier, QtCore.Qt.Key_F11),
    '<F12>': (QtCore.Qt.NoModifier, QtCore.Qt.Key_F12),
}

default_qt_modifier_map = {
    '<NONE>': QtCore.Qt.NoModifier,
    '<ALT>': QtCore.Qt.AltModifier,
    '<CTRL>': QtCore.Qt.ControlModifier,
    '<META>': QtCore.Qt.MetaModifier
}


def determine_keymap(qteMain=None):
    """
    Return the conversion from keys and modifiers to Qt constants.

    This mapping depends on the used OS and keyboard layout.

    .. warning :: This method is currently only a dummy that always
       returns the same mapping from characters to keys. It works fine
       on my Linux and Windows 7 machine using English/US keyboard
       layouts, but other layouts will eventually have to be
       supported.
    """
    if qteMain is None:
        # This case should only happen for testing purposes.
        qte_global.Qt_key_map = default_qt_keymap
        qte_global.Qt_modifier_map = default_qt_modifier_map
    else:
        doc = 'Conversion table from local characters to Qt constants'
        qteMain.qteDefVar("Qt_key_map", default_qt_keymap, doc=doc)
        doc = 'Conversion table from local modifier keys to Qt constants'
        qteMain.qteDefVar("Qt_modifier_map", default_qt_modifier_map, doc=doc)


def setup(qteMain):
    """
    Coordinate the entire setup.
    """
    determine_keymap(qteMain)

if __name__ == "__main__":
    pass

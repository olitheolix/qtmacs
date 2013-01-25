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
A generally agreed upon module to store global variables.

This module should not import any modules itself, and always be
imported with::

    import qtmacs.qte_global as qte_global

Variables in this modules (ie. attributes) can be freely defined and
it is the responsibility of the developer to ensure unique names and
administrate them correctly. If a variable need not be global it
should go into a different module, eg. the applet module if it is
applet specific, or even an instance variable.

In addition to simply setting/retrieving variables, the ``QtmacsMain``
also provides ``qteDefVar`` to define a variable with associated
doc-string, and ``qteGetVar`` to retrieve both the variable and
doc-string.

.. warning:: Never use::

     from qtmacs.qte_global import *

   or similar, because this will only create a copy of the module in
   the name space of the calling object. Consequently, changes made to
   this objects will not be visible by other objects and vice versa.
"""

# Reference to the QtmacsMain instance.
qteMain = None

# Default key-bindings for arbitrary Qt widgets. The key-value denotes
# the actual widget, eg. QTextEdit, and the value points to the module
# that loads the macros and assigns the key bindings. Note that the
# modules must all be in the load path.
default_widget_keybindings = {
    'QLineEdit': 'qtmacs.extensions.qlineedit_macros',
    'QTextEdit': 'qtmacs.extensions.qtmacstextedit_macros',
    'QtmacsTextEdit': 'qtmacs.extensions.qtmacstextedit_macros',
    'QtmacsScintilla': 'qtmacs.extensions.qtmacsscintilla_macros',
}

# A list of tuples that associate file types with applets. The first
# element in the tuple must be a valid regular expression, whereas
# the second element must denote a valid applet name, ie. an applet
# that has been registered with ``qteRegisterApplet``. An example
# entry that associates all files that end with `.txt` with the
# ``RichEditor`` applet would be:
#
#   findFile_types = [('.*\.txt$','RichEditor')]
#
# Note that Qtmacs does not automatically register the applet. The
# above association will do nothing if no applet with name `TextEdit`
# has been registered with ``qteRegisterApplet`` beforehand. It is
# usually a good idea to update this list in the
# ``__qteRegisterAppletInit__`` method so that the ``find-file`` macro
# can create this applet if it encounters a supported file type.
findFile_types = [('.*\.txt$', 'RichEditor')]

# If the file name does not match any pattern in ``findFile_types``
# (see above), then use this applet as the fallback option.
findFile_default = 'SciEditor'

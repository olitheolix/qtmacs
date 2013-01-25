Qtmacs Package
**************

.. code-block:: text

    Copyright 2012-2013, Oliver Nagy.
    
    Qtmacs is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    
    Qtmacs is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.
    
    You should have received a copy of the GNU General Public License
    along with Qtmacs. If not, see <http://www.gnu.org/licenses/>.

Core Distribution
=================

auxiliary.py
------------
.. automodule:: qtmacs.auxiliary
   :members:
   :show-inheritance:

base_applet.py
--------------
.. automodule:: qtmacs.base_applet
   :members:
   :show-inheritance:

base_macro.py
-------------
.. automodule:: qtmacs.base_macro
   :members:

exceptions.py
-------------
.. automodule:: qtmacs.exceptions
   :members:

kill_list.py
-------------
.. automodule:: qtmacs.kill_list
   :members:

logging_handler.py
------------------
.. automodule:: qtmacs.logging_handler
   :members:

platform_setup.py
-----------------
.. automodule:: qtmacs.platform_setup
   :members:

qte_global.py
-------------
.. automodule:: qtmacs.qte_global
   :members:

qtmacsmain.py
-------------
.. automodule:: qtmacs.qtmacsmain
   :members:

qtmacsmain_macros.py
--------------------
.. automodule:: qtmacs.qtmacsmain_macros
   :members:

type_check.py
-------------
.. automodule:: qtmacs.type_check
   :members:

undo_stack.py
-------------
.. automodule:: qtmacs.undo_stack
   :members:

Applets
=======
These are the default applets included in the latest Qtmacs distribution.
They are located in the `qtmacs/applets` directory.

bash.py
------------
.. automodule:: qtmacs.applets.bash
   :members:

log_viewer.py
-------------
.. automodule:: qtmacs.applets.logviewer
   :members:

richeditor.py
-------------
.. automodule:: qtmacs.applets.richeditor
   :members:

scieditor.py
------------
.. automodule:: qtmacs.applets.scieditor
   :members:

statusbar.py
------------
.. automodule:: qtmacs.applets.statusbar
   :members:

Mini Applets
============

Base Query
----------
.. automodule:: qtmacs.miniapplets.base_query
   :members:

File Query
----------
.. automodule:: qtmacs.miniapplets.file_query
   :members:

Widgets and Macros
==================

.. |QtmacsTextEdit| replace:: :py:mod:`~qtmacs.extensions.qtmacstextedit_widget.QtmacsTextEdit`
.. |QtmacsScintilla| replace:: :py:mod:`~qtmacs.extensions.qtmacsscintilla_widget.QtmacsScintilla`
.. _QTextEdit: http://qt-project.org/doc/qt-4.8/QTextEdit.html

While applets may use any widget from the Qt library, some widgets have
been specifically tailored to Qtmacs, like |QtmacsTextEdit| and
|QtmacsScintilla|. In essence, these are drop-in replacements for
`QTextEdit`_ and `QsciScintilla
<http://www.riverbankcomputing.co.uk/static/Docs/QScintilla2/index.html>`_,
respectively, but with an improved undo framework and other minor tweaks.

By convention (not enforced by Qtmacs), for every widget ``foo`` there
is at least a ``foo_macros.py`` file which contains the default macros
for ``foo``.If foo is not a default widget from the Qt library then
``foo_widget`` contains the class definition of ``foo``.

qlineedit_macros.py
-------------------
.. automodule:: qtmacs.extensions.qlineedit_macros
   :members:

qtmacsscintilla_macros.py
-------------------------
.. automodule:: qtmacs.extensions.qtmacsscintilla_macros
   :members:

qtmacsscintilla_widget.py
-------------------------
.. automodule:: qtmacs.extensions.qtmacsscintilla_widget
   :members:

qtmacstextedit_macros.py
------------------------
.. automodule:: qtmacs.extensions.qtmacstextedit_macros
   :members:

qtmacstextedit_widget.py
------------------------
.. automodule:: qtmacs.extensions.qtmacstextedit_widget
   :members:

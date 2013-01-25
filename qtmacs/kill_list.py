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
Provide ``QtmacsKillList`` to encapsulates the actual kill-list, and
``KillListElement`` to represent each killed element.

At startup, Qtmacs will automatically create one instance of
``QtmacsKillList`` and places it into the global variable
``qte_global.kill_list``. There is probably no need to create another
instance of ``QtmacsKillList`` ever again unless an applet wishes to
implement a local kill-list based on the same classes.

The ``KillListElement`` container takes three arguments: a plain
string, an arbitrary object, and another plain string. The first
argument represents the killed element in text form, the second in an
arbitrary format (eg. Html or a binary image), and the third
specifies the format of the second. This specification string is
completely arbitrary and if a macro cannot interpret it, then it
should use the plain text version as a fallback option.

The idea behind this system is to facilitate text copying between
eg. a ``QtmacsTextEdit`` (which is a Html based rich text editor that
may contain images, tables, etc.) and plain text widgets like
``QLineEdit`` or ``QScintilla``, which are incapable to display the
\"rich\" elements, but can handle the text.

Usage example inside a macro/applet::

    import qtmacs.kill_list as kill_list
    import qtmacs.qte_global as qte_global

    # Create an instance of KillListElement to hold the killed element.
    # Provide a plain text version and a custom version (Html in this
    # case).
    el = kill_list.KillListElement('some bold text',
                                   'some <b>bold</b> text',
                                   'html')

    # Add the element to the kill-list.
    qte_global.kill_list.append(el)

"""

# Import the type check decorator and make it available via a shortcut.
import qtmacs.type_check
type_check = qtmacs.type_check.type_check


class KillListElement(object):
    """
    Container class for every element in the kill-list.

    |Args|

    * ``data_text`` (**str**): the killed element as a pure string (ie.
      without any embedded data like images)
    * ``data_custom`` (*): the killed element in an arbitrary format
      native to the applet.
    * ``data_type`` (**str**): type description of ``data_custom``.

    """
    @type_check
    def __init__(self, data_text: str=None, data_custom: str=None,
                 data_type: str=None):
        super().__init__()
        self._data_text = data_text
        self._data_custom = data_custom
        self._data_type = data_type

    def setDataText(self, data_text: str):
        """
        Change the content of the plain text data.

        |Args|

        * ``data_text`` (**str**): the killed text as a pure string (ie.
          without any embedded data like images)

        |Returns|

        * **None**

        |Raises|

        * **None**
        """
        self._data_text = data_text

    def setDataCustom(self, data_custom: str):
        """
        Change the content of the custom typed text.

        |Args|

        * ``data_custom`` (**any**): the killed element in an arbitrary format
          native to the applet.

        |Returns|

        * **None**

        |Raises|

        * **None**
        """
        self._data_custom = data_custom

    def setDataType(self, data_type: str):
        """
        Change the data type.

        The data type is an arbitrary string set by the killing
        macro to describe the custom data set. If the another
        macro can interpret this string then it can use the
        custom data, otherwise it should use the plain text data.

        |Args|

        * ``data_type`` (**str**): type description of ``data_custom``.

        |Returns|

        * **None**

        |Raises|

        * **None**
        """
        self._data_type = data_type

    def dataText(self):
        """
        Retrieve the data in plain text.

        |Args|

        * **None**

        |Returns|

        * **None**

        |Raises|

        * **str**: the killed text as pure string.
        """
        return self._data_text

    def dataCustom(self):
        """
        Retrieve the data in custom format.

        |Args|

        * **None**

        |Returns|

        * **None**

        |Raises|

        * **str**: the killed text as in a custom format (eg. Html).
        """
        return self._data_custom

    def dataType(self):
        """
        Retrieve the type of the custom data.

        |Args|

        * **None**

        |Returns|

        * **None**

        |Raises|

        * **str**: the type of the custom text.
        """
        return self._data_type


class QtmacsKillList(object):
    """
    Hold the kill-list and provide access to it.

    The kill list implements the iterator protocol and can thus
    be indexed and sliced.

    |Args|

    * **None**
    """
    def __init__(self):
        super().__init__()
        self._kill_list = []

    def __getitem__(self, key: (int, slice)):
        return self._kill_list[key]

    def __len__(self):
        return len(self._kill_list)

    def __next__(self):
        if self._iterIdx >= len(self):
            raise StopIteration
        else:
            self._iterIdx += 1
            return self._kill_list[self._iterIdx - 1]

    def __iter__(self):
        self._iterIdx = 0
        return self

    @type_check
    def append(self, data: KillListElement):
        """
        Append another element to the kill list.

        |Args|

        * ``data`` (**KillListElement**): the killed element.

        |Returns|

        * **None**

        |Raises|

        * **None**
        """
        self._kill_list.append(data)

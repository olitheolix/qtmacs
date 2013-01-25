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
An empty applet.

As with every applet, do not use::

    from demo_empty import DemoEmpty

"""

from PyQt4 import QtCore, QtGui, QtWebKit
from qtmacs.base_applet import QtmacsApplet


class DemoEmpty(QtmacsApplet):
    """
    An empty applet.
    """
    def __init__(self, appletID):
        # Initialise the base class.
        super().__init__(appletID)

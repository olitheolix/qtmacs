#!/usr/bin/python3
"""
Check requirements and start Qtmacs.
"""

import os
import sys
import argparse

try:
    import sip
    from PyQt4 import QtCore, QtGui
    _PyQtVersion = QtCore.PYQT_VERSION_STR
except ImportError:
    print('PyQt4 not found.')
    sys.exit(1)

try:
    from PyQt4 import Qsci
except ImportError:
    print('PyQt4 was installed without the Qsci module.\n'
          'Please consult the PyQt4 documentation on how\n'
          'to install it. On Debian/Linux based systems\n'
          'you can usually install it with\n'
          '  >> sudo apt-get install python3-pyqt4.Qsci')
    sys.exit(1)


sys.path.insert(0, '../')
import qtmacs.qtmacsmain
import qtmacs.type_check
from qtmacs.exceptions import *

# Shorthands
type_check = qtmacs.type_check.type_check

"""
Main program
"""


def versionCheck():
    import platform

    # Get Python version.
    pyver = platform.python_version()
    try:
        major = int(pyver[0])
    except ValueError:
        print('Unable to determine Python version.')
        sys.exit(1)

    # Running Python3?
    if major != 3:
        print('Qtmacs requires Python 3.x')
        sys.exit(1)

    # Get PyQt version.
    qtver = _PyQtVersion.split('.')
    try:
        major = int(qtver[0])
        minor = int(qtver[1])
    except ValueError:
        print('Unable to determine PyQt4 version.')
        sys.exit(1)

    # Running PyQt 4.8 or higher?
    if not ((major == 4) and (minor >= 8)):
        print('PyQt4 must be version 4.8 or newer')
        sys.exit(1)


def keysequence_test():
    import qtmacs.platform_setup
    import qtmacs.auxiliary
    QtmacsKeysequence = qtmacs.auxiliary.QtmacsKeysequence

    # Install the keymap and modifier to use for the test bench.
    qtmacs.platform_setup.determine_keymap()

    # Test the QtmacsKeysequence class by letting it parse and convert
    # elaborate key sequences.
    test_sequences = [
        ' <ctrl>+f <ctrl>++ <ctrl>+<space> <ctrl>+< <ctrl>+> < > <space>  ',
        '<ctrl>+f <ctrl>+<alt>++ <ctrl>+<alt>+<space>',
        '<ctrl>+f h <alt>+K <ctrl>+k',
        [(QtCore.Qt.ControlModifier, QtCore.Qt.Key_H),
         (QtCore.Qt.NoModifier, QtCore.Qt.Key_K)]]

    for seq in test_sequences:
        print('Input         : {}'.format(seq))
        tmp = QtmacsKeysequence(seq)
        print('Converted (HR): {}'.format(tmp.toString()))
        print('Converted (Qt): {}\n'.format(tmp.toQtKeylist()))


def type_check_test():
    @type_check
    def testfun(x, y: str='str_y', widObj: (list, int)=None):
        """
        A function to test the type_check decorator.
        """
        pass

    try:
        testfun(5)
        print('Pass')
    except QtmacsArgumentError:
        print('Fail')

    try:
        testfun(5, y='Hi')
        print('Pass')
    except QtmacsArgumentError:
        print('Fail')

    try:
        testfun(5, widObj=['Hi'])
        print('Pass')
    except QtmacsArgumentError:
        print('Fail')

    try:
        testfun(5, y=5)
        print('Fail')
    except QtmacsArgumentError:
        print('Pass')

    try:
        testfun(5, widObj=5.)
        print('Fail')
    except QtmacsArgumentError:
        print('Pass')

    try:
        testfun(5, 5)
        print('Fail')
    except QtmacsArgumentError:
        print('Pass')

    try:
        testfun(5, 'str_y', 5.)
        print('Fail')
    except QtmacsArgumentError:
        print('Pass')

    @type_check
    def testfun(newAppObj: int=0, splitHoriz=True,
                windowObj: list=None):
        """
        A function to test the type_check decorator.
        """
        pass

    try:
        testfun(7)
        print('Pass')
    except QtmacsArgumentError:
        print('Fail')

    @type_check
    def testfun(appletID: str):
        """
        A function to test the type_check decorator.
        """
        pass

    try:
        testfun('blah')
        print('Pass')
    except QtmacsArgumentError:
        print('Fail')

    @type_check
    def testfun(test: (str, int)):
        pass

    try:
        testfun(False)
        print('Fail')
    except QtmacsArgumentError:
        print('Pass')


if __name__ == '__main__':
    # Ensure we are running at least Python 3.x and Qt 4.8.
    versionCheck()

    # Parse the command line options.
    parser = argparse.ArgumentParser(
        description='Start Qtmacs. Per default, no arguments are required')
    parser.add_argument('--load', metavar='file',
                        help='import a Python module on startup')
    parser.add_argument('--logconsole', action='store_true',
                        help='write all log messages to the console '
                             'in addition to the internal message applet')
    args = parser.parse_args()

    # Create the Qt application and the one-and-only QtmacsMain instance.
    QtApplicationInstance = QtGui.QApplication(sys.argv)
    qtmacsMain = qtmacs.qtmacsmain.QtmacsMain(
        importFile=args.load,
        logConsole=args.logconsole)
    sys.exit(QtApplicationInstance.exec_())

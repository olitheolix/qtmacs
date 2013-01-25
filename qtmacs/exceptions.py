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
Provide Qtmacs specific exception classes.

It is safe to use::

    from exceptions import *
"""

import re


class QtmacsArgumentError(Exception):
    """
    A variable has incorrect type (eg. 'int' when a 'str' was
    expected).

    |Args|

    * ``varName`` (**str**): name of variable.
    * ``methodName`` (**str**): name of method where the error was raised.
    * ``typeExpected`` (**type**): the expected type of the variable.
    * ``typePassed`` (**type**): the actually passed type of the variable.

    """
    def __init__(self, varName, methodName, typeExpected, typePassed):
        # Backup the variables in case the exception clause wants to
        # inspect them.
        self.varName = varName
        self.typeExpected = typeExpected
        self.typePassed = typePassed
        self.methodName = methodName

        # Convert the ``typeExpected`` argument to a tuple, if it is
        # not already a tuple or list.
        if type(typeExpected) not in (tuple, list):
            typeExpected = typeExpected,

        # Format the admissible types from the Python internal format
        # to a bold Html version, eg. from "<type 'bool'>" to
        # "<b>bool</b>". This is purely for formatting the log-message.
        typeExpForm = []
        for _ in typeExpected:
            varTypeStr = str(_)
            r = re.search("'.*'", varTypeStr)
            if r.start() is not None:
                msg = '<b>' + varTypeStr[r.start() + 1:r.end() - 1] + '</b>'
                typeExpForm.append(msg)
            else:
                typeExpForm.append('<b>???</b>')

        # Do the same for the type of the passed argument.
        varTypeStr = str(typePassed)
        r = re.search("'.*'", varTypeStr)
        if r.start() is not None:
            msg = '<b>' + varTypeStr[r.start() + 1:r.end() - 1] + '</b>'
            typePassForm = msg
        else:
            typePassForm = '<b>???</b>'

        # Format the error message in singular or plural, depending on whether
        # only one or more types are admissible.
        if len(typeExpected) > 1:
            self.msg = ('Argument <b>{}</b> of <b>{}</b> must have one of the'
                        'types {}, but was of type {}.')
            self.msg = self.msg.format(varName, methodName, typeExpForm,
                                       typePassForm)
        else:
            self.msg = ('Argument <b>{}</b> of <b>{}</b> must be of type {},'
                        'but was of type {}.'.format(
                            varName, methodName, typeExpForm[0], typePassForm))

        # Call the original constructor with the formatted message.
        super().__init__(self.msg)

    def __repr__(self):
        return self.msg

    def __str__(self):
        return self.msg


class QtmacsKeysequenceError(Exception):
    """
    The provided key sequence could not be parsed.

    This exception is usually only raised by instances of
    ``QtmacsKeysequence`` and usually means that the provided key
    sequence is invalid, eg. '<ctrlxx>+x' instead of '<ctrl>+x', or
    the more subtle '<ctrl>-x' instead of '<ctrl>+x'.
    """
    def __init__(self, msg):
        self.msg = msg
        super().__init__(self.msg)

    def __repr__(self):
        return self.msg


class QtmacsOtherError(Exception):
    """
    Generic exception when no specialised one is available.
    """
    pass

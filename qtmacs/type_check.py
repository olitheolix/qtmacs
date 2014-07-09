# Copyright 2012, Oliver Nagy <olitheolix@gmail.com>
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
Provide a decorator to automatically type check arguments based on
the annotations in the function signature.

It is *not* safe to use::

    from type_check import *

Usage example::

    import qtmacs.type_check
    type_check = qtmacs.type_check.type_check

    @type_check
    def foo(a, b:str, c:int =0, d:(int, str)=None):
        pass

"""
import inspect
import functools
from qtmacs.exceptions import *


def type_check(func_handle):
    """
    Ensure arguments have the type specified in the annotation signature.

    Example::

        def foo(a, b:str, c:int =0, d:(int, list)=None):
            pass

    This function accepts an arbitrary parameter for ``a``, a string
    for ``b``, an integer for ``c`` which defaults to 0, and either
    an integer or a list for ``d`` and defaults to ``None``.

    The decorator does not check return types and considers derived
    classes as valid (ie. the type check uses the Python native
    ``isinstance`` to do its job). For instance, if the function is
    defined as::

        @type_check
        def foo(a: QtGui.QWidget):
            pass

    then the following two calls will both succeed::

        foo(QtGui.QWidget())
        foo(QtGui.QTextEdit())

    because ``QTextEdit`` inherits ``QWidget``.

    .. note:: the check is skipped if the value (either passed or by
              default) is **None**.

    |Raises|

    * **QtmacsArgumentError** if at least one argument has an invalid type.
    """
    def checkType(var_name, var_val, annot):
        # Retrieve the annotation for this variable and determine
        # if the type of that variable matches with the annotation.
        # This annotation is stored in the dictionary ``annot``
        # but contains only variables for such an annotation exists,
        # hence the if/else branch.
        if var_name in annot:
            # Fetch the type-annotation of the variable.
            var_anno = annot[var_name]

            # Skip the type check if the variable is none, otherwise
            # check if it is a derived class. The only exception from
            # the latter rule are binary values, because in Python
            #
            # >> isinstance(False, int)
            # True
            #
            # and warrants a special check.
            if var_val is None:
                type_ok = True
            elif (type(var_val) is bool):
                type_ok = (type(var_val) in var_anno)
            else:
                type_ok = True in [isinstance(var_val, _) for _ in var_anno]
        else:
            # Variable without annotation are compatible by assumption.
            var_anno = 'Unspecified'
            type_ok = True

        # If the check failed then raise a QtmacsArgumentError.
        if not type_ok:
            args = (var_name, func_handle.__name__, var_anno, type(var_val))
            raise QtmacsArgumentError(*args)

    @functools.wraps(func_handle)
    def wrapper(*args, **kwds):
        # Retrieve information about all arguments passed to the function,
        # as well as their annotations in the function signature.
        argspec = inspect.getfullargspec(func_handle)

        # Convert all variable annotations that were not specified as a
        # tuple or list into one, eg. str --> will become (str,)
        annot = {}
        for key, val in argspec.annotations.items():
            if isinstance(val, tuple) or isinstance(val, list):
                annot[key] = val
            else:
                annot[key] = val,       # Note the trailing colon!

        # Prefix the argspec.defaults tuple with **None** elements to make
        # its length equal to the number of variables (for sanity in the
        # code below). Since **None** types are always ignored by this
        # decorator this change is neutral.
        if argspec.defaults is None:
            defaults = tuple([None] * len(argspec.args))
        else:
            num_none = len(argspec.args) - len(argspec.defaults)
            defaults = tuple([None] * num_none) + argspec.defaults

        # Shorthand for the number of unnamed arguments.
        ofs = len(args)

        # Process the unnamed arguments. These are always the first ``ofs``
        # elements in argspec.args.
        for idx, var_name in enumerate(argspec.args[:ofs]):
            # Look up the value in the ``args`` variable.
            var_val = args[idx]
            checkType(var_name, var_val, annot)

        # Process the named- and default arguments.
        for idx, var_name in enumerate(argspec.args[ofs:]):
            # Extract the argument value. If it was passed to the
            # function as a named (ie. keyword) argument then extract
            # it from ``kwds``, otherwise look it up in the tuple with
            # the default values.
            if var_name in kwds:
                var_val = kwds[var_name]
            else:
                var_val = defaults[idx + ofs]
            checkType(var_name, var_val, annot)
        return func_handle(*args, **kwds)
    return wrapper

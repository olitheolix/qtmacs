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
Provide ``QtmacsMacro``, the base class for all Qtmacs macros.

To implement a macro, subclass ``QtmacsMacro``, specify the applet-
and signatures it is compatible with in the constructor, and overload
the (by default empty) ``qteRun`` method.

Usage example::

    class DemoMacroLineEdit(QtmacsMacro):
        \"\"\"
        Display hello world in the status applet of Qtmacs.

        |Signature|

        * *applet*: '*'
        * *widget*: '*'
        \"\"\"
        def __init__(self):
            super().__init__()
            self.qteSetAppletSignature('*')
            self.qteSetWidgetSignature('*')

        def qteRun(self):
            self.qteMain.qteStatus('Hello world')


Noteworthy facts about macros:

* Macros are instantiated as soon as they are registered, and will not
  be re-instantiated ever again (ie. all instance variables defined
  during runtime will remain there for as long as Qtmacs is running).
* Every macro calls has at most one instance.

Macros always carry the following attributes:

* ``qteMain``: reference to ``QtmacsMain`` instance,
* ``qteLogger``: reference to the Qtmacs logging mechanism,
* ``qteVersionInformation``: instance of ``QtmacsVersionStructure``,
* ``self.qteApplet``: reference to the active applet,
* ``self.qteWidget``: reference to the active widget.

The first three attributes are fixed for entire life of the macro, the
last two attributes are automatically updated before the ``qteRun``
method is called and always point to the applet and widget that were
active when the macro shortcut was triggered (or the macro was queried
via the mini applet). As such, ``qteApplet`` is never **None**,
whereas ``qteWidget`` can be (eg. an empty applet).

It is safe to use::

    from macro import QtmacsMacro
"""

import inspect
import qtmacs.auxiliary
import qtmacs.type_check
import qtmacs.qte_global as qte_global

from PyQt4 import QtCore, QtGui
from qtmacs.exceptions import *

# Shorthands
type_check = qtmacs.type_check.type_check
QtmacsKeymap = qtmacs.auxiliary.QtmacsKeymap
QtmacsMessage = qtmacs.auxiliary.QtmacsMessage
QtmacsKeysequence = qtmacs.auxiliary.QtmacsKeysequence
QtmacsVersionStructure = qtmacs.auxiliary.QtmacsVersionStructure


class QtmacsMacro(QtCore.QObject):
    """
    Macros for ``Qtmacs`` must inherit from this class.

    To write a custom macro, set the applet- and widget signature
    compatibilities, and overload the ``qteRun`` method.

    Every macro has the following five attributes available to them at
    run time:

    * ``qteMain``: reference to QtmacsMain instance (comes straight
      from the global variables).
    * ``qteLogger``: the Qtmacs wide logger (see ``logger`` module
      in Python standard library).
    * ``self.qteApplet``: reference to the calling applet.
    * ``self.qteWidget``: reference to the calling widget.
    * ``self.qteVersionInformation``: version information.

    The first attibute is a reference to the one and only
    ``QtmacsMain`` instance and the the second attribute to its
    logging mechanism (a logger from the ``logger`` module in the
    standard Python library). The ``qteApplet`` and ``qteWidget``
    attributes are updated before the ``qteRun`` method is triggered
    and therefore always current inside the ``qteRun`` method. The
    last attribute contains general information not used by Qtmacs
    directly.

    A minimalist example that works for all applets and widgets would
    be the following (put this in your configuration file)::

        class SampleMacro(QtmacsMacro):
            \"\"\"
            Display a status message.
            \"\"\"
            def __init__(self):
                super().__init__()

                # This macro works for all applet- and widget signatures.
                self.qteSetAppletSignature('*')
                self.qteSetWidgetSignature('*')

            def qteRun(self):
                \"\"\"
                Overload the virtual qteRun method with our desired
                functionality.
                \"\"\"
                msg = ('This is the <b>{}</b> macro speaking'
                       .format(self.macroName))
                self.qteMain.qteStatus(msg)

        # Register the macro with Qtmacs.
        qteRegisterMacro(SampleMacro)


    |Args|

    * **None**

    |Signals|

    * ``qtesigMacroError``: a macro triggered an exception it did not handle.

      - ``macroName`` (**str**): name of macro.
      - ``widgetObj`` (**QWidget**): target of macro (ie. the value of
        ``qteWidget`` when its ``qteRun`` method was called).

    * ``qtesigMacroStart``: a macro is about to be executed.

      - ``macroName`` (**str**): name of macro.
      - ``widgetObj`` (**QWidget**): target of macro (ie. the value of
        ``qteWidget`` when its ``qteRun`` method was called).

    * ``qtesigMacroFinished``: a macro finished without raising an
      un-handled error.

      - ``macroName`` (**str**): name of macro.
      - ``widgetObj`` (**QWidget**): target of macro (ie. the value of
        ``qteWidget`` when its ``qteRun`` method was called).

    """
    def __init__(self):
        super().__init__()

        # Reference to QtmacsMain instance and its logger.
        self.qteMain = qte_global.qteMain
        self.qteLogger = self.qteMain.qteLogger

        # Version information for this applet.
        self.qteVersionInformation = QtmacsVersionStructure()

        # Macro name as a string (will be set by qteRegisterMacro)
        self._qteMacroName = None

        # These two variables are set by ``_qteRunQueuedMacro`` and
        # specify the applet and widget respectively, that were active
        # when the macro was activated. Note that ``qteApplet``
        # cannot be **None** whereas ``qteWidget`` can.
        self.qteApplet = None
        self.qteWidget = None

        # List of applet- and widget signature that are compatible
        # with this macro. An empty list implies that it is
        # compatible with all applets and widgets. This is typically
        # the case for macros that do not operate directly on applets,
        # eg. ``otherApplet``. It is the macro programmer's
        # responsibility to set this variable appropriately.
        self._qteAppletSignatures = []
        self._qteWidgetSignatures = []

    def qteMacroName(self):
        """
        Return applet the macro name as a string.

        |Args|

        * **None**

        |Returns|

        * **str**: macro name.

        |Raises|

        * **None**
        """
        return self._qteMacroName

    @type_check
    def qteSaveMacroData(self, data, widgetObj: QtGui.QWidget=None):
        """
        Associate arbitrary ``data`` with ``widgetObj``.

        This is a convenience method to easily store applet/widget
        specific information in between calls.

        If ``widgetObj`` is **None** then the calling widget
        ``self.qteWidget`` will be used.

        Note that this function overwrites any previously saved data.

        |Args|

        * ``data`` (**object**): arbitrary python object to save.
        * ``widgetObj`` (**QWidget**): the widget/applet with which
          the data should be associated.

        |Returns|

        * **None**

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        * **QtmacsOtherError** if ``widgetObj`` was not added with
          ``qteAddWidget`` method.
        """

        # Check type of input arguments.
        if not hasattr(widgetObj, '_qteAdmin') and (widgetObj is not None):
            msg = '<widgetObj> was probably not added with <qteAddWidget>'
            msg += ' method because it lacks the <_qteAdmin> attribute.'
            raise QtmacsOtherError(msg)

        # If no widget was specified then use the calling widget.
        if not widgetObj:
            widgetObj = self.qteWidget

        # Store the supplied data in the applet specific macro storage.
        widgetObj._qteAdmin.macroData[self.qteMacroName()] = data

    @type_check
    def qteMacroData(self, widgetObj: QtGui.QWidget=None):
        """
        Retrieve ``widgetObj`` specific data previously saved with
        ``qteSaveMacroData``.

        If no data has been stored previously then **None** is
        returned.

        If ``widgetObj`` is **None** then the calling widget
        ``self.qteWidget`` will be used.

        |Args|

        * ``widgetObj`` (**QWidget**): the widget/applet with which
          the data should be associated.

        |Returns|

        * **object**: the previously stored data.

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        * **QtmacsOtherError** if ``widgetObj`` was not added with
          ``qteAddWidget`` method.

        """

        # Check type of input arguments.
        if not hasattr(widgetObj, '_qteAdmin') and (widgetObj is not None):
            msg = '<widgetObj> was probably not added with <qteAddWidget>'
            msg += ' method because it lacks the <_qteAdmin> attribute.'
            raise QtmacsOtherError(msg)

        # If no widget was specified then use the calling widget.
        if not widgetObj:
            widgetObj = self.qteWidget

        # Retrieve the data structure.
        try:
            _ = widgetObj._qteAdmin.macroData[self.qteMacroName()]
        except KeyError:
            # If the entry does not exist then this is a bug; create
            # an empty entry for next time.
            widgetObj._qteAdmin.macroData[self.qteMacroName()] = None

        # Return the data.
        return widgetObj._qteAdmin.macroData[self.qteMacroName()]

    def qteAppletSignature(self):
        """
        Return a copy of the applet signatures with which this macro
        is compatible.

        |Args|

        * **None**

        |Returns|

        * **tuple of str**

        |Raises|

        * **None**
        """
        return tuple(self._qteAppletSignatures)

    def qteWidgetSignature(self):
        """
        Return a copy of the widget signatures with which this macro
        is compatible.

        |Args|

        * **None**

        |Returns|

        * **tuple of str**
        """
        return tuple(self._qteWidgetSignatures)

    @type_check
    def qteSetAppletSignature(self, appletSignatures: (str, tuple, list)):
        """
        Specify the applet signatures with which this macro is compatible.

        Qtmacs uses this information at run time to determine if this
        macro is compatible with a particular applet, as specified by
        the applet's signature. Note that this function overwrites
        all previously set values.

        |Args|

        * ``*appletSignatures`` (**str, tuple, list**): applet signatures
          as a string, or tuple/list of strings.

        |Returns|

        * **None**

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        # Convert the argument to a tuple if it is not already a tuple
        # or list.
        if not isinstance(appletSignatures, (tuple, list)):
            appletSignatures = appletSignatures,

        # Ensure that all arguments in the tuple/list are strings.
        for idx, val in enumerate(appletSignatures):
            if not isinstance(val, str):
                args = ('appletSignatures', 'str', inspect.stack()[0][3])
                raise QtmacsArgumentError(*args)

        # Store the compatible applet signatures as a tuple (of strings).
        self._qteAppletSignatures = tuple(appletSignatures)

    @type_check
    def qteSetWidgetSignature(self, widgetSignatures: (str, tuple, list)):
        """
        Specify the widget signatures with which this macro is
        compatible.

        Qtmacs uses this information at run time to determine if this
        macro is compatible with a particular widget, as specified by
        the widget's signature. Note that this function overwrites all
        previously set values.

        |Args|

        * ``*widgetSignatures`` (**str, tuple, list**): widget signatures
          as a string, or tuple/list of strings.

        |Returns|

        * **None**

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """

        # Convert the argument to a tuple if it is not already a tuple
        # or list.
        if not isinstance(widgetSignatures, (tuple, list)):
            widgetSignatures = widgetSignatures,

        # Ensure that all arguments in the tuple/list are strings.
        for idx, val in enumerate(widgetSignatures):
            if not isinstance(val, str):
                args = ('widgetSignatures', 'str', inspect.stack()[0][3])
                raise QtmacsArgumentError(*args)

        # Store the compatible widget signatures as a tuple (of strings).
        self._qteWidgetSignatures = tuple(widgetSignatures)

    def qtePrepareToRun(self):
        """
        This method is called by Qtmacs to prepare the macro for
        execution.

        It is probably a bad idea to overload this method as it only
        administrates the macro execution and calls the ``qteRun``
        method (which *should* be overloaded by the macro programmer
        in order for the macro to do something).

        |Args|

        * **None**

        |Returns|

        * **None**

        |Raises|

        * **None**
        """

        # Report the execution attempt.
        msgObj = QtmacsMessage((self.qteMacroName(), self.qteWidget), None)
        msgObj.setSignalName('qtesigMacroStart')
        self.qteMain.qtesigMacroStart.emit(msgObj)

        # Try to run the macro and radio the success via the
        # ``qtesigMacroFinished`` signal.
        try:
            self.qteRun()
            self.qteMain.qtesigMacroFinished.emit(msgObj)
        except Exception as err:
            if self.qteApplet is None:
                appID = appSig = None
            else:
                appID = self.qteApplet.qteAppletID()
                appSig = self.qteApplet.qteAppletSignature()
            msg = ('Macro <b>{}</b> (called from the <b>{}</b> applet'
                   ' with ID <b>{}</b>) did not execute properly.')
            msg = msg.format(self.qteMacroName(), appSig, appID)

            if isinstance(err, QtmacsArgumentError):
                msg += '<br/>' + str(err)

            # Irrespective of the error, log it, enable macro
            # processing (in case it got disabled), and trigger the
            # error signal.
            self.qteMain.qteEnableMacroProcessing()
            self.qteMain.qtesigMacroError.emit(msgObj)
            self.qteLogger.exception(msg, exc_info=True, stack_info=True)

    def qteRun(self):
        """
        The actual macro code.

        Overload this method with your own code. This method has
        access to the calling applet and widget via ``self.qteApplet``
        (never **None**) and ``self.qteWidget`` (may be **None**).

        |Args|

        * **None**

        |Returns|

        * **None**

        |Raises|

        * **None**
        """
        pass

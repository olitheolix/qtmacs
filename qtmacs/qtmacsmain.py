# Copyright 2012-2013, Oliver Nagy <qtmacsdev@gmail.com>
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
This is the central Qtmacs module.

It contains the following classes:

* ``QtmacsMain``: the engine behind Qtmacs. It defines *all* signals
  that Qtmacs (as an application) can emit, has no visible appearance,
  there can ever only be one instance of this class which must be
  created by hand.
* ``QtmacsWindow``: a window to display applets. There is always at
  least one instance. Do not instantiate this class manually.
* ``QtmacsEventFilter``: intercepts and filters all keyboard
  events. There is always only one instance of this class and it is
  (semi-)automatically installed on all widgets to ensure Qtmacs
  reacts to keyboard shortcuts. Do not instantiate this class
  manually.
* ``QtmacsSplitter``: used to visually split applets inside a
  ``QtmacsWindow``. The only difference with a normal ``QSplitter``
  are additional convenience methods and admin attributes for the
  Qtmacs layout engine.
* ``QtmacsPlaceholderApplet``: a virtual applet that is automatically
  inserted whenever no other applets are left to display in a window.

.. warning:: It is *not* safe to use ``from`` in order to import
   classes from this module.

Usage example (requires Python 3.x and PyQt 4.8)::

    import sys
    import qtmacs.qtmacsmain
    from PyQt4 import QtGui

    if __name__ == '__main__':
        QtApplicationInstance = QtGui.QApplication(sys.argv)
        qtmacsMain = qtmacs.qtmacsmain.QtmacsMain()
        sys.exit(QtApplicationInstance.exec_())

.. note:: It is almost certainly a bad idea to use any of the classes
   in this module directly, except for a single instance of ``QtmacsMain``.
"""

import re
import os
import imp
import sip
import sys
import types
import inspect
import logging
import qtmacs.auxiliary
import qtmacs.kill_list
import qtmacs.type_check
import qtmacs.base_macro
import qtmacs.base_applet
import qtmacs.qtmacsmain_macros
import qtmacs.qte_global as qte_global

from PyQt4 import QtCore, QtGui
from qtmacs.exceptions import *

# Shorthands.
type_check = qtmacs.type_check.type_check
QtmacsMacro = qtmacs.base_macro.QtmacsMacro
QtmacsApplet = qtmacs.base_applet.QtmacsApplet
QtmacsKeymap = qtmacs.auxiliary.QtmacsKeymap
QtmacsMessage = qtmacs.auxiliary.QtmacsMessage
QtmacsKeysequence = qtmacs.auxiliary.QtmacsKeysequence
QtmacsAdminStructure = qtmacs.auxiliary.QtmacsAdminStructure
qteIsQtmacsWidget = qtmacs.auxiliary.qteIsQtmacsWidget
qteGetAppletFromWidget = qtmacs.auxiliary.qteGetAppletFromWidget


class DeliverQtKeyEvent(QtmacsMacro):
    """
    Deliver a Qt key event to an unregistered Qt widget.

    This macro passes a ``QKeyEvent`` through to the Qt native
    ``keyPressed`` method. The purpose of this macro is to seamlessly
    integrate regular Qt widgets (ie. those not added with
    ``qteAddWidget``) into the macro framework, despite the fact that
    such widgets cannot have Qtmacs macros associated with it.

    The advantage of delivering key events via this macro is that
    such widgets are not served out of order and receive their
    respective key events only when all preceding keys (and their
    associated macros) were processed.

    ..note: this macro is the only \"hard coded\" macro in Qtmacs.
      It is registered in the constructor of ``QtmacsMain`` and
      explicitly used in the ``QtmacsEventFilter``.

    |Signature|

    * *applet*: '*'
    * *widget*: '*'
    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('*')

    def qteRun(self):
        """
        Extract the last ``QKeyEvent`` from the keyboard sequence
        (there should only be one anyway, but just to be sure) and
        deliver it to the native ``keyPressEvent`` method of the
        widget. The actual call is wrapped in a try-except construct
        because the ``keyPressEvent`` are protected methods in the C++
        code and cannot be called from PyQt, unless the widget itself
        was created in PyQt as opposed to by Qt itself. A typical
        example are the automatic scrollbars of windows. If they have
        the focus (just click on them) when a keyboard event occurs
        then Python 3.2 throws the following exception: "`RuntimeError:
        no access to protected functions or signals for objects not
        created from Python`".

        It remains to be seen if this poses a problem.
        """
        # Ignore the request if the widget has no keyPressEvent method.
        if not hasattr(self.qteWidget, 'keyPressEvent'):
            return

        # Extract the last key and send it to the widget.
        keyEvent = qte_global.last_key_sequence.toQKeyEventList()[-1]
        try:
            self.qteWidget.keyPressEvent(keyEvent)
        except RuntimeError:
            pass


class QtmacsEventFilter(QtCore.QObject):
    """
    Intercept keystrokes, parse them, and queue the associated macros.

    This is the one and only event filter in Qtmacs. Every applet and
    registered widget (ie. widgets added with the ``qteAddWidget``) is
    under its control.

    This event handler is also the source for the ``qtesigAbort`` and
    ``qtesigKeyparsed`` signals that applets and macros can connect
    themselves to.

    |Args|

    * ``qteMain`` (**QtmacsMain**): reference to the one and only
      ``QtmacsMain`` instance.

    |Signals|

    * ``qtesigAbort``: the user pressed <ctrl>-g. The signal is emitted
      after Qtmacs' internal cleanup actions, but (almost certainly)
      before GUI had a chance to update itself.
    * ``qtesigKeypressed``: a key was pressed. Connect to this signal if
      a global equivalent of the Qt native ``keypressed`` method is required.

      - ``targetObj`` (**QObject**): the original recipient of the signal.
      - ``keyEvent`` (**QKeyEvent**): last pressed key.

    * ``qtesigKeyparsed`` (targetObj, keysequence, macroName): Qtmacs
      has finished parsing the key sequence. This signal is similar to
      ``qtesigKeypressed`` but is never triggered for pure modifier
      combinations (eg. just pressing <ctrl> will not trigger it).

      - ``targetObj`` (**QObject**): the original recipient of the signal.
      - ``keysequence`` (**QtmacsKeysequence**): key sequence since it
        was last reset (ie. was either invalid or specified a macro).
      - ``macroName`` (**str**): either the name of the macro associated
        with the just completed
        ``keysequence``, or **None** if still incomplete.

    * qtesigKeyseqComplete: the last key completed a valid
      shortcut sequence for a macro.

      - ``macroName`` (**str**): name of macro associated with
        ``keysequence``.
      - ``keysequence`` (**QtmacsKeysequence**): the actual key
        sequence.

    * qtesigKeyseqPartial: the last key did not complete a
      macro shortcut.

      - ``keysequence`` (**QtmacsKeysequence**): the actual key
        sequence.

    * qtesigKeyseqInvalid: the last key rendered the key sequence
      invalid, ie. it cannot possibly lead to valid macro shortcut
      anymore.

      - ``keysequence`` (**QtmacsKeysequence**): the actual key
        sequence.
    """
    def __init__(self):
        super().__init__()

        # The keysequence typed by the user until it either
        # points to a macro becomes invalid.
        self._keysequence = QtmacsKeysequence()

        # Flag to turn off macro processing (automatically reset
        # when the user presses <ctrl>+g).
        self._qteFlagRunMacro = True

        # Shorhands:
        self.qteMain = qte_global.qteMain
        self.qApp = QtGui.QApplication.instance()

        # List of events intercepted by this handler.
        self.qteEventList = (QtCore.QEvent.KeyPress,
                             QtCore.QEvent.MouseButtonPress)

        # The name of the macro that will deliver key events
        # to widgets not registered with Qtmacs, yet are part of
        # its widget hierarchy.
        self.QtDelivery = self.qteMain.qteMacroNameMangling(DeliverQtKeyEvent)

    def eventFilter(self, targetObj, event_qt):
        """
        Intercept keyboard events and pass them on to the key parser
        and/or applet and/or widget.

        The handler only intercepts keyboard events and lets Qt handle
        the remaining ones (eg. mouse clicks) as usual.

        |Args|

        * ``targetObj`` (**QObject**): the source of the event (see Qt
          documentation).
        * ``event_qt`` (**QEvent**): information about the event (see Qt
          documentation).

        |Returns|

        * **bool**: if **True**, Qt will consider the event handled.

        |Raises|

        * **None**
        """
        # Return immediately if Qtmacs is not interested in it.
        if event_qt.type() not in self.qteEventList:
            return False

        # Determine if the widget belongs to the Qtmacs hierarchy and
        # return immediately if not.
        if not qteIsQtmacsWidget(targetObj):
            return False

        # If the event is a mouse click then update the Qtmacs internal
        # focus state and tell the Qt library that the event was NOT
        # handled. This ensures the click is propagated to the widget.
        if event_qt.type() == QtCore.QEvent.MouseButtonPress:
            self.qteMain._qteMouseClicked(targetObj)
            return False

        # Make a copy of the QKeyEvent because Qt will delete the
        # underlying object as soon as the event is handled. However, some
        # macros might retain a reference which will then become invalid
        # and result in a difficult to trace bug. Therefore, supply them
        # with an explicit copy only.
        event = QtGui.QKeyEvent(event_qt.type(), event_qt.key(),
                                event_qt.modifiers(), event_qt.text(),
                                event_qt.isAutoRepeat(), event_qt.count())

        # Abort the input if the user presses <ctrl>-g and declare the
        # keyboard event handled.
        mod = event.modifiers()
        key = event.key()
        if (mod == QtCore.Qt.ControlModifier) and (key == QtCore.Qt.Key_G):
            # Furthermore, clear the key sequence and ensure macro execution
            # is turned on again.
            self._keysequence.reset()
            self._qteFlagRunMacro = True

            # Remove the mini applet.
            self.qteMain.qteKillMiniApplet()

            # Drop all macros and keys left in the respective queues.
            self.qteMain._qteMacroQueue = []
            self.qteMain._qteKeyEmulationQueue = []

            # Ensure the focus manager runs once the event loop is idle again.
            # Also, emit the abort signal.
            msgObj = QtmacsMessage()
            msgObj.setSignalName('qtesigAbort')
            self.qteMain.qtesigAbort.emit(msgObj)
            return True

        # If the widget is unregistered then parse the key without further
        # ado and declare the key event handled via the return value.
        if not hasattr(targetObj, '_qteAdmin'):
            self.qteProcessKey(event, targetObj)
            return True

        # Shorthand to the QtmacsApplet that received this event.
        qteApplet = targetObj._qteAdmin.qteApplet

        # Retrieve information about how the widget wants its keyboard
        # events processed.
        tmp = targetObj._qteAdmin.keyFilterPolicy()
        receiveBefore, useQtmacs, receiveAfter = tmp
        del tmp

        # If the applet requested the keyboard input before being
        # processed by Qtmacs then send the event to the applet which
        # harbours the object (ie. *NOT* the object itself). It is the
        # responsibility of the applet to enact the desired
        # behaviour. If this action is the native behaviour of the
        # widget then the applet should consider using
        # "self.qteText.keyPressEvent(keyEvent)" to achieve this.
        if receiveBefore:
            qteApplet.qteKeyPressEventBefore(event, targetObj)

        # If the applet wants Qtmacs to process the keyboard event then do so.
        if useQtmacs:
            self.qteProcessKey(event, targetObj)

        # If the applet requested the keyboard input after being
        # processed by Qtmacs then send the event to the applet which
        # harbours the object (ie. *NOT* the object itself). It is the
        # responsibility of the applet to enact the desired behaviour
        # on the object.
        if receiveAfter:
            qteApplet.qteKeyPressEventAfter(event, targetObj)

        # Declare the key event handled.
        return True

    def qteProcessKey(self, event, targetObj):
        """
        If the key completes a valid key sequence then queue the
        associated macro.

        |Args|

        * ``targetObj`` (**QObject**): the source of the event
          (see Qt documentation).
        * ``event_qt`` (**QKeyEvent**): information about the key
          event (see Qt documentation).

        |Returns|

        * **Bool**: **True** if there was at least a partial match and
                    **False** if the key sequence was invalid.

        |Raises|

        * **None**
        """
        # Announce the key and targeted Qtmacs widget.
        msgObj = QtmacsMessage((targetObj, event), None)
        msgObj.setSignalName('qtesigKeypressed')
        self.qteMain.qtesigKeypressed.emit(msgObj)

        # Ignore standalone <Shift>, <Ctrl>, <Win>, <Alt>, and <AltGr>
        # events.
        if event.key() in (QtCore.Qt.Key_Shift, QtCore.Qt.Key_Control,
                           QtCore.Qt.Key_Meta, QtCore.Qt.Key_Alt,
                           QtCore.Qt.Key_AltGr):
            return False

        # Add the latest key stroke to the current key sequence.
        self._keysequence.appendQKeyEvent(event)

        # Determine if the widget was registered with qteAddWidget
        isRegisteredWidget = hasattr(targetObj, '_qteAdmin')

        if isRegisteredWidget and hasattr(targetObj._qteAdmin, 'keyMap'):
            keyMap = targetObj._qteAdmin.keyMap
        else:
            keyMap = self.qteMain._qteGlobalKeyMapByReference()

        # See if there is a match with an entry from the key map of
        # the current object. If ``isPartialMatch`` is True then the
        # key sequence is potentially incomplete, but not invalid.
        # If ``macroName`` is not **None** then it is indeed complete.
        (macroName, isPartialMatch) = keyMap.match(self._keysequence)

        # Make a convenience copy of the key sequence.
        keyseq_copy = QtmacsKeysequence(self._keysequence)

        if isPartialMatch:
            # Reset the key combination history if a valid macro was
            # found so that the next key that arrives starts a new key
            # sequence.
            if macroName is None:
                # Report a partially completed key-sequence.
                msgObj = QtmacsMessage(keyseq_copy, None)
                msgObj.setSignalName('qtesigKeyseqPartial')
                self.qteMain.qtesigKeyseqPartial.emit(msgObj)
            else:
                # Execute the macro if requested.
                if self._qteFlagRunMacro:
                    self.qteMain.qteRunMacro(macroName, targetObj, keyseq_copy)

                # Announce that the key sequence lead to a valid macro.
                msgObj = QtmacsMessage((macroName, keyseq_copy), None)
                msgObj.setSignalName('qtesigKeyseqComplete')
                self.qteMain.qtesigKeyseqComplete.emit(msgObj)
                self._keysequence.reset()
        else:
            if isRegisteredWidget:
                # Announce (and log) that the key sequence is invalid. However,
                # format the key string to Html first, eg. "<ctrl>-x i" to
                # "<b>&lt;Ctrl&gt;+x i</b>".
                tmp = keyseq_copy.toString()
                tmp = tmp.replace('<', '&lt;')
                tmp = tmp.replace('>', '&gt;')
                msg = 'No macro is bound to <b>{}</b>.'.format(tmp)
                self.qteMain.qteLogger.warning(msg)
                msgObj = QtmacsMessage(keyseq_copy, None)
                msgObj.setSignalName('qtesigKeyseqInvalid')
                self.qteMain.qtesigKeyseqInvalid.emit(msgObj)
            else:
                # If we are in this branch then the widet is part of the
                # Qtmacs widget hierachy yet was not registered with
                # the qteAddWidget method. In this case use the QtDelivery
                # macro to pass on whatever the event was (assuming
                # macro processing is enabled).
                if self._qteFlagRunMacro:
                    self.qteMain.qteRunMacro(
                        self.QtDelivery, targetObj, keyseq_copy)
            self._keysequence.reset()

        # Announce that Qtmacs has processed another key event. The
        # outcome of this processing is communicated along with the
        # signal.
        msgObj = QtmacsMessage((targetObj, keyseq_copy, macroName), None)
        msgObj.setSignalName('qtesigKeyparsed')
        self.qteMain.qtesigKeyparsed.emit(msgObj)
        return isPartialMatch

    def qteEnableMacroProcessing(self):
        """
        Execute macro whenever a valid key sequence was entered.

        This method clears any partially entered key sequence.

        |Args|

        * **None**

        |Returns|

        * **None**

        |Raises|

        * **None**
        """
        self._qteFlagRunMacro = True
        self._keysequence.reset()

    def qteDisableMacroProcessing(self):
        """
        Do not execute any macros upon typing a valid key sequence.

        This method only prevents the event handler from queuing any
        macro for execution, but other than that it operates as
        usual. In particular, it keeps filtering the keys, matching
        them against pre-defined keyboard sequence, and emit all its
        signals, eg. ``abort``.

        This method does not reset itself unless either
        ``qteEnableMacroProcessing`` is called or the user enters
        <ctrl>+g.

        |Args|

        * **None**

        |Returns|

        * **None**

        |Raises|

        * **None**
        """
        self._qteFlagRunMacro = False


class QtmacsSplitter(QtGui.QSplitter):
    """
    A normal ``QSplitter`` but with an _qteAdmin structure to disguise
    it as a ``Qtmacs`` widget.

    The disguise is necessary because these splitters are the parent
    of every visible applet, and some methods query information about
    its parent assuming that it is another widget under the control of
    Qtmacs.

    |Args|

    * ``orient`` (**Qt.Orientation**): orientation of the splitter
      (ie. horizontal or vertical)
    * ``parent_win`` (**QtmacsApplet**): the window in which the
      splitter exists.
    """
    def __init__(self, orient, parent_win):
        super().__init__(orient)

        # Destroy the splitter when its close() method is called.
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # Add a _qteAdmin structure to the splitter and give it a hard
        # coded signature.
        self._qteAdmin = QtmacsAdminStructure(None)
        self._qteAdmin.widgetSignature = '__QtmacsLayoutSplitter__'
        self._qteAdmin.parentWindow = parent_win

    def qteAddWidget(self, widget):
        """
        Add a widget to the splitter and make it visible.

        The only two differences between this method and the native
        ``QSplitter.insertWidget()`` method is that this one 1)
        expects the widget to have a ``QtmacsAdmin`` structure (ie. to
        be a ``QtmacsApplet`` or a ``QtmacsSplitter``) and 2) make the
        widget visible automatically. Both is mostly for convenience
        because adding a widget to the splitter in Qtmacs is
        tantamount to displaying it.

        |Args|

        * ``widget`` (**QWidget**): the widget to add to the splitter.

        |Returns|

        * **None**

        |Raises|

        * **None**
        """
        QtGui.QSplitter.addWidget(self, widget)

        # If the widget is QtmacsSplitter then its show() methods has
        # no argument, whereas any applet has an overloaded show()
        # function.
        if widget._qteAdmin.widgetSignature == '__QtmacsLayoutSplitter__':
            widget.show()
        else:
            widget.show(True)

    def qteInsertWidget(self, idx, widget):
        """
        Insert ``widget`` to the splitter at the specified ``idx``
        position and make it visible.

        The only two differences between this method and the native
        ``QSplitter.insertWidget()`` method is that this one

        1. expects the widget to have a ``QtmacsAdmin`` structure
           (ie. to be a ``QtmacsApplet`` or a ``QtmacsSplitter``)
        2. make the widget visible automatically.

        Both are mostly for convenience because adding a ``widget`` to
        the splitter in Qtmacs is tantamount to displaying it.

        |Args|

        * ``idx`` (**int**): non-negative index position.
        * ``widget`` (**QWidget**): the widget to insert into the
          splitter at position ``idx``.

        |Returns|

        * **None**

        |Raises|

        * **None**
        """
        QtGui.QSplitter.insertWidget(self, idx, widget)

        # If the widget is QtmacsSplitter then its show() methods has
        # no argument, whereas any applet has an overloaded show()
        # function.
        if widget._qteAdmin.widgetSignature == '__QtmacsLayoutSplitter__':
            widget.show()
        else:
            widget.show(True)

    def qteParentWindow(self):
        """
        Return a reference to the parent window.

        |Args|

        * **None**

        |Returns|

        * **QtmacsWindow**: reference to window object that harbours
          this splitter.

        |Raises|

        * **None**
        """
        return self._qteAdmin.parentWindow


class QtmacsWindow(QtGui.QWidget):
    """
    A window that can display Qtmacs applets.

    Upon creation this window is empty.

    |Args|

    * ``windowPos`` (**QRect**): position and size of window
      on screen.
    * ``windowID`` (**str**): unique window ID.
    """
    def __init__(self, windowPos, windowID):
        # Call the base class constructors.
        super().__init__()

        # Keep a handle to the QtmacsMain instance.
        self.qteMain = qte_global.qteMain

        # Insert the admin structure and populate it with hard coded values.
        self._qteAdmin = QtmacsAdminStructure(None, isQtmacsWindow=True)
        self._qteAdmin.appletID = '__QtmacsMain__'
        self._qteAdmin.appletSignature = '__QtmacsMain__'
        self._qteAdmin.widgetSignature = '__QtmacsMain__'
        self._qteWindowID = windowID

        # Set the window title and icon.
        self.setWindowTitle('Qtmacs Window: {}'.format(self._qteWindowID))

        # Locate the Qtmacs logo and install it as the application icon.
        path, _ = os.path.split(qtmacs.qtmacsmain.__file__)
        self.setWindowIcon(QtGui.QIcon(path + '/misc/Max.png'))

        # Specify the initial size of the main applet.
        self.setGeometry(windowPos)

        # Instantiate the status applet.
        import qtmacs.applets.statusbar as statusbar
        self.qteStatusBar = statusbar.StatusBar('**Status**')

        # Create two splitters. The ``qteAppletSplitter`` always
        # contains the normal applets and is capable of tiling them
        # (if necessary, by adding more sub-splitters), whereas
        # ``qteLayoutSplitter`` separates the applet splitter and the
        # mini/status applet.
        self.qteAppletSplitter = QtmacsSplitter(QtCore.Qt.Horizontal, self)
        self.qteLayoutSplitter = QtmacsSplitter(QtCore.Qt.Vertical, self)
        self.qteLayoutSplitter.addWidget(self.qteAppletSplitter)
        self.qteLayoutSplitter.addWidget(self.qteStatusBar)

        # Install the just created layout as the window layout.
        hbox = QtGui.QHBoxLayout(self)
        hbox.addWidget(self.qteLayoutSplitter)
        self.setLayout(hbox)


class QtmacsMain(QtCore.QObject):
    """
    This class administrates Qtmacs and has exactly **one** instance.

    ``QtmacsMain`` itself has no visible appearance but spawns a
    ``QmacsWindow`` upon instantiation which it populates with the
    ``LogViewer`` applet to log messages. It then sets up a logger
    object (from the standard ``logging`` module) to facilitate a
    unified logging interface, defines the signals that Qtmacs emits
    (not necessarily from this class).

    This class also defines *all* Qtmacs wide signals despite emitting
    hardly any of them itself (most are issued by applet- and macro
    classes). The reason for defining them here nonetheless is to make
    it easier on the applet/macro programmer and put them all into a
    single place where they can be reached via ``self.qteMain``
    (eg. ``qtesigAbort.connect(myAbortMethod)``).

    .. note:: Qtmacs is a ~3000 lines long state machine as well as a
              plugin system on steroids that uses its own Python
              instance to run third party Python code over which it
              has no control. To shield it from as many unintended
              errors and inconsistencies as practically possible its
              methods enforce strict (and unpythonic) annotation based
              type checks on all its input arguments. These checks
              alleviate the risk of inconsistent arguments going
              unnoticed until either an unrelated applet or macro uses
              it (almost impossible to trace, but not probably
              uncritical), or Qtmacs itself uses it (also almost
              impossible to trace, but possibly fatal). For the same
              reason, the methods are simple, task oriented, and do
              not try to be smart. It is the responsibility of the
              applet/macro programmer to combine these methods to
              implement a more complex behaviour.

    |Args|

    * ``parent`` (**QWidget**): **None** if Qtmacs runs standalone,
        otherwise the parent widget.
    * ``importFile`` (**str**): name of module to import at startup.
    * ``logConsole`` (**bool**): if **True**, write all log messages
        to the console and log viewer applet.
    """
    # Define the signals Qtmacs can emit.
    qtesigAbort = QtCore.pyqtSignal(QtmacsMessage)
    qtesigCloseQtmacs = QtCore.pyqtSignal(QtmacsMessage)
    qtesigMacroStart = QtCore.pyqtSignal(QtmacsMessage)
    qtesigMacroFinished = QtCore.pyqtSignal(QtmacsMessage)
    qtesigMacroError = QtCore.pyqtSignal(QtmacsMessage)
    qtesigKeypressed = QtCore.pyqtSignal(QtmacsMessage)
    qtesigKeyparsed = QtCore.pyqtSignal(QtmacsMessage)
    qtesigKeyseqPartial = QtCore.pyqtSignal(QtmacsMessage)
    qtesigKeyseqComplete = QtCore.pyqtSignal(QtmacsMessage)
    qtesigKeyseqInvalid = QtCore.pyqtSignal(QtmacsMessage)

    def __init__(self, parent=None, importFile=None, logConsole=False):
        # Call the base class constructors.
        super().__init__(parent)

        # Copy a reference of this instance into the qte_global
        # module. Note that this is the first- and last time this
        # variable is set for the entire life of this Qtmacs instance!
        qte_global.qteMain = self

        # ------------------------------------------------------------
        # Define all lists, queues, timers, and admin variables.
        # ------------------------------------------------------------
        self._qteAppletList = []
        self._qteWindowList = []
        self._qteMacroQueue = []
        self._qteRegistryHooks = {}
        self._qteRegistryMacros = {}
        self._qteRegistryApplets = {}
        self._qteKeyEmulationQueue = []
        self._qteGlobalKeyMap = QtmacsKeymap()
        self._qteMiniApplet = None
        self._qteActiveApplet = None

        # Timer ID to trigger the focus manager. At startup,
        # invoke it as soon as this class was fully initialised.
        self._qteTimerFocusManager = None

        # Timer ID to execute a queued macro.
        self._qteTimerRunMacro = None

        # ------------------------------------------------------------
        # Setup the logging facility for Qtmacs. This consists of
        # a ``logging.getLogger`` instance that can henceforth be
        # used throughout all of Qtmacs. A reference is copied to
        # ``qte_global`` but all applets and macros automatically
        # have access to it via their ``self.qteLogger`` attribute.
        # ------------------------------------------------------------

        # Create the logger instance.
        self.qteLogger = logging.getLogger('qtmacs')
        self.qteLogger.setLevel(logging.DEBUG)
        self.qteDefVar('qteLogger', self.qteLogger,
                       doc="Instance of ``logging.getLogger('qtmacs')``.")

        # Add a stream handler if requested. This handler dumps all
        # log messages to the console but has no effect on the log
        # viewer applet in Qtmacs. The main purpose of this additional
        # handler is to track error messages that occur before the
        # logging applet is started (cannot be done this early), or
        # when Qtmacs fails start up at all (eg. error in this very
        # constructor).
        if logConsole:
            formatter = logging.Formatter('%(levelname)s - %(message)s')
            streamHandler = logging.StreamHandler()
            streamHandler.setLevel(logging.DEBUG)
            streamHandler.setFormatter(formatter)
            self.qteLogger.addHandler(streamHandler)

        # Re-route the except hook to a custom object to capture all
        # errors not otherwise captured, and feed them into the
        # Qtmacs logger.
        sys.excepthook = self.QtmacsExceptHook

        # Perform OS- and machine specific setup.
        import qtmacs.platform_setup
        qtmacs.platform_setup.setup(self)

        # ------------------------------------------------------------
        # Instantiate the (one and only) event filter for Qtmacs,
        # load the global macros and keybindings (eg. for switching
        # applets, executing macros, quitting Qtmacs, etc.), and
        # manually create the first Qtmacs window.
        # ------------------------------------------------------------

        # Register the macro that delivers Qt key events to widgets
        # that are part of the Qtmacs widget hierarchy, but were
        # not officially registered with Qtmacs. Since the keyboard
        # events for these widgets are nonetheless intercepted by
        # the Qtmacs event handler they are delivered with the
        # special macro ``DelierQtKeyEvent``.
        self.qteRegisterMacro(DeliverQtKeyEvent)

        # Instantiate the keyboard filter for Qtmacs. This must
        # happen after the call to qtmacs.platform_setup (see
        # line above) since it relies on the variables
        # "Qt_key_map" and "Qt_modifier_map".
        self._qteEventFilter = QtmacsEventFilter()

        # Import the applet- and widget independent macros and
        # key-bindings to provide the core functionality for Qtmacs.
        qtmacs.qtmacsmain_macros.install_macros_and_bindings()

        # Instantiate the first window.
        self.qteNewWindow(QtCore.QRect(100, 200, 750, 500))

        # ------------------------------------------------------------
        # Create an instance of the ``QtmacsKillList`` and add it to
        # qte_global to make the same instance available to every
        # applet that wants to use it.
        # ------------------------------------------------------------
        import qtmacs.kill_list
        self.qteDefVar('kill_list',
                       qtmacs.kill_list.QtmacsKillList(),
                       doc="Instance of ``QtmacsKillList`` class.")

        # ------------------------------------------------------------
        # Register and instantiate the ``logviewer`` applet. It will
        # automatically connect to the Qtmacs wide logger instance to
        # intercept all log messages.
        # ------------------------------------------------------------
        import qtmacs.applets.logviewer as logviewer
        appName = self.qteRegisterApplet(logviewer.LogViewer)
        appObj = self.qteNewApplet(appName, '**LogViewer**')

        # Error checking.
        if appObj is None:
            msg = 'Fatal error: could not instantiate the log viewer applet.'
            raise QtmacsOtherError(msg)
        else:
            self.qteMakeAppletActive(appObj)
            del logviewer

        # ------------------------------------------------------------
        # Pick up mouse clicks to synchronise the Qtmacs internal
        # state variables.
        # ------------------------------------------------------------
        qApp = QtGui.QApplication.instance()
        qApp.installEventFilter(self._qteEventFilter)

        qApp.focusChanged.connect(self.qteFocusChanged)
        del qApp

        # ------------------------------------------------------------
        # Load the global configuration file.
        # ------------------------------------------------------------
        # Determine the path of this very file and add it to the
        # Python load path. Then load the global configuration file
        # which is in the same path.
        path, _ = os.path.split(qtmacs.qtmacsmain.__file__)
        sys.path.insert(0, path)
        self.qteLogger.info('Loading global configuration file.')
        self.qteImportModule('config.py')

        # ------------------------------------------------------------
        # So far, so good.
        # ------------------------------------------------------------
        self.qteLogger.info('Initialisation of Qtmacs complete.')
        if importFile is not None:
            self.qteLogger.info('Loading file <b>{}</b>.'
                                .format(importFile))
            # Load the user specific configuration file.
            self.qteImportModule(importFile)

        # Trigger the focus manager.
        self.qteUpdate()

        # ------------------------------------------------------------
        # Testing and debugging from here on.
        # ------------------------------------------------------------
        #self.debugTimer = self.startTimer(2000)

    def timerEvent(self, event):
        """
        Trigger the focus manager and work off all queued macros.

        The main purpose of using this timer event is to postpone
        updating the visual layout of Qtmacs until all macro code has
        been fully executed. Furthermore, this GUI update needs to
        happen in between any two macros.

        This method will trigger itself until all macros in the queue
        were executed.

        |Args|

        * ``event`` (**QTimerEvent**): Qt native event description.

        |Returns|

        * **None**

        |Raises|

        * **None**
        """
        self.killTimer(event.timerId())

        if event.timerId() == self._qteTimerRunMacro:
            # Declare the macro execution timer event handled.
            self._qteTimerRunMacro = None

            # If we are in this branch then the focus manager was just
            # executed, the event loop has updated all widgets and
            # cleared out all signals, and there is at least one macro
            # in the macro queue and/or at least one key to emulate
            # in the key queue. Execute the macros/keys and trigger
            # the focus manager after each. The macro queue is cleared
            # out first and the keys are only emulated if no more
            # macros are left.
            while True:
                if len(self._qteMacroQueue) > 0:
                    (macroName, qteWidget, event) = self._qteMacroQueue.pop(0)
                    self._qteRunQueuedMacro(macroName, qteWidget, event)
                elif len(self._qteKeyEmulationQueue) > 0:
                    # Determine the recipient of the event. This can
                    # be, in order of preference, the active widget in
                    # the active applet, or just the active applet (if
                    # it has no widget inside), or the active window
                    # (if no applets are available).
                    if self._qteActiveApplet is None:
                        receiver = self.qteActiveWindow()
                    else:
                        if self._qteActiveApplet._qteActiveWidget is None:
                            receiver = self._qteActiveApplet
                        else:
                            receiver = self._qteActiveApplet._qteActiveWidget

                    # Call the event filter directly and trigger the focus
                    # manager again.
                    keysequence = self._qteKeyEmulationQueue.pop(0)
                    self._qteEventFilter.eventFilter(receiver, keysequence)
                else:
                    # If we are in this branch then no more macros are left
                    # to run. So trigger the focus manager one more time
                    # and then leave the while-loop.
                    self._qteFocusManager()
                    break
                self._qteFocusManager()
        elif event.timerId() == self.debugTimer:
            #win = self.qteNextWindow()
            #self.qteMakeWindowActive(win)
            #self.debugTimer = self.startTimer(1000)
            pass
        else:
            # Should not happen.
            print('Unknown timer ID')
            pass

    def _qteFocusManager(self):
        """
        Give the focus to the correct applet and widget.

        This method is the only method in all of Qtmacs that actually
        instructs the Qt library to focus a widget. It does so by
        first synchronising what Qtmacs thinks is visible and what Qt
        knows is visible, and then make the applet/widget active for
        which ``qteMakeAppletActive`` and/or ``qteMakeWidgetActive``
        were called last. If these applets do not exist anymore, then
        the next possible widget and or applet will be chosen.

        To trigger the focus manger *do not call this method
        directly*, but use ``qteUpdate`` instead. This ensures that
        the focus manager only runs *after* the Qt event loop was able
        to show/hide all the widgets and update internal status variables
        like the Qt native ``isVisible``.

        This method also performs several sanity checks to ensure that
        all visible applets are part of a splitter while all invisible
        applets are not. Violations of this rule are reported and
        should be debugged, as otherwise floating applets are a
        possibility.

        The focus policy:
        ------------------

        Facts:

          * There are windows, applets in windows, and widgets in
            applets.
          * The currently active applet is
            QtmacsMain._qteActiveApplet.
          * The currently active widget inside that applet is
            QtmacsApplet._qteActiveWidget.
          * No one except the focus manager calls the Qt native
            ``setFocus`` or ``activateWindow`` methods.
          * To queue an applet/widget for activation call
            ``qteMake{Applet,Widget}Active``. This will update the
            aforementioned variables ``_qteActiveApplet`` and
            ``_qteActiveWidget`` attributes in ``QtmacsMain`` and
            ``QtmacsApplet``, respectively.
          * The focus manager will inspect these variables and make
            the specified applet and widget active, if they still
            exists. If they do not exists, it will automatically pick
            a substitute.

        The tasks of the focus manager are, in this order:

          * Ensure Qt and Qtmacs agree on what is currently visible and
            go into damage control if this does not check out.
          * Activate the top level window containing ``_qteActiveApplet``.
          * Focus the active widget ``_qteActiveWidget`` inside the applet.


        |Args|

        * **None**

        |Returns|

        * **None**

        |Raises|

        * **None**
        """
        # Process all but user input events.
        flag = QtCore.QEventLoop.ExcludeUserInputEvents
        qApp = QtGui.QApplication.instance()
        qApp.processEvents(flag)

        # Ensure _qteActiveApplet is not a dangling pointer.
        if self._qteActiveApplet is not None:
            if sip.isdeleted(self._qteActiveApplet):
                self._qteActiveApplet = None

        # Perform sanity checks on all applets.
        if len(self._qteAppletList) > 0:
            # Compile a list of visible and invisible applets (include
            # the mini applet).
            isVis = [_ for _ in self._qteAppletList if _.qteIsVisible()]
            isNotVis = [_ for _ in self._qteAppletList if not _.qteIsVisible()]

            # Ensure that the parent of every visible applet is a
            # QtmacsSplitter instance.
            for app in isVis:
                signatureParent = app.parent()._qteAdmin.widgetSignature
                if signatureParent != '__QtmacsLayoutSplitter__':
                    msg = 'Applet <b>{}</b> is visible but not in splitter.'
                    msg = msg.format(app.qteAppletID())
                    self.qteLogger.error(msg, stack_info=True)

            # Ensure all invisible applets have no parent.
            for app in isNotVis:
                if app.parent() is not None:
                    msg = 'Applet <b>{}</b> is invisible yet has a parent.'
                    msg = msg.format(app.qteAppletID())
                    self.qteLogger.error(msg, stack_info=True)

            # Ensure that Qt and Qtmacs agree on whether or not an
            # applet is visible.
            isFaulty = False
            for app in (_ for _ in self._qteAppletList
                        if(_.isVisible() != _.qteIsVisible())):
                isFaulty = True
                msg = 'Inconsistent visibility for applet <b>{}</b>.'
                msg = msg.format(app.qteAppletID())
                msg += ' Qt: {}, Qtmacs: {}'
                msg = msg.format(app.isVisible(), app.qteIsVisible())
                self.qteLogger.error(msg, stack_info=True)

            # If one or more visibility inconsistencies occurred then
            # go into damage control and reset the layout as best as
            # possible.
            if isFaulty:
                msg = 'Resetting applet layout due to visibility'
                msg += ' inconsistencies.'
                self.qteLogger.critical(msg)

                # Close all but the first window.
                if len(self._qteWindowList) > 1:
                    for window in self._qteWindowList[1:]:
                        window.close()

                # Hide all applets except the mini applet. Note that
                # the hide() method will reparent the widget to None
                # which implies that they are also removed from any
                # they might be in.
                for app in (_ for _ in self._qteAppletList
                            if _ is not self._qteMiniApplet):
                    app.hide(True)

                # Manually insert the first applet into the splitter
                # and make it visible.
                if len(self._qteAppletList) > 0:
                    app = self._qteAppletList[0]

        # ------------------------------------------------------------
        # If the _qteActiveApplet pointer is void try to assign it
        # another applet, even if it is just the mini applet. If
        # nothing is available, then return.
        # ------------------------------------------------------------
        if self._qteActiveApplet is None:
            if len(self._qteAppletList) > 0:
                self._qteActiveApplet = self.qteNextApplet(
                    numSkip=0, skipMiniApplet=False)
            else:
                win = self._qteWindowList[0]
                self._qteActiveApplet = None

        if self._qteActiveApplet is None:
            return

        # ------------------------------------------------------------
        # Activate the Qt window that harbours the applet and is only
        # relevant if multiple windows are open. The activation is
        # necessary because giving the focus to a any widget (an
        # applet in this case) does not automatically active the
        # window it is in (see Qt documentation for more details).
        # This is the only place in Qtmacs where the Qt libraray is
        # actually instructed to activate a window.
        # ------------------------------------------------------------
        try:
            self._qteActiveApplet.activateWindow()
        except Exception as err:
            msg = 'Qt had a serious problem activating a window'
            msg += ' --> try to reproduce.'
            print(msg)
            print('Raised error:', err)
            print('Current applet', self._qteActiveApplet)
            self.qteLogger.exception('Tried to focus a non-existing applet.',
                                     exc_info=True, stack_info=True)

        # Shorthand.
        app = self._qteActiveApplet
        self.qteMakeAppletActive(app)

        # ------------------------------------------------------------
        # Activate the next focusable widget in the applet. Note that
        # the qteMakeWidgetActive method
        #   * can cope with nextWidget being None,
        #   * does not actually set the focus of anything but only
        #     asks Qtmacs to do it. The actual focussing is done
        #     a few lines further down.
        # ------------------------------------------------------------
        wid = app.qteNextWidget(numSkip=0)
        app.qteMakeWidgetActive(wid)

        # ------------------------------------------------------------
        # Actually focus the active widget in the active applet. This
        # is the only place in Qtmacs where the Qt library is actually
        # instructed to focus a widget.
        # ------------------------------------------------------------
        try:
            if app._qteActiveWidget is None:
                app.setFocus(QtCore.Qt.OtherFocusReason)
            else:
                app._qteActiveWidget.setFocus(QtCore.Qt.OtherFocusReason)
        except Exception as err:
            print('Serious problem activating the applet --> '
                  'try to reproduce.')
            print('Raised error:', err)
            print('Current applet object', app)
            print('Next widget: ', nextWidget)
            print('Current applet ID', app.qteAppletID())
            print('Active widget inside this applet', app._qteActiveWidget)
            self.qteLogger.exception('Tried to focus a non-existing applet.',
                                     exc_info=True, stack_info=True)

    def _qteMouseClicked(self, widgetObj):
        """
        Update the Qtmacs internal focus state as the result of a mouse click.

        |Args|

        * ``new`` (**QWidget**): the widget that received the focus.

        |Returns|

        * **None**

        |Raises|

        * **None**
        """

        # ------------------------------------------------------------
        # The following cases for widgetObj have to be distinguished:
        #   1: not part of the Qtmacs widget hierarchy
        #   2: part of the Qtmacs widget hierarchy but not registered
        #   3: registered with Qtmacs and an applet
        #   4: registered with Qtmacs and anything but an applet
        # ------------------------------------------------------------

        # Case 1: return immediately if widgetObj is not part of the
        # Qtmacs widget hierarchy; otherwise, declare the applet
        # containing the widgetObj active.
        app = qteGetAppletFromWidget(widgetObj)
        if app is None:
            return
        else:
            self._qteActiveApplet = app

        # Case 2: unregistered widgets are activated immediately.
        if not hasattr(widgetObj, '_qteAdmin'):
            self._qteActiveApplet.qteMakeWidgetActive(widgetObj)
        else:
            if app._qteAdmin.isQtmacsApplet:
                # Case 3: widgetObj is a QtmacsApplet instance; do not
                # focus any of its widgets as the focus manager will
                # take care of it.
                self._qteActiveApplet.qteMakeWidgetActive(None)
            else:
                # Case 4: widgetObj was registered with qteAddWidget
                # and can thus be focused directly.
                self._qteActiveApplet.qteMakeWidgetActive(widgetObj)

        # Trigger the focus manager.
        self._qteFocusManager()

    def qteFocusChanged(self, old, new):
        """
        Slot for Qt native focus-changed signal to notify Qtmacs if
        the window was switched.

        .. note: This method is work in progress.
        """
        # Do nothing if new is old.
        if old is new:
            return

        # If neither is None but both have the same top level
        # window then do nothing.
        if (old is not None) and (new is not None):
            if old.isActiveWindow() is new.isActiveWindow():
                return

    def qteUpdate(self):
        """
        Trigger the focus manager to update all widgets once the event
        loop is in control again.

        It is safe to call this method multiple times. Qtmacs ensures
        that the focus manager is only triggered once.

        |Args|

        * **None**

        |Returns|

        * **None**

        |Raises|

        * **None**
        """
        if self._qteTimerRunMacro is None:
            self._qteTimerRunMacro = self.startTimer(0)

    def QtmacsExceptHook(self, *exc_info):
        """
        Error handler for all errors that are not captured inside
        Qtmacs.

        This handler substitutes the ``sys.excepthook`` which is
        called whenever an error propagates all the way up to the
        interpreter. This hook should only be invoked rarely because
        all the macros in Qtmacs are executed within a try/catch
        statement, but if a faulty code is not triggered by Qtmacs
        itself but eg. one of its signals, or an external event, then
        the error cannot be caught directly. Instead, Qtmacs re-routed
        these error to this method which feeds them into the logger
        module like any other message.

        |Args|

        * ``exc_info`` (**tuple**): native error information and stack
          trace.

        |Returns|

        * **None**

        |Raises|

        * **None**
        """
        self.qteLogger.error('*** Global Error ***', exc_info=exc_info)

    def qteIsMiniApplet(self, obj):
        """
        Test if instance ``obj`` is a mini applet.

        |Args|

        * ``obj`` (**object**): object to test.

        |Returns|

        * **bool**: whether or not ``obj`` is the mini applet.

        |Raises|

        * **None**
        """
        try:
            ret = obj._qteAdmin.isMiniApplet
        except AttributeError:
            ret = False

        return ret

    @type_check
    def qteNewWindow(self, pos: QtCore.QRect=None, windowID: str=None):
        """
        Create a new, empty window with ``windowID`` at position ``pos``.

        |Args|

        * ``pos`` (**QRect**): size and position of new window.
        * ``windowID`` (**str**): unique window ID.

        |Returns|

        * **QtmacsWindow**: reference to the just created window instance.

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """

        # Compile a list of all window IDs.
        winIDList = [_._qteWindowID for _ in self._qteWindowList]

        # If no window ID was supplied simply count until a new and
        # unique ID was found.
        if windowID is None:
            cnt = 0
            while str(cnt) in winIDList:
                cnt += 1
            windowID = str(cnt)

        # If no position was specified use a default one.
        if pos is None:
            pos = QtCore.QRect(500, 300, 1000, 500)

        # Raise an error if a window with this ID already exists.
        if windowID in winIDList:
            msg = 'Window with ID <b>{}</b> already exists.'.format(windowID)
            raise QtmacsOtherError(msg)

        # Instantiate a new window object.
        window = QtmacsWindow(pos, windowID)

        # Add the new window to the window list and make it visible.
        self._qteWindowList.append(window)
        window.show()

        # Trigger the focus manager once the event loop is in control again.
        return window

    @type_check
    def qteMakeWindowActive(self, windowObj: QtmacsWindow):
        """
        Make the window ``windowObj`` active and focus the first
        applet therein.

        |Args|

        * ``windowObj`` (**QtmacsWindow**): window to activate.

        |Returns|

        * **None**

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """

        if windowObj in self._qteWindowList:
            # This will trigger the focusChanged slot which, in
            # conjunction with the focus manager, will take care of
            # the rest. Note that ``activateWindow`` is a native Qt
            # method, not a Qtmacs invention.
            windowObj.activateWindow()
        else:
            self.qteLogger.warning('Window to activate does not exist')

    def qteActiveWindow(self):
        """
        Return the currently active ``QtmacsWindow`` object.

        If no Qtmacs window is currently active (for instance because
        the user is working with another application at the moment)
        then the method returns the first window in the window list.

        The method only returns **None** if the window list is empty,
        which is definitively a bug.

        |Args|

        * **None**

        |Returns|

        * **QtmacsWindow**: the currently active window or **None** if
          no window is currently active.

        |Raises|

        * **None**
        """
        if len(self._qteWindowList) == 0:
            self.qteLogger.critical('The window list is empty.')
            return None
        elif len(self._qteWindowList) == 1:
            return self._qteWindowList[0]
        else:
            # Find the active window.
            for win in self._qteWindowList:
                if win.isActiveWindow():
                    return win

        # Return the first window if none is active.
        return self._qteWindowList[0]

    def qteNextWindow(self):
        """
        Return next window in cyclic order.

        |Args|

        * **None**

        |Returns|

        * **QtmacsWindow**: the next window in the Qtmacs internal
            window list.

        |Raises|

        * **None**
        """
        # Get the currently active window.
        win = self.qteActiveWindow()

        if win in self._qteWindowList:
            # Find the index of the window in the window list and
            # cyclically move to the next element in this list to find
            # the next window object.
            idx = self._qteWindowList.index(win)
            idx = (idx + 1) % len(self._qteWindowList)
            return self._qteWindowList[idx]
        else:
            msg = 'qteNextWindow method found a non-existing window.'
            self.qteLogger.warning(msg)
            return None

    @type_check
    def qteKillWindow(self, windowObj: QtmacsWindow=None):
        """
        Kill the specified window (applets inside the window are not
        deleted).

        .. note:: The method does nothing if ``windowObj`` is the only
           window left.

        |Args|

        * *windowObj* (**QtmacsWindow**): window object to delete.

        |Returns|

        * **None**

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        # Use the currently active window if none was specified.
        if windowObj is None:
            windowObj = self.qteActiveWindow()
            if windowObj is None:
                msg = ('Cannot kill the currently active window because'
                       ' it does not exist')
                self.qteLogger.error(msg, stack_info=True)
                return

        # If Qtmacs shows only one window then do nothing, because
        # deleting this window is akin to quitting Qtmacs without
        # going through the proper shutdown process.
        if len(self._qteWindowList) <= 1:
            msg = 'The last available window cannot be deleted.'
            self.qteLogger.error(msg, stack_info=True)
            return

        # Remove the window from the list.
        try:
            self._qteWindowList.remove(windowObj)
        except ValueError:
            msg = 'Cannot delete window with ID <b>{}</b> because it'
            msg += ' does not exist.'.format(windowObj._qteWindowID)
            self.qteLogger.error(msg, stack_info=True)
            return

        # Shorthand
        activeWindow = self.qteActiveWindow()

        # If the window to delete is currently active then switch the
        # focus to the first window in the list (not particularly
        # smart, but will do for now).
        if windowObj is activeWindow:
            activeWindow = self._qteWindowList[0]
            self.activeWindow.activateWindow()

            # Since the window with the active applet is deleted,
            # try to find a new applet to activate instead. It is
            # ok if there is no such applet.
            self._qteActiveApplet = self.qteNextApplet(
                windowObj=self._qteWindowList[0])

        # Move the mini applet if it is currently in the doomed
        # window.
        if self._qteMiniApplet is not None:
            if self._qteMiniApplet.qteParentWindow() is windowObj:
                # Re-parent the mini applet to the splitter in the new
                # window.
                activeWindow.qteLayoutSplitter.addWidget(self._qteMiniApplet)
                self._qteMiniApplet.show(True)

                # Give the focus to the first focusable widget (if any).
                wid = self._qteMiniApplet.qteNextWidget(numSkip=0)
                self._qteMiniApplet.qteMakeWidgetActive(wid)
                self.qteMakeAppletActive(self._qteMiniApplet)

        # Compile the list of visible applets in the doomed window
        # (use ``qteParentWindow`` to find all applets that have the
        # doomed window as parent).
        app_list = [_ for _ in self._qteAppletList
                    if _.qteParentWindow() == windowObj]

        # Hide all visible applets in the doomed window. Do not use
        # ``qteRemoveFromLayout`` for this since that method attempts
        # to replace the removed applet with another one, ie. the
        # doomed window would once again contain an applet.
        for app_obj in app_list:
            if not self.qteIsMiniApplet(app_obj):
                app_obj.hide(True)

        # Ensure the focus manager is triggered and the window deleted
        # once the event loop has regained control.
        windowObj.deleteLater()

    @type_check
    def qteNextApplet(self, numSkip: int=1, ofsApp: (QtmacsApplet, str)=None,
                      skipInvisible: bool=True, skipVisible: bool=False,
                      skipMiniApplet: bool=True,
                      windowObj: QtmacsWindow=None):
        """
        Return the next applet in cyclic order.

        If ``ofsApp=None`` then start cycling at the currently active
        applet. If ``ofsApp`` does not fit the selection criteria,
        then the cycling starts at the next applet in cyclic order
        that does.

        The returned applet is ``numSkip`` items in cyclic order away
        from the offset applet. If ``numSkip`` is positive traverse
        the applet list forwards, otherwise backwards.

        The method supports the following Boolean selection criteria:

        * ``skipInvisible``: ignore all invisible applets.
        * ``skipVisible``: ignore all visible applets.
        * ``skipMiniApplet``: ignore the mini applet applet.

        The ``ofsApp`` parameter can either be an instance of
        ``QtmacsApplet`` or a string denoting an applet ID. In the
        latter case the ``qteGetAppletHandle`` method is used to fetch
        the respective applet instance.

        |Args|

        * ``numSkip`` (**int**): number of applets to skip.
        * ``ofsApp`` (**QtmacsApplet**, **str**): applet from where to
          start counting.
        * ``skipInvisible`` (**bool**): whether or not to skip currently
          not shown applets.
        * ``skipVisible`` (**bool**): whether or not to skip currently
          shown applets.
        * ``skipMiniApplet`` (**bool**): whether or not to skip the mini
          applet.
        * ``windowObj`` (**QtmacsWindow**): the window to use when looking
          for applets. If **None**, then search in all windows.

        |Returns|

        * **QtmacsApplet**: either the next applet that fits the criteria,
          or **None** if no such applet exists.

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        # If ``applet`` was specified by its ID (ie. a string) then
        # fetch the associated ``QtmacsApplet`` instance. If
        # ``applet`` is already an instance of ``QtmacsApplet`` then
        # use it directly.
        if isinstance(ofsApp, str):
            ofsApp = self.qteGetAppletHandle(ofsApp)

        # Return immediately if the applet list is empty.
        if len(self._qteAppletList) == 0:
            return None

        # Sanity check: if the user requests applets that are neither
        # visible nor invisible then return immediately because no
        # such applet can possibly exist.
        if skipVisible and skipInvisible:
            return None

        # Make a copy of the applet list.
        appList = list(self._qteAppletList)

        # Remove all invisible applets from the list if the
        # skipInvisible flag is set.
        if skipInvisible:
            appList = [app for app in appList if app.qteIsVisible()]

            # From the list of (now guaranteed visible) applets remove
            # all those that are not in the specified window.
            if windowObj is not None:
                appList = [app for app in appList
                           if app.qteParentWindow() == windowObj]

        # Remove all visible applets from the list if the
        # skipInvisible flag is set.
        if skipVisible:
            appList = [app for app in appList if not app.qteIsVisible()]

        # If the mini-buffer is to be skipped remove it (if a custom
        # mini applet even exists).
        if skipMiniApplet:
            if self._qteMiniApplet in appList:
                appList.remove(self._qteMiniApplet)

        # Return immediately if no applet satisfied all criteria.
        if len(appList) == 0:
            return None

        # If no offset applet was given use the currently active one.
        if ofsApp is None:
            ofsApp = self._qteActiveApplet

        if ofsApp in self._qteAppletList:
            # Determine if the offset applet is part of the pruned
            # list.
            if ofsApp in appList:
                # Yes: determine its index in the list.
                ofsIdx = appList.index(ofsApp)
            else:
                # No: traverse all applets until one is found that is
                # also part of the pruned list (start at ofsIdx). Then
                # determine its index in the list.
                ofsIdx = self._qteAppletList.index(ofsApp)
                glob_list = self._qteAppletList[ofsIdx:]
                glob_list += self._qteAppletList[:ofsIdx]

                # Compile the intersection between the global and pruned list.
                ofsIdx = [appList.index(_) for _ in glob_list if _ in appList]
                if len(ofsIdx) == 0:
                    msg = ('No match between global and local applet list'
                           ' --> Bug.')
                    self.qteLogger.error(msg, stack_info=True)
                    return None
                else:
                    # Pick the first match.
                    ofsIdx = ofsIdx[0]
        else:
            # The offset applet does not exist, eg. because the user
            # supplied a handle that does not point to an applet or
            # we are called from qteKillApplet to replace the just
            # removed (and active) applet.
            ofsIdx = 0

        # Compute the index of the next applet and wrap around the
        # list if necessary.
        ofsIdx = (ofsIdx + numSkip) % len(appList)

        # Return a handle to the applet that meets the specified
        # criteria.
        return appList[ofsIdx]

    @type_check
    def qteRunMacro(self, macroName: str, widgetObj: QtGui.QWidget=None,
                    keysequence: QtmacsKeysequence=None):
        """
        Queue a previously registered macro for execution once the
        event loop is idle.

        The reason for queuing macros in the first place, instead of
        running them straight away, is to ensure that the event loop
        updates all the widgets in between any two macros. This will
        avoid many spurious and hard to find bugs due to macros
        assuming that all user interface elements have been updated
        when in fact they were not.

        |Args|

        * ``macroName`` (**str**): name of macro.
        * ``widgetObj`` (**QWidget**): widget (if any) on which the
          macro should operate.
        * ``keysequence`` (**QtmacsKeysequence**): key sequence that
          triggered the macro.

        |Returns|

        * **None**

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        # Add the new macro to the queue and call qteUpdate to ensure
        # that the macro is processed once the event loop is idle again.
        self._qteMacroQueue.append((macroName, widgetObj, keysequence))
        self.qteUpdate()

    @type_check
    def _qteRunQueuedMacro(self, macroName: str,
                           widgetObj: QtGui.QWidget=None,
                           keysequence: QtmacsKeysequence=None):
        """
        Execute the next macro in the macro queue.

        This method is triggered by the ``timerEvent`` in conjunction
        with the focus manager to ensure the event loop updates the
        GUI in between any two macros.

        .. warning:: Never call this method directly.

        |Args|

        * ``macroName`` (**str**): name of macro
        * ``widgetObj`` (**QWidget**): widget (if any) for which the
          macro applies
        * ``keysequence* (**QtmacsKeysequence**): key sequence that
          triggered the macro.

        |Returns|

        * **None**

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        # Fetch the applet holding the widget (this may be None).
        app = qteGetAppletFromWidget(widgetObj)

        # Double check that the applet still exists, unless there is
        # no applet (can happen when the windows are empty).
        if app is not None:
            if sip.isdeleted(app):
                msg = 'Ignored macro <b>{}</b> because it targeted a'
                msg += '  nonexistent applet.'.format(macroName)
                self.qteLogger.warning(msg)
                return

        # Fetch a signature compatible macro object.
        macroObj = self.qteGetMacroObject(macroName, widgetObj)

        # Log an error if no compatible macro was found.
        if macroObj is None:
            msg = 'No <b>{}</b>-macro compatible with {}:{}-type applet'
            msg = msg.format(macroName, app.qteAppletSignature(),
                             widgetObj._qteAdmin.widgetSignature)
            self.qteLogger.warning(msg)
            return

        # Update the 'last_key_sequence' variable in case the macros,
        # or slots triggered by that macro, have access to it.
        self.qteDefVar('last_key_sequence', keysequence,
                       doc="Last valid key sequence that triggered a macro.")

        # Set some variables in the macro object for convenient access
        # from inside the macro.
        if app is None:
            macroObj.qteApplet = macroObj.qteWidget = None
        else:
            macroObj.qteApplet = app
            macroObj.qteWidget = widgetObj

        # Run the macro and trigger the focus manager.
        macroObj.qtePrepareToRun()

    @type_check
    def qteNewApplet(self, appletName: str, appletID: str=None,
                     windowObj: QtmacsWindow=None):
        """
        Create a new instance of ``appletName`` and assign it the
        ``appletID``.

        This method creates a new instance of ``appletName``, as
        registered by the ``qteRegisterApplet`` method. If an applet
        with ``appletID`` already exists then the method does nothing
        and returns **None**, otherwise the newly created instance.

        If ``appletID`` is **None** then the method will create an
        applet with the next unique ID that fits the format
        ``appletName_0``, eg. 'RichEditor_0', 'RichEditor_1', etc.

        .. note:: The applet is not automatically made visible.

        |Args|

        * ``appletName`` (**str**): name of applet to create
          (eg. 'LogViewer')
        * ``appletID`` (**str**): unique applet identifier.
        * ``windowObj`` (**QtmacsWindow**): the window in which
          the applet should be created.

        |Returns|

        * **QtmacsApplet**: applet handle or **None** if no applet
          was created.

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        # Use the currently active window if none was specified.
        if windowObj is None:
            windowObj = self.qteActiveWindow()
            if windowObj is None:
                msg = 'Cannot determine the currently active window.'
                self.qteLogger.error(msg, stack_info=True)
                return

        # Determine an automatic applet ID if none was provided.
        if appletID is None:
            cnt = 0
            while True:
                appletID = appletName + '_' + str(cnt)
                if self.qteGetAppletHandle(appletID) is None:
                    break
                else:
                    cnt += 1

        # Return immediately if an applet with the same ID already
        # exists.
        if self.qteGetAppletHandle(appletID) is not None:
            msg = 'Applet with ID <b>{}</b> already exists'.format(appletID)
            self.qteLogger.error(msg, stack_info=True)
            return None

        # Verify that the requested applet class was registered
        # beforehand and fetch it.
        if appletName not in self._qteRegistryApplets:
            msg = 'Unknown applet <b>{}</b>'.format(appletName)
            self.qteLogger.error(msg, stack_info=True)
            return None
        else:
            cls = self._qteRegistryApplets[appletName]

        # Try to instantiate the class.
        try:
            app = cls(appletID)
        except Exception:
            msg = 'Applet <b>{}</b> has a faulty constructor.'.format(appletID)
            self.qteLogger.exception(msg, exc_info=True, stack_info=True)
            return None

        # Ensure the applet class has an applet signature.
        if app.qteAppletSignature() is None:
            msg = 'Cannot add applet <b>{}</b> '.format(app.qteAppletID())
            msg += 'because it has not applet signature.'
            msg += ' Use self.qteSetAppletSignature in the constructor'
            msg += ' of the class to fix this.'
            self.qteLogger.error(msg, stack_info=True)
            return None

        # Add the applet to the list of instantiated Qtmacs applets.
        self._qteAppletList.insert(0, app)

        # If the new applet does not yet have an internal layout then
        # arrange all its children automatically. The layout used for
        # this is horizontal and the widgets are added in the order in
        # which they were registered with Qtmacs.
        if app.layout() is None:
            appLayout = QtGui.QHBoxLayout()
            for handle in app._qteAdmin.widgetList:
                appLayout.addWidget(handle)
            app.setLayout(appLayout)

        # Initially, the window does not have a parent. A parent will
        # be assigned automatically once the applet is made visible,
        # in which case it is re-parented into a QtmacsSplitter.
        app.qteReparent(None)

        # Emit the init hook for this applet.
        self.qteRunHook('init', QtmacsMessage(None, app))

        # Return applet handle.
        return app

    @type_check
    def qteAddMiniApplet(self, appletObj: QtmacsApplet):
        """
        Install ``appletObj`` as the mini applet in the window layout.

        At any given point there can ever only be one mini applet in
        the entire Qtmacs application, irrespective of how many
        windows are open.

        Note that this method does nothing if a custom mini applet is
        already active. Use ``qteKillMiniApplet`` to remove that one
        first before installing a new one.

        |Args|

        * ``appletObj`` (**QtmacsApplet**): the new mini applet.

        |Returns|

        * **bool**: if **True** the mini applet was installed
          successfully.

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        # Do nothing if a custom mini applet has already been
        # installed.
        if self._qteMiniApplet is not None:
            msg = 'Cannot replace mini applet more than once.'
            self.qteLogger.warning(msg)
            return False

        # Arrange all registered widgets inside this applet
        # automatically if the mini applet object did not install its
        # own layout.
        if appletObj.layout() is None:
            appLayout = QtGui.QHBoxLayout()
            for handle in appletObj._qteAdmin.widgetList:
                appLayout.addWidget(handle)
            appletObj.setLayout(appLayout)

        # Now that we have decided to install this mini applet, keep a
        # reference to it and set the mini applet flag in the
        # applet. This flag is necessary for some methods to separate
        # conventional applets from mini applets.
        appletObj._qteAdmin.isMiniApplet = True
        self._qteMiniApplet = appletObj

        # Shorthands.
        app = self._qteActiveApplet
        appWin = self.qteActiveWindow()

        # Remember which window and applet spawned this mini applet.
        self._qteMiniApplet._qteCallingApplet = app
        self._qteMiniApplet._qteCallingWindow = appWin
        del app

        # Add the mini applet to the applet registry, ie. for most
        # purposes the mini applet is treated like any other applet.
        self._qteAppletList.insert(0, self._qteMiniApplet)

        # Add the mini applet to the respective splitter in the window
        # layout and show it.
        appWin.qteLayoutSplitter.addWidget(self._qteMiniApplet)
        self._qteMiniApplet.show(True)

        # Give focus to first focusable widget in the mini applet
        # applet (if one exists)
        wid = self._qteMiniApplet.qteNextWidget(numSkip=0)
        self._qteMiniApplet.qteMakeWidgetActive(wid)
        self.qteMakeAppletActive(self._qteMiniApplet)

        # Mini applet was successfully installed.
        return True

    def qteKillMiniApplet(self):
        """
        Remove the mini applet.

        If a different applet is to be restored/focused then call
        ``qteMakeAppletActive`` for that applet *after* calling this
        method.

        |Args|

        * **None**

        |Returns|

        * **None**

        |Raises|

        * **None**
        """
        # Sanity check: is the handle valid?
        if self._qteMiniApplet is None:
            return

        # Sanity check: is it really a mini applet?
        if not self.qteIsMiniApplet(self._qteMiniApplet):
            msg = ('Mini applet does not have its mini applet flag set.'
                   ' Ignored.')
            self.qteLogger.warning(msg)

        if self._qteMiniApplet not in self._qteAppletList:
            # Something is wrong because the mini applet is not part
            # of the applet list.
            msg = 'Custom mini applet not in applet list --> Bug.'
            self.qteLogger.warning(msg)
        else:
            # Inform the mini applet that it is about to be killed.
            try:
                self._qteMiniApplet.qteToBeKilled()
            except Exception:
                msg = 'qteToBeKilledRoutine is faulty'
                self.qteLogger.exception(msg, exc_info=True, stack_info=True)

            # Shorthands to calling window.
            win = self._qteMiniApplet._qteCallingWindow

            # We need to move the focus from the mini applet back to a
            # regular applet. Therefore, first look for the next
            # visible applet in the current window (ie. the last one
            # that was made active).
            app = self.qteNextApplet(windowObj=win)
            if app is not None:
                # Found another (visible or invisible) applet --> make
                # it active/visible.
                self.qteMakeAppletActive(app)
            else:
                # No visible applet available in this window --> look
                # for an invisible one.
                app = self.qteNextApplet(skipInvisible=False, skipVisible=True)
                if app is not None:
                    # Found an invisible applet --> make it
                    # active/visible.
                    self.qteMakeAppletActive(app)
                else:
                    # There is no other visible applet in this window.
                    # The focus manager will therefore make a new applet
                    # active.
                    self._qteActiveApplet = None
            self._qteAppletList.remove(self._qteMiniApplet)

        # Close the mini applet applet and schedule it for deletion.
        self._qteMiniApplet.close()
        self._qteMiniApplet.deleteLater()

        # Clear the handle to the mini applet.
        self._qteMiniApplet = None

    @type_check
    def _qteFindAppletInSplitter(self, appletObj: QtmacsApplet,
                                 split: QtmacsSplitter):
        """
        Return the splitter that holds ``appletObj``.

        This method recursively searches for ``appletObj`` in the
        nested splitter hierarchy of the window layout, starting at
        ``split``. If successful, the method returns a reference to
        the splitter, otherwise it returns **None**.

        |Args|

        * ``appletObj`` (**QtmacsApplet**): the applet to look for.
        * ``split`` (**QtmacsSplitter**): the splitter where to begin.

        |Returns|

        * **QtmacsSplitter**: the splitter that holds ``appletObj``
          or **None**.

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        # Compile a list of all widgets in the splitter and check if
        # one of them is the desired ``appletObj``.
        widget_in_splitter = [split.widget(ii) for ii in range(split.count())]
        if appletObj in widget_in_splitter:
            return split

        # Retain only those widgets that are QtmacsSplitter instances.
        split_in_splitter = [
            _ for _ in widget_in_splitter
            if _._qteAdmin.widgetSignature == '__QtmacsLayoutSplitter__']

        # Iterate over these splitters and by recursively calling ourselves.
        for nextSplit in split_in_splitter:
            ret = self._qteFindAppletInSplitter(appletObj, nextSplit)

            # If ``nextSplit`` holds the desired ``appletObj`` return
            # a reference to it.
            if ret is not None:
                return ret

        # The desired ``appletObj`` was not found in any of the
        # splitter widgets inside the current splitter, or any of the
        # children of these splitters.
        return None

    @type_check
    def qteSplitApplet(self, applet: (QtmacsApplet, str)=None,
                       splitHoriz: bool=True,
                       windowObj: QtmacsWindow=None):
        """
        Reveal ``applet`` by splitting the space occupied by the
        current applet.

        If ``applet`` is already visible then the method does
        nothing. Furthermore, this method does not change the focus,
        ie. the currently active applet will remain active.

        If ``applet`` is **None** then the next invisible applet
        will be shown. If ``windowObj`` is **None** then the
        currently active window will be used.

        The ``applet`` parameter can either be an instance of
        ``QtmacsApplet`` or a string denoting an applet ID. In the
        latter case the ``qteGetAppletHandle`` method is used to fetch
        the respective applet instance.

        |Args|

        * ``applet`` (**QtmacsApplet**, **str**): the applet to reveal.
        * ``splitHoriz`` (**bool**): whether to split horizontally
          or vertically.
        * ``windowObj`` (**QtmacsWindow**): the window in which to
          reveal ``applet``.

        |Returns|

        * **bool**: if **True**, ``applet`` was revealed.

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        # If ``newAppObj`` was specified by its ID (ie. a string) then
        # fetch the associated ``QtmacsApplet`` instance. If
        # ``newAppObj`` is already an instance of ``QtmacsApplet``
        # then use it directly.
        if isinstance(applet, str):
            newAppObj = self.qteGetAppletHandle(applet)
        else:
            newAppObj = applet

        # Use the currently active window if none was specified.
        if windowObj is None:
            windowObj = self.qteActiveWindow()
            if windowObj is None:
                msg = 'Cannot determine the currently active window.'
                self.qteLogger.error(msg, stack_info=True)
                return

        # Obtain the Qt constant that defines the horizontal or
        # vertical split.
        if splitHoriz:
            splitOrientation = QtCore.Qt.Horizontal
        else:
            splitOrientation = QtCore.Qt.Vertical

        if newAppObj is None:
            # If no new applet was specified use the next available
            # invisible applet.
            newAppObj = self.qteNextApplet(skipVisible=True,
                                           skipInvisible=False)
        else:
            # Do nothing if the new applet is already visible.
            if newAppObj.qteIsVisible():
                return False

        # If we still have not found an applet then there are no
        # invisible applets left to show. Therefore, splitting makes
        # no sense.
        if newAppObj is None:
            self.qteLogger.warning('All applets are already visible.')
            return False

        # If the root splitter is empty then add the new applet and
        # return immediately.
        if windowObj.qteAppletSplitter.count() == 0:
            windowObj.qteAppletSplitter.qteAddWidget(newAppObj)
            windowObj.qteAppletSplitter.setOrientation(splitOrientation)
            return True

        # ------------------------------------------------------------
        # If we got this far the root splitter contains at least one
        # element.
        # ------------------------------------------------------------

        # Shorthand to last active applet in the current window. Query
        # this applet with qteNextApplet method because
        # self._qteActiveApplet may be a mini applet, and we are only
        # interested in genuine applets.
        curApp = self.qteNextApplet(numSkip=0, windowObj=windowObj)

        # Get a reference to the splitter in which the currently
        # active applet lives. This may be the root splitter, or one
        # of its child splitters.
        split = self._qteFindAppletInSplitter(curApp,
                                              windowObj.qteAppletSplitter)
        if split is None:
            msg = 'Active applet <b>{}</b> not in the layout.'
            msg = msg.format(curApp.qteAppletID())
            self.qteLogger.error(msg, stack_info=True)
            return False

        # If 'curApp' lives in the root splitter, and the root
        # splitter contains only a single element, then simply add the
        # new applet as the second element and return.
        if split is windowObj.qteAppletSplitter:
            if windowObj.qteAppletSplitter.count() == 1:
                windowObj.qteAppletSplitter.qteAddWidget(newAppObj)
                windowObj.qteAppletSplitter.setOrientation(splitOrientation)
                return True

        # ------------------------------------------------------------
        # If we got this far the splitter (root or not) contains two
        # elements
        # ------------------------------------------------------------

        # Determine the index of the applet inside the splitter.
        curAppIdx = split.indexOf(curApp)

        # Create a new splitter and move 'curApp' and the previously
        # invisible ``newAppObj`` into it. Then insert this new
        # splitter at the position where the old applet was taken
        # from. Note: the widgets are inserted with the
        # ``qteAddWidget`` function (because they are Qtmacs applets)
        # but the splitter is added with ``insertWidget`` and NOT with
        # ``qteInsertWidget``. The reason is that the splitter is not
        # a Qtmacs applet and therefore does not require the extra TLC
        # for applets in terms of how and where to show them.
        newSplit = QtmacsSplitter(splitOrientation, windowObj)
        curApp.setParent(None)
        newSplit.qteAddWidget(curApp)
        newSplit.qteAddWidget(newAppObj)
        split.insertWidget(curAppIdx, newSplit)

        # Ensure that the applets inside the new splitter share half
        # the space. If this is impossible then the Qt layout engine
        # will take care of it.
        _ = int(sum(newSplit.sizes()) / 2)
        newSplit.setSizes([_, _])
        return True

    @type_check
    def qteReplaceAppletInLayout(self, newApplet: (QtmacsApplet, str),
                                 oldApplet: (QtmacsApplet, str)=None,
                                 windowObj: QtmacsWindow=None):
        """
        Replace ``oldApplet`` with ``newApplet`` in the window layout.

        If ``oldApplet`` is **None** then the currently active applet
        will be replaced. If ``windowObj`` is **None** then the
        currently active window is used.

        The ``oldApplet`` and ``newApplet`` parameters can either be
        instances of ``QtmacsApplet`` or strings denoting the applet
        IDs. In the latter case the ``qteGetAppletHandle`` method is
        used to fetch the respective applet instances.

        |Args|

        * ``newApplet`` (**QtmacsApplet**, **str**): applet to add.
        * ``oldApplet`` (**QtmacsApplet**, **str**): applet to replace.
        * ``windowObj`` (**QtmacsWindow**): the window in which to operate.

        |Returns|

        * **None**

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        # If ``oldAppObj`` was specified by its ID (ie. a string) then
        # fetch the associated ``QtmacsApplet`` instance. If
        # ``oldAppObj`` is already an instance of ``QtmacsApplet``
        # then use it directly.
        if isinstance(oldApplet, str):
            oldAppObj = self.qteGetAppletHandle(oldApplet)
        else:
            oldAppObj = oldApplet

        # If ``newAppObj`` was specified by its ID (ie. a string) then
        # fetch the associated ``QtmacsApplet`` instance. If
        # ``newAppObj`` is already an instance of ``QtmacsApplet``
        # then use it directly.
        if isinstance(newApplet, str):
            newAppObj = self.qteGetAppletHandle(newApplet)
        else:
            newAppObj = newApplet

        # Use the currently active window if none was specified.
        if windowObj is None:
            windowObj = self.qteActiveWindow()
            if windowObj is None:
                msg = 'Cannot determine the currently active window.'
                self.qteLogger.warning(msg, stack_info=True)
                return

        # If the main splitter contains no applet then just add newAppObj.
        if windowObj.qteAppletSplitter.count() == 0:
            windowObj.qteAppletSplitter.qteAddWidget(newAppObj)
            return

        # If no oldAppObj was specified use the currently active one
        # instead. Do not use qteActiveApplet to determine it, though,
        # because it may point to a mini buffer. If it is, then we
        # need the last active Qtmacs applet. In either case, the
        # qteNextApplet method will take care of these distinctions.
        if oldAppObj is None:
            oldAppObj = self.qteNextApplet(numSkip=0, windowObj=windowObj)

        # Sanity check: the applet to replace must exist.
        if oldAppObj is None:
            msg = 'Applet to replace does not exist.'
            self.qteLogger.error(msg, stack_info=True)
            return

        # Sanity check: do nothing if the old- and new applet are the
        # same.
        if newAppObj is oldAppObj:
            return

        # Sanity check: do nothing if both applets are already
        # visible.
        if oldAppObj.qteIsVisible() and newAppObj.qteIsVisible():
            return

        # Search for the splitter that contains 'oldAppObj'.
        split = self._qteFindAppletInSplitter(oldAppObj,
                                              windowObj.qteAppletSplitter)
        if split is None:
            msg = ('Applet <b>{}</b> not replaced because it is not'
                   'in the layout.'.format(oldAppObj.qteAppletID()))
            self.qteLogger.warning(msg)
            return

        # Determine the position of oldAppObj inside the splitter.
        oldAppIdx = split.indexOf(oldAppObj)

        # Replace oldAppObj with newAppObj. To do so, first insert
        # newAppObj into the splitter at the position of oldAppObj and
        # then remove oldAppObj by re-parenting it and making it
        # invisible.
        split.qteInsertWidget(oldAppIdx, newAppObj)
        oldAppObj.hide(True)

    @type_check
    def qteRemoveAppletFromLayout(self, applet: (QtmacsApplet, str)):
        """
        Remove ``applet`` from the window layout.

        This method removes ``applet`` and implicitly deletes
        obsolete (ie. half-full) splitters in the process. If
        ``applet`` is the only visible applet in the layout then it
        will be replaced with the first invisible applet. If no
        invisible applets are left then the method does nothing.

        The ``applet`` parameter can either be an instance of
        ``QtmacsApplet`` or a string denoting an applet ID. In the
        latter case the ``qteGetAppletHandle`` method is used to fetch
        the respective applet instance.

        If ``applet`` does not refer to an existing applet then
        nothing happens.

        |Args|

        * ``applet`` (**QtmacsApplet**, **str**): the applet to remove
          from the layout.

        |Returns|

        * **None**

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        # If ``applet`` was specified by its ID (ie. a string) then
        # fetch the associated ``QtmacsApplet`` instance. If
        # ``applet`` is already an instance of ``QtmacsApplet`` then
        # use it directly.
        if isinstance(applet, str):
            appletObj = self.qteGetAppletHandle(applet)
        else:
            appletObj = applet

        # Return immediately if the applet does not exist in any splitter.
        for window in self._qteWindowList:
            split = self._qteFindAppletInSplitter(
                appletObj, window.qteAppletSplitter)
            if split is not None:
                break
        if split is None:
            return

        # If the applet lives in the main splitter and is the only
        # widget there it must be replaced with another applet. This
        # case needs to be handled separately from the other options
        # because every other splitter will always contain exactly two
        # items (ie. two applets, two splitters, or one of each).
        if (split is window.qteAppletSplitter) and (split.count() == 1):
            # Remove the existing applet object from the splitter and
            # hide it.
            split.widget(0).hide(True)

            # Get the next available applet to focus on. Try to find a
            # visible applet in the current window, and if none exists
            # then pick the first invisible one. If there is neither
            # a visible nor an invisible applet left then do nothing.
            nextApp = self.qteNextApplet(windowObj=window)
            if nextApp is None:
                nextApp = self.qteNextApplet(skipInvisible=False,
                                             skipVisible=True)
                if nextApp is None:
                    return

            # Ok, we found an applet to show.
            split.qteAddWidget(nextApp)
            return

        # ------------------------------------------------------------
        # If we got until here we know that the splitter (root or not)
        # contains (at least) two elements. Note: if it contains more
        # than two elements then there is a bug somewhere.
        # ------------------------------------------------------------

        # Find the index of the object inside the splitter.
        appletIdx = split.indexOf(appletObj)

        # Detach the applet from the splitter and make it invisible.
        appletObj.hide(True)

        # Verify that really only one additional element is left in
        # the splitter. If not, then something is wrong.
        if split.count() != 1:
            msg = ('Splitter has <b>{}</b> elements left instead of'
                   ' exactly one.'.format(split.count()))
            self.qteLogger.warning(msg)

        # Get a reference to the other widget in the splitter (either
        # a QtmacsSplitter or a QtmacsApplet).
        otherWidget = split.widget(0)

        # Is the other widget another splitter?
        if otherWidget._qteAdmin.widgetSignature == '__QtmacsLayoutSplitter__':
            # Yes, ``otherWidget`` is a QtmacsSplitter object,
            # therefore shift all its widgets over to the current
            # splitter.
            for ii in range(otherWidget.count()):
                # Get the next widget from that splitter. Note that we
                # always pick the widget at the 0'th position because
                # the splitter will re-index the remaining widgets
                # after each removal.
                obj = otherWidget.widget(0)
                if appletIdx == 0:
                    split.qteAddWidget(obj)
                else:
                    split.qteInsertWidget(1 + ii, obj)

            # Delete the child splitter.
            otherWidget.setParent(None)
            otherWidget.close()
        else:
            # No, ``otherWidget`` is a QtmacsApplet, therefore move it
            # to the parent splitter and delete the current one,
            # unless 'split' is the root splitter in which case
            # nothing happens.
            if split is not window.qteAppletSplitter:
                otherWidget.qteReparent(split.parent())
                split.setParent(None)
                split.close()

    @type_check
    def qteKillApplet(self, appletID: str):
        """
        Destroy the applet with ID ``appletID``.

        This method removes ``appletID`` from Qtmacs permanently - no
        questions asked. It is the responsibility of the (macro)
        programmer to use it responsibly.

        If the applet was visible then the method also takes care of
        replacing with the next invisible applet, if one is available.

        If ``appletID`` does not refer to a valid applet then nothing
        happens.

        |Args|

        * ``appletID`` (**str**): name of applet to be destroyed.

        |Returns|

        * **None**

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        # Compile list of all applet IDs.
        ID_list = [_.qteAppletID() for _ in self._qteAppletList]

        if appletID not in ID_list:
            # Do nothing if the applet does not exist.
            return
        else:
            # Get a reference to the actual applet object based on the
            # name.
            idx = ID_list.index(appletID)
            appObj = self._qteAppletList[idx]

        # Mini applets are killed with a special method.
        if self.qteIsMiniApplet(appObj):
            self.qteKillMiniApplet()
            return

        # Inform the applet that it is about to be killed.
        appObj.qteToBeKilled()

        # Determine the window of the applet.
        window = appObj.qteParentWindow()

        # Get the previous invisible applet (*may* come in handy a few
        # lines below).
        newApplet = self.qteNextApplet(numSkip=-1, skipInvisible=False,
                                       skipVisible=True)

        # If there is no invisible applet available, or the only available
        # applet is the one to be killed, then set newApplet to None.
        if (newApplet is None) or (newApplet is appObj):
            newApplet = None
        else:
            self.qteReplaceAppletInLayout(newApplet, appObj, window)

        # Ensure that _qteActiveApplet does not point to the applet
        # to be killed as it will otherwise result in a dangling
        # pointer.
        if self._qteActiveApplet is appObj:
            self._qteActiveApplet = newApplet

        # Remove the applet object from the applet list.
        self.qteLogger.debug('Kill applet: <b>{}</b>'.format(appletID))
        self._qteAppletList.remove(appObj)

        # Close the applet and schedule it for destruction. Explicitly
        # call the sip.delete() method to ensure that all signals are
        # *immediately* disconnected, as otherwise there is a good
        # chance that Qtmacs segfaults if Python/Qt thinks the slots
        # are still connected when really the object does not exist
        # anymore.
        appObj.close()
        sip.delete(appObj)

    @type_check
    def qteRunHook(self, hookName: str, msgObj: QtmacsMessage=None):
        """
        Trigger the hook named ``hookName`` and pass on ``msgObj``.

        This will call all slots associated with ``hookName`` but
        without calling the event loop in between. Therefore, if
        one slots changes the state of the GUI, every subsequent slot
        may have difficulties determining the actual state of the GUI
        using Qt accessor functions. It is thus usually a good idea
        to either avoid manipulating the GUI directly, or call macros
        because Qtmacs will always run the event loop in between any
        two macros.

        .. note: the slots are executed in the order in which they
          were registered via ``qteConnectHook``, but there is no
          guarantee that this is really so. However, it is guaranteed
          that all slots will be triggered, even if some raise an error
          during the execution.

        |Args|

        * ``hookName`` (**str**): the name of the hook to trigger.
        * ``msgObj`` (**QtmacsMessage**): data passed to the function.

        |Returns|

        * **None**

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        # Shorthand.
        reg = self._qteRegistryHooks

        # Do nothing if there are not recipients for the hook.
        if hookName not in reg:
            return

        # Create an empty ``QtmacsMessage`` object if none was provided.
        if msgObj is None:
            msgObj = QtmacsMessage()

        # Add information about the hook that will deliver ``msgObj``.
        msgObj.setHookName(hookName)

        # Try to call each slot. Intercept any errors but ensure that
        # really all slots are called, irrespective of how many of them
        # raise an error during execution.
        for fun in reg[hookName]:
            try:
                fun(msgObj)
            except Exception as err:
                # Format the error message.
                msg = '<b>{}</b>-hook function <b>{}</b>'.format(
                    hookName, str(fun)[1:-1])
                msg += " did not execute properly."
                if isinstance(err, QtmacsArgumentError):
                    msg += '<br/>' + str(err)

                # Log the error.
                self.qteLogger.exception(msg, exc_info=True, stack_info=True)

    @type_check
    def qteConnectHook(self, hookName: str,
                       slot: (types.FunctionType, types.MethodType)):
        """
        Connect the method or function ``slot`` to ``hookName``.

        |Args|

        * ``hookName`` (**str**): name of the hook.
        * ``slot`` (**function**, **method**): the routine to execute
          when the hook triggers.

        |Returns|

        * **None**

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        # Shorthand.
        reg = self._qteRegistryHooks
        if hookName in reg:
            reg[hookName].append(slot)
        else:
            reg[hookName] = [slot]

    @type_check
    def qteDisconnectHook(self, hookName: str,
                          slot: (types.FunctionType, types.MethodType)):
        """
        Disconnect ``slot`` from ``hookName``.

        If ``hookName`` does not exist, or ``slot`` is not connected
        to ``hookName`` then return **False**, otherwise disassociate
        ``slot`` with ``hookName`` and return **True**.

        |Args|

        * ``hookName`` (**str**): name of the hook.
        * ``slot`` (**function**, **method**): the routine to
          execute when the hook triggers.

        |Returns|

        * **bool**: **True** if ``slot`` was disconnected from ``hookName``,
          and **False** in all other cases.

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        # Shorthand.
        reg = self._qteRegistryHooks

        # Return immediately if no hook with that name exists.
        if hookName not in reg:
            msg = 'There is no hook called <b>{}</b>.'
            self.qteLogger.info(msg.format(hookName))
            return False

        # Return immediately if the ``slot`` is not connected to the hook.
        if slot not in reg[hookName]:
            msg = 'Slot <b>{}</b> is not connected to hook <b>{}</b>.'
            self.qteLogger.info(msg.format(str(slot)[1:-1], hookName))
            return False

        # Remove ``slot`` from the list.
        reg[hookName].remove(slot)

        # If the list is now empty, then remove it altogether.
        if len(reg[hookName]) == 0:
            reg.pop(hookName)
        return True

    @type_check
    def qteImportModule(self, fileName: str):
        """
        Import ``fileName`` at run-time.

        If ``fileName`` has no path prefix then it must be in the
        standard Python module path. Relative path names are possible.

        |Args|

        * ``fileName`` (**str**): file name (with full path) of module
          to import.

        |Returns|

        * **module**: the imported Python module, or **None** if an
            error occurred.

        |Raises|

        * **None**
        """
        # Split the absolute file name into the path- and file name.
        path, name = os.path.split(fileName)
        name, ext = os.path.splitext(name)

        # If the file name has a path prefix then search there, other
        # search the default paths for Python.
        if path == '':
            path = sys.path
        else:
            path = [path]

        # Try to locate the module.
        try:
            fp, pathname, desc = imp.find_module(name, path)
        except ImportError:
            msg = 'Could not find module <b>{}</b>.'.format(fileName)
            self.qteLogger.error(msg)
            return None

        # Try to import the module.
        try:
            mod = imp.load_module(name, fp, pathname, desc)
            return mod
        except ImportError:
            msg = 'Could not import module <b>{}</b>.'.format(fileName)
            self.qteLogger.error(msg)
            return None
        finally:
            # According to the imp documentation the file pointer
            # should always be closed explicitly.
            if fp:
                fp.close()

    def qteMacroNameMangling(self, macroCls):
        """
        Convert the class name of a macro class to macro name.

        The name mangling inserts a '-' character after every capital
        letter and then lowers the entire string.

        Example: if the class name of ``macroCls`` is 'ThisIsAMacro'
        then this method will return 'this-is-a-macro', ie. every
        capital letter (except the first) will be prefixed with a
        hyphen and changed to lower case.

        The method returns the name mangled macro name or **None**
        if an error occurred.

        |Args|

        * ``macroCls`` (**QtmacsMacro**): ``QtmacsMacro``- or derived
          class (not an instance!)

        |Returns|

        **str**: the name mangled string or **None** if an error occurred.

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        # Replace camel bump as hyphenated lower case string.
        macroName = re.sub(r"([A-Z])", r'-\1', macroCls.__name__)

        # If the first character of the class name was a
        # capital letter (likely) then the above substitution would have
        # resulted in a leading hyphen. Remove it.
        if macroName[0] == '-':
            macroName = macroName[1:]

        # Return the lower case string.
        return macroName.lower()

    @type_check
    def qteRegisterMacro(self, macroCls, replaceMacro: bool=False,
                         macroName: str=None):
        """
        Register a macro.

        If ``macroName`` is **None** then its named is deduced from
        its class name (see ``qteMacroNameMangling`` for details).

        Multiple macros with the same name can co-exist as long as
        their applet- and widget signatures, as reported by the
        ``qteAppletSignature`` and ``qteWidgetSignature`` methods,
        differ. If ``macroCls`` has the same name and signatures as an
        already registered macro then the ``replaceMacro`` flag
        decides:

        * **True**: the existing macro will be replaced for all
          applet- and widget signatures specified by the new macro
          ``macroCls``.
        * **False**: the ``macroCls`` will not be registered.

        The method returns **None** if an error occurred (eg. the
        macro constructor is faulty), or the macro name as a
        string. If a macro was already registered and not replaced
        (ie. ``replaceMacro``) then the macro name is returned
        nonetheless.

        .. note:: if an existing macro is replaced the old macro
           is not deleted (it probably should be, though).

        |Args|

        * ``macroCls`` (**QtmacsMacro**): QtmacsMacro or derived
          (not type checked!)
        * ``replaceMacro`` (**bool**): whether or not to replace
          an existing macro.
        * ``macroName`` (**str**): the name under which the macro
          should be registered.

        |Returns|

        **str**: the name of the just registered macro, or **None** if
          that failed.

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        # Check type of input arguments.
        if not issubclass(macroCls, QtmacsMacro):
            args = ('macroCls', 'class QtmacsMacro', inspect.stack()[0][3])
            raise QtmacsArgumentError(*args)

        # Try to instantiate the macro class.
        try:
            macroObj = macroCls()
        except Exception:
            msg = 'The macro <b>{}</b> has a faulty constructor.'
            msg = msg.format(macroCls.__name__)

            self.qteLogger.error(msg, stack_info=True)
            return None

        # The three options to determine the macro name, in order of
        # precedence, are: passed to this function, specified in the
        # macro constructor, name mangled.
        if macroName is None:
            # No macro name was passed to the function.
            if macroObj.qteMacroName() is None:
                # The macro has already named itself.
                macroName = self.qteMacroNameMangling(macroCls)
            else:
                # The macro name is inferred from the class name.
                macroName = macroObj.qteMacroName()

        # Let the macro know under which name it is known inside Qtmacs.
        macroObj._qteMacroName = macroName

        # Ensure the macro has applet signatures.
        if len(macroObj.qteAppletSignature()) == 0:
            msg = 'Macro <b>{}</b> has no applet signatures.'.format(macroName)
            self.qteLogger.error(msg, stack_info=True)
            return None

        # Ensure the macro has widget signatures.
        if len(macroObj.qteWidgetSignature()) == 0:
            msg = 'Macro <b>{}</b> has no widget signatures.'.format(macroName)
            self.qteLogger.error(msg, stack_info=True)
            return None

        # Flag to indicate that at least one new macro type was
        # registered.
        anyRegistered = False

        # Iterate over all applet signatures.
        for app_sig in macroObj.qteAppletSignature():
            # Iterate over all widget signatures.
            for wid_sig in macroObj.qteWidgetSignature():
                # Infer the macro name from the class name of the
                # passed macro object.
                macroNameInternal = (macroName, app_sig, wid_sig)

                # If a macro with this name already exists then either
                # replace it, or skip the registration process for the
                # new one.
                if macroNameInternal in self._qteRegistryMacros:
                    if replaceMacro:
                        # Remove existing macro.
                        tmp = self._qteRegistryMacros.pop(macroNameInternal)
                        msg = 'Replacing existing macro <b>{}</b> with new {}.'
                        msg = msg.format(macroNameInternal, macroObj)
                        self.qteLogger.info(msg)
                        tmp.deleteLater()
                    else:
                        msg = 'Macro <b>{}</b> already exists (not replaced).'
                        msg = msg.format(macroNameInternal)
                        self.qteLogger.info(msg)
                        # Macro was not registered for this widget
                        # signature.
                        continue

                # Add macro object to the registry.
                self._qteRegistryMacros[macroNameInternal] = macroObj
                msg = ('Macro <b>{}</b> successfully registered.'
                       .format(macroNameInternal))
                self.qteLogger.info(msg)
                anyRegistered = True

        # Return the name of the macro, irrespective of whether or not
        # it is a newly created macro, or if the old macro was kept
        # (in case of a name conflict).
        return macroName

    @type_check
    def qteIsMacroRegistered(self, macroName: str,
                             widgetObj: QtGui.QWidget=None):
        """
        Return **True** if a macro with name ``macroName`` exists.

        If ``widgetObj`` is **None** then only the macro name is
        matched. Otherwise, only macros that are compatible with
        ``widgetObj`` are returned.


        |Args|

        * ``macroName`` (**str**): name of macro.
        * ``widgetObj`` (**QWidget**): widget with which the macro
          must be compatible.

        |Returns|

        * **bool**: whether or not a compatible macro exists.

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        if widgetObj is None:
            # Ignore the applet- and widget signature and simply check
            # if a macro with the desired name exists.
            macroList = [_ for _ in self._qteRegistryMacros
                         if _[0] == macroName]
            if len(macroList) > 0:
                return True
            else:
                return False
        else:
            # Take the applet- and widget signature into account.
            macroObj = self.qteGetMacroObject(macroName, widgetObj)
            if macroObj is None:
                return False
            else:
                return True

    @type_check
    def qteGetMacroObject(self, macroName: str, widgetObj: QtGui.QWidget):
        """
        Return macro that is name- and signature compatible with
        ``macroName`` and ``widgetObj``.

        The method considers all macros with name ``macroName`` and
        returns the one that matches 'best'. To determine this best
        match, the applet-and widget signatures of the macro are
        compared to those of ``widgetObj`` and picked in the following
        order:

        1. Applet- and widget signature of both match.
        2. Widget signature matches, applet signature in macro is "*"
        3. Applet signature matches, widget signature in macro is "*"
        4. Macro reports "*" for both its applet- and widget signature.

        If the macro does not fit any of these four criteria, then no
        compatible macro is available and the method returns **None**.

        |Args|

        * ``macroName`` (**str**): name of macro.
        * ``widgetObj`` (**QWidget**): widget for which a compatible
          macro is sought.

        |Returns|

        * **QtmacsMacro**: best matching macro, or **None**.

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        # Determine the applet- and widget signature. This is trivial
        # if the widget was registered with Qtmacs because its
        # '_qteAdmin' attribute will provide this information. If, on
        # the other hand, the widget was not registered with Qtmacs
        # then it has no signature, yet its parent applet must because
        # every applet has one. The only exception when the applet
        # signature is therefore when there are no applets to begin
        # with, ie. the the window is empty.
        if hasattr(widgetObj, '_qteAdmin'):
            app_signature = widgetObj._qteAdmin.appletSignature
            wid_signature = widgetObj._qteAdmin.widgetSignature

            # Return immediately if the applet signature is None
            # (should be impossible).
            if app_signature is None:
                msg = 'Applet has no signature.'
                self.qteLogger.error(msg, stack_info=True)
                return None
        else:
            wid_signature = None
            app = qteGetAppletFromWidget(widgetObj)
            if app is None:
                app_signature = None
            else:
                app_signature = app._qteAdmin.appletSignature

        # Find all macros with name 'macroName'. This will produce a list of
        # tuples with entries (macroName, app_sig, wid_sig).
        name_match = [m for m in self._qteRegistryMacros if m[0] == macroName]

        # Find all macros with a compatible applet signature. This is
        # produce another list of tuples with the same format as
        # the name_match list (see above).
        app_sig_match = [_ for _ in name_match if _[1] in (app_signature, '*')]

        if wid_signature is None:
            wid_sig_match = [_ for _ in app_sig_match if _[2] == '*']
        else:
            # Find all macros with a compatible widget signature. This is
            # a list of tuples, each tuple consisting of (macroName,
            # app_sig, wid_sig).
            wid_sig_match = [_ for _ in app_sig_match
                             if _[2] in (wid_signature, '*')]

        # Pick a macro.
        if len(wid_sig_match) == 0:
            # No macro is compatible with either the applet- or widget
            # signature.
            return None
        elif len(wid_sig_match) == 1:
            match = wid_sig_match[0]
            # Exactly one macro is compatible with either the applet-
            # or widget signature.
            return self._qteRegistryMacros[match]
        else:
            # Found multiple matches. For any given macro 'name',
            # applet signature 'app', and widget signature 'wid' there
            # can be at most four macros in the list: *:*:name,
            # wid:*:name, *:app:name, and wid:app:name.

            # See if there is a macro for which both the applet and
            # widget signature match.
            tmp = [match for match in wid_sig_match if (match[1] != '*')
                   and (match[2] != '*')]
            if len(tmp) > 0:
                match = tmp[0]
                return self._qteRegistryMacros[match]

            # See if there is a macro with a matching widget signature.
            tmp = [match for match in wid_sig_match if match[2] != '*']
            if len(tmp) > 0:
                match = tmp[0]
                return self._qteRegistryMacros[match]

            # See if there is a macro with a matching applet signature.
            tmp = [match for match in wid_sig_match if match[1] != '*']
            if len(tmp) > 0:
                match = tmp[0]
                return self._qteRegistryMacros[match]

            # At this point only one possibility is left, namely a
            # generic macro that is applicable to arbitrary applets
            # and widgets, eg. NextApplet.
            tmp = [match for match in wid_sig_match if (match[1] == '*')
                   and (match[2] == '*')]
            if len(tmp) > 0:
                match = tmp[0]
                return self._qteRegistryMacros[match]

            # This should be impossible.
            msg = 'No compatible macro found - should be impossible.'
            self.qteLogger.error(msg, stack_info=True)

    @type_check
    def qteGetAllMacroNames(self, widgetObj: QtGui.QWidget=None):
        """
        Return all macro names known to Qtmacs as a list.

        If ``widgetObj`` is **None** then the names of all registered
        macros are returned as a tuple. Otherwise, only those macro
        compatible with ``widgetObj`` are returned. See
        ``qteGetMacroObject`` for the definition of a compatible
        macro.

        |Args|

        * ``widgetObj`` (**QWidget**): widget with which the macros
          must be compatible.

        |Returns|

        * **tuple**: tuple of macro names.

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        # The keys of qteRegistryMacros are (macroObj, app_sig,
        # wid_sig) tuples. Get them, extract the macro names, and
        # remove all duplicates.
        macro_list = tuple(self._qteRegistryMacros.keys())
        macro_list = [_[0] for _ in macro_list]
        macro_list = tuple(set(macro_list))

        # If no widget object was supplied then omit the signature
        # check and return the macro list verbatim.
        if widgetObj is None:
            return macro_list
        else:
            # Use qteGetMacroObject to compile a list of macros that
            # are compatible with widgetObj. This list contains
            # (macroObj, macroName, app_sig, wid_sig) tuples.
            macro_list = [self.qteGetMacroObject(macroName, widgetObj)
                          for macroName in macro_list]

            # Remove all elements where macroObj=None. This is the
            # case if no compatible macro with the specified name
            # could be found for widgetObj.
            macro_list = [_.qteMacroName() for _ in macro_list
                          if _ is not None]
            return macro_list

    @type_check
    def qteBindKeyGlobal(self, keysequence, macroName: str):
        """
        Associate ``macroName`` with ``keysequence`` in all current
        applets.

        This method will bind ``macroName`` to ``keysequence`` in the
        global key map and **all** local key maps. This also applies
        for all applets (and their constituent widgets) yet to be
        instantiated because they will inherit a copy of the global
        keymap.

        .. note::  This binding is signature independent.

        If the ``macroName`` was not registered the method returns
        **False**.

        The ``keysequence`` can be specified either as a string (eg
        '<ctrl>+x <ctrl>+f'), or a list of tuples containing the
        constants from the ``QtCore.Qt`` name space
        (eg. [(ControlModifier, Key_X), (ControlModifier, Key_F)]), or
        as a ``QtmacsKeysequence`` object.

        |Args|

        * ``keysequence`` (**str**, **list** of **tuples**,
          **QtmacsKeysequence**): key sequence to activate ``macroName``
          for specified ``widgetSignature``.
        * ``macroName`` (**str**): name of macro to associate with
          ``keysequence``.

        |Returns|

        **bool**: **True** if the binding was successful.

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        * **QtmacsKeysequenceError** if the provided ``keysequence``
          could not be parsed.
        """
        # Convert the key sequence into a QtmacsKeysequence object, or
        # raise an QtmacsOtherError if the conversion is impossible.
        keysequence = QtmacsKeysequence(keysequence)

        # Sanity check: the macro must have been registered
        # beforehand.
        if not self.qteIsMacroRegistered(macroName):
            msg = 'Cannot globally bind key to unknown macro <b>{}</b>.'
            msg = msg.format(macroName)
            self.qteLogger.error(msg, stack_info=True)
            return False

        # Insert/overwrite the key sequence and associate it with the
        # new macro.
        self._qteGlobalKeyMap.qteInsertKey(keysequence, macroName)

        # Now update the local key map of every applet. Note that
        # globally bound macros apply to every applet (hence the loop
        # below) and every widget therein (hence the "*" parameter for
        # the widget signature).
        for app in self._qteAppletList:
            self.qteBindKeyApplet(keysequence, macroName, app)
        return True

    @type_check
    def qteBindKeyApplet(self, keysequence, macroName: str,
                         appletObj: QtmacsApplet):
        """
        Bind ``macroName`` to all widgets in ``appletObj``.

        This method does not affect the key bindings of other applets,
        or other instances of the same applet.

        The ``keysequence`` can be specified either as a string (eg
        '<ctrl>+x <ctrl>+f'), or a list of tuples containing the
        constants from the ``QtCore.Qt`` name space
        (eg. [(ControlModifier, Key_X), (ControlModifier, Key_F)]), or
        as a ``QtmacsKeysequence`` object.

        |Args|

        * ``keysequence`` (**str**, **list** of **tuples**,
          **QtmacsKeysequence**):
          key sequence to activate ``macroName`` for specified
          ``widgetSignature``.
        * ``macroName`` (**str**): the macro to associated with
          ``keysequence``.
        * ``appletObj`` (**QtmacsApplet**): only widgets in this
          applet are affected.

        |Returns|

        * **bool**: whether or not at least one widget was
          successfully bound.

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        * **QtmacsKeysequenceError** if the provided ``keysequence``
          could not be parsed.
        """
        # Convert the key sequence into a QtmacsKeysequence object, or
        # raise a QtmacsKeysequenceError if the conversion is
        # impossible.
        keysequence = QtmacsKeysequence(keysequence)

        # Verify that Qtmacs knows a macro named 'macroName'.
        if not self.qteIsMacroRegistered(macroName):
            msg = ('Cannot bind key because the macro <b>{}</b> does'
                   'not exist.'.format(macroName))
            self.qteLogger.error(msg, stack_info=True)
            return False

        # Bind the key also to the applet itself because it can
        # receive keyboard events (eg. when it is empty).
        appletObj._qteAdmin.keyMap.qteInsertKey(keysequence, macroName)

        # Update the key map of every widget inside the applet.
        for wid in appletObj._qteAdmin.widgetList:
            self.qteBindKeyWidget(keysequence, macroName, wid)
        return True

    @type_check
    def qteBindKeyWidget(self, keysequence, macroName: str,
                         widgetObj: QtGui.QWidget):
        """
        Bind ``macroName`` to ``widgetObj`` and associate it with
        ``keysequence``.

        This method does not affect the key bindings of other applets
        and/or widgets and can be used to individualise the key
        bindings inside every applet instance and every widget inside
        that instance. Even multiple instances of the same applet type
        (eg. multiple text buffers) can all have individual key
        bindings.

        The ``keysequence`` can be specified either as a string (eg
        '<ctrl>+x <ctrl>+f'), or a list of tuples containing the
        constants from the ``QtCore.Qt`` name space
        (eg. [(ControlModifier, Key_X), (ControlModifier, Key_F)]), or
        as a ``QtmacsKeysequence`` object.

        |Args|

        * ``keysequence`` (**str**, **list** of **tuples**,
          **QtmacsKeysequence**):
          key sequence to activate ``macroName`` for specified
          ``widgetSignature``.
        * ``macroName`` (**str**): the macro to associated with
          ``keysequence``.
        * ``widgetObj`` (**QWidget**): determines which widgets
          signature to use.

        |Returns|

        * **bool**: whether or not at least one widget was
            successfully bound.

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        * **QtmacsKeysequenceError** if the provided ``keysequence``
          could not be parsed.
        * **QtmacsOtherError** if ``widgetObj`` was not added with
          ``qteAddWidget``.
        """
        # Convert the key sequence into a QtmacsKeysequence object, or
        # raise an QtmacsKeysequenceError if the conversion is
        # impossible.
        keysequence = QtmacsKeysequence(keysequence)

        # Check type of input arguments.
        if not hasattr(widgetObj, '_qteAdmin'):
            msg = '<widgetObj> was probably not added with <qteAddWidget>'
            msg += ' method because it lacks the <_qteAdmin> attribute.'
            raise QtmacsOtherError(msg)

        # Verify that Qtmacs knows a macro named 'macroName'.
        if not self.qteIsMacroRegistered(macroName):
            msg = ('Cannot bind key to unknown macro <b>{}</b>.'
                   .format(macroName))
            self.qteLogger.error(msg, stack_info=True)
            return False

        # Associate 'keysequence' with 'macroName' for 'widgetObj'.
        try:
            widgetObj._qteAdmin.keyMap.qteInsertKey(keysequence, macroName)
        except AttributeError:
            msg = 'Received an invalid macro object.'
            self.qteLogger.error(msg, stack_info=True)
            return False
        return True

    @type_check
    def qteUnbindKeyApplet(self, applet: (QtmacsApplet, str), keysequence):
        """
        Remove ``keysequence`` bindings from all widgets inside ``applet``.

        This method does not affect the key bindings of other applets,
        or different instances of the same applet.

        The ``keysequence`` can be specified either as a string (eg
        '<ctrl>+x <ctrl>+f'), or a list of tuples containing the
        constants from the ``QtCore.Qt`` name space
        (eg. [(ControlModifier, Key_X), (ControlModifier, Key_F)]), or
        as a ``QtmacsKeysequence`` object.

        The ``applet`` parameter can either be an instance of
        ``QtmacsApplet`` or a string denoting an applet ID. In the
        latter case the ``qteGetAppletHandle`` method is used to fetch
        the respective applet instance.

        If ``applet`` does not refer to an existing applet then
        nothing happens.

        |Args|

        * ``applet`` (**QtmacsApplet**, **str**): only widgets in this
          applet are affected.
        * ``keysequence`` (**str**, **list** of **tuples**,
          **QtmacsKeysequence**): the key sequence to remove.

        |Returns|

        * **None**

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        * **QtmacsKeysequenceError** if the provided ``keysequence``
          could not be parsed.
        """
        # If ``applet`` was specified by its ID (ie. a string) then
        # fetch the associated ``QtmacsApplet`` instance. If
        # ``applet`` is already an instance of ``QtmacsApplet`` then
        # use it directly.
        if isinstance(applet, str):
            appletObj = self.qteGetAppletHandle(applet)
        else:
            appletObj = applet

        # Return immediately if the appletObj is invalid.
        if appletObj is None:
            return

        # Convert the key sequence into a QtmacsKeysequence object, or
        # raise a QtmacsKeysequenceError if the conversion is
        # impossible.
        keysequence = QtmacsKeysequence(keysequence)

        # Remove the key sequence from the applet window itself.
        appletObj._qteAdmin.keyMap.qteRemoveKey(keysequence)

        for wid in appletObj._qteAdmin.widgetList:
            self.qteUnbindKeyFromWidgetObject(keysequence, wid)

    @type_check
    def qteUnbindKeyFromWidgetObject(self, keysequence,
                                     widgetObj: QtGui.QWidget):
        """
        Disassociate the macro triggered by ``keysequence`` from
        ``widgetObj``.

        The ``keysequence`` can be specified either as a string (eg
        '<ctrl>+x <ctrl>+f'), or a list of tuples containing the
        constants from the ``QtCore.Qt`` name space
        (eg. [(ControlModifier, Key_X), (ControlModifier, Key_F)]), or
        as a ``QtmacsKeysequence`` object.

        This method does not affect the key bindings of other applets.

        |Args|

        * ``keysequence`` (**str**, **list** of **tuples**,
          **QtmacsKeysequence**):
          key sequence to activate ``macroName`` for specified
          ``widgetSignature``.
        * ``widgetObj`` (**QWidget**): determines which widgets
          signature to use.

        |Returns|

        * **None**

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        * **QtmacsKeysequenceError** if the provided ``keysequence``
          could not be parsed.
        * **QtmacsOtherError** if ``widgetObj`` was not added with
          ``qteAddWidget``.
        """
        # Convert the key sequence into a QtmacsKeysequence object, or
        # raise an QtmacsKeysequenceError if the conversion is
        # impossible.
        keysequence = QtmacsKeysequence(keysequence)

        # Check type of input arguments.
        if not hasattr(widgetObj, '_qteAdmin'):
            msg = '<widgetObj> was probably not added with <qteAddWidget>'
            msg += ' method because it lacks the <_qteAdmin> attribute.'
            raise QtmacsOtherError(msg)

        # Remove the key sequence from the local key maps.
        widgetObj._qteAdmin.keyMap.qteRemoveKey(keysequence)

    @type_check
    def qteUnbindAllFromApplet(self, applet: (QtmacsApplet, str)):
        """
        Restore the global key-map for all widgets inside ``applet``.

        This method effectively resets the key map of all widgets to
        the state they would be in if the widgets were newly
        instantiated right now.

        The ``applet`` parameter can either be an instance of
        ``QtmacsApplet`` or a string denoting an applet ID. In the
        latter case the ``qteGetAppletHandle`` method is used to fetch
        the respective applet instance.

        If ``applet`` does not refer to an existing applet then
        nothing happens.

        |Args|

        * ``applet`` (**QtmacsApplet**, **str**): only widgets in this
          applet are affected.

        |Returns|

        * **None**

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        # If ``applet`` was specified by its ID (ie. a string) then
        # fetch the associated ``QtmacsApplet`` instance. If
        # ``applet`` is already an instance of ``QtmacsApplet`` then
        # use it directly.
        if isinstance(applet, str):
            appletObj = self.qteGetAppletHandle(applet)
        else:
            appletObj = applet

        # Return immediately if the appletObj is invalid.
        if appletObj is None:
            return

        # Remove the key sequence from the applet window itself.
        appletObj._qteAdmin.keyMap = self.qteCopyGlobalKeyMap()

        # Restore the global key-map for every widget.
        for wid in appletObj._qteAdmin.widgetList:
            wid._qteAdmin.keyMap = self.qteCopyGlobalKeyMap()

    @type_check
    def qteUnbindAllFromWidgetObject(self, widgetObj: QtGui.QWidget):
        """
        Reset the local key-map of ``widgetObj`` to the current global
        key-map.

        |Args|

        * ``widgetObj`` (**QWidget**): determines which widgets
          signature to use.

        |Returns|

        * **None**

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        * **QtmacsOtherError** if ``widgetObj`` was not added with
          ``qteAddWidget``.
        """
        # Check type of input arguments.
        if not hasattr(widgetObj, '_qteAdmin'):
            msg = '<widgetObj> was probably not added with <qteAddWidget>'
            msg += ' method because it lacks the <_qteAdmin> attribute.'
            raise QtmacsOtherError(msg)

        # Install the global key-map for this widget.
        widgetObj._qteAdmin.keyMap = self.qteCopyGlobalKeyMap()

    def qteCopyGlobalKeyMap(self):
        """
        Return a copy of the global key map, not a reference.

        |Args|

        * **None**

        |Returns|

        * **QtmacsKeymap**: a copy of the global key map object.

        |Raises|

        * **None**
        """
        return QtmacsKeymap(self._qteGlobalKeyMap)

    def _qteGlobalKeyMapByReference(self):
        """
        Return a reference of the global key map, not a copy.

        |Args|

        * **None**

        |Returns|

        * **QtmacsKeymap**: a copy of the global key map object.

        |Raises|

        * **None**
        """
        return self._qteGlobalKeyMap

    @type_check
    def qteRegisterApplet(self, cls, replaceApplet: bool=False):
        """
        Register ``cls`` as an applet.

        The name of the applet is the class name of ``cls``
        itself. For instance, if the applet was defined and registered
        as

            class NewApplet17(QtmacsApplet):
                ...

            app_name = qteRegisterApplet(NewApplet17)

        then the applet will be known as *NewApplet17*, which is also
        returned in ``app_name``.

        If an applet with this name already exists then
        ``replaceApplet`` decides whether the registration will
        overwrite the existing definition or ignore the registration
        request altogether. In the first case, none of the already
        instantiated applets will be affected, only newly created ones
        will use the new definition.

        .. note:: this method expects a *class*, not an instance.

        |Args|

        * ``cls`` (**class QtmacsApplet**): this must really be a class,
          not an instance.
        * ``replaceApplet`` (**bool**): if applet with same name exists,
          then replace it.

        |Returns|

        * **str**: name under which the applet was registered with Qtmacs.

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        # Check type of input arguments.
        if not issubclass(cls, QtmacsApplet):
            args = ('cls', 'class QtmacsApplet', inspect.stack()[0][3])
            raise QtmacsArgumentError(*args)

        # Extract the class name as string, because this is the name
        # under which the applet will be known.
        class_name = cls.__name__

        # Issue a warning if an applet with this name already exists.
        if class_name in self._qteRegistryApplets:
            msg = 'The original applet <b>{}</b>'.format(class_name)
            if replaceApplet:
                msg += ' was redefined.'
                self.qteLogger.warning(msg)
            else:
                msg += ' was not redefined.'
                self.qteLogger.warning(msg)
                return class_name

        # Execute the classmethod __qteRegisterAppletInit__ to
        # allow the applet to make global initialisations that do
        # not depend on a particular instance, eg. the supported
        # file types.
        cls.__qteRegisterAppletInit__()

        # Add the class (not instance!) to the applet registry.
        self._qteRegistryApplets[class_name] = cls
        self.qteLogger.info('Applet <b>{}</b> now registered.'
                            .format(class_name))
        return class_name

    def qteGetAllAppletIDs(self):
        """
        Return a tuple of all applet IDs currently active in Qtmacs.

        |Args|

        * **None**

        |Returns|

        * **tuple**: IDs of all open applets.

        |Raises|

        * **None**
        """
        return tuple(_.qteAppletID() for _ in self._qteAppletList)

    def qteGetAllAppletNames(self):
        """
        Return a tuple of all registered applet names.

        |Args|

        * **None**

        |Returns|

        * **tuple**: name of applets.

        |Raises|

        * **None**
        """
        return tuple(self._qteRegistryApplets.keys())

    @type_check
    def qteGetAppletHandle(self, appletID: str):
        """
        Return a handle to ``appletID``.

        If no applet with ID ``appletID`` exists then **None** is
        returned.

        |Args|

        * ``appletID`` (**str**): ID of applet.

        |Returns|

        * **QtmacsApplet**: handle to applet with ID ``appletID``.

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        # Compile list of applet Ids.
        id_list = [_.qteAppletID() for _ in self._qteAppletList]

        # If one of the applets has ``appletID`` then return a
        # reference to it.
        if appletID in id_list:
            idx = id_list.index(appletID)
            return self._qteAppletList[idx]
        else:
            return None

    @type_check
    def qteMakeAppletActive(self, applet: (QtmacsApplet, str)):
        """
        Make ``applet`` visible and give it the focus.

        If ``applet`` is not yet visible it will replace the
        currently active applet, otherwise only the focus will shift.

        The ``applet`` parameter can either be an instance of
        ``QtmacsApplet`` or a string denoting an applet ID. In the
        latter case the ``qteGetAppletHandle`` method is used to fetch
        the respective applet instance.

        |Args|

        * ``applet`` (**QtmacsApplet**, **str**): the applet to activate.

        |Returns|

        * **bool**: whether or not an applet was activated.

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        # If ``applet`` was specified by its ID (ie. a string) then
        # fetch the associated ``QtmacsApplet`` instance. If
        # ``applet`` is already an instance of ``QtmacsApplet`` then
        # use it directly.
        if isinstance(applet, str):
            appletObj = self.qteGetAppletHandle(applet)
        else:
            appletObj = applet

        # Sanity check: return if the applet does not exist.
        if appletObj not in self._qteAppletList:
            return False

        # If ``appletObj`` is a mini applet then double check that it
        # is actually installed and visible. If it is a conventional
        # applet then insert it into the layout.
        if self.qteIsMiniApplet(appletObj):
            if appletObj is not self._qteMiniApplet:
                self.qteLogger.warning('Wrong mini applet. Not activated.')
                print(appletObj)
                print(self._qteMiniApplet)
                return False
            if not appletObj.qteIsVisible():
                appletObj.show(True)
        else:
            if not appletObj.qteIsVisible():
                # Add the applet to the layout by replacing the
                # currently active applet.
                self.qteReplaceAppletInLayout(appletObj)

        # Update the qteActiveApplet pointer. Note that the actual
        # focusing is done exclusively in the focus manager.
        self._qteActiveApplet = appletObj
        return True

    def qteCloseQtmacs(self):
        """
        Close Qtmacs.

        First kill all applets, then shut down Qtmacs.

        |Args|

        * **None**

        |Returns|

        * **None**

        |Raises|

        * **None**
        """
        # Announce the shutdown.
        msgObj = QtmacsMessage()
        msgObj.setSignalName('qtesigCloseQtmacs')
        self.qtesigCloseQtmacs.emit(msgObj)

        # Kill all applets and update the GUI.
        for appName in self.qteGetAllAppletIDs():
            self.qteKillApplet(appName)
        self._qteFocusManager()

        # Kill all windows and update the GUI.
        for window in self._qteWindowList:
            window.close()
        self._qteFocusManager()

        # Schedule QtmacsMain for deletion.
        self.deleteLater()

    @type_check
    def qteStatus(self, msg: str=None):
        """
        Dispatch ``msg`` via the ``qteStatus`` hook.

        |Args|

        * ``msg`` (**str**): the message to distribute.

        |Returns|

        * **None**

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        self.qteRunHook('qteStatus', QtmacsMessage(msg, None))

    @type_check
    def qteDefVar(self, varName: str, value, module=None, doc: str=None):
        """
        Define and document ``varName`` in an arbitrary name space.

        If ``module`` is **None** then ``qte_global`` will be used.

        .. warning: If the ``varName`` was already defined in
           ``module`` then its value and documentation are overwritten
           without warning.

        |Args|

        * ``varName`` (**str**): variable name.
        * ``value`` (**object**): arbitrary data to store.
        * ``module`` (**Python module**): the module in which the
          variable should be defined.
        * ``doc`` (**str**): documentation string for variable.

        |Returns|

        **bool**: **True** if ``varName`` could be defined in
          ``module``.

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        # Use the global name space per default.
        if module is None:
            module = qte_global

        # Create the documentation dictionary if it does not exist
        # already.
        if not hasattr(module, '_qte__variable__docstring__dictionary__'):
            module._qte__variable__docstring__dictionary__ = {}

        # Set the variable value and documentation string.
        setattr(module, varName, value)
        module._qte__variable__docstring__dictionary__[varName] = doc
        return True

    @type_check
    def qteGetVariableDoc(self, varName: str, module=None):
        """
        Retrieve documentation for ``varName`` defined in ``module``.

        If ``module`` is **None** then ``qte_global`` will be used.

        |Args|

        * ``varName`` (**str**): variable name.
        * ``module`` (**Python module**): the module in which the
          variable should be defined.

        |Returns|

        **str**: documentation string for ``varName``.

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        # Use the global name space per default.
        if module is None:
            module = qte_global

        # No documentation for the variable can exists if the doc
        # string dictionary is undefined.
        if not hasattr(module, '_qte__variable__docstring__dictionary__'):
            return None

        # If the variable is undefined then return **None**.
        if varName not in module._qte__variable__docstring__dictionary__:
            return None

        # Return the requested value.
        return module._qte__variable__docstring__dictionary__[varName]

    def qteEnableMacroProcessing(self):
        self._qteEventFilter.qteEnableMacroProcessing()

    def qteDisableMacroProcessing(self):
        self._qteEventFilter.qteDisableMacroProcessing()

    def qteEmulateKeypresses(self, keysequence):
        """
        Emulate the Qt key presses that define ``keysequence``.

        The method will put the keys into a queue and process them one
        by one once the event loop is idle, ie. the event loop
        executes all signals and macros associated with the emulated
        key press first before the next one is emulated.

        |Args|

        * ``keysequence`` (**QtmacsKeysequence**): the key sequence to
          emulate.

        |Returns|

        * **None**

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        # Convert the key sequence into a QtmacsKeysequence object, or
        # raise an QtmacsOtherError if the conversion is impossible.
        keysequence = QtmacsKeysequence(keysequence)
        key_list = keysequence.toQKeyEventList()

        # Do nothing if the key list is empty.
        if len(key_list) > 0:
            # Add the keys to the queue which the event timer will
            # process.
            for event in key_list:
                self._qteKeyEmulationQueue.append(event)

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
Provide ``QtmacsApplet``, the base class for all Qtmacs applets.

To implement an applet, subclass ``QtmacsApplet``, and treat it like
the ``QWidget`` it was derived from, with two notable exceptions:

1. ``show()`` and ``hide()`` do not work; use dedicated Qtmacs layout
   commands (eg. ``qteMakeWindowActive``) instead. This rule only
   applies to the applet, not to any widgets inside the applet.
2. All widget instances must be registered with ``qteAddWidget``.

Usage example::

    class HelloWorldApp(QtmacsApplet):
        \"\"\"
        A 'Hello world' applet.
        \"\"\"
        def __init__(self, appletID):
            # Initialise the base class.
            super().__init__(appletID)

            # Instantiate a QLabel and tell Qtmacs about it.
            label = QtGui.QLabel('Hello world.', parent=self)
            self.qteLabel = self.qteAddWidget(label)

Noteworthy facts about applets:

* Applets are only instantiated when ``qteNewWidget`` is called.
* Applets can have arbitrarily many instances, but their ``appletID``
  (a string) must be unique.

Applets always carry the following attributes:

* ``qteMain``: reference to ``QtmacsMain`` instance,
* ``qteLogger``: reference to the Qtmacs logging mechanism,
* ``qteVersionInformation``: instance of ``QtmacsVersionStructure``,
* ``_qteActiveWidget``: the widget currently active inside the applet.

The first three attributes are fixed for entire life of the applet,
whereas the last attribute is updated by Qtmacs and always points to
the active widget inside the applet (this may be **None**).

It is safe to use::

    from applet import QtmacsApplet
"""

import sip
import inspect
import importlib
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
QtmacsAdminStructure = qtmacs.auxiliary.QtmacsAdminStructure
QtmacsVersionStructure = qtmacs.auxiliary.QtmacsVersionStructure
qteIsQtmacsWidget = qtmacs.auxiliary.qteIsQtmacsWidget
qteGetAppletFromWidget = qtmacs.auxiliary.qteGetAppletFromWidget


class QtmacsApplet(QtGui.QWidget):
    """
    Base class for every Qtmacs (mini) applet.

    For all practical purposes this class should be considered a
    QWidget class that can be filled with arbitrary widgets in order
    to display the desired functionality. The main difference between
    this class and a native QWidget, again from a practical point of
    view, is that none of the widgets added with ``qteAddWidget`` will
    react to keyboard inputs. Instead, macros are required to
    implement this functionality.

    The methods of this class are almost exclusively interfaces to
    ``QtmacsMain`` to administrate the applet. Consequently, there
    should be no need to overload any of its existing methods.

    Every applet has the following three attributes available to them
    at run time:

    * ``qteMain``: reference to QtmacsMain instance (comes straight
      from the global variables).
    * ``qteLogger``: the Qtmacs wide logger (see ``logger`` module
      in Python standard library).
    * ``_qteActiveWidget``: the widget currently active inside the applet.
    * ``qteVersionInformation``: version information.

    |Args|

    * ``appletID`` (**str**): unique ID used by ``QtmacsMain`` to
      distinguish applets.

    |Raises|

    * **QtmacsArgumentError** if appletID is not a string.
    * **QtmacsOthertError** if the appletID is not unique.
    """
    @type_check
    def __init__(self, appletID: str):
        super().__init__()

        # Raise an error if an applet with the same ID already exists.
        if qte_global.qteMain.qteGetAppletHandle(appletID):
            msg = 'Applet with ID <b>{}</b> already exists'.format(appletID)
            raise QtmacsOtherError(msg)

        # Destroy the object when its close() method is called.
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # Install the admin structure that contains information about
        # this applet.
        self._qteAdmin = QtmacsAdminStructure(self, appletID=appletID)

        # Reference to QtmacsMain instance and its logger.
        self.qteMain = qte_global.qteMain
        self.qteLogger = self.qteMain.qteLogger

        # Version information for this applet.
        self.qteVersionInformation = QtmacsVersionStructure()

        # Give the widget a custom background color (I do not know how
        # to actually specify this color though).
        self.setAutoFillBackground(True)

        # The widget currently considered active inside this applet.
        self._qteActiveWidget = None

        # The currently active modes.
        self._qteModes = {}

        # The default applet signature is identical with the class name.
        self.qteSetAppletSignature(self.__class__.__name__)

    @classmethod
    def __qteRegisterAppletInit__(cls):
        """
        Triggered by ``qteRegisterApplet`` when the applet is registered.

        This method will only be executed once, namely when the applet
        is registered with Qtmacs via ``qteRegisterApplet``. It will
        *not* be called again for any instances of the class.

        The purpose of this method is to perform setup tasks that do
        not depend on a particular instance. Examples for this would
        be to update ``findFile_types`` in `qte_global.py` so that
        find-file know that this applet can deal with them, or to
        verify that the conditions for this applet are met (eg. check
        that third party modules and external libraries are
        available), or to initialise the the module name space of the
        object.

        If no such setup is required then it does not need to be
        overloaded (the default implementation does nothing).
        """
        pass

    def mousePressEvent(self, event):
        """
        Prevent mouse clicks from being propagated further.

        The sole purpose of this (stub) method is to declare the event
        handled to avoid calling the event handler more often than
        necessary. Without this method, Qt would generate another
        mouse event for the parent because applets themselves do not
        accept mouse clicks. Since the parent is likely another widget
        that does not accept the focus (eg. a QtmacsSplitter) there
        would be several calls to no avail until the top level window
        is reached.
        """
        pass

    def qteParentWindow(self):
        """
        Return a reference to the parent window.
        |Args|

        * **None**

        |Returns|

        * **QtmacsWindow**: the parent window.

        |Raises|

        * **None**
        """
        return self._qteAdmin.parentWindow

    def qteReparent(self, parent):
        """
        Re-parent the applet.

        This is little more then calling Qt's native ``setParent()``
        method but also updates the ``qteParentWindow`` handle. This
        method is usually called when the applet is added/removed from
        a splitter and thus requires re-parenting.

        |Args|

        * ``parent`` (**QWidget**): the new parent of this object.

        |Returns|

        * **None**

        |Raises|

        * **None**
        """

        # Set the new parent.
        self.setParent(parent)

        # If this parent has a Qtmacs structure then query it for the
        # parent window, otherwise set the parent to None.
        try:
            self._qteAdmin.parentWindow = parent.qteParentWindow()
        except AttributeError:
            self._qteAdmin.parentWindow = None
            # Sanity check:
            if parent:
                msg = 'Parent is neither None, nor does it have a'
                msg += 'qteParentWindow field --> bug'
                print(msg)

    @type_check
    def qteAddWidget(self, widgetObj: QtGui.QWidget, isFocusable: bool=True,
                     widgetSignature: str=None, autoBind: bool=True):
        """
        Augment the standard Qt ``widgetObj`` with Qtmacs specific fields.

        Example: from a programmers perspective there is no difference
        between::

            wid = QtGui.QTextEdit(self)

        and::

            wid = self.qteAddWidget(QtGui.QTextEdit(self))

        Both return a handle to a Qt widget (a ``QTextEdit`` in this
        case). However, the ``qteAddWidget`` adds the following fields
        to the object:

        * ``_qteAdmin``: this is an instance of the ``QtmacsAdminStructure``
          to tell Qtmacs how to treat the widget.
        * ``qteSignature``: an attribute that returns the signature of the
          widget and equals ``widgetSignature``. If no such signature was
          specified it defaults to the Qt internal name as a string, eg.
          for a push button this would be 'QPushButton'.
        * ``qteSetKeyFilterPolicy``: this points directly to the equally
          named method inside the _qteAdmin object. This is a convenience
          shortcut to avoid using the _qteAdmin structure directly in
          macro/applet code, because only Qtmacs itself should temper
          with it.

        |Args|

        * ``widgetObj`` (**QWidget**): any widget from the QtGui library.
        * ``isFocusable`` (**bool**): whether or not the widget can
          receive the focus.
        * ``widgetSignature`` (**str**): specify the widget signature
          (defaults to class name)
        * ``autoBind`` (**bool**): if **True** and ``widgetSignature``
          is a recognisable name (eg. **QTextEdit**) then automatically
          load the appropriate key-bindings for this widget.

        |Returns|

        * **QWidget**: handle to widget object (or **None** if it could
          not be added).

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        # Add a Qtmacs data structure to the widget to allow their
        # event administration. Note that, in all likelihood, the
        # widget is an arbitrary Qt widget (eg. QLineEdit,
        # QPushButton, etc).
        widgetObj._qteAdmin = QtmacsAdminStructure(
            self, isFocusable=isFocusable)
        widgetObj._qteAdmin.appletID = self._qteAdmin.appletID

        # Specify that this widget is not a QtmacsApplet.
        widgetObj._qteAdmin.isQtmacsApplet = False

        # Remember the signature of the applet containing this widget.
        widgetObj._qteAdmin.appletSignature = self.qteAppletSignature()

        # Set the widget signature. If none was specified, use the
        # class name (eg. QLineEdit).
        if widgetSignature is None:
            widgetObj._qteAdmin.widgetSignature = widgetObj.__class__.__name__
        else:
            widgetObj._qteAdmin.widgetSignature = widgetSignature

        # For convenience, as it is otherwise difficult for the macro
        # programmer to determine the widget signature used by Qtmacs.
        # Note: the "wo" is only a shorthand to avoid too long lines.
        wo = widgetObj
        wo.qteSignature = wo._qteAdmin.widgetSignature
        wo.qteSetKeyFilterPolicy = wo._qteAdmin.qteSetKeyFilterPolicy
        del wo

        # Add the widget to the widgetList of this QtmacsApplet.
        # Important: this MUST happen before macros and key-bindings are loaded
        # and bound automatically (see code below) because the method to
        # bind the keys will verify that the widget exists in ``widgetList``.
        self._qteAdmin.widgetList.append(widgetObj)

        # If a widget has a default key-bindings file then the global
        # dictionary ``default_widget_keybindings`` will contain its
        # name.
        default_bind = qte_global.default_widget_keybindings
        if autoBind and (widgetObj.qteSignature in default_bind):
            # Shorthand.
            module_name = default_bind[widgetObj.qteSignature]

            # Import the module with the default key-bindings for the
            # current widget type.
            try:
                mod = importlib.import_module(module_name)
            except ImportError:
                msg = ('Module <b>{}</b> could not be imported.'.format(
                       module_name))
                self.qteLogger.exception(msg, stack_info=True)
                return

            if hasattr(mod, 'install_macros_and_bindings'):
                # By convention, the module has an
                # install_macros_and_bindings method. If an error
                # occurs intercept it, but do not abort the method
                # since the error only relates to a failed attempt to
                # apply default key-bindings, not to register the
                # widget (the main purpose of this method).
                try:
                    mod.install_macros_and_bindings(widgetObj)
                except Exception:
                    msg = ('<b>install_macros_and_bindings</b> function'
                           ' in <b>{}</b> did not execute properly.')
                    msg = msg.format(module_name)
                    self.qteLogger.error(msg, stack_info=True)
            else:
                msg = ('Module <b>{}</b> has no '
                       '<b>install_macros_and_bindings</b>'
                       ' method'.format(module_name))
                self.qteLogger.error(msg)

        return widgetObj

    @type_check
    def qteSetAppletSignature(self, signature: str):
        """
        Specify the applet signature.

        This signature is used by Qtmacs at run time to determine
        which macros are compatible with the apple. Macros have an
        identically called method so that Qtmacs can determine which
        macros are compatible with which applets. This method is
        typically called only in the applet constructor, but changing
        the macro signature at run time, is possible.

        The signature must be a non-empty string and not contain the
        '*' symbol.

        Note: the default signature is the class name as a string,
        eg. if the applet class is called MyAppClass, then the initial
        macro signature is the string 'MyAppClass'.

        |Args|

        * ``signature`` (**str**): the signature of this applet to
          determine compatible macros run time.

        |Returns|

        * **None**

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        * **QtmacsOtherError** if the signature is empty or contains
          the '*' wildcard symbol.
        """
        if '*' in signature:
            raise QtmacsOtherError('The applet signature must not contain "*"')

        if signature == '':
            raise QtmacsOtherError('The applet signature must be non-empty')

        self._qteAdmin.appletSignature = signature

    def qteAppletSignature(self):
        """
        Return the signature (a string) of this applet.

        |Args|

        * **None**

        |Returns|

        * **str**: the signature of this applet as set by
            ``qteSetAppletSignature``

        |Raises|

        * **None**
        """
        return self._qteAdmin.appletSignature

    def qteAutoremoveDeletedWidgets(self):
        """
        Remove all widgets from the internal widget list that do not
        exist anymore according to SIP.

        |Args|

        * **None**

        |Returns|

        * **None**

        |Raises|

        * **None**
        """
        widget_list = self._qteAdmin.widgetList
        deleted_widgets = [_ for _ in widget_list if sip.isdeleted(_)]
        for widgetObj in deleted_widgets:
            self._qteAdmin.widgetList.remove(widgetObj)

    @type_check
    def qteSetWidgetFocusOrder(self, widList: tuple):
        """
        Change the focus order of the widgets in this applet.

        This method re-arranges the internal (cyclic) widget list so
        that all widgets specified in ``widList`` will be focused in
        the given order.

        |Args|

        * ``widList`` (**tuple**): a tuple of widget objects.

        |Returns|

        * **None**

        |Raises|

        * **None**
        """
        # A list with less than two entries cannot be re-ordered.
        if len(widList) < 2:
            return

        # Housekeeping: remove non-existing widgets from the admin structure.
        self.qteAutoremoveDeletedWidgets()

        # Remove all **None** widgets.
        widList = [_ for _ in widList if _ is not None]

        # Ensure that all widgets exist in the current applet.
        for wid in widList:
            if wid not in self._qteAdmin.widgetList:
                msg = 'Cannot change focus order because some '
                msg += 'widgets do not exist.'
                self.qteLogger.warning(msg)
                return

        # Remove all duplicates from the user supplied list.
        newList = [widList[0]]
        for wid in widList[1:]:
            if wid not in newList:
                newList.append(wid)

        # If the duplicate free list has only one entry then there is
        # nothing left to reorder.
        if len(newList) < 2:
            return

        # The purpose of the code is the following: suppose
        # _qteAdmin.widgetList = [0,1,2,3,4,5] and newList=[2,5,1].
        # Then change _qteAdmin.widgetList to [0,1,2,5,1,3,4]. Step
        # 1: remove all but the first widget in newList from
        # _qteAdmin.widgetList.
        for wid in newList[1:]:
            self._qteAdmin.widgetList.remove(wid)

        # 2: re-insert the removed elements as a sequence again.
        startIdx = self._qteAdmin.widgetList.index(newList[0]) + 1
        for idx, wid in enumerate(newList[1:]):
            self._qteAdmin.widgetList.insert(startIdx + idx, wid)

    @type_check
    def qteNextWidget(self, numSkip: int=1, ofsWidget: QtGui.QWidget=None,
                      skipVisible: bool=False, skipInvisible: bool=True,
                      skipFocusable: bool=False,
                      skipUnfocusable: bool=True):
        """
        Return the next widget in cyclic order.

        If ``ofsWidget`` is **None** then start counting at the
        currently active widget and return the applet ``numSkip``
        items away in cyclic order in the internal widget list. If
        ``numSkip`` is positive traverse the applet list forwards,
        otherwise backwards. The methods supports the following
        selection criteria:

        * ``skipVisible``: only invisible widgets are considered.
        * ``skipInvisible``: only visible widgets are considered.
        * ``skipFocusable``: only unfocusable widgets are considered.
        * ``skipUnfocusable``: only unfocusable widgets are considered.

        |Args|

        * ``numSkip`` (**int**): number of applets to skip.
        * ``ofsWidget`` (**QWidget**): widget from where to start counting.
        * ``skipVisible`` (**bool**): whether or not to skip currently
          shown widgets.
        * ``skipInvisible`` (**bool**): whether or not to skip currently
          not shown widgets.
        * ``skipFocusable`` (**bool**): whether or not to skip focusable
          widgets.
        * ``skipUnfocusable`` (**bool**): whether or not to skip unfocusable
          widgets.

        |Returns|

        * **QWidget**: either the next widget that fits the criteria, or
          **None** if no such widget exists.

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        * **QtmacsOtherError** if ``ofsWidget`` was not added with
          ``qteAddWidget``.
        """
        # Check type of input arguments.
        if not hasattr(ofsWidget, '_qteAdmin') and (ofsWidget is not None):
            msg = '<ofsWidget> was probably not added with <qteAddWidget>'
            msg += ' method because it lacks the <_qteAdmin> attribute.'
            raise QtmacsOtherError(msg)

        # Housekeeping: remove non-existing widgets from the admin structure.
        self.qteAutoremoveDeletedWidgets()

        # Make a copy of the widget list.
        widList = list(self._qteAdmin.widgetList)

        # Return immediately if the widget list is empty. The actual
        # return value is either self._qteActiveWidget (if it points
        # to a child widget of the current applet), or None.
        if not len(widList):
            if qteGetAppletFromWidget(self._qteActiveWidget) is self:
                return self._qteActiveWidget
            else:
                return None

        if skipInvisible:
            # Remove all invisible widgets.
            widList = [wid for wid in widList if wid.isVisible()]

        if skipVisible:
            # Remove all visible widgets.
            widList = [wid for wid in widList if not wid.isVisible()]

        if skipFocusable:
            # Remove all visible widgets.
            widList = [wid for wid in widList if not wid._qteAdmin.isFocusable]

        if skipUnfocusable:
            # Remove all unfocusable widgets.
            widList = [wid for wid in widList if wid._qteAdmin.isFocusable]

        # Return immediately if the list is empty. This is typically
        # the case at startup before any applet has been added.
        if not len(widList):
            return None

        # If no offset widget was given then use the currently active one.
        if ofsWidget is None:
            ofsWidget = self._qteActiveWidget

        if (ofsWidget is not None) and (numSkip == 0):
            if qteIsQtmacsWidget(ofsWidget):
                return ofsWidget

        # Determine the index of the offset widget; assume it is zero
        # if the widget does not exist, eg. if the currently active
        # applet is not part of the pruned widList list.
        try:
            ofsIdx = widList.index(ofsWidget)
        except ValueError:
            ofsIdx = 0

        # Compute the index of the next widget and wrap around the
        # list if necessary.
        ofsIdx = (ofsIdx + numSkip) % len(widList)

        # Return the widget.
        return widList[ofsIdx]

    @type_check
    def qteMakeWidgetActive(self, widgetObj: QtGui.QWidget):
        """
        Give keyboard focus to ``widgetObj``.

        If ``widgetObj`` is **None** then the internal focus state
        is reset, but the focus manger will automatically
        activate the first available widget again.

        |Args|

        * ``widgetObj`` (**QWidget**): the widget to focus on.

        |Returns|

        * **None**

        |Raises|

        * **QtmacsOtherError** if ``widgetObj`` was not added with
            ``qteAddWidget``.
        """
        # Void the active widget information.
        if widgetObj is None:
            self._qteActiveWidget = None
            return

        # Ensure that this applet is an ancestor of ``widgetObj``
        # inside the Qt hierarchy.
        if qteGetAppletFromWidget(widgetObj) is not self:
            msg = 'The specified widget is not inside the current applet.'
            raise QtmacsOtherError(msg)

        # If widgetObj is not registered with Qtmacs then simply declare
        # it active and return.
        if not hasattr(widgetObj, '_qteAdmin'):
            self._qteActiveWidget = widgetObj
            return

        # Do nothing if widgetObj refers to an applet.
        if widgetObj._qteAdmin.isQtmacsApplet:
            self._qteActiveWidget = None
            return

        # Housekeeping: remove non-existing widgets from the admin structure.
        self.qteAutoremoveDeletedWidgets()

        # Verify the widget is registered for this applet.
        if widgetObj not in self._qteAdmin.widgetList:
            msg = 'Widget is not registered for this applet.'
            self.qteLogger.error(msg, stack_info=True)
            self._qteActiveWidget = None
            return

        # The focus manager in QtmacsMain will hand the focus to
        # whatever the _qteActiveWidget variable of the active applet
        # points to.
        self.qteSetWidgetFocusOrder((self._qteActiveWidget, widgetObj))
        self._qteActiveWidget = widgetObj

    def qteAppletID(self):
        """
        Return the applet ID.

        |Args|

        * **None**

        |Returns|

        * **str**: applet ID.

        |Raises|

        * **None**
        """
        return self._qteAdmin.appletID

    def qteKeyPressEventBefore(self, event, srcObj):
        """
        Virtual method: triggers just before the key is processed by Qtmacs.

        This function is only called if ``receiveBeforeQtmacsParser``
        was explicitly set with the ``qteSetKeyFilterPolicy`` method
        of ``srcObj``.

        |Args|

        * ``event`` (**QKeyEvent**): the key event passed down by Qt itself.
        * ``srcObj`` (**QWidget**): object that received the key event.

        |Returns|

        * **None**

        |Raises|

        * **None**
        """
        pass

    def qteKeyPressEventAfter(self, event, srcObj):
        """
        Virtual method: triggers after the key was processed by Qtmacs.

        This function is only called if ``receiveBeforeQtmacsParser``
        was explicitly set with the ``qteSetKeyFilterPolicy`` method
        of ``srcObj``.

        |Args|

        * ``event`` (**QKeyEvent**): the key event passed down by Qt itself.
        * ``srcObj`` (**QWidget**): object that received the key event.

        |Returns|

        * **None**

        |Raises|

        * **None**
        """
        pass

    def keyPressEvent(self, event):
        """
        Qt-native slot.

        This slot can only be triggered if the event filter of Qtmacs
        is not in control of this applet for whatever reason. This
        implies that none of the macro associated with keys will run
        and Qtmacs is therefore unresponsive. However, the method
        raises an error which *should* ensure that Qtmacs will restore
        itself, but the problem should nonetheless not be present in
        the first place.
        """
        msg = 'Main applet received keyboard event. '
        msg += 'This is almost certainly a bug.'
        raise QtmacsOtherError(msg)

    def qteIsVisible(self):
        """
        Returns **True** if the window is visible according to Qtmacs.

        Note that this flag is set as soon as Qtmacs scheduled it to
        become visible, but it may not yet be visible because the
        event loop has not yet been called. This is also the reason
        why this flag may differ from Qt's native ``isVisible``.

        Note that more than one applet may have this flag set because
        multiple applets might have been scheduled to become visible,
        even if they are mutually exclusively. However, once the GUI
        was updated the focus manager ensures that the flags are
        consistent again.

        |Args|

        * **None**

        |Returns|

        * **bool**: visibility status of applet according to Qtmacs,
            not Qt.

        |Raises|

        * **None**
        """
        return self._qteAdmin.isVisible

    @type_check
    def qteSetReadyToKill(self, flag: bool=True):
        """
        If **True**, then the default ``kill-applet`` macro will
        delete us immediately if triggered.

        The purpose of this method is to ensure that no applets are
        accidentally killed when they contain eg. unsaved
        data. However, heeding this flag is the responsibility of the
        macros, whereas the ``qteKillApplet`` method from ``Qtmacs``
        will do as told.

        |Args|

        * ``flag`` (**bool**): if **True**, the applet can be safely killed.

        |Returns|

        * **None**

        |Raises|

        * **None**
        """
        self._qteAdmin.readyToKill = flag

    def qteReadyToKill(self):
        """
        Return the ``readyToKill`` status for this applet.

        |Args|

        * **None**

        |Returns|

        * **bool**: if **True**, the applet can be safely killed.

        |Raises|

        * **None**
        """
        return self._qteAdmin.readyToKill

    def qteToBeKilled(self):
        """
        Cleanup actions.

        This method is a stub and called immediately before Qtmacs
        kills the applet.

        |Args|

        * **None**

        |Returns|

        * **None**

        |Raises|

        * **None**
        """
        pass

    @type_check
    def loadFile(self, fileName: str=None):
        """
        Overload this method with applet specific code that can make
        sense of the passed ``fileName`` argument. In many case this
        will literally mean a file name, but could equally well be a
        URL (eg. ``QWebView`` based applets) or any other resource
        descriptor, as long as it is in text form.

        |Args|

        * ``fileName`` (**str**): name of file to open.

        |Returns|

        * **None**

        |Raises|

        * **None**
        """
        msg = ('The <b>{}</b> applet has not implemented the '
               '<b>LoadFile</b> method')
        self.qteLogger.info(msg.format(self.qteAppletSignature()))

    @type_check
    def show(self, fromQtmacs: bool=False):
        """
        Overloaded ``show()`` function to avoid calling it
        accidentally.

        This method is a (weak) security mechanism to prevent
        programmers from using the ``show`` method as originally
        intended by Qt, ie. to show a window. In Qtmacs, applets can
        only be made visible with either ``qteMakeAppletActive`` or by
        replacing another window in the layout with eg
        ``qteReplaceWindowInLayout``. Using the Qt native ``show()``
        method messes with the Qtmacs layout engine and can lead to
        unexpected visual results and more serious errors.

        This method should only be used by ``QtmacsMain`` to implement
        the layout but not by any applets or macros, unless it is for
        a widget not under the control of Qtmacs (probably a bad
        idea).

        The user should call the ``qteNewApplet`` method to create and
        show a applet.

        |Args|

        * ``fromQtmacs`` (**bool**): if **True** then the original
          ``show()`` method is called

        |Returns|

        * **None**

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        if not fromQtmacs:
            # Log a warning message if someone tries to call the
            # native show() method.
            msg = 'show() command for applet <b>{}</b> ignored. '
            msg += ' Use qteNewApplet instead.'.format(self.qteAppletID())
            self.qteLogger.warning(msg)
        else:
            # Sanity check: the parent of this applet *must* be a
            # ``QtmacsLayoutSplitter`` as otherwise it cannot be
            # shown.
            sig_ = self.parent()._qteAdmin.widgetSignature
            if sig_ != '__QtmacsLayoutSplitter__':
                msg = 'show() command for applet <b>{}</b> ignored'
                msg = msg.format(self.qteAppletID())
                msg += ' because its parent is not a '
                msg += 'QtmacsLayoutSplitter --> Bug.'
                return

            # Before the applet is actually shown update the
            # ``parentWindow`` reference in the admin structure. To
            # obtain this reference, query the parent of this very
            # applet (which is a QtmacsSplitter instance) for its
            # parent window since both must necessarily be shown in
            # the same window and thus have the same parent window.
            self._qteAdmin.parentWindow = self.parent().qteParentWindow()

            # Update the Qtmacs internal visibility flag (used in the
            # focus manager to ensure that Qt and Qtmacs agree on
            # which applets are visible and which are not) and then
            # tell Qt to make the applet visible once the event loop
            # regains control.
            self._qteAdmin.isVisible = True
            QtGui.QWidget.show(self)

    @type_check
    def hide(self, fromQtmacs: bool=False):
        """
        Overloaded ``hide()`` function to avoid calling it
        accidentally.

        This method is a (weak) security mechanism to prevent
        programmers from using the ``hide`` method as originally
        intended by Qt, ie. to hide a window. However, in Qtmacs,
        applets can only be made invisible by either killing them with
        ``qteKillApplet`` or replacing them with another applet (see
        eg. ``qteReplaceAppletInLayout``). Using the Qt native
        ``hide()`` method messes with the Qtmacs layout engine and can
        lead to unexpected visual results and more serious errors.

        This method should only be used by ``QtmacsMain`` to implement
        the layout but not by any applets or macros, unless it is for
        a widget not under the control of Qtmacs (probably a bad
        idea).

        |Args|

        * *fromQtmacs (**bool**): if **True** then the original
           ``hide()`` method is called

        |Returns|

        * **None**

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        if not fromQtmacs:
            # Log a warning message if someone tries to call the
            # native hide() method.
            msg = ('hide() command for applet <b>{}</b> ignored. Use '
                   ' qteNewApplet instead.'.format(self.qteAppletID()))
            self.qteLogger.warning(msg)
        else:
            # If we are explicitly requested to hide() the widget,
            # then clear the Qtmacs internal visibility flag (will be
            # used in the focus manager to double check that Qtmacs
            # and Qt agree on which widgets are visible), remove the
            # applet from the QtmacsSplitter by re-parenting it to
            # **None**, and tell Qt to actually hide the widget as
            # soon as the event loop is in control again.
            self._qteAdmin.isVisible = False
            self.qteReparent(None)
            QtGui.QWidget.hide(self)

    @type_check
    def setMode(self, mode: str, value):
        """
        Set ``mode`` to ``value``.

        |Args|

        * *mode (**str**): name of the mode.
        * *value (**object**): value associated with mode.

        |Returns|

        * **None**

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        self._qteModes[mode] = value

    @type_check
    def getMode(self, mode: str):
        """
        Retrieve the value for ``mode``.

        If ``mode`` does not exist then raise a ``KeyError``.

        |Args|

        * *mode (**str**): name of the mode.

        |Returns|

        * **None**

        |Raises|

        * **KeyError** if ``mode`` is not a key.
        """
        return self._qteModes[mode]

    def getModeDict(self):
        """
        Return a *copy* of the modes.

        |Args|

        * **None**

        |Returns|

        * **dict**: copy of the currently set modes.

        |Raises|

        * **None**
        """
        return dict(self._qteModes)

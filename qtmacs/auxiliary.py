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
Qtmacs internal support classes.

The classes and functions in this module are used by various internal
modules and serve mostly administrative purposes that do not require
state information of the objects that use them.

While all classes in this file can safely be used in any applet/macro,
only ``QtmacsKeysequence`` is likely be of any practical value.

It is safe to use::

    from auxiliary import something

"""
import re
import inspect
import qtmacs.type_check
import qtmacs.qte_global as qte_global

from PyQt4 import QtCore, QtGui
from qtmacs.exceptions import *

# Shorthands
type_check = qtmacs.type_check.type_check


# ----------------------------------------------------------------------
#                              Classes
# ----------------------------------------------------------------------


class QtmacsMessage(object):
    """
    Data container that is passed along with every signal or hook.

    The ``data`` field is an arbitrary Python object and ``senderObj``
    specifies the object that triggered the delivery of the message.

    The message recipient can query both fields directly via the
    ``data`` and ``senderObj`` attributes. Furthermore, the ``isHook``
    flag indicates if the message was delivered via a hook (**True**)
    or a signal (**False**). Finally, the ``messengerName`` attribute,
    specifies the name of the signal or hook that delivered the
    object.

    |Args|

    * ``data`` (**object**): arbitrary. The recipient must know what to
    * ``senderObj`` (**QObject**): reference to calling object.

    |Raises|

    * **None**
    """
    @type_check
    def __init__(self, data=None, senderObj: QtCore.QObject=None):
        super().__init__()
        self.data = data
        self.senderObj = senderObj

        # Indicate whether this message was sent by a signal or a hook.
        self.isHook = None

        # Name of signal (without the `qtesig` prefix) or hook.
        self.messengerName = None

    @type_check
    def setHookName(self, name: str):
        """
        Specify that the message will be delivered with the hook ``name``.
        """
        self.isHook = True
        self.messengerName = name

    @type_check
    def setSignalName(self, name: str):
        """
        Specify that the message will be delivered with the signal ``name``.
        """
        self.isHook = False
        self.messengerName = name


class QtmacsVersionStructure(object):
    """
    Container object to maintain version information.

    |Args|

    * **None**

    |Raises|

    * **None**
    """
    def __init__(self):
        self.version = None
        self.created = None
        self.last_changed = None


class QtmacsAdminStructure(object):
    """
    Container object carried by every applet and widget in the
    instance variable ``_qteAdmin``.

    This class holds all the information needed by Qtmacs to
    administrate its applets and widgets to avoids name space
    pollution of the Qt classes.

    As a rule of thumb, do not set any values in this object
    manually. Instead, use the dedicated access methods. If there is
    no such method, then the variable is like not meant to be tempered
    with.

    |Args|

    * ``qteApplet`` (**QtmacsApplet**): handle to applet holding this
      either this structure directly, or the widget which holds it.
    * ``appletID`` (**str**): applet ID.
    * ``isFocusable`` (**bool**): whether a widget can have the focus
      (ignored for``QtmacsApplets``).
    * ``isQtmacsWindow`` (**bool**): whether or not the caller is
      ``QtmacsMain``. This flag only exists to avoid problems with
      assigning this object to ``QtmacsMain`` at start up.

    |Raises|

    * **None**
    """
    def __init__(self, qteApplet, appletID=None,
                 isFocusable=True, isQtmacsWindow=False):
        # Keep a reference to the main Qtmacs class.
        self.qteMain = qte_global.qteMain

        # Save a handle to the parent applet.
        self.qteApplet = qteApplet

        # Save the applet name (a string).
        self.appletID = appletID

        # Unfocusable widgets are skipped when cycling the focus.
        self.isFocusable = isFocusable

        # If true, call the qteKeyPressEventBefore method of the
        # applet (not the widget!) before it is processed by Qtmacs.
        self.receiveBeforeQtmacsParser = False

        # If true, call the qteKeyPressEventAfter method of the applet
        # (not the widget!) after it was processed by Qtmacs.
        self.receiveAfterQtmacsParser = False

        # If True, Qtmacs will intercept the key events for this widget.
        self.filterKeyEvents = True

        if not isQtmacsWindow:
            # Initially, the local key map mirrors the global one.
            self.keyMap = self.qteMain.qteCopyGlobalKeyMap()

        # Applet signature. This information determines which macros
        # are compatible.
        self.appletSignature = None

        # Widget Signature. This variable is automatically set for
        # every widget added via ``qteAddWidget``. If the object is
        # not a widget but a reference then it defaults to the string
        # "QWidget".
        self.widgetSignature = "QWidget"

        # List of widgets held by this applet. The ordering of this
        # list determines the focus sequence.
        self.widgetList = []

        # Specify whether the widget is a QtmacsApplet. The default
        # value is true because the qteAddWidget routine will
        # overwrite this flag for widgets.
        self.isQtmacsApplet = True

        # Specify if the applet is a mini applet.
        self.isMiniApplet = False

        # Handle to parent window. This is always **None** if the
        # widget is invisible. This flag is updated automatically by
        # the show() and hide() methods.
        self.parentWindow = None

        # Visibility flag. This is usually the same as Qt's native
        # ``isVisible`` but whereas Qt does not actually update this
        # flag until the event loop had a chance to paint the applet,
        # the isVisible flag will update as soon as the show/hide
        # methods are called. This extra information is necessary
        # because several methods in QtmacsMain make applets visible
        # and invisible without calling the event loop in between,
        # which makes it impossible to track the visibility states.
        self.isVisible = False

        # This is general purpose dictionary that macros can use to
        # store applet specific information.
        self.macroData = {}

        # If True, then the applet can be killed without loosing
        # data. This is mostly a convenience flag to facilitate a
        # reasonably generic kill-applet macro, but the applet
        # programmer is free to provide his own kill-applet macro for
        # his applet. That macro may use applet specific variables to
        # determine whether or not the applet can be safely killed and
        # if not, how to achieve it.
        self.readyToKill = True

    @type_check
    def qteSetKeyFilterPolicy(self, receiveBefore: bool=False,
                              useQtmacs: bool=None,
                              receiveAfter: bool=False):
        """
        Set the policy on how Qtmacs filters keyboard events for a
        particular widgets.

        The options can be arbitrarily combined, eg. ::

            widget.qteSetKeyFilterPolicy(True, True, False)

        will first pass the event to the applet's ``keyPressEvent``
        method and afterwards pass the same event to Qtmacs' keyboard
        filter.

        For all text-processing widgets (eg. ``QLineEdit``,
        ``QTextEdit``, ``QWebView``, etc.) it is almost always a good
        idea to use the default, ie. (False, True, False, False),
        which lets Qtmacs process everything. In this case the only
        way to interact with the widget is via macros (and the mouse).

        If ``receiveBefore`` and/or ``receiveAfter`` is set then
        ``qteKeyPressEventBefore`` and/or ``qteKeyPressEventAfter`` of
        the QtmacsApplet (not widget) is called to inspect the event.

        .. note:: The default behaviour is to let Qtmacs handle all
           keyboard events and interact with the applet only via
           macros. It may be more convenient for a programmer to
           handle keyboard events directly in the keyPressEvent
           routine, as is customary with Qt applications, but this
           compromises the customisation ability of Qtmacs. As a rule
           of thumb, applet classes should not implement keyPressEvent
           at all. However, since there is an exception to every rule
           Qtmacs allows it.

        .. note:: This method must be part of the qteAdmin object
                  because which is attached to every object under the
                  control of Qtmacs.

        |Args|

        * ``receiveBefore`` (**bool**): pass the keyEvent to the applet
          before Qtmacs processes it.
        * ``useQtmacs`` (**bool**): let Qtmacs parse the key.
        * ``receiveAfter`` (**bool**): pass the keyEvent to the applet
          after Qtmacs processed it.

        |Returns|

        * **None**

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        # Store key filter policy flags.
        self.filterKeyEvents = useQtmacs
        self.receiveBeforeQtmacsParser = receiveBefore
        self.receiveAfterQtmacsParser = receiveAfter

    def keyFilterPolicy(self):
        """
        Return the key filter policy for the current applet.

        .. note:: This method must be part of the qteAdmin object
                  because which is attached to every object under the
                  control of Qtmacs.

        |Args|

        * **None**

        |Returns|

        ``tuple``: (receiveBefore, useQtmacs, receiveAfter)

        |Raises|

        * **None**
        """
        return (self.receiveBeforeQtmacsParser, self.filterKeyEvents,
                self.receiveAfterQtmacsParser)


class QtmacsKeysequence(object):
    """
    Parse and represent a Qtmacs keyboard sequence.

    Without any argument, it represents an empty sequence. If the
    argument is a string or a list/tuple, then a parser attempts to
    convert it into a sequence of valid ``QKeyEvent`` objects. If the
    argument is another QtmacsKeysequence, then a copy of the object
    is returned.

    Examples for instantiating this object with human readable
    keyboard sequences::

        QtmacsKeysequence('<ctrl>+f h <alt>+K <ctrl>+k')
        QtmacsKeysequence('<ctrl>+f <ctrl>+<alt>++ <ctrl>+<alt>+<space>')
        QtmacsKeysequence('<ctrl>+f <ctrl>+F <ctrl>++ <ctrl>+<space>'
                          '<ctrl>+< <alt>+> < > <space>')

    The syntax of the string should be self explanatory. In addition,
    everything in angular brackets is case insensitive, eg. '<ctrl>-f'
    and '<CtRL>-f' are the same, and so is '<space>' and
    '<SPAce>'. However, non-bracketed keys are case sensitive,
    eg. '<ctrl>-f>' is not the same as '<ctrl>+F'. Note that it is not
    necessary (in fact impossible) to specify a <shift> modifier.

    Keyboard combination are separated by (an arbitrary number of)
    white spaces. Non-printable characters have a bracketed mnemonic,
    eg. <space>, <backspace>, <tab>, <F1>. The exact list of available
    characters, as well as the necessity for <shift> modifiers,
    depends on the used OS and keyboard. The used layout is specified
    in ``Qt_keymap`` variable from the global name space which
    ``QtmacsMain`` sets at startup, although it utilises the
    ``platform_setup.py`` module to do the actual work. That module is
    also the point of entry for adding new key maps, and/or extending
    existing ones.

    Instead of specifying a human readable string it is also possible
    to instantiate ``QtmacsKeyboardsequence`` with sequence of Qt
    constants from the ``QtCore.Qt`` name space, for instance::

        QtmacsKeysequence([(QtCore.Qt.ControlModifier, QtCore.Qt.Key_H),
                       (QtCore.Qt.NoModifier, QtCore.Qt.Key_K)])

    is the same as::

        QtmacsKeysequence('<ctrl>+h k').

    The macro/applet programmer is unlikely to encounter this class at
    all as the methods of these classes that require keyboard
    sequences (eg. ``qteBindKeyWidget``) are usually called
    with human readable strings anyway because they are convenient.
    However, Qtmacs internally, the only accepted way to deal with
    keyboard shortcuts is via this class.

    |Args|

    * ``keysequence`` (**str** or **tuple** or **list** or
      **QtmacsKeysequence**)

    |Raises|

    * **QtmacsKeysequenceError** if ``keysequence`` could not be parsed.
    """
    def __init__(self, keysequence=None):
        # Only used when called as an iterator to yield the individual
        # QKeyEvents that make up the key sequence represented by this
        # class.
        self._iterCnt = 0

        # Get a reference to the key map for this machine. This
        # reference is usually set by the constructor of the
        # QtmacsMain class early on and should therefore be
        # available. If not, then something is seriously wrong.
        if hasattr(qte_global, 'Qt_key_map'):
            # Dictionary that maps human readable keys to Qt
            # constants.
            self.keyDict = qte_global.Qt_key_map
        else:
            msg = '"Qt_key_map" variable does not exist in global name space'
            raise QtmacsKeysequenceError(msg)

        # Get a reference to the modifier map for this machine (set at
        # the same time as Qt_key_map above).
        if hasattr(qte_global, 'Qt_modifier_map'):
            # Dictionary that maps modifier keys to Qt constants.
            self.modDict = qte_global.Qt_modifier_map
        else:
            msg = '"Qt_modifier_map" variable does not exist '
            msg += 'in global name space.'
            raise QtmacsKeysequenceError(msg)

        # Make a copy of keyDict but with keys as values and vice
        # versa. This dictionary will be used to map the binary (Qt
        # internal) representation of keys to human readable values.
        self.keyDictReverse = {}
        for key, value in self.keyDict.items():
            self.keyDictReverse[value] = key

        # A list of QKeyEvent events and numerical constants from the
        # Qt library. Both lists represent the same key sequence and
        # the reset() method clears both.
        self.keylistQtConstants = None
        self.keylistKeyEvent = None
        self.reset()

        # Act on the argument passed to the constructor.
        if isinstance(keysequence, str):
            # We were passed a string --> parse it to extract the key sequence.
            self.str2key(keysequence)
        elif isinstance(keysequence, list) or isinstance(keysequence, tuple):
            # We were passed a list --> parse it to extract the key sequence.
            self.list2key(keysequence)
        elif isinstance(keysequence, QtmacsKeysequence):
            # We were passed another QtmacsKeysequence object --> copy
            # all its attributes.
            self.keylistQtConstants = keysequence.keylistQtConstants
            self.keylistKeyEvent = keysequence.keylistKeyEvent
        elif keysequence is None:
            # We were passed nothing --> do nothing.
            pass
        else:
            msg = 'Argument must be either None, a string, a list, '
            msg += 'or a QtmacsKeySequence.'
            raise QtmacsKeysequenceError(msg)

    def __repr__(self):
        """
        Print a human readable version of the key sequence represented
        by this object.
        """
        return self.toString()

    def reset(self):
        """
        Flush the key sequences.

        |Args|

        * **None**

        |Returns|

        **None**

        |Raises|

        * **None**
        """
        self.keylistQtConstants = []
        self.keylistKeyEvent = []

    def list2key(self, keyList):
        """
        Convert a list of (``QtModifier``, ``QtCore.Qt.Key_*``) tuples
        into a key sequence.

        If no error is raised, then the list was accepted.

        |Args|

        * ``keyList`` (**list**): eg. (QtCore.Qt.ControlModifier,
          QtCore.Qt.Key_F).

        |Returns|

        **None**

        |Raises|

        * **QtmacsKeysequenceError** if the provided ``keysequence``
            could not be parsed.
        """
        for keyCombo in keyList:
            if not (isinstance(keyCombo, list) or isinstance(keyCombo, tuple)):
                msg = ('Format of native key list is invalid.'
                       ' Must be a list/tuple of list/tuples.')
                raise QtmacsKeysequenceError(msg)
            if len(keyCombo) != 2:
                msg = 'Format of native key list is invalid.'
                msg += 'Each element must have exactly 2 entries.'
                raise QtmacsKeysequenceError(msg)

            # Construct a new QKeyEvent. Note that the general
            # modifier (ie. <ctrl> and <alt>) still need to be
            # combined with shift modifier (which is never a general
            # modifier) if the key demands it. This combination is a
            # simple "or" on the QFlags structure. Also note that the
            # "text" argument is omitted because Qt is smart enough to
            # fill it internally. Furthermore, the QKeyEvent method
            # will raise an error if the provided key sequence makes
            # no sense, but to avoid raising an exception inside an
            # exception the QtmacsKeysequenceError is not raised
            # inside the exception block.
            key_event = QtGui.QKeyEvent(QtCore.QEvent.KeyPress, keyCombo[1],
                                        keyCombo[0])
            try:
                key_event = QtGui.QKeyEvent(QtCore.QEvent.KeyPress,
                                            keyCombo[1], keyCombo[0])
                err = False
            except TypeError:
                err = True

            if err:
                msg = ('Format of native key list is invalid. '
                       'Must be a list/tuple of list/tuples.')
                raise QtmacsKeysequenceError(msg)
            else:
                self.appendQKeyEvent(key_event)

    def str2key(self, keyString):
        """
        Parse a human readable key sequence.

        If no error is raised, then ``keyString`` could be
        successfully converted into a valid key sequence and is
        henceforth represented by this object.

        |Args|

        * ``keyString`` (**QtmacsKeysequence**): eg. "<ctrl>+f"

        |Returns|

        **None**

        |Raises|

        * **QtmacsKeysequenceError** if ``keyString`` could not be parsed.
        """

        # Ensure the string is non-empty.
        if keyString == '':
            raise QtmacsKeysequenceError('Cannot parse empty string')

        tmp = str(keyString)
        tmp = tmp.replace('<', '&lt;')
        tmp = tmp.replace('>', '&gt;')
        keyStringHtml = '<b>{}</b>.'.format(tmp)
        del tmp

        # Remove leading and trailing white spaces, and reduce
        # sequences of white spaces to a single white space. If this
        # results in an emtpy string (typically the case when the user
        # tries to register a white space with ' ' instead of with
        # '<space>') then raise an error.
        rawKeyStr = keyString.strip()
        if len(rawKeyStr) == 0:
            msg = 'Cannot parse the key combination {}.'.format(keyStringHtml)
            raise QtmacsKeysequenceError(msg)

        # Split the string at these white spaces and convert eg.
        # " <ctrl>+x <ctrl>+f " first into
        # "<ctrl>+x <ctrl>+f" and from there into the list of
        # individual key combinations ["<ctrl>+x", "<ctrl>+f"].
        rawKeyStr = re.sub(' +', ' ', rawKeyStr)
        rawKeyStr = rawKeyStr.split(' ')

        # Now process the key combinations one by one. By definition.
        for key in rawKeyStr:
            # Find all bracketed keys in the key combination
            # (eg. <ctrl>, <space>).
            desc_keys = re.findall('<.*?>', key)

            # There are four possibilities:
            #   * no bracketed key (eg. "x" or "X")
            #   * one bracketed key (eg. "<ctrl>+x", or just "<space>")
            #   * two bracketed keys (eg. "<ctrl>+<space>" or "<ctrl>+<alt>+f")
            #   * three bracketed keys (eg. <ctrl>+<alt>+<space>).
            if len(desc_keys) == 0:
                # No bracketed key means no modifier, so the key must
                # stand by itself.
                modStr = ['<NONE>']
                keyStr = key
            elif len(desc_keys) == 1:
                if '+' not in key:
                    # If no '+' sign is present then it must be
                    # bracketed key without any modifier
                    # (eg. "<space>").
                    modStr = ['<NONE>']
                    keyStr = key
                else:
                    # Since a '+' sign and exactly one bracketed key
                    # is available, it must be a modifier plus a
                    # normal key (eg. "<ctrl>+f", "<alt>++").
                    idx = key.find('+')
                    modStr = [key[:idx]]
                    keyStr = key[idx + 1:]
            elif len(desc_keys) == 2:
                # There are either two modifiers and a normal key
                # (eg. "<ctrl>+<alt>+x") or one modifier and one
                # bracketed key (eg. "<ctrl>+<space>").
                if (key.count('+') == 0) or (key.count('+') > 3):
                    # A valid key combination must feature at least
                    # one- and at most three "+" symbols.
                    msg = 'Cannot parse the key combination {}.'
                    msg = msg.format(keyStringHtml)
                    raise QtmacsKeysequenceError(msg)
                elif key.count('+') == 1:
                    # One modifier and one bracketed key
                    # (eg. "<ctrl>+<space>").
                    idx = key.find('+')
                    modStr = [key[:idx]]
                    keyStr = key[idx + 1:]
                elif (key.count('+') == 2) or (key.count('+') == 3):
                    # Two modifiers and one normal key
                    # (eg. "<ctrl>+<alt>+f", "<ctrl>+<alt>++").
                    idx1 = key.find('+')
                    idx2 = key.find('+', idx1 + 1)
                    modStr = [key[:idx1], key[idx1 + 1:idx2]]
                    keyStr = key[idx2 + 1:]
            elif len(desc_keys) == 3:
                if key.count('+') == 2:
                    # There are two modifiers and one bracketed key
                    # (eg. "<ctrl>+<alt>+<space>").
                    idx1 = key.find('+')
                    idx2 = key.find('+', idx1 + 1)
                    modStr = [key[:idx1], key[idx1 + 1:idx2]]
                    keyStr = key[idx2 + 1:]
                else:
                    # A key combination with three bracketed entries
                    # must have exactly two '+' symbols. It cannot be
                    # valid otherwise.
                    msg = 'Cannot parse the key combination {}.'
                    msg = msg.format(keyStringHtml)
                    raise QtmacsKeysequenceError(msg)
            else:
                msg = 'Cannot parse the key combination {}.'
                msg = msg.format(keyStringHtml)
                raise QtmacsKeysequenceError(msg)

            # The dictionary keys that map the modifiers and bracketed
            # keys to Qt constants are all upper case by
            # convention. Therefore, convert all modifier keys and
            # bracketed normal keys.
            modStr = [_.upper() for _ in modStr]
            if (keyStr[0] == '<') and (keyStr[-1] == '>'):
                keyStr = keyStr.upper()

            # Convert the text version of the modifier key into the
            # QFlags structure used by Qt by "or"ing them
            # together. The loop is necessary because more than one
            # modifier may be active (eg. <ctrl>+<alt>).
            modQt = QtCore.Qt.NoModifier
            for mod in modStr:
                # Ensure that the modifier actually exists (eg. the
                # user might have made type like "<ctlr>" instead of
                # "<ctrl>"). Also, the keys in the dictionary consist
                # of only upper case letter for the modifier keys.
                if mod not in self.modDict:
                    msg = 'Cannot parse the key combination {}.'
                    msg = msg.format(keyStringHtml)
                    raise QtmacsKeysequenceError(msg)

                # Since the modifier exists in the dictionary, "or"
                # them with the other flags.
                modQt = modQt | self.modDict[mod]

            # Repeat the modifier procedure for the key. However,
            # unlike for the modifiers, no loop is necessary here
            # because only one key can be pressed at the same time.
            if keyStr in self.keyDict:
                modQt_shift, keyQt = self.keyDict[keyStr]
            else:
                msg = 'Cannot parse the key combination {}.'
                msg = msg.format(keyStringHtml)
                raise QtmacsKeysequenceError(msg)

            # Construct a new QKeyEvent. Note that the general
            # modifier (ie. <ctrl> and <alt>) still need to be
            # combined with shift modifier if the key demands it. This
            # combination is a simple "or" on the QFlags structure.
            # Also note that the "text" argument is omitted because Qt
            # is smart enough to determine it internally.
            key_event = QtGui.QKeyEvent(QtCore.QEvent.KeyPress, keyQt,
                                        modQt | modQt_shift)

            # Finally, append this key to the key sequence represented
            # by this object.
            self.appendQKeyEvent(key_event)

    @type_check
    def appendQKeyEvent(self, keyEvent: QtGui.QKeyEvent):
        """
        Append another key to the key sequence represented by this object.

        |Args|

        * ``keyEvent`` (**QKeyEvent**): the key to add.

        |Returns|

        **None**

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        # Store the QKeyEvent.
        self.keylistKeyEvent.append(keyEvent)

        # Convenience shortcuts.
        mod = keyEvent.modifiers()
        key = keyEvent.key()

        # Add the modifier and key to the list. The modifier is a
        # QFlag structure and must by typecast to an integer to avoid
        # difficulties with the hashing in the ``match`` routine of
        # the ``QtmacsKeymap`` object.
        self.keylistQtConstants.append((int(mod), key))

    def toQtKeylist(self):
        """
        Return the key sequence represented by this object as a tuple
        of Qt constants.

        The tuple contains as many elements as there are individual
        key combination, each represented by a (QtModifier,
        QtCore.Qt.Key_xxx) tuple itself. For instance, if the object
        was created as Qtmacs('<Ctrl>+h k') then this function would
        return the tuple ((67108864, 72), (0, 75)). Note that this
        list is suitable as an argument to QtmacsKeysequence, which
        would create another object representing the same key
        sequence.

        Note that the numerical constants may be machine dependent.

        |Args|

        * **None**

        |Returns|

        **list**: list of (QtModifer, Qt.Key_xxx) tuples.

        |Raises|

        * **None**
        """
        return tuple(self.keylistQtConstants)

    def toQKeyEventList(self):
        """
        Return the key sequence represented by this object as a tuple
        of Qt constants.

        The tuple contains as many elements as there are individual
        key combination, each represented by a
        (QtModifier, QtCore.Qt.Key_***) tuple itself. For instance, if
        the object was created as Qtmacs('<Ctrl>+h k') then this
        function would return the tuple ((67108864, 72), (0, 75)).
        Note that this list is suitable as an argument to QtmacsKeysequence,
        which would create another object representing the same key sequence.

        Note that the numerical constants may be machine dependent.

        |Args|

        **None**

        |Returns|

        **list**: list of QKeyEvents.

        |Raises|

        * **None**
        """
        return tuple(self.keylistKeyEvent)

    def toString(self):
        """
        Return the key sequence as a human readable string, eg. "<ctrl>+x".

        Note that this list is suitable as an argument to
        QtmacsKeysequence, which would create another object
        representing the same key sequence. If a key could not be
        converted then it will be displayed as '<Unknown>'. If this
        happens, then the key map in ``qte_global.default_qt_keymap``
        is incomplete and should be amended accordingly.

        |Args|

        * **None**

        |Returns|

        **str**: the key sequence, eg. '<ctrl>+f', or '<F1>', or
          '<Unknown>'.

        |Raises|

        * **None**
        """
        # Initialise the final output string.
        retVal = ''

        for mod, key in self.keylistQtConstants:
            out = ''
            # Check for any modifiers except <shift> and add the
            # corresponding string.
            if (mod & QtCore.Qt.ControlModifier):
                out += '<Ctrl>+'
            if (mod & QtCore.Qt.AltModifier):
                out += '<Alt>+'
            if (mod & QtCore.Qt.MetaModifier):
                out += '<Meta>+'
            if (mod & QtCore.Qt.KeypadModifier):
                out += '<Keypad>+'
            if (mod & QtCore.Qt.GroupSwitchModifier):
                out += '<GroupSwitch>+'

            # Format the string representation depending on whether or
            # not <Shift> is active.
            if (mod & QtCore.Qt.ShiftModifier):
                # If the key with the shift modifier exists in the
                # reverse dictionary then use that string, otherwise
                # construct it manually be printing the modifier and
                # the key name. The first case is typically
                # encountered for upper case characters, where eg. 'F'
                # is preferable over '<Shift>+f'.
                if (QtCore.Qt.ShiftModifier, key) in self.keyDictReverse:
                    # The shift-combined key exists in the dictionary,
                    # so use it.
                    out += self.keyDictReverse[(QtCore.Qt.ShiftModifier, key)]
                elif (QtCore.Qt.NoModifier, key) in self.keyDictReverse:
                    # The shift-combined key does not exists in the
                    # dictionary, so assemble the modifier and key by
                    # hand.
                    out += ('<Shift>+' +
                            self.keyDictReverse[(QtCore.Qt.NoModifier, key)])
                else:
                    out += '<Unknown>'
            else:
                if (QtCore.Qt.NoModifier, key) in self.keyDictReverse:
                    out += self.keyDictReverse[(QtCore.Qt.NoModifier, key)]
                else:
                    out += '<Unknown>'

            # Add a spacer.
            retVal += out + ' '

        # Return the final string (minus the last spacer).
        return retVal[:-1]


class QtmacsKeymap(dict):
    """
    Implement the required functionality for a Qtmacs key map.

    This class is effectively a dictionary.

    |Args|

    ** None **

    |Raises|

    * **None**
    """
    @type_check
    def qteInsertKey(self, keysequence: QtmacsKeysequence, macroName: str):
        """
        Insert a new key into the key map and associate it with a
        macro.

        If the key sequence is already associated with a macro then it
        will be overwritten.

        |Args|

        * ``keysequence`` (**QtmacsKeysequence**): associate a macro with
          a key sequence in this key map.
        * ``macroName`` (**str**): macro name.

        |Returns|

        **None**

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        # Get a dedicated reference to self to facilitate traversing
        # through the key map.
        keyMap = self

        # Get the key sequence as a list of tuples, where each tuple
        # contains the the control modifier and the key code, and both
        # are specified as Qt constants.
        keysequence = keysequence.toQtKeylist()

        # Traverse the shortcut sequence and generate new keys as
        # necessary.
        for key in keysequence[:-1]:
            # If the key does not yet exist add an empty dictionary
            # (it will be filled later).
            if key not in keyMap:
                keyMap[key] = {}

            # Similarly, if the key does exist but references anything
            # other than a dictionary (eg. a previously installed
            # ``QtmacdMacro`` instance), then delete it.
            if not isinstance(keyMap[key], dict):
                keyMap[key] = {}

            # Go one level down in the key-map tree.
            keyMap = keyMap[key]

        # Assign the new macro object associated with this key.
        keyMap[keysequence[-1]] = macroName

    @type_check
    def qteRemoveKey(self, keysequence: QtmacsKeysequence):
        """
        Remove ``keysequence`` from this key map.

        |Args|

        * ``keysequence`` (**QtmacsKeysequence**): key sequence to
          remove from this key map.

        |Returns|

        **None**

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        # Get a dedicated reference to self to facilitate traversing
        # through the key map.
        keyMap = self

        # Keep a reference to the root element in the key map.
        keyMapRef = keyMap

        # Get the key sequence as a list of tuples, where each tuple
        # contains the the control modifier and the key code, and both
        # are specified as Qt constants.
        keysequence = keysequence.toQtKeylist()

        # ------------------------------------------------------------
        # Remove the leaf element from the tree.
        # ------------------------------------------------------------
        for key in keysequence[:-1]:
            # Quit if the key does not exist. This can happen if the
            # user tries to remove a key that has never been
            # registered.
            if key not in keyMap:
                return

            # Go one level down in the key-map tree.
            keyMap = keyMap[key]

        # The specified key sequence does not exist if the leaf
        # element (ie. last entry in the key sequence) is missing.
        if keysequence[-1] not in keyMap:
            return
        else:
            # Remove the leaf.
            keyMap.pop(keysequence[-1])

        # ------------------------------------------------------------
        # Prune the prefix path defined by ``keysequence`` and remove
        # all empty dictionaries. Start at the leaf level.
        # ------------------------------------------------------------

        # Drop the last element in the key sequence, because it was
        # removed in the above code fragment already.
        keysequence = keysequence[:-1]

        # Now successively remove the key sequence in reverse order.
        while(len(keysequence)):
            # Start at the root and move to the last branch level
            # before the leaf level.
            keyMap = keyMapRef
            for key in keysequence[:-1]:
                keyMap = keyMap[key]

            # If the leaf is a non-empty dictionary then another key
            # with the same prefix still exists. In this case do
            # nothing. However, if the leaf is now empty it must be
            # removed.
            if len(keyMap[key]):
                return
            else:
                keyMap.pop(key)

    @type_check
    def match(self, keysequence: QtmacsKeysequence):
        """
        Look up the key sequence in key map.

        If ``keysequence`` leads to a macro in the key map represented
        by this object then the method returns ``(macroName,
        True)``. If it does not lead to a macro but is nonetheless
        valid (ie. the sequence is still incomplete), then it returns
        ``(None, True)``. Finally, if the sequence cannot lead to a
        macro because it is invalid then the return value is ``(None,
        False)``.

        |Args|

        * ``keysequence`` (**QtmacsKeysequence**): associate a macro
          with a key sequence in this key map.
        * ``macroName`` (**str**): macro name.

        |Returns|

        (**str**: macro name, **bool**: partial match)

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        try:
            # Look up the ``keysequence`` in the current key map (ie.
            # this very object which inherits from ``dict``). If
            # ``keysequence`` does not lead to a valid macro then
            # return **None**.
            macroName = self
            for _ in keysequence.toQtKeylist():
                macroName = macroName[_]
        except KeyError:
            # This error occurs if the keyboard sequence does not lead
            # to any macro and is therefore invalid.
            return (None, False)

        # At this point we know that the key sequence entered so far
        # exists. Two possibilities from here on forward: 1) the key
        # sequence now points to a macro or 2) the key sequence is
        # still incomplete.
        if isinstance(macroName, dict):
            # Another dictionary --> key sequence is still incomplete.
            return (None, True)
        else:
            # Macro object --> return it.
            return (macroName, True)


# ----------------------------------------------------------------------
#                            Functions
# ----------------------------------------------------------------------

def qteIsQtmacsWidget(widgetObj):
    """
    Determine if a widget is part of Qtmacs widget hierarchy.

    A widget belongs to the Qtmacs hierarchy if it, or one of its
    parents, has a "_qteAdmin" attribute (added via ``qteAddWidget``).
    Since every applet has this attribute is guaranteed that the
    function returns **True** if the widget is embedded inside
    somewhere.

    |Args|

    * ``widgetObj`` (**QWidget**): the widget to test.

    |Returns|

    * **bool**: **True** if the widget, or one of its ancestors
      in the Qt hierarchy have a '_qteAdmin' attribute.

    |Raises|

    * **None**
    """
    if widgetObj is None:
        return False

    if hasattr(widgetObj, '_qteAdmin'):
        return True

    # Keep track of the already visited objects to avoid infinite loops.
    visited = [widgetObj]

    # Traverse the hierarchy until a parent features the '_qteAdmin'
    # attribute, the parent is None, or the parent is an already
    # visited widget.
    wid = widgetObj.parent()
    while wid not in visited:
        if hasattr(wid, '_qteAdmin'):
            return True
        elif wid is None:
            return False
        else:
            visited.append(wid)
            wid = wid.parent()
    return False


def qteGetAppletFromWidget(widgetObj):
    """
    Return the parent applet of ``widgetObj``.

    |Args|

    * ``widgetObj`` (**QWidget**): widget (if any) for which the
      containing applet is requested.

    |Returns|

    * **QtmacsApplet**: the applet containing ``widgetObj`` or **None**.

    |Raises|

    * **None**
    """
    if widgetObj is None:
        return None

    if hasattr(widgetObj, '_qteAdmin'):
        return widgetObj._qteAdmin.qteApplet

    # Keep track of the already visited objects to avoid infinite loops.
    visited = [widgetObj]

    # Traverse the hierarchy until a parent features the '_qteAdmin'
    # attribute, the parent is None, or the parent is an already
    # visited widget.
    wid = widgetObj.parent()
    while wid not in visited:
        if hasattr(wid, '_qteAdmin'):
            return wid._qteAdmin.qteApplet
        elif wid is None:
            return None
        else:
            visited.append(wid)
            wid = wid.parent()
    return None


class QtmacsModeBar(QtGui.QWidget):
    """
    Represent a list of modes, each represented by a ``QLabel``.

    The purpose of this class is to facilitate a flexible mechanims
    to display various modes or status flags. It consists of a list
    of modes, each with an associated value and a ``QLabel`` instance
    that are lined up horizontally.

    It is typically displayed beneath another widget eg. ``SciEditor``.

    The class takes care that all but the rightmost label are only as
    long and high as necessary.

    A typical use case inside an applet with a ``QtmacsScintilla`` widget
    could be as follows::

        # Create a mode bar instance and add some modes.
        self.qteScintilla = QtmacsScintilla(self)
        self._qteModeBar = QtmacsModeBar()
        self._qteModeBar.qteAddMode('EOL', 'U')
        self._qteModeBar.qteAddMode('READONLY', 'R')
        self._qteModeBar.qteAddMode('MODIFIED', '-')

        # Arrange the layout so that the mode bar is at the bottom.
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.qteScintilla)
        vbox.addWidget(self._qteModeBar)
        self.setLayout(vbox)


    |Args|

    * **None**

    |Raises|

    * **None**

    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setLayout(QtGui.QHBoxLayout())
        self._qteModeList = []

    def _qteGetLabelInstance(self):
        """
        Return an instance of a ``QLabel`` with the correct color scheme.

        |Args|

        * **None**

        |Returns|

        * **QLabel**

        |Raises|

        * **None**
        """
        # Create a label with the proper colour appearance.
        layout = self.layout()
        label = QtGui.QLabel(self)
        style = 'QLabel { background-color : white; color : blue; }'
        label.setStyleSheet(style)
        return label

    def _qteUpdateLabelWidths(self):
        """
        Ensure all but the last ``QLabel`` are only as wide as necessary.

        The width of the last label is manually set to a large value to
        ensure that it stretches as much as possible. The height of all
        widgets is also set appropriately. The method also takes care
        or rearranging the widgets in the correct order, ie. in the
        order specified by ``self._qteModeList``.

        |Args|

        * **None**

        |Returns|

        * **None**

        |Raises|

        * **None**
        """
        layout = self.layout()
        # Remove all labels from the list and add them again in the
        # new order.
        for ii in range(layout.count()):
            label = layout.itemAt(ii)
            layout.removeItem(label)

        # Add all labels and ensure they have appropriate width.
        for item in self._qteModeList:
            label = item[2]
            width = label.fontMetrics().size(0, str(item[1])).width()
            label.setMaximumWidth(width)
            label.setMinimumWidth(width)
            layout.addWidget(label)

        # Remove the width constraint from the last label so that
        # it can expand to the right.
        _, _, label = self._qteModeList[-1]
        label.setMaximumWidth(1600000)

    @type_check
    def qteGetMode(self, mode: str):
        """
        Return a tuple containing the ``mode``, its value, and
        its associated ``QLabel`` instance.

        |Args|

        * ``mode`` (**str**): size and position of new window.

        |Returns|

        * (**str**, **object**, **QLabel**: (mode, value, label).

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        for item in self._qteModeList:
            if item[0] == mode:
                return item
        return None

    @type_check
    def qteAddMode(self, mode: str, value):
        """
        Append label for ``mode`` and display ``value`` on it.

        |Args|

        * ``mode`` (**str**): mode of mode.
        * ``value`` (**object**): value of mode.

        |Returns|

        * **None**

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        # Add the label to the layout and the local mode list.
        label = self._qteGetLabelInstance()
        label.setText(value)
        self._qteModeList.append((mode, value, label))
        self._qteUpdateLabelWidths()

    @type_check
    def qteChangeModeValue(self, mode: str, value):
        """
        Change the value of ``mode`` to ``value``.

        If ``mode`` does not exist then nothing happens and the method
        returns **False**, otherwise **True**.

        |Args|

        * ``mode`` (**str**): mode of mode.
        * ``value`` (**object**): value of mode.

        |Returns|

        * **bool**: **True** if the item was removed and **False** if there
          was an error (most likely ``mode`` does not exist).

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        # Search through the list for ``mode``.
        for idx, item in enumerate(self._qteModeList):
            if item[0] == mode:
                # Update the displayed value in the label.
                label = item[2]
                label.setText(value)

                # Overwrite the old data record with the updated one
                # and adjust the widths of the modes.
                self._qteModeList[idx] = (mode, value, label)
                self._qteUpdateLabelWidths()
                return True
        return False

    @type_check
    def qteInsertMode(self, pos: int, mode: str, value):
        """
        Insert ``mode`` at position ``pos``.

        If ``pos`` is negative then this is equivalent to ``pos=0``. If it
        is larger than the number of modes in the list then it is appended
        as the last element.

        |Args|

        * ``pos`` (**int**): insertion point.
        * ``mode`` (**str**): name of mode.
        * ``value`` (**object**) value associated with ``mode``.

        |Returns|

        * **None**

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        # Add the label to the list.
        label = self._qteGetLabelInstance()
        label.setText(value)
        self._qteModeList.insert(pos, (mode, value, label))
        self._qteUpdateLabelWidths()

    @type_check
    def qteRemoveMode(self, mode: str):
        """
        Remove ``mode`` and associated label.

        If ``mode`` does not exist then nothing happens and the method
        returns **False**, otherwise **True**.

        |Args|

        * ``pos`` (**QRect**): size and position of new window.
        * ``windowID`` (**str**): unique window ID.

        |Returns|

        * **bool**: **True** if the item was removed and **False** if there
          was an error (most likely ``mode`` does not exist).

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        # Search through the list for ``mode``.
        for idx, item in enumerate(self._qteModeList):
            if item[0] == mode:
                # Remove the record and delete the label.
                self._qteModeList.remove(item)
                item[2].hide()
                item[2].deleteLater()
                self._qteUpdateLabelWidths()
                return True
        return False

    def qteAllModes(self):
        """
        |Args|

        * ``pos`` (**QRect**): size and position of new window.
        * ``windowID`` (**str**): unique window ID.

        |Returns|

        * **list**: a list of all modes.

        |Raises|

        * **QtmacsArgumentError** if at least one argument has an invalid type.
        """
        return [_[0] for _ in self._qteModeList]

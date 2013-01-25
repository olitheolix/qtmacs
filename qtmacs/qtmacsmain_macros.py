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
Generic macros that are neither applet- nor widget specific.

The entry point to this module is the function
``install_macros_and_bindings``. It registers all applet independent
macros (eg. execute-macro, kill-window) and assigns their respective
default key bindings.

This module is called in the constructor of ``QtmacsMain`` to furnish
the default functionality of Qtmacs.

.. note: Macros are only registered if they do not yet exist. However,
   if a macro with the same name already exists, then it is *not*
   replaced.

"""

import re
import qtmacs.auxiliary
import qtmacs.miniapplets.base_query
import qtmacs.miniapplets.file_query
import qtmacs.qte_global as qte_global

from PyQt4 import QtCore, QtGui
from qtmacs.base_macro import QtmacsMacro

# Shorthands
QtmacsKeysequence = qtmacs.auxiliary.QtmacsKeysequence


# ------------------------------------------------------------
#             Define the Qtmacs standard macros.
# ------------------------------------------------------------
class DescribeKey(QtmacsMacro):
    """
    Query a key sequence and display the documentation for the
    associated macro.

    |Signature|

    * *applet*: '*'
    * *widget*: '*'

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('*')

    def qteRun(self):
        # Disable macro execution and only "listen" to the user typed
        # keys in order to provide a description once a valid key
        # sequence was entered.
        self.qteMain.qteDisableMacroProcessing()
        self.qteMain.qtesigKeyseqComplete.connect(
            self.qteDescribeValidKeySlot)
        self.qteMain.qtesigKeyseqInvalid.connect(
            self.qteDescribeInvalidKeySlot)
        self.qteMain.qteStatus("Describe Next Key")
        self.qteMain.qtesigAbort.connect(self.qteAbort)

    def qteDescribeInvalidKeySlot(self, msgObj):
        # Sequence typed so far cannot lead to a valid key sequence
        # anymore.
        keysequence = msgObj.data
        msg = 'Key <b>{}</b> is unbound.'.format(keysequence.toString())
        self.qteShowDocumentation(msg)

    def qteDescribeValidKeySlot(self, msgObj):
        # Unpack the data structure.
        macroName, keysequence = msgObj.data

        # The key sequence is associated with a macro --> retrieve its
        # doc-string.
        macroObj = self.qteMain.qteGetMacroObject(macroName, self.qteWidget)

        # Double check that the macro really exists.
        if macroObj is None:
            msg = "Invalid macro object. This is a bug."
        else:
            # Compile the doc-string.
            msg = ('<b>{}</b> runs the macro <b>{}</b>.\n'
                   .format(keysequence, macroName))
            if(macroObj.__doc__):
                msg += macroObj.__doc__
            else:
                msg += "No description available."
        self.qteShowDocumentation(msg)

    def qteShowDocumentation(self, msg):
        # Reset the macro and re-enable event processing.
        self.qteAbort(None)
        self.qteMain.qteEnableMacroProcessing()

        # Get handle to the help window applet (create a new applet if
        # necessary).
        app = self.qteMain.qteGetAppletHandle('**Help**')
        if app is None:
            app = self.qteMain.qteNewApplet('RichEditor', '**Help**')
            self.qteMain.qteSplitApplet(app)

        # Ensure the applet is visible and empty.
        if not app.qteIsVisible():
            self.qteMain.qteSplitApplet(app)
        app.qteText.clear()
        app.qteText.insertPlainText(msg)

    def qteAbort(self, msgObj):
        # Disconnect the signals.
        self.qteMain.qtesigKeyseqComplete.disconnect(
            self.qteDescribeValidKeySlot)
        self.qteMain.qtesigKeyseqInvalid.disconnect(
            self.qteDescribeInvalidKeySlot)
        self.qteMain.qtesigAbort.disconnect(
            self.qteAbort)


class ReplayKeysequence(QtmacsMacro):
    """
    Replay a previously recorded key sequence.

    If no keys have been recorded yet then nothing happens. If the key
    recording is still in progress then the recording process will be
    terminated prior to the replay.

    |Signature|

    * *applet*: '*'
    * *widget*: '*'

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('*')

    def qteRun(self):
        # The entire macro- recording and replay happens in the
        # ``RecordKeysequenceCore`` class and is triggered with
        # hooks. Therefore, trigger the replay hook here.
        self.qteMain.qteRunHook('record-macro-replay')


class RecordKeysequenceStart(QtmacsMacro):
    """
    Start recording the key sequence.

    |Signature|

    * *applet*: '*'
    * *widget*: '*'

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('*')

    def qteRun(self):
        # The entire macro- recording and replay happens in the
        # ``RecordKeysequenceCore`` class and is triggered with
        # hooks. Therefore, trigger the start-recording hook here.
        self.qteMain.qteRunHook('record-macro-start')


class RecordKeysequenceStop(QtmacsMacro):
    """
    Stop recording the key sequence.

    |Signature|

    * *applet*: '*'
    * *widget*: '*'

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('*')

    def qteRun(self):
        # The entire macro- recording and replay happens in the
        # ``RecordKeysequenceCore`` class and is triggered with
        # hooks. Therefore, trigger the start-recording hook here.
        self.qteMain.qteRunHook('record-macro-stop')


class RecordKeysequenceCore(QtmacsMacro):
    """
    Manage the key sequence recording and replay.

    This macro can only be controlled via the
    record-keysequence-{start,stop,replay} macros.

    The last recorded list of of key events is available for all in
    the global variable ``recorded_keysequence``.

    .. warning:: the recording a key sequence that triggers the
       recording of another key sequence will result in an infinite
       loop upon the second replay. It is probably impossible to endow
       this macro with the ability to detect it because the recorded
       macros are all queued at once, and Qtmacs will then issue them
       one by one. It might well be necessary to make macro- recording
       and replay a feature of QtmacsMain that can be triggered by
       macros, but not influenced by them.

    |Signature|

    * *applet*: '*'
    * *widget*: '*'

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('*')

        # The recorded key sequence.
        self.recorded_keysequence = QtmacsKeysequence()

        # Control flags.
        self.qteRecording = False

        # Connect the methods with which this macro is controlled.
        self.qteMain.qteConnectHook('record-macro-start',
                                    self.qteStartRecordingHook)
        self.qteMain.qteConnectHook('record-macro-stop',
                                    self.qteStopRecordingHook)
        self.qteMain.qteConnectHook('record-macro-replay',
                                    self.qteReplayKeysequenceHook)

    def qteRun(self):
        # This macro does do anything. All its functionality is
        # triggered via hooks from the RecordMacro{Start,Stop,Replay}.
        pass

    def qteStartRecordingHook(self, msgObj):
        """
        Commence macro recording.

        Macros are recorded by connecting to the 'keypressed' signal
        it emits.

        If the recording has already commenced, or if this method was
        called during a macro replay, then return immediately.
        """
        if self.qteRecording:
            self.qteMain.qteStatus('Macro recording already enabled')
            return

        # Update status flag.
        self.qteRecording = True

        # Reset the variables.
        self.qteMain.qteStatus('Macro recording started')
        self.recorded_keysequence = QtmacsKeysequence()

        # Connect the 'keypressed' and 'abort' signals.
        self.qteMain.qtesigKeyparsed.connect(self.qteKeyPress)
        self.qteMain.qtesigAbort.connect(self.qteStopRecordingHook)

    def qteStopRecordingHook(self, msgObj):
        """
        Stop macro recording.

        The signals from the event handler are disconnected and the
        event handler policy set to default.
        """
        # Update status flag and disconnect all signals.
        if self.qteRecording:
            self.qteRecording = False
            self.qteMain.qteStatus('Macro recording stopped')
            self.qteMain.qtesigKeyparsed.disconnect(self.qteKeyPress)
            self.qteMain.qtesigAbort.disconnect(self.qteStopRecordingHook)

    def qteReplayKeysequenceHook(self, msgObj):
        """
        Replay the macro sequence.
        """

        # Quit if there is nothing to replay.
        if self.recorded_keysequence.toString() == '':
            return

        # Stop the recording before the replay, if necessary.
        if self.qteRecording:
            return

        # Simulate the key presses.
        self.qteMain.qteEmulateKeypresses(self.recorded_keysequence)

    def qteKeyPress(self, msgObj):
        """
        Record the key presses reported by the key handler.
        """
        # Unpack the data structure.
        (srcObj, keysequence, macroName) = msgObj.data

        # Append the last QKeyEvent object to the so far recorded
        # sequence. Note that both ``keysequence`` and
        # ``self.recorded_keysequence`` are ``QtmacsKeysequence``
        # instances.
        last_key = keysequence.toQKeyEventList()[-1]
        self.recorded_keysequence.appendQKeyEvent(last_key)


class RepeatMacro(QtmacsMacro):
    """
    Repeat a macro a user-specified number of times.

    The user can type in the number of repetitions and then either
    invoke this macro again to explicitly finalise the input, or
    simply type the keyboard combination for the macro to repeat. For
    instance, if the macro was bound to <ctrl>+u then the key sequence
    '<ctr>+u 12 f' will issue the macro associated with the 'f' key
    twelve times, ie. it will print the character 'f' twelve times. To
    repeat a number the input needs to finalised with another <ctrl>+u
    command, eg. '<ctrl>+u 5 <ctrl>+u 3' will print the number '3'
    five times.

    .. note:: this does not work for macros that lack a key-binding.

    |Signature|

    * *applet*: '*'
    * *widget*: '*'

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('*')

    def qteRun(self):
        # Connect the 'keypressed' signal from the event handler to
        # intercept the keys.
        self.qteMain.qtesigKeyparsed.connect(self.qteKeyPress)

        # Disable macro processing and only "listen" to the
        # keystrokes.
        self.qteMain.qteDisableMacroProcessing()

        self.input_complete = False
        self.repeat_cnt = '0'

    def qteRepeatTheMacro(self, msgObj):
        # Unpack the data structure.
        (srcObj, keysequence, macroName) = msgObj.data

        # Disconnect the signal and reset the keyboard filter.
        self.qteMain.qtesigKeyparsed.disconnect(self.qteKeyPress)
        self.qteMain.qteEnableMacroProcessing()

        # Convert self.repeat_cnt to a number.
        try:
            num_repeat = int(self.repeat_cnt)
        except ValueError:
            num_repeat = 0

        # Queue up the specified number of macros, unless this macro
        # is us.
        if macroName != self.qteMacroName():
            for ii in range(num_repeat):
                self.qteMain.qteRunMacro(macroName, srcObj, keysequence)

        # Clear the flags.
        self.input_complete = False
        self.repeat_cnt = ''

    def qteKeyPress(self, msgObj):
        """
        Record the key presses reported by the key handler.
        """
        # Unpack the data structure.
        (srcObj, keysequence, macroName) = msgObj.data
        key = keysequence.toQKeyEventList()[-1]

        # If the current key did not complete a macro ignore it.
        if macroName is None:
            return

        if self.input_complete:
            # The user has terminated reading digits by calling this
            # macro directly, ie. the 'macroName ==
            # self.qteMacroName()' branch below ran previously.
            self.qteRepeatTheMacro(msgObj)
        elif (macroName == 'self-insert') and (key.text().isdigit()):
            # User typed a digit.
            self.repeat_cnt += key.text()
        elif macroName == self.qteMacroName():
            # User called us again. This completes reading the
            # digits. The next macro is executed self.prefix_num
            # times.
            self.input_complete = True
        else:
            # If we got until here we know that a macro is supposed to
            # be executed, that it is not the self-insert macro for a
            # digit, and that it was not another call to this macro to
            # complete the input explicitly.
            self.qteRepeatTheMacro(msgObj)


class MacroProxyDemo(QtmacsMacro):
    """
    Intercept all macros and execute them through this proxy.

    The main purpose of this class is to demonstrate how macros can be
    executed from another macro. To this end, this class disables the
    macro execution in the event filter and connects to the
    ``qtesigKeyparsed`` signal. Once a valid key sequence is
    completed this class will execute it. The result is that
    everything works as usual and that this macro is completely
    transparent. To disable the proxy, simply call this macro again,
    or press <ctrl>-g.

    |Signature|

    * *applet*: '*'
    * *widget*: '*'

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('*')
        self.qteActive = False

    def qteRun(self):
        if self.qteActive:
            self.abort()
        else:
            self.qteActive = True

            # Connect the 'keypressed' signal from the event handler
            # to intercept the keys and the abort signal to turn off
            # this macro again.
            self.qteMain.qtesigKeyparsed.connect(self.qteKeyPress)
            self.qteMain.qtesigAbort.connect(self.abort)

            # Prevent the event handler from executing any macros.
            self.qteMain.qteDisableMacroProcessing()

    def qteKeyPress(self, msgObj):
        """
        Record the key presses.
        """
        # Unpack the data structure.
        (srcObj, keysequence, macroName) = msgObj.data

        # Return immediately if the key sequence does not specify a
        # macro (yet).
        if macroName is None:
            return

        # If the macro to repeat is this very macro then disable the
        # macro proxy, otherwise execute the macro that would have run
        # originally.
        if macroName == self.qteMacroName():
            self.abort()
        else:
            msg = 'Executing macro {} through {}'
            msg = msg.format(macroName, self.qteMacroName())
            self.qteMain.qteStatus(msg)
            self.qteMain.qteRunMacro(macroName, srcObj, keysequence)

    def abort(self, msgObj):
        """
        Disconnect all signals and turn macro processing in the event
        handler back on.
        """
        self.qteMain.qtesigKeyparsed.disconnect(self.qteKeyPress)
        self.qteMain.qtesigAbort.disconnect(self.abort)
        self.qteActive = False
        self.qteMain.qteEnableMacroProcessing()


class OtherApplet(QtmacsMacro):
    """
    Move focus to next visible applet.

    This macro can be used to cycle the focus through all currently
    visible applets, including the mini applet (if one is active).

    |Signature|

    * *applet*: '*'
    * *widget*: '*'

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('*')

    def qteRun(self):
        nextApp = self.qteMain.qteNextApplet(skipInvisible=True,
                                             skipMiniApplet=False)
        self.qteMain.qteMakeAppletActive(nextApp)


class KillWindow(QtmacsMacro):
    """
    Delete the active window.

    Applets inside this window are not destroyed in the process.

    |Signature|

    * *applet*: '*'
    * *widget*: '*'

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('*')

    def qteRun(self):
        self.qteMain.qteKillWindow()


class NewWindow(QtmacsMacro):
    """
    Create a new window.

    The window is initially empty.

    |Signature|

    * *applet*: '*'
    * *widget*: '*'

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('*')

    def qteRun(self):
        self.qteMain.qteNewWindow()


class NextHiddenApplet(QtmacsMacro):
    """
    Replace the current applet with the next hidden one.

    |Signature|

    * *applet*: '*'
    * *widget*: '*'

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('*')

    def qteRun(self):
        nextApp = self.qteMain.qteNextApplet(
            numSkip=0, skipVisible=True, skipInvisible=False)
        if nextApp is not None:
            self.qteMain.qteMakeAppletActive(nextApp)


class SplitVertical(QtmacsMacro):
    """
    Split the active applet vertically and show a hitherto invisible
    applet.

    If no further invisible applet exists then the function does
    nothing, ie. the applet is not split in half.

    |Signature|

    * *applet*: '*'
    * *widget*: '*'

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('*')

    def qteRun(self):
        self.qteMain.qteSplitApplet(splitHoriz=True)


class SplitHorizontal(QtmacsMacro):
    """
    Split the active applet horizontally and show a hitherto invisible
    applet.

    If no further invisible applet exists then the function does
    nothing, ie. the applet is not split in half.

    |Signature|

    * *applet*: '*'
    * *widget*: '*'

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('*')

    def qteRun(self):
        self.qteMain.qteSplitApplet(splitHoriz=False)


class DeleteOtherApplets(QtmacsMacro):
    """
    Make all but the active applet invisible in the layout.

    The applets are only removed from the layout, not killed. This
    macro is typically used to undo all previously issued splitting
    commands. If the layout only displays a single applet then nothing
    happens.

    |Signature|

    * *applet*: '*'
    * *widget*: '*'

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('*')

    def qteRun(self):
        # Get currently active applet.
        curApp = self.qteMain.qteNextApplet(numSkip=0)

        # Remove all but the active applet from the layout.
        for appName in self.qteMain.qteGetAllAppletIDs():
            appObj = self.qteMain.qteGetAppletHandle(appName)
            if appObj is curApp:
                continue
            else:
                self.qteMain.qteRemoveAppletFromLayout(appObj)


class OtherWidget(QtmacsMacro):
    """
    Switch focus cyclically to next widget *inside* the active applet.

    This macro is the widget equivalent of ``OtherApplet``.

    |Signature|

    * *applet*: '*'
    * *widget*: '*'

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('*')

    def qteRun(self):
        wid = self.qteApplet.qteNextWidget()
        if wid is not None:
            self.qteApplet.qteMakeWidgetActive(wid)


class KillApplet(QtmacsMacro):
    """
    Kill an applet.

    If the ``readyToKill`` flag for the applet is **True** then the
    applet is killed immediately. If not, then the user is presented
    with the mini applet to answer
    'Yes' or 'No'.

    |Signature|

    * *applet*: '*'
    * *widget*: '*'

    """
    class Query(qtmacs.miniapplets.base_query.MiniAppletBaseQuery):
        """
        Query the name of one of the registered macros, eg. split-horizontal.
        """
        def generateCompletions(self, entry):
            return ('Yes', 'No')

        def inputCompleted(self, userInput):
            if userInput.upper() == 'YES':
                self.qteMain.qteKillApplet(self.qteApplet.qteAppletID())

    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('*')

        # History of macros issued through the mini applet.
        self.qteQueryHistory = []

    def qteRun(self):
        if self.qteApplet.qteReadyToKill():
            self.qteMain.qteKillApplet(self.qteApplet.qteAppletID())
        else:
            prefix_str = 'Applet does not want to be killed. Kill Anyway?',
            # Ask the user if the applet should really be deleted.
            query = self.Query(self.qteApplet, self.qteWidget,
                               prefix=prefix_str, history=('Yes', 'No'))

            # Install the query object as the mini applet and return
            # control to the event loop.
            self.qteMain.qteAddMiniApplet(query)


class CloseQtmacs(QtmacsMacro):
    """
    Close Qtmacs.

    |Signature|

    * *applet*: '*'
    * *widget*: '*'

    """
    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('*')

    def qteRun(self):
        self.qteMain.qteCloseQtmacs()


class ExecuteMacro(QtmacsMacro):
    """
    Use the mini applet to query for a macro name and then execute it.

    |Signature|

    * *applet*: '*'
    * *widget*: '*'

    """

    class Query(qtmacs.miniapplets.base_query.MiniAppletBaseQuery):
        """
        Query the name of one of the registered macros, eg. split-horizontal.
        """
        def generateCompletions(self, entry):
            # Retrieve a list of all compatible macro names and return
            # a sorted version thereof.
            macro_list = self.qteMain.qteGetAllMacroNames(self.qteWidget)
            return sorted(macro_list)

        def inputCompleted(self, userInput):
            self.qteMain.qteRunMacro(userInput, widgetObj=self.qteWidget,
                                     keysequence=None)

    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('*')

        # History of macros issued through the mini applet.
        self.qteQueryHistory = []

    def qteRun(self):
        # Instantiate the customised new mini applet query object to
        # ask the user for the next macro to execute.
        query = self.Query(self.qteApplet, self.qteWidget,
                           prefix='Execute Macro:',
                           history=self.qteQueryHistory)

        # Install the query object as the mini applet and return
        # control to the event loop.
        self.qteMain.qteAddMiniApplet(query)


class NewApplet(QtmacsMacro):
    """
    Use the mini applet to query for an applet name and then
    instantiate it.

    |Signature|

    * *applet*: '*'
    * *widget*: '*'

    """
    class Query(qtmacs.miniapplets.base_query.MiniAppletBaseQuery):
        """
        Query the name of one of the registered applet types,
        eg. DemoThread.
        """
        def generateCompletions(self, userInput):
            return sorted(self.qteMain.qteGetAllAppletNames())

        def inputCompleted(self, userInput):
            # Create a new instance of the applet requested by the user.
            newApplet = self.qteMain.qteNewApplet(userInput)
            if newApplet is not None:
                self.qteMain.qteMakeAppletActive(newApplet)
            else:
                msg = 'Cannot create new applet because the ID <b>{}</b>'
                msg += ' is already taken.'.format(userInput)
                self.qteMain.qteStatus(msg)

    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('*')

        # History of applets created through the mini applet.
        self.qteQueryHistory = []

    def qteRun(self):
        # Instantiate the customised new mini applet query object to
        # ask the user for the name of the applet to create.
        query = self.Query(self.qteApplet, self.qteWidget,
                           prefix='Create Applet:',
                           history=self.qteQueryHistory)

        # Install the query object as the mini applet and return
        # control to the event loop.
        self.qteMain.qteAddMiniApplet(query)


class FindFile(QtmacsMacro):
    """
    Use the mini applet to query a file name.

    |Signature|

    * *applet*: '*'
    * *widget*: '*'

    """
    class Query(qtmacs.miniapplets.file_query.MiniAppletFindFile):
        """
        Query the name of a file (always starts in the current directory).
        """
        def generateCompletions(self, completions):
            return completions

        def inputCompleted(self, userInput):
            # Look if one of the known file patterns matches with the
            # current user input to determine which applet to open.
            # If none matches, then open the file with the default
            # applet.
            appName = None
            for (pat, name) in qte_global.findFile_types:
                if re.match(pat, userInput):
                    appName = name
                    break

            # If none of the currently registered applets can process
            # the file then use the fallback option (usually a simple
            # text editor widget).
            if appName is None:
                appName = qte_global.findFile_default

            # Try to instantiate the new applet.
            app = self.qteMain.qteNewApplet(appName, userInput)
            if app is None:
                return
            self.qteMain.qteMakeAppletActive(app)

    def __init__(self):
        super().__init__()
        self.qteSetAppletSignature('*')
        self.qteSetWidgetSignature('*')

        # History of applets created through the mini applet.
        self.qteQueryHistory = []

    def qteRun(self):
        # Instantiate the file name query.
        query = self.Query(self.qteApplet, self.qteWidget,
                           history=self.qteQueryHistory)

        # Install the query object as the mini applet and return
        # control to the event loop.
        self.qteMain.qteAddMiniApplet(query)


# -----------------------------------------------------------------
#   Assign the default key bindings for the Qtmacs standard macros.
# -----------------------------------------------------------------
def install_macros_and_bindings():
    qteMain = qte_global.qteMain

    # For readability purposes, compile a list where each entry
    # contains the macro name, macro class, and key binding associated
    # with this macro.
    macro_list = (
        (DescribeKey, '<ctrl>+h k'),
        (CloseQtmacs, '<ctrl>+x <ctrl>+c'),
        (KillApplet, '<ctrl>+x k'),
        (ReplayKeysequence, '<ctrl>+x e'),
        (RecordKeysequenceCore, None),
        (RecordKeysequenceStart, '<ctrl>+x ('),
        (RecordKeysequenceStop, '<ctrl>+x )'),
        (OtherApplet, '<ctrl>+x o'),
        (NextHiddenApplet, '<ctrl>+x <ctrl>+n'),
        (OtherWidget, '<ctrl>+x <ctrl>+o'),
        (RepeatMacro, '<ctrl>+u'),
        (DeleteOtherApplets, '<ctrl>+x 1'),
        (SplitHorizontal, '<ctrl>+x 2'),
        (SplitVertical, '<ctrl>+x 3'),
        (ExecuteMacro, '<alt>+x'),
        (NewApplet, '<ctrl>+x <ctrl>+a'),
        (FindFile, '<ctrl>+x <ctrl>+f'),
        (KillWindow, None),
        (NewWindow, None),
        (MacroProxyDemo, None))

    # Iterate over the list of all macros.
    for macroCls, keysequence in macro_list:
        # Get the macro name.
        macroName = qteMain.qteMacroNameMangling(macroCls)

        # Register the macro if it has not been registered already.
        if not qteMain.qteIsMacroRegistered(macroName):
            macroName = qteMain.qteRegisterMacro(macroCls, True, macroName)

        # Assign a shortcut if one was provided.
        if keysequence is not None:
            qteMain.qteBindKeyGlobal(keysequence, macroName)

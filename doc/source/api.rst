.. _Api:

=================
API Documentation
=================

This page lists frequently used commands grouped by class and category.

.. note:: The API listed here is incomplete and devoid of examples.

QtmacsMain
==========
The following methods are available to all macros and applets via their
``self.qteMain`` attribute, eg.::

    self.qteMain.qteStatus('A status message')


Layout
------
* :py:meth:`~qtmacs.qtmacsmain.QtmacsMain.qteSplitApplet` 
* :py:meth:`~qtmacs.qtmacsmain.QtmacsMain.qteReplaceAppletInLayout` 
* :py:meth:`~qtmacs.qtmacsmain.QtmacsMain.qteRemoveAppletFromLayout` 
* :py:meth:`~qtmacs.qtmacsmain.QtmacsMain.qteKillApplet`

Windows
-------
* :py:meth:`~qtmacs.qtmacsmain.QtmacsMain.qteNewWindow`
* :py:meth:`~qtmacs.qtmacsmain.QtmacsMain.qteMakeWindowActive`
* :py:meth:`~qtmacs.qtmacsmain.QtmacsMain.qteNextWindow`
* :py:meth:`~qtmacs.qtmacsmain.QtmacsMain.qteKillWindow`

Applets
-------
* :py:meth:`~qtmacs.qtmacsmain.QtmacsMain.qteNextApplet`
* :py:meth:`~qtmacs.qtmacsmain.QtmacsMain.qteNewApplet`
* :py:meth:`~qtmacs.qtmacsmain.QtmacsMain.qteAddMiniApplet`
* :py:meth:`~qtmacs.qtmacsmain.QtmacsMain.qteKillMiniApplet`
* :py:meth:`~qtmacs.qtmacsmain.QtmacsMain.qteRegisterApplet`
* :py:meth:`~qtmacs.qtmacsmain.QtmacsMain.qteGetAllAppletIDs`
* :py:meth:`~qtmacs.qtmacsmain.QtmacsMain.qteGetAllAppletNames`
* :py:meth:`~qtmacs.qtmacsmain.QtmacsMain.qteGetAppletHandle`
* :py:meth:`~qtmacs.qtmacsmain.QtmacsMain.qteMakeAppletActive`

Macros
------
* :py:meth:`~qtmacs.qtmacsmain.QtmacsMain.qteRunMacro`
* :py:meth:`~qtmacs.qtmacsmain.QtmacsMain.qteRegisterMacro`
* :py:meth:`~qtmacs.qtmacsmain.QtmacsMain.qteIsMacroRegistered`
* :py:meth:`~qtmacs.qtmacsmain.QtmacsMain.qteGetMacroObject`
* :py:meth:`~qtmacs.qtmacsmain.QtmacsMain.qteGetAllMacroNames`

Hooks
-----
* :py:meth:`~qtmacs.qtmacsmain.QtmacsMain.qteRunHook`
* :py:meth:`~qtmacs.qtmacsmain.QtmacsMain.qteConnectHook`
* :py:meth:`~qtmacs.qtmacsmain.QtmacsMain.qteDisconnectHook`

Key Processing
--------------
* :py:meth:`~qtmacs.qtmacsmain.QtmacsMain.qteBindKeyGlobal`
* :py:meth:`~qtmacs.qtmacsmain.QtmacsMain.qteBindKeyApplet`
* :py:meth:`~qtmacs.qtmacsmain.QtmacsMain.qteBindKeyWidget`
* :py:meth:`~qtmacs.qtmacsmain.QtmacsMain.qteUnbindKeyApplet`
* :py:meth:`~qtmacs.qtmacsmain.QtmacsMain.qteUnbindKeyFromWidgetObject`
* :py:meth:`~qtmacs.qtmacsmain.QtmacsMain.qteUnbindAllFromApplet`
* :py:meth:`~qtmacs.qtmacsmain.QtmacsMain.qteUnbindAllFromWidgetObject`
* :py:meth:`~qtmacs.qtmacsmain.QtmacsMain.qteCopyGlobalKeyMap`

Other
-----
* :py:meth:`~qtmacs.qtmacsmain.QtmacsMain.qteUpdate`
* :py:meth:`~qtmacs.qtmacsmain.QtmacsMain.qteImportModule`
* :py:meth:`~qtmacs.qtmacsmain.QtmacsMain.qteCloseQtmacs`
* :py:meth:`~qtmacs.qtmacsmain.QtmacsMain.qteStatus`
* :py:meth:`~qtmacs.qtmacsmain.QtmacsMain.qteDefVar`
* :py:meth:`~qtmacs.qtmacsmain.QtmacsMain.qteGetVariableDoc`
* :py:meth:`qteDisableMacroProcessing()
  <qtmacs.qtmacsmain.QtmacsEventFilter.qteDisableMacroProcessing>`
* :py:meth:`qteEnableMacroProcessing()
  <qtmacs.qtmacsmain.QtmacsEventFilter.qteEnableMacroProcessing>`
* :py:meth:`~qtmacs.qtmacsmain.QtmacsMain.qteEmulateKeypresses`
* :py:meth:`~qtmacs.qtmacsmain.QtmacsMain.qteIsMiniApplet`


QtmacsApplet
============
The following methods are only available from inside the 
:py:mod:`QtmacsApplet <qtmacs.base_applet.QtmacsApplet>` class.

* :py:meth:`~qtmacs.base_applet.QtmacsApplet.qteParentWindow`
* :py:meth:`~qtmacs.base_applet.QtmacsApplet.qteAddWidget`
* :py:meth:`~qtmacs.base_applet.QtmacsApplet.qteSetAppletSignature`
* :py:meth:`~qtmacs.base_applet.QtmacsApplet.qteAppletSignature`
* :py:meth:`~qtmacs.base_applet.QtmacsApplet.qteSetWidgetFocusOrder`
* :py:meth:`~qtmacs.base_applet.QtmacsApplet.qteNextWidget`
* :py:meth:`~qtmacs.base_applet.QtmacsApplet.qteMakeWidgetActive`
* :py:meth:`~qtmacs.base_applet.QtmacsApplet.qteAppletID`
* :py:meth:`~qtmacs.base_applet.QtmacsApplet.qteIsVisible`
* :py:meth:`~qtmacs.base_applet.QtmacsApplet.qteSetReadyToKill`
* :py:meth:`~qtmacs.base_applet.QtmacsApplet.qteReadyToKill`


QtmacsMacro
===========
The following methods are only available from inside the 
:py:mod:`QtmacsMacro <qtmacs.base_macro.QtmacsMacro>` class.

* :py:meth:`~qtmacs.base_macro.QtmacsMacro.qteMacroName`
* :py:meth:`~qtmacs.base_macro.QtmacsMacro.qteSaveMacroData`
* :py:meth:`~qtmacs.base_macro.QtmacsMacro.qteMacroData`
* :py:meth:`~qtmacs.base_macro.QtmacsMacro.qteAppletSignature`
* :py:meth:`~qtmacs.base_macro.QtmacsMacro.qteWidgetSignature`
* :py:meth:`~qtmacs.base_macro.QtmacsMacro.qteSetAppletSignature`
* :py:meth:`~qtmacs.base_macro.QtmacsMacro.qteSetWidgetSignature`

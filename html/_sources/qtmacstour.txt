.. _QtmacsTour:

A Brief Tour of Qtmacs
======================

This tour guide is as alpha as Qtmacs itself but Emacs users should feel
right at home.

To cycle through applets press ``<ctrl>+n``, and to execute a macro by
name press ``<alt>+x`` (use ``<tab>`` to get a list all macros and/or
auto-complete the input).

To spawn a new applet press ``<alt>+x`` and type `new-applet`. In the
newly spawned input query at the bottom hit ``<tab>`` again to see the
available applets. Alternatively, you may use the shortcut ``<ctrl>+x
<ctrl>+a`` to get directly to the applet query.

Most commands can be aborted with ``<ctrl>+g``. For instance, if the
macro query is open (``<alt>+x``) you can abort the action with
``<ctrl>+g``.

Next, spawn the `DemoMultiWidget` applet (``<ctrl>+x <ctrl>+a`` and then
type `DemoMultiWidget`). It consists of three widgets and you can cycle
the focus through them with ``<ctrl>+x <ctrl>+o``, just as you can cycle
through open applets with ``<ctrl>+x <ctrl>+n``.

Applets can also be split to display more than one at a time. For the
following demonstration to work ensure there are at least three open
applets. Then press ``<ctrl>+x 2`` to split the active applet
vertically, and ``<ctrl>+x 3`` to split it again horizontally. To cycle
through the currently visible applets use ``<ctrl>+x o``, or hide all
but the current applet with ``<ctrl>+x 1``.

To open a new window issue the `new-window` macro (``<alt>+x``, then
type `new-window`).

.. note:: Qtmacs cannot show the same applet more than once because
	  Qt does not support this feature.

To close a window run the `kill-window` macro (``<alt>+x`` and then
type `kill-window`). Similarly, to kill the active applet press
``<ctrl>+x k``, and to kill Qtmacs as whole use ``<ctrl>+x <ctrl>+c``.

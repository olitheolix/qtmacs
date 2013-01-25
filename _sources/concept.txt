.. _Concept:

=======
Concept
=======

Qtmacs is built around Qt widgets in general. The widgets can be
logically grouped into *applets* where they provide the means
to eg. edit text, show an image, browse the web, or display a directory
in a tree view.

By default, all widgets react to keyboard events as
usual. Alternatively, Qtmacs can also intercept these events for individual
widgets, parse them for shortcuts, and execute associated macros.

Macros, in turn, can contain any code and do as they
please. Nevertheless, they tend to leverage the existing widget
functionality to achieve a particular effect, for instance insert a
character, scroll an image, or navigate a tree view without the
mouse. Since macros can be swapped out at run-time and bound to
arbitrary keyboard shortcuts, the widget- and applet behaviour can be
customised as desired.

In terms of functionality, applets may implement anything that is
possible with Qt, including text editors, PDF viewers, shells, audio-
and movie players, paint programs, web browsers, version control
clients, database frontends, games...


Qtmacs is not Emacs
===================

Qtmacs inherits the *everything-is-a-macro* concept from Emacs but
does not strive to be feature- or code compatible with it.

Qtmacs is also not about editing text. Instead, it is about the ability
to customise the interactions with Qt based GUI programs (ie. applets) as
the user sees fit.

Among these applets is currently the SciEditor. Its macros do indeed
strive to emulate the basic text editing features of Emacs but they may
nevertheless be swapped out for other macros to emulate anything from
Notepad to Vi.

Ultimately, the user -- and only the user -- decides which applets to
load and, consequently, the functionality of Qtmacs. If none of the
applets pertains to text editing, then so be it.

What Qtmacs therefore can and will become is still everybody's guess,
but I intend to find out.

Current State
=============
No major changes to the engine or the API are anticipated at the moment.
The current focus is on developing and improving applets.

Next Steps
==========
Qtmacs should eventually facilitate its own development. The primary
obstacles towards this goal are the lack of applets and SciEditor
macros.

Some of the applets I would like to eventually have are

* version control (something as useful as Magit would be great),
* various shells (Bash, Matlab, Octave, Mathematica),
* IPython (using its qtconsole, or notebook, or both; `Spyder
  <https://code.google.com/p/spyderlib/>`_ is a good example),
* mature PDF reader (ideally without the Poppler installation hassles),
* mature browser with the ability to edit web forms like the SciEditor
  (within reason),
* anything else someone deems useful, or fun, or both.

Max - The Qtmacs Mascot
=======================

The Qtmacs mascot, *Max*, is the result of `pronouncing Qt
<http://en.wikipedia.org/wiki/Qt_(framework)>`_ as "Cute", a bad pun,
and flawed logic: from "Qtmacs" to "Cute-macs" to "Cute Max". Flawed
logic then insists on a cute girl called Max as the project logo.

To draw (or improve) Max yourself, I recommend `this clip
<www.youtube.com/watch?v=DFLgr6gyOOc>`_ .

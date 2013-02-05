.. _Installation:

==============
Getting Qtmacs
==============

System Requirements
====================

Qtmacs is currently developed with:

* Python 3.2,
* PyQt 4.8.

Older versions of PyQt and Python *may* work as well, but Python 3.x is
mandatory. Qtmacs should run on any platform supported by Python,
and PyQt4 (ie. at least Linux/X11, Windows, and Mac).

.. note:: Optional applets may require extra libraries (eg. the PDF
	  applet requires `Poppler`).


Binary Installation
===================

Windows 7 & 8
-------------
You need `Python 3 <http://python.org>`_ and the matching
`PyQt-Py3.x <http://riverbankcomputing.com/software/pyqt/download>`_
library. Only the 3.2 versions of Python and PyQt4 have been tested but
3.3 should work as well. For Python 3.2 proceed as follows:

* Install `Python 3.2 <http://www.python.org/download/releases/3.2.3/>`_
* Install `PyQt-Py3.2
  <http://riverbankcomputing.com/software/pyqt/download>`_ and use the 
  `Full Installation` option when asked (it is the default).

Then download the Qtmacs installer from `here
<http://pypi.python.org/pypi/qtmacs/0.1.0>`_.


(K)Ubuntu
---------
These instructions were tested on `Ubuntu 12.10
<http://www.ubuntu.com>`_ and `Kubuntu 12.10 <http://www.kubuntu.org>`_.

As root, install Qtmacs with the following commands:

.. code-block:: bash

  sudo apt-get install python3-pip python3-pyqt4.qsci
  pip-3.2 install qtmacs

Then start Qtmacs from the command line with

.. code-block:: bash

  qtmacs


Fedora
------

These instructions were tested on `Fedora 18
<http://fedoraproject.org/>`_

As root, install Qtmacs with the following commands:

.. code-block:: bash

  yum install python3-pip python3-PyQt4
  python3-pip install qtmacs

Then start Qtmacs from the command line with

.. code-block:: bash

  qtmacs

.. note: In Fedora 18 the python3-qscintilla is not (yet) available
   which means that the SciEditor applet will not work. A workaround
   is provides here https://bugzilla.redhat.com/show_bug.cgi?id=808911


OpenSuse
--------

These instructions were tested on `openSUSE 12.2
<http://en.opensuse.org/Portal:12.2>`_ (Gnome edition).

As root, install Qtmacs with the following commands:

.. code-block:: bash

  zypper in python3-qscintilla python3-pip python3-xml
  pip-3.2 install qtmacs

Then start Qtmacs from the command line with


.. code-block:: bash

  qtmacs


Source Installation
===================

To work directly with the source code:

.. code-block:: bash

   git clone https://github.com/qtmacsdev/qtmacs.git
   cd qtmacs/bin
   ./qtmacs

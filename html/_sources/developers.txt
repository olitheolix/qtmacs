.. _Contribute:

**********
Developers
**********

.. _Styleguide:

Style Guide
===========

* The coding style is `PEP8
  <http://www.python.org/dev/peps/pep-0008/>`_ with
  :ref:`these exceptions <PEP8Exceptions>`,
* every module and non-trivial method must be documented,
* code must be annotated (the `Google style guide 
  <http://google-styleguide.googlecode.com/svn/trunk/pyguide.html>`_ has
  good examples),
* method- and attribute names in Qt classes should be prefixed with "*qte*"
  (eg. `qteMyMethod` instead of just `myMethod`) to avoid
  name clashes with Qt,
* the code must run under Python 3.

As for the documentation style, please look at existing code for
templates (the `qtmacs/qtmacsmain.py` file is a good example). 

A style checker like `pytest <http://pytest.org/latest/>`_ (see
`here <http://pypi.python.org/pypi/pytest-pep8>`_ for installation and
usage) is also useful to spot `PEP8
<http://www.python.org/dev/peps/pep-0008/>`_ violations.

.. _PEP8Exceptions:

PEP8 Exception
---------------
Class methods, method arguments, and attributes use the Qt convention
to maintain some consistency within Qtmacs. This means that all methods
and all their arguments use camel case notation instead of underscores
(eg. *thisIsMyMethod* instead of *this_is_my_method*). However, local
variables may use either style depending on preference.


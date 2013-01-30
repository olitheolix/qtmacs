"""
Place a shortcut to Qtmacs on the windows desktop.

A Visual Basic script is used to actually place the shortcut because
I could not figure out how to use the built in create_shortcut method
properly.

The external VB script (`mkshortcut`) is based on
http://www.computerhope.com/forum/index.php?topic=130603.0
and invoked from the Windows command line with

.. code-block:: bash

   mkshortcut /src:myapp /dest:foo/myapp /desc:description /icon:path/icon.ico

.. note:: This script is supposed to be called upon deinstallation as
          well but this does not appear to be the case.

This script can be used with the `bdist_msi` and `bdist_wininst` arguments
to `setup.py` when creating the package, eg.

.. code-block:: bash

   python3 setup.py bdist_wininst --install-script postinstallation_windows.py

"""

#!python
import os
import sys
import imp
import subprocess

# Define a shortcut.
pjoin = os.path.join


def install():
    # Path to the scripts directory (the install script will copy
    # the 'qtmacs' and 'mkshortcut.vbs' files there).
    script = pjoin(sys.prefix, 'Scripts')

    # Locate the user's desktop directory.
    desk = pjoin(os.environ['HOMEPATH'], 'Desktop')

    # Construct the destination path (ie. the desktop).
    dest = pjoin(desk, 'Qtmacs')

    # In Python's scripts directory rename `qtmacs` to
    # `qtmacs_start.pyw` to avoid problems when importing the
    # equally named 'qtmacs' package from that script (does
    # not appear to be a problem on Unix based systems).
    src_old = pjoin(script, 'qtmacs')
    src = pjoin(script, 'qtmacs_startup.pyw')
    os.rename(src_old, src)
    file_created(src)

    # Locate the qtmacs module and 'misc' folder inside it.
    try:
        fp, path, desc = imp.find_module('qtmacs')
    except ImportError:
        # Currently unhandled.
        pass
    finally:
        if fp:
            fp.close()
    misc_path = pjoin(path, 'misc')

    # Construct the path to mkshortcut.vbs in the scripts directory.
    mks = pjoin(misc_path, 'mkshortcut.vbs')

    # Construct the path to icon in the scripts directory.
    icon = pjoin(misc_path, 'Max.ico')

    # Define the description carried by the shortcut.
    desc = "Qtmacs"

    # Assemble and execute 'mkshortcut' parameters to actually
    # create the shortcut on the desktop.
    cmd = (mks
           + ' /src:' + src
           + ' /dest:' + dest
           + ' /desc:' + desc
           + ' /icon:' + icon)
    subprocess.call(cmd, shell=True)


def uninstall():
    pass


# If no command line argument was given then call the install routine.
# This case is basically to comply with the bdist_msi routine event
# though the generated files cannot be uploaded to PyPi for whatever
# reason.
if len(sys.argv) < 2:
    install()
    sys.exit(0)

if sys.argv[1] == '-install':
    install()
elif sys.argv[1] == '-remove':
    uninstall()
else:
    sys.exit(1)

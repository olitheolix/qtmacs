from distutils.core import setup

setup(
    name='qtmacs',
    version='0.1.0',
    author='Oliver Nagy',
    author_email='qtmacsdev@gmail.com',
    url='https://github.com/qtmacsdev/qtmacs',
    description='An Emacs inspired macro framework for Qt.',
    license='GPLv3',
    packages=['qtmacs', 'qtmacs/applets',
              'qtmacs/extensions', 'qtmacs/miniapplets'],
    package_data={'qtmacs': ['misc/*']},
    scripts=['bin/qtmacs', 'postinstall_windows.py'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Text Editors :: Emacs',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development',
        'Topic :: Software Development :: User Interfaces',
        'Topic :: Software Development :: Widget Sets',
        'Topic :: Utilities',
    ],
)

#!/usr/bin/env python

from distutils.core import setup, Extension

setup(name='Mirage',
        version='0.7.3',
        description='A fast GTK+ image viewer',
        author='Scott Horowitz',
        author_email='stonecrest@gmail.com',
        url='http://mirageiv.berlios.de',
        classifiers=[
            'Environment :: X11 Applications',
            'Intended Audience :: End Users/Desktop',
            'License :: GNU General Public License (GPL)',
            'Operating System :: Linux',
            'Programming Language :: Python',
            'Topic :: Multimedia :: Graphics :: Viewers'
            ],
        py_modules = ['mirage'],
	ext_modules = [Extension('imgfuncs', ['imgfuncs.c'])],
        scripts = ['mirage'],
        data_files=[('share/mirage', ['README', 'COPYING', 'CHANGELOG', 'stock_shuffle.png']),
                    ('share/applications', ['mirage.desktop']),
                    ('share/pixmaps', ['mirage.png', 'mirage_large.png']),
		    ('share/locale/pl/LC_MESSAGES', ['locale/pl/LC_MESSAGES/mirage.mo']),
		    ('share/locale/fr/LC_MESSAGES', ['locale/fr/LC_MESSAGES/mirage.mo']),
		    ('share/locale/es/LC_MESSAGES', ['locale/es/LC_MESSAGES/mirage.mo']),
		    ('share/locale/de/LC_MESSAGES', ['locale/de/LC_MESSAGES/mirage.mo'])],
        )

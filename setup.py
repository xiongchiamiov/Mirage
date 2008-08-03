#!/usr/bin/env python

# $HeadURL$
# $Id$

import os

from distutils.core import setup, Extension

def removeall(path):
	if not os.path.isdir(path):
		return

	files=os.listdir(path)

	for x in files:
		fullpath=os.path.join(path, x)
		if os.path.isfile(fullpath):
			f=os.remove
			rmgeneric(fullpath, f)
		elif os.path.isdir(fullpath):
			removeall(fullpath)
			f=os.rmdir
			rmgeneric(fullpath, f)

def rmgeneric(path, __func__):
	try:
		__func__(path)
	except OSError, (errno, strerror):
		pass

# Create mo files:
if not os.path.exists("mo/"):
	os.mkdir("mo/")
for lang in ('it', 'de', 'pl', 'es', 'fr', 'ru', 'hu', 'cs', 'pt_BR', 'zh_CN'):
	pofile = "po/" + lang + ".po"
	mofile = "mo/" + lang + "/mirage.mo"
	if not os.path.exists("mo/" + lang + "/"):
		os.mkdir("mo/" + lang + "/")
	print "generating", mofile
	os.system("msgfmt %s -o %s" % (pofile, mofile))

setup(name='Mirage',
		version='0.9.3',
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
		ext_modules = [Extension(name='imgfuncs', sources=['imgfuncs.c']), 
		               Extension(name='xmouse', sources=['xmouse.c'], libraries=['X11'])],
		scripts = ['mirage'],
		data_files=[('share/mirage', ['README', 'COPYING', 'CHANGELOG', 'TODO', 'TRANSLATORS', 'stock_shuffle.png', 'stock_leave-fullscreen.png', 'stock_fullscreen.png', 'mirage_blank.png']),
			('share/applications', ['mirage.desktop']),
			('share/pixmaps', ['mirage.png']),
			('share/locale/ru/LC_MESSAGES', ['mo/ru/mirage.mo']),
			('share/locale/pl/LC_MESSAGES', ['mo/pl/mirage.mo']),
			('share/locale/fr/LC_MESSAGES', ['mo/fr/mirage.mo']),
			('share/locale/es/LC_MESSAGES', ['mo/es/mirage.mo']),
			('share/locale/de/LC_MESSAGES', ['mo/de/mirage.mo']),
			('share/locale/hu/LC_MESSAGES', ['mo/hu/mirage.mo']),
			('share/locale/cs/LC_MESSAGES', ['mo/cs/mirage.mo']),
			('share/locale/pt_BR/LC_MESSAGES', ['mo/pt_BR/mirage.mo']),
			('share/locale/zh_CN/LC_MESSAGES', ['mo/zh_CN/mirage.mo']),
			('share/locale/it/LC_MESSAGES', ['mo/it/mirage.mo'])],
		)

# Cleanup (remove /build, /mo, and *.pyc files:
print "Cleaning up..."
try:
	removeall("build/")
	os.rmdir("build/")
except:
	pass
try:
	removeall("mo/")
	os.rmdir("mo/")
except:
	pass
try:
	for f in os.listdir("."):
		if os.path.isfile(f):
			if os.path.splitext(os.path.basename(f))[1] == ".pyc":
				os.remove(f)
except:
	pass

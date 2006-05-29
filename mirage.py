#!/usr/bin/env python

__version__ = "0.6"

__license__ = """
Mirage, a simple GTK+ Image Viewer
Copyright 2006 Scott Horowitz <stonecrest@gmail.com>

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the Free
Software Foundation; either version 2 of the License, or (at your option)
any later version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
more details.

You should have received a copy of the GNU General Public License along with
this program; if not, write to the Free Software Foundation, Inc., 59 Temple
Place, Suite 330, Boston, MA  02111-1307  USA.
"""

import pygtk
pygtk.require('2.0')
import gtk
import gtk.gdk
import os
import sys, getopt
import ConfigParser
import string
import gc
import random
import imgfuncs
import urllib
import sets
import gobject

class Base:

	def __init__(self):
	
		# Constants
		self.open_mode_smart = 0
		self.open_mode_fit = 1
		self.open_mode_1to1 = 2
		self.open_mode_last = 3
		self.max_zoomratio = 5       # 5 x self.zoomratio_for_zoom_to_fit
		self.min_zoomratio = 0.1     # 0.1 x self.zoomratio_for_zoom_to_fit

		# Initialize vars:
		self.userimage = ""
		width=600
		height=400
		self.toolbar_show = True
		self.statusbar_show = True
		self.fullscreen_mode = False
		self.opendialogpath = ""
		self.zoom_quality = gtk.gdk.INTERP_BILINEAR
		bgcolor_found = False
		self.recursive = False
		self.verbose = False
		self.image_loaded = False
		self.open_all_images = False
		self.use_last_dir = True
		self.last_dir = os.path.expanduser("~")
		self.fixed_dir = os.path.expanduser("~")
		self.image_list = []
		self.open_mode = self.open_mode_smart
		self.last_mode = self.open_mode_smart
		self.zoomratio = 1
		self.zoomratio_for_zoom_to_fit = 1
		self.curr_img_in_list = 0
		self.mousewheel_nav = True
		self.currimg_width = 0
		self.currimg_height = 0

		# Read any passed options/arguments:
		try:
			opts, args = getopt.getopt(sys.argv[1:], "hRvV", ["help", "version", "recursive", "verbose"])
		except getopt.GetoptError:
			# print help information and exit:
			self.print_usage()
			sys.exit(2)
		# If options were passed, perform action on them:
		if opts != []:
			for o, a in opts:
				if o in ("-v", "--version"):
					self.print_version()
					sys.exit(2)
				elif o in ("-h", "--help"):
					self.print_usage()
					sys.exit(2)
				elif o in ("-R", "--recursive"):
					self.recursive = True
				elif o in ("-V", "--verbose"):
					self.verbose = True
				else:
					self.print_usage()
					sys.exit(2)

		# Load config from disk:
		conf = ConfigParser.ConfigParser()
		if os.path.isfile(os.path.expanduser('~/.config/mirage/miragerc')):
			conf.read(os.path.expanduser('~/.config/mirage/miragerc'))
		elif os.path.isfile(os.path.expanduser('~/.miragerc')):
			conf.read(os.path.expanduser('~/.miragerc'))
			os.remove(os.path.expanduser('~/.miragerc'))
		try:
			width = conf.getint('window', 'w')
			height = conf.getint('window', 'h')
			self.toolbar_show = conf.getboolean('window', 'toolbar')
			self.statusbar_show = conf.getboolean('window', 'statusbar')
			self.zoom_quality = conf.get('prefs', 'quality')
			if str(self.zoom_quality) == str(gtk.gdk.INTERP_NEAREST):
				self.zoom_quality = gtk.gdk.INTERP_NEAREST
			elif str(self.zoom_quality) == str(gtk.gdk.INTERP_TILES):
				self.zoom_quality = gtk.gdk.INTERP_TILES
			elif str(self.zoom_quality) == str(gtk.gdk.INTERP_BILINEAR):
				self.zoom_quality = gtk.gdk.INTERP_BILINEAR
			elif str(self.zoom_quality) == str(gtk.gdk.INTERP_HYPER):
				self.zoom_quality = gtk.gdk.INTERP_HYPER
			bgr = conf.getint('prefs', 'bgcolor-red')
			bgg = conf.getint('prefs', 'bgcolor-green')
			bgb = conf.getint('prefs', 'bgcolor-blue')
			bgcolor_found = True
			self.bgcolor = gtk.gdk.Color(red=bgr, green=bgg, blue=bgb)
			self.use_last_dir = conf.getboolean('prefs', 'use_last_dir')
			self.last_dir = conf.get('prefs', 'last_dir')
			self.fixed_dir = conf.get('prefs', 'fixed_dir')
			self.open_all_images = conf.getboolean('prefs', 'open_all')
			self.open_mode = conf.getint('prefs', 'open_mode')
			self.last_mode = conf.getint('prefs', 'last_mode')
			self.mousewheel_nav = conf.getboolean('prefs', 'mousewheel')
		except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
                        pass

		# Define the main menubar and toolbar:
		actions = (  
			('FileMenu', None, '_File'),  
			('ViewMenu', None, '_View'),  
			('ImageMenu', None, '_Image'),  
			('GoMenu', None, '_Go'),  
			('HelpMenu', None, '_Help'),  
			('ToolsMenu', None, '_Tools'),  
			('Open Image', gtk.STOCK_OPEN, '_Open Image', '<control>O', 'Open Image', self.open_file),  
			('Open Folder', gtk.STOCK_DIRECTORY, 'Open _Folder', '<control>F', 'Open Folder', self.open_folder),  
			('Exit', gtk.STOCK_QUIT, 'E_xit', '<control>Q', 'Exit', self.exit_app),  
			('Previous Image', gtk.STOCK_GO_BACK, '_Previous Image', 'Left', 'Previous Image', self.prev_img_in_list),  
			('Next Image', gtk.STOCK_GO_FORWARD, '_Next Image', 'Right', 'Next Image', self.next_img_in_list),  
			('Previous2', gtk.STOCK_GO_BACK, '_Previous', 'Left', 'Previous', self.prev_img_in_list),  
			('Next2', gtk.STOCK_GO_FORWARD, '_Next', 'Right', 'Next', self.next_img_in_list),  
			('Random Image', None, '_Random Image', 'R', 'Random Image', self.random_img_in_list),  
			('First Image', None, '_First Image', 'Home', 'First Image', self.first_img_in_list),  
			('Last Image', None, '_Last Image', 'End', 'Last Image', self.last_img_in_list),  
			('In', gtk.STOCK_ZOOM_IN, 'Zoom _In', '<Ctrl>Up', 'Zoom In', self.zoom_in),  
			('Out', gtk.STOCK_ZOOM_OUT, 'Zoom _Out', '<Ctrl>Down', 'Zoom Out', self.zoom_out),  
			('Fit', gtk.STOCK_ZOOM_FIT, 'Zoom To _Fit', '<Ctrl>0', 'Fit', self.zoom_to_fit_window),  
			('1:1', gtk.STOCK_ZOOM_100, '_1:1', '<Ctrl>1', '1:1', self.zoom_1_to_1),  
			('Rotate Left', None, 'Rotate _Left', '<Ctrl>Left', 'Rotate Left', self.rotate_left),  
			('Rotate Right', None, 'Rotate _Right', '<Ctrl>Right', 'Rotate Right', self.rotate_right),  
			('Flip Vertically', None, 'Flip _Vertically', '<Ctrl>V', 'Flip Vertically', self.image_flip_vert),  
			('Flip Horizontally', None, 'Flip _Horizontally', '<Ctrl>H', 'Flip Horizontally', self.image_flip_horiz),  
			('About', gtk.STOCK_ABOUT, '_About', 'F1', 'About', self.show_about),  
			('Options', gtk.STOCK_PREFERENCES, '_Options', None, 'Options', self.show_prefs),  
			('Full Screen', gtk.STOCK_FULLSCREEN, '_Full Screen', '<Shift>Return', 'Full Screen', self.toggle_fullscreen),
			('Exit Full Screen', gtk.STOCK_FULLSCREEN, 'E_xit Full Screen', None, 'Full Screen', self.toggle_fullscreen),
			)
		toggle_actions = (
			('Status Bar', None, '_Status Bar', None, 'Status Bar', self.toggle_status_bar, self.statusbar_show),  
			('Toolbar', None, '_Toolbar', None, 'Toolbar', self.toggle_toolbar, self.toolbar_show),  
				)
		uiDescription = """  
			<ui>  
			  <popup name="Popup">
			    <menuitem action="Next Image"/>
			    <menuitem action="Previous Image"/>
			    <separator name="FM1"/> 
			    <menuitem action="Out"/>
			    <menuitem action="In"/>
			    <menuitem action="1:1"/>
			    <menuitem action="Fit"/>
			    <separator name="FM2"/>  
			    <menuitem action="Rotate Left"/>
			    <menuitem action="Rotate Right"/>
			    <separator name="FM3"/>  
			    <menuitem action="Flip Vertically"/>
			    <menuitem action="Flip Horizontally"/>
			    <separator name="FM4"/>
			    <menuitem action="Exit Full Screen"/>
			  </popup>
			  <menubar name="MainMenu">
			    <menu action="FileMenu">  
			      <menuitem action="Open Image"/>  
			      <menuitem action="Open Folder"/>  
			      <separator name="FM1"/>  
			      <menuitem action="Exit"/>  
			    </menu>
			    <menu action="ViewMenu">
			      <menuitem action="Toolbar"/>
			      <menuitem action="Status Bar"/>
			      <separator name="FM1"/>  
			      <menuitem action="Full Screen"/>
			   </menu>
			    <menu action="GoMenu">
			      <menuitem action="Next Image"/>
			      <menuitem action="Previous Image"/>
			      <menuitem action="Random Image"/>
			      <separator name="FM1"/>
			      <menuitem action="First Image"/>
			      <menuitem action="Last Image"/>
			    </menu>
			    <menu action="ImageMenu">
			      <menuitem action="Out"/>
			      <menuitem action="In"/>
			      <menuitem action="1:1"/>
			      <menuitem action="Fit"/>
			      <separator name="FM1"/>  
			      <menuitem action="Rotate Left"/>
			      <menuitem action="Rotate Right"/>
			      <separator name="FM2"/>  
			      <menuitem action="Flip Vertically"/>
			      <menuitem action="Flip Horizontally"/>
			    </menu>
			    <menu action="ToolsMenu">  
			      <menuitem action="Options"/>  
			    </menu>  
			    <menu action="HelpMenu">  
			      <menuitem action="About"/>  
			    </menu>  
			  </menubar>  
			  <toolbar name="MainToolbar">  
			    <toolitem action="Open Image"/>  
			    <separator name="FM1"/> 
			    <toolitem action="Out"/>
			    <toolitem action="In"/>
			    <toolitem action="1:1"/>
			    <toolitem action="Fit"/>
			    <separator name="FM2"/> 
			    <toolitem action="Previous2"/>
			    <toolitem action="Next2"/>
			  </toolbar>
			</ui>  
			"""


		# Create interface
		self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
		self.window.set_title("Mirage")
		iconname = 'mirage.png'
		if os.path.exists(iconname):
			icon_path = iconname
		elif os.path.exists('../share/pixmaps/' + iconname):
			icon_path = '../share/pixmaps/' + iconname
		elif os.path.exists('/usr/local/share/pixmaps/' + iconname):
			icon_path = '/usr/local/share/pixmaps/' + iconname
		elif os.path.exists('/usr/share/pixmaps/' + iconname):
			icon_path = '/usr/share/pixmaps/' + iconname
		try:
			gtk.window_set_default_icon_from_file(icon_path)
		except:
			pass
		vbox = gtk.VBox(False, 0)
		self.UIManager = gtk.UIManager()
		actionGroup = gtk.ActionGroup('Actions')
		actionGroup.add_actions(actions)
		actionGroup.add_toggle_actions(toggle_actions)
		self.UIManager.insert_action_group(actionGroup, 0)
		self.UIManager.add_ui_from_string(uiDescription)
		self.window.add_accel_group(self.UIManager.get_accel_group())
		self.menubar = self.UIManager.get_widget('/MainMenu')
		self.UIManager.get_widget('/Popup/FM4').hide()
		self.UIManager.get_widget('/Popup/Exit Full Screen').hide()
		vbox.pack_start(self.menubar, False, False, 0)
		self.toolbar = self.UIManager.get_widget('/MainToolbar')
		vbox.pack_start(self.toolbar, False, False, 0)
		self.toolbar.set_property('visible', self.toolbar_show)
		self.layout = gtk.Layout()
		self.vscroll = gtk.VScrollbar(None)
		self.vscroll.set_adjustment(self.layout.get_vadjustment())
		self.hscroll = gtk.HScrollbar(None)
		self.hscroll.set_adjustment(self.layout.get_hadjustment())
		self.table = gtk.Table(2, 2, False)
		self.table.attach(self.layout, 0, 1, 0, 1, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
		self.table.attach(self.hscroll, 0, 1, 1, 2, gtk.FILL|gtk.SHRINK, gtk.FILL|gtk.SHRINK, 0, 0)
		self.table.attach(self.vscroll, 1, 2, 0, 1, gtk.FILL|gtk.SHRINK, gtk.FILL|gtk.SHRINK, 0, 0)
		vbox.pack_start(self.table, True, True, 0)
		if bgcolor_found == False:
			self.bgcolor = self.layout.rc_get_style().bg[gtk.STATE_NORMAL] # Initializes color to user's default rc_style
		self.layout.modify_bg(gtk.STATE_NORMAL, self.bgcolor)
		self.imageview = gtk.Image()
		self.layout.add(self.imageview)
		self.statusbar = gtk.Statusbar()
		vbox.pack_start(self.statusbar, False, False, 0)
		self.statusbar.set_has_resize_grip(True)
		self.statusbar.set_property('visible', self.statusbar_show)
		self.window.add(vbox)
		self.window.set_property('allow-shrink', False)
		self.window.set_default_size(width,height)

		# Connect signals
		self.window.connect("delete_event", self.delete_event)
		self.window.connect("destroy", self.destroy)
		self.window.connect("size-allocate", self.window_resized)
		self.window.connect('key-press-event', self.topwindow_keypress)
		self.layout.drag_dest_set(gtk.DEST_DEFAULT_HIGHLIGHT | gtk.DEST_DEFAULT_DROP, [("text/uri-list", 0, 80)], gtk.gdk.ACTION_DEFAULT)
		self.layout.connect('drag_motion', self.motion_cb)
		self.layout.connect('drag_data_received', self.drop_cb)
		self.layout.add_events(gtk.gdk.KEY_PRESS_MASK | gtk.gdk.POINTER_MOTION_MASK | gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.BUTTON_MOTION_MASK | gtk.gdk.SCROLL_MASK)
		self.layout.connect("scroll-event", self.mousewheel_scrolled)
		self.layout.add_events(gtk.gdk.BUTTON_PRESS_MASK | gtk.gdk.KEY_PRESS_MASK)
		self.layout.connect("button_press_event", self.button_pressed)
		self.layout.add_events(gtk.gdk.POINTER_MOTION_MASK | gtk.gdk.POINTER_MOTION_HINT_MASK | gtk.gdk.BUTTON_RELEASE_MASK)
                self.layout.connect("motion-notify-event", self.mouse_moved)
		self.layout.connect("button-release-event", self.button_released)
		self.layout.get_hadjustment().connect("changed", self.x_adjustment_changed)
		self.layout.get_vadjustment().connect("changed", self.y_adjustment_changed)

		# Show GUI:
		self.window.show_all()
		self.layout.set_flags(gtk.CAN_FOCUS)
		self.window.set_focus(self.layout)
		self.hscroll.hide()
		self.vscroll.hide()

		# If arguments (filenames) were passed, try to open them:
		self.image_list = []
		if args != []:
			for i in range(len(args)):
				args[i] = urllib.url2pathname(args[i])
			self.expand_filelist_and_load_image(args)
		else:
			self.set_go_sensitivities(False)
			self.set_image_sensitivities(False)

	def topwindow_keypress(self, widget, event):
		if event.state != gtk.gdk.SHIFT_MASK and event.state != gtk.gdk.CONTROL_MASK and event.state != gtk.gdk.MOD1_MASK and event.state != gtk.gdk.CONTROL_MASK | gtk.gdk.MOD2_MASK:
			if event.keyval == 65361:    # Left arrow
				self.prev_img_in_list(None)
			elif event.keyval == 65363 or event.keyval == 32:  # Right arrow or spacebar
				self.next_img_in_list(None)
			elif event.keyval == 65360:  # Home key
				self.first_img_in_list(None)
			elif event.keyval == 65367:  # End key
				self.last_img_in_list(None)
			#elif event.keyval == 114:    # "R" key
			#	self.random_img_in_list(None)
			elif event.keyval == 65307:  # Escape key
				if self.fullscreen_mode == True:
					self.toggle_fullscreen(None)
		elif event.state == gtk.gdk.CONTROL_MASK or event.state == gtk.gdk.CONTROL_MASK | gtk.gdk.MOD2_MASK:
			if event.keyval == 65456:    # "0" key on numpad
				self.zoom_to_fit_window(None)
			if event.keyval == 65457:    # "1" key on numpad
				self.zoom_1_to_1(None)
				
	def set_go_sensitivities(self, enable):
		self.UIManager.get_widget('/MainMenu/GoMenu/Previous Image').set_sensitive(enable)
		self.UIManager.get_widget('/MainMenu/GoMenu/Next Image').set_sensitive(enable)
		self.UIManager.get_widget('/MainMenu/GoMenu/Random Image').set_sensitive(enable)
		self.UIManager.get_widget('/MainMenu/GoMenu/First Image').set_sensitive(enable)
		self.UIManager.get_widget('/MainMenu/GoMenu/Last Image').set_sensitive(enable)
		self.UIManager.get_widget('/Popup/Previous Image').set_sensitive(enable)
		self.UIManager.get_widget('/Popup/Next Image').set_sensitive(enable)
		self.UIManager.get_widget('/MainToolbar/Previous2').set_sensitive(enable)
		self.UIManager.get_widget('/MainToolbar/Next2').set_sensitive(enable)

	def set_image_sensitivities(self, enable):
		self.UIManager.get_widget('/MainMenu/ImageMenu/Out').set_sensitive(enable)
		self.UIManager.get_widget('/MainMenu/ImageMenu/In').set_sensitive(enable)
		self.UIManager.get_widget('/MainMenu/ImageMenu/1:1').set_sensitive(enable)
		self.UIManager.get_widget('/MainMenu/ImageMenu/Fit').set_sensitive(enable)
		self.UIManager.get_widget('/MainMenu/ImageMenu/Rotate Left').set_sensitive(enable)
		self.UIManager.get_widget('/MainMenu/ImageMenu/Rotate Right').set_sensitive(enable)
		self.UIManager.get_widget('/MainMenu/ImageMenu/Flip Vertically').set_sensitive(enable)
		self.UIManager.get_widget('/MainMenu/ImageMenu/Flip Horizontally').set_sensitive(enable)
		self.UIManager.get_widget('/MainToolbar/Out').set_sensitive(enable)
		self.UIManager.get_widget('/MainToolbar/In').set_sensitive(enable)
		self.UIManager.get_widget('/MainToolbar/1:1').set_sensitive(enable)
		self.UIManager.get_widget('/MainToolbar/Fit').set_sensitive(enable)
		
	def set_zoom_in_sensitivities(self, enable):
		self.UIManager.get_widget('/MainMenu/ImageMenu/In').set_sensitive(enable)
		self.UIManager.get_widget('/MainToolbar/In').set_sensitive(enable)		
		self.UIManager.get_widget('/Popup/In').set_sensitive(enable)

	def set_zoom_out_sensitivities(self, enable):
		self.UIManager.get_widget('/MainMenu/ImageMenu/Out').set_sensitive(enable)
		self.UIManager.get_widget('/MainToolbar/Out').set_sensitive(enable)		
		self.UIManager.get_widget('/Popup/Out').set_sensitive(enable)

	def print_version(self):
		print "Version: Mirage", __version__
		print "Website: http://www.theskyiscrape.com/scott/mirage.html"

	def print_usage(self):
		self.print_version()
		print ""
		print "Usage: mirage [OPTION]... FILES|FOLDERS..."
		print ""
		print "Options:"
		print "  -h, --help                   Show this help and exit"
		print "  -v, --version                Show version information and exit"
		print "  -V, --verbose                Show more detailed information"
		print "  -R, --recursive              Recursively include all images found in"
		print "                               subdirectories of FOLDERS"

	def motion_cb(self, widget, context, x, y, time):
		context.drag_status(gtk.gdk.ACTION_COPY, time)
		return True

	def drop_cb(self, widget, context, x, y, selection, info, time):
		uri = selection.data.strip()
		path = urllib.url2pathname(uri)
		paths = path.rsplit('\n')
		for i, path in enumerate(paths):
			paths[i] = path.rstrip('\r')		
		self.expand_filelist_and_load_image(paths)

	def put_error_image_to_window(self):
		self.imageview.set_from_stock(gtk.STOCK_MISSING_IMAGE, gtk.ICON_SIZE_LARGE_TOOLBAR)
		self.set_go_sensitivities(False)
		self.set_image_sensitivities(False)
		return

	def x_adjustment_changed(self, xadjust):
		try:
			zoomratio = float(self.currimg_width)/self.previmg_width
			newvalue = abs(xadjust.get_value() * zoomratio + (self.available_image_width()) * (zoomratio - 1) / 2)
			if newvalue >= xadjust.lower and newvalue <= (xadjust.upper - xadjust.page_size):
				xadjust.set_value(newvalue)
		except:
			pass

	def y_adjustment_changed(self, yadjust):
		try:
			zoomratio = float(self.currimg_width)/self.previmg_width
			newvalue = abs(yadjust.get_value() * zoomratio + (self.available_image_height()) * (zoomratio - 1) / 2)
			if newvalue >= yadjust.lower and newvalue <= (yadjust.upper - yadjust.page_size):
				yadjust.set_value(newvalue)
			# Since the y adjustment happens after the x adjustment, re-initialize the
			# variables now:
			self.previmg_width = self.currimg_width
		except:
			pass

	def window_resized(self, widget, allocation):
		# Update the image size on window resize if the current image was last fit:
		if self.image_loaded == True:
			if allocation.width != self.prevwinwidth or allocation.height != self.prevwinheight:
				if self.last_image_action_was_fit == True and self.zoomratio != 1:
					self.zoom_to_fit_window(None)
				else:
					self.center_image()
		self.prevwinwidth = allocation.width
		self.prevwinheight = allocation.height
		return

	def save_settings(self):
		rect = self.window.get_allocation()
		conf = ConfigParser.ConfigParser()
		conf.add_section('window')
		conf.set('window', 'w', rect.width)
		conf.set('window', 'h', rect.height)
		conf.set('window', 'toolbar', self.toolbar_show)
		conf.set('window', 'statusbar', self.statusbar_show)
		conf.add_section('prefs')
		conf.set('prefs', 'quality', self.zoom_quality)
		conf.set('prefs', 'bgcolor-red', self.bgcolor.red)
		conf.set('prefs', 'bgcolor-green', self.bgcolor.green)
		conf.set('prefs', 'bgcolor-blue', self.bgcolor.blue)
		conf.set('prefs', 'open_all', self.open_all_images)
		conf.set('prefs', 'use_last_dir', self.use_last_dir)
		conf.set('prefs', 'last_dir', self.last_dir)
		conf.set('prefs', 'fixed_dir', self.fixed_dir)
		conf.set('prefs', 'open_mode', self.open_mode)
		conf.set('prefs', 'last_mode', self.last_mode)
		conf.set('prefs', 'mousewheel_nav', self.mousewheel_nav)
		if os.path.exists(os.path.expanduser('~/.config/mirage/')) == False:
			os.mkdir(os.path.expanduser('~/.config/mirage/'))
		conf.write(file(os.path.expanduser('~/.config/mirage/miragerc'), 'w'))
		return

	def delete_event(self, widget, event, data=None):
		self.save_settings()
		gtk.main_quit()
		return False

	def destroy(self, event, data=None):
		self.save_settings()
		return False

	def put_zoom_image_to_window(self):
		previmg = self.currimg
		# Always start with the original image to preserve quality!
		# Calculate image size:
		finalimg_width = int(self.originalimg.get_width() * self.zoomratio)
		finalimg_height = int(self.originalimg.get_height() * self.zoomratio)
		# If self.zoomratio < 1, scale first so that rotating/flipping is performed
		# on the smaller image for speed improvements
		if self.zoomratio < 1:
			# Scale image:
			if self.originalimg.get_has_alpha() == False:
				self.currimg = self.originalimg.scale_simple(finalimg_width, finalimg_height, self.zoom_quality)
			else:
				colormap = self.imageview.get_colormap()
				light_grey = colormap.alloc_color('#666666', True, True)
				dark_grey = colormap.alloc_color('#999999', True, True)
				self.currimg = self.originalimg.composite_color_simple(finalimg_width, finalimg_height, self.zoom_quality, 255, 8, light_grey.pixel, dark_grey.pixel)		
			# Now check if we need any rotating/flipping
			if self.orientation == 1:
				if self.location == 0:
					self.currimg = self.image_rotate(self.currimg, 270)
					self.currimg = self.image_flip(self.currimg, False)
				elif self.location == 1:
					self.currimg = self.image_rotate(self.currimg, 270)
				elif self.location == 2:
					self.currimg = self.image_rotate(self.currimg, 270)
					self.currimg = self.image_flip(self.currimg, True)
				elif self.location == 3:
					self.currimg = self.image_rotate(self.currimg, 90)
			else:
				if self.location == 1:
					self.currimg = self.image_flip(self.currimg, False)
				elif self.location == 2:
					self.currimg = self.image_rotate(self.currimg, 180)
				elif self.location == 3:
					self.currimg = self.image_flip(self.currimg, True)
		# If self.zoomratio >= 1, perform any rotating/flipping on the smaller image
		# (before scaling up) for speed improvements
		if self.zoomratio >= 1:
			# Check if we need any rotating/flipping
			if self.orientation == 1:
				finalimg_width, finalimg_height = finalimg_height, finalimg_width
				if self.location == 0:
					self.currimg = self.image_rotate(self.originalimg, 270)
					self.currimg = self.image_flip(self.currimg, False)
				elif self.location == 1:
					self.currimg = self.image_rotate(self.originalimg, 270)
				elif self.location == 2:
					self.currimg = self.image_rotate(self.originalimg, 270)
					self.currimg = self.image_flip(self.currimg, True)
				elif self.location == 3:
					self.currimg = self.image_rotate(self.originalimg, 90)
			else:
				if self.location == 0:
					self.currimg = self.originalimg
				elif self.location == 1:
					self.currimg = self.image_flip(self.originalimg, False)
				elif self.location == 2:
					self.currimg = self.image_rotate(self.originalimg, 180)
				elif self.location == 3:
					self.currimg = self.image_flip(self.originalimg, True)
			# Scale image:
			if self.originalimg.get_has_alpha() == False:
				if self.zoomratio != 1:
					self.currimg = self.currimg.scale_simple(finalimg_width, finalimg_height, self.zoom_quality)
			else:
				colormap = self.imageview.get_colormap()
				light_grey = colormap.alloc_color('#666666', True, True)
				dark_grey = colormap.alloc_color('#999999', True, True)
				self.currimg = self.currimg.composite_color_simple(finalimg_width, finalimg_height, self.zoom_quality, 255, 8, light_grey.pixel, dark_grey.pixel)
		if self.orientation == 0:
			self.currimg_width, self.currimg_height = finalimg_width, finalimg_height
		else:
			self.currimg_width, self.currimg_height = finalimg_height, finalimg_width
		self.show_scrollbars_if_needed()
		self.layout.set_size(self.currimg_width, self.currimg_height)
		self.center_image()
		self.imageview.set_from_pixbuf(self.currimg)
		self.first_image_load = False
		# Clean up (free memory) because I'm lazy
		gc.collect()
		return
		
	def show_scrollbars_if_needed(self):
		if self.currimg_width > self.available_image_width():
			self.hscroll.show()
		else:
			self.hscroll.hide()
		if self.currimg_height > self.available_image_height():
			self.vscroll.show()
		else:
			self.vscroll.hide()

	def center_image(self):
		x_shift = int((self.available_image_width() - self.currimg_width)/2)
		if x_shift < 0:
			x_shift = 0
		y_shift = int((self.available_image_height() - self.currimg_height)/2)
		if y_shift < 0:
			y_shift = 0
		self.layout.move(self.imageview, x_shift, y_shift)
		
	def available_image_width(self):
		width = self.window.get_size()[0]
		return width
	
	def available_image_height(self):
		height = self.window.get_size()[1]
		if self.fullscreen_mode == False:
			height -= self.menubar.size_request()[1]
			if self.toolbar_show == True:
				height -= self.toolbar.size_request()[1] 
			if self.statusbar_show == True:
				height -= self.statusbar.size_request()[1]
		return height

	def open_file(self, action):
		self.open_file_or_folder(action, True)

	def open_folder(self, action):
		self.open_file_or_folder(action, False)

	def update_preview(self, file_chooser, preview):
		filename = file_chooser.get_preview_filename()
		try:
			pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(filename, 128, 128)
			preview.set_from_pixbuf(pixbuf)
			have_preview = True
		except:
			pixbuf = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, 1, 8, 128, 128)
			pixbuf.fill(0x00000000)
			preview.set_from_pixbuf(pixbuf)
			have_preview = True
		file_chooser.set_preview_widget_active(have_preview)
		return

	def open_file_or_folder(self, action, isfile):
		# If file = True, file; If file = False, folder
		dialog = gtk.FileChooserDialog(title="Open",action=gtk.FILE_CHOOSER_ACTION_OPEN,buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
		if isfile == True:
			filter = gtk.FileFilter()
			filter.set_name("Images")
			filter.add_pixbuf_formats()
			dialog.add_filter(filter)
			filter = gtk.FileFilter()
			filter.set_name("All files")
			filter.add_pattern("*")
			dialog.add_filter(filter)
			preview = gtk.Image()
			dialog.set_preview_widget(preview)
			dialog.set_use_preview_label(False)
			dialog.connect("update-preview", self.update_preview, preview)
		else:
			dialog.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
			recursivebutton = gtk.CheckButton(label="Include images in subdirectories")
			dialog.set_extra_widget(recursivebutton)
		dialog.set_default_response(gtk.RESPONSE_OK)
		dialog.set_select_multiple(True)
		if self.use_last_dir == True:
			if self.last_dir != None:
				dialog.set_current_folder(self.last_dir)
		else:
			if self.fixed_dir != None:
				dialog.set_current_folder(self.fixed_dir)
		response = dialog.run()
		if response == gtk.RESPONSE_OK:
			if self.use_last_dir == True:
				self.last_dir = dialog.get_current_folder()
			if isfile == False and recursivebutton.get_property('active') == True:
				self.recursive = True
			filenames = dialog.get_filenames()
			dialog.destroy()
			self.expand_filelist_and_load_image(filenames)
			self.recursive = False
		else:
			dialog.destroy()
		return

	def exit_app(self, action):
		self.save_settings()
		gtk.main_quit()
		
	def hide_cursor(self):
		if self.fullscreen_mode == True:
			pix_data = """/* XPM */
			static char * invisible_xpm[] = {
			"1 1 1 1",
			"       c None",
			" "};"""
			color = gtk.gdk.Color()
			pix = gtk.gdk.pixmap_create_from_data(None, pix_data, 1, 1, 1, color, color)
			invisible = gtk.gdk.Cursor(pix, pix, color, color, 0, 0)
			self.change_cursor(invisible)
		return False

	def toggle_fullscreen(self, action):
		if self.fullscreen_mode == True:
			self.fullscreen_mode = False
			self.UIManager.get_widget('/Popup/FM4').hide()
			self.UIManager.get_widget('/Popup/Exit Full Screen').hide()
			self.window.unfullscreen()
			if self.toolbar_show == True:
				self.toolbar.show()
			self.menubar.show()
			if self.statusbar_show == True:
				self.statusbar.show()
			self.change_cursor(None)
		else:
			self.fullscreen_mode = True
			self.UIManager.get_widget('/Popup/FM4').show()
			self.UIManager.get_widget('/Popup/Exit Full Screen').show()
			self.statusbar.hide()
			self.toolbar.hide()
			self.menubar.hide()
			self.window.fullscreen()
			self.timer_id = gobject.timeout_add(2000, self.hide_cursor)

	def toggle_status_bar(self, action):
		if self.statusbar.get_property('visible') == True:
			self.statusbar.hide()
			self.statusbar_show = False
		else:
			self.statusbar.show()
			self.statusbar_show = True
		if self.image_loaded == True and self.last_image_action_was_fit == True:
			self.zoom_to_fit_window(None)

	def toggle_toolbar(self, action):
		if self.toolbar.get_property('visible') == True:
			self.toolbar.hide()
			self.toolbar_show = False
		else:
			self.toolbar.show()
			self.toolbar_show = True
		if self.image_loaded == True and self.last_image_action_was_fit == True:
			self.zoom_to_fit_window(None)

	def update_statusbar(self):
		# Update status bar:
		st = os.stat(self.userimage)
		filesize = st[6]/1000
		ratio = int(100 * self.zoomratio)
		status_text=str(self.originalimg.get_width()) + "x" + str(self.originalimg.get_height()) + "   " + str(filesize) + "KB   " + str(ratio) + "%   "
		context_id = self.statusbar.get_context_id("i don't get this")
		self.statusbar.push(context_id, status_text)
		return

	def show_prefs(self, action):
		self.prefs_dialog = gtk.Dialog(title="Mirage Options", parent=self.window)
		self.prefs_dialog.set_has_separator(False)
		self.prefs_dialog.set_resizable(False)
		# Add "general" prefs:
		table_settings = gtk.Table(13, 3, False)
		table_settings.attach(gtk.Label(), 1, 3, 1, 2, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
		bglabel = gtk.Label()
		bglabel.set_markup("<b>Background Color</b>")
		bglabel.set_alignment(0, 1)
		table_settings.attach(bglabel, 1, 3, 2, 3, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 15, 0)
		table_settings.attach(gtk.Label(), 1, 3, 3, 4, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
		colorbutton = gtk.ColorButton(self.bgcolor)
		colorbutton.connect('color-set', self.bgcolor_selected)
		table_settings.attach(colorbutton, 1, 2, 4, 5, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 30, 0)
		table_settings.attach(gtk.Label(), 1, 3, 5, 6, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
		zoomlabel = gtk.Label()
		zoomlabel.set_markup("<b>Zoom Quality</b>")
		zoomlabel.set_alignment(0, 1)
		table_settings.attach(zoomlabel, 1, 3, 6, 7, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 15, 0)
		table_settings.attach(gtk.Label(), 1, 3, 7, 8, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
		zoompref = gtk.RadioButton()
		zoompref1 = gtk.RadioButton(group=zoompref, label="Nearest (Fastest)")
		zoompref2 = gtk.RadioButton(group=zoompref, label="Tiles")
		zoompref3 = gtk.RadioButton(group=zoompref, label="Bilinear")
		zoompref4 = gtk.RadioButton(group=zoompref, label="Hyper (Highest Quality)")
		table_settings.attach(zoompref1, 1, 3, 8, 9,  gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 30, 0)
		table_settings.attach(zoompref2, 1, 3, 9, 10,  gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 30, 0)
		table_settings.attach(zoompref3, 1, 3, 10, 11,  gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 30, 0)
		table_settings.attach(zoompref4, 1, 3, 11, 12,  gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 30, 0)
		table_settings.attach(gtk.Label(), 1, 3, 12, 13, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
		if self.zoom_quality == gtk.gdk.INTERP_NEAREST:
			zoompref1.set_active(True)
		elif self.zoom_quality == gtk.gdk.INTERP_TILES:
			zoompref2.set_active(True)
		elif self.zoom_quality == gtk.gdk.INTERP_BILINEAR:
			zoompref3.set_active(True)
		elif self.zoom_quality == gtk.gdk.INTERP_HYPER:
			zoompref4.set_active(True)
		# Add "behavior" tab:
		table_behavior = gtk.Table(13, 2, False)
		table_behavior.attach(gtk.Label(), 1, 2, 1, 2, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
		openlabel = gtk.Label()
		openlabel.set_markup("<b>Open Behavior</b>")
		openlabel.set_alignment(0, 1)
		table_behavior.attach(openlabel, 1, 2, 2, 3, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 15, 0)
		table_behavior.attach(gtk.Label(), 1, 2, 3, 4, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
		hbox_openmode = gtk.HBox()
		hbox_openmode.pack_start(gtk.Label("Open new image in:"), False, False, 0)
		combobox = gtk.combo_box_new_text()
		combobox.append_text("Smart Mode")
		combobox.append_text("Zoom To Fit Mode")
		combobox.append_text("1:1 Mode")
		combobox.append_text("Last Active Mode")
		combobox.set_active(self.open_mode)
		gtk.Tooltips().set_tip(combobox, "Smart mode uses 1:1 for images smaller than the window and Fit To Window for images larger..")
		hbox_openmode.pack_start(combobox, False, False, 5)
		table_behavior.attach(hbox_openmode, 1, 2, 4, 5, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 30, 0)
		table_behavior.attach(gtk.Label(), 1, 2, 5, 6, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
		openallimages = gtk.CheckButton(label="Load all images in current directory", use_underline=False)
		openallimages.set_active(self.open_all_images)
		gtk.Tooltips().set_tip(openallimages, "If enabled, opening an image in Mirage will automatically load all images found in that image's directory.")
		table_behavior.attach(openallimages, 1, 2, 6, 7, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 30, 0)
		table_behavior.attach(gtk.Label(), 1, 2, 7, 8, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
		openpref = gtk.RadioButton()
		openpref1 = gtk.RadioButton(group=openpref, label="Use last chosen directory")
		gtk.Tooltips().set_tip(openpref1, "The default 'Open' directory will be the last directory used.")
		openpref2 = gtk.RadioButton(group=openpref, label="Use this fixed directory:")
		openpref2.connect('toggled', self.use_fixed_dir_clicked)
		gtk.Tooltips().set_tip(openpref2, "The default 'Open' directory will be this specified directory.")
		table_behavior.attach(openpref1, 1, 2, 8, 9, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 30, 0)
		table_behavior.attach(openpref2, 1, 2, 9, 10, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 30, 0)
		self.defaultdir = gtk.Button()
		if len(self.fixed_dir) > 25:
			self.defaultdir.set_label('...' + self.fixed_dir[-22:])
		else:
			self.defaultdir.set_label(self.fixed_dir)
		self.defaultdir.connect('clicked', self.defaultdir_clicked)
		if self.use_last_dir == True:
			openpref1.set_active(True)
			self.defaultdir.set_sensitive(False)
		else:
			openpref2.set_active(True)
			self.defaultdir.set_sensitive(True)
		table_behavior.attach(self.defaultdir, 1, 2, 10, 11, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 45, 0)
		table_behavior.attach(gtk.Label(), 1, 2, 11, 12, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
		table_behavior.attach(gtk.Label(), 1, 2, 12, 13, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
		# Add "Navigation" tab:
		table_navigation = gtk.Table(13, 2, False)
		table_navigation.attach(gtk.Label(), 1, 2, 1, 2, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
		navlabel = gtk.Label()
		navlabel.set_markup("<b>Navigation</b>")
		navlabel.set_alignment(0, 1)
		table_navigation.attach(navlabel, 1, 2, 2, 3, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 15, 0)
		mousewheelnav = gtk.CheckButton(label="Use mousewheel for imagelist navigation", use_underline=False)
		mousewheelnav.set_active(self.mousewheel_nav)
		gtk.Tooltips().set_tip(mousewheelnav, "If enabled, mousewheel-down/up will go to the next/previous image. Note that disabling mousewheel navigation will allow panning images with the mousewheel; panning is otherwise available with left-click/drag or middle-click/drag.")
		table_navigation.attach(gtk.Label(), 1, 2, 3, 4, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
		table_navigation.attach(mousewheelnav, 1, 2, 4, 5, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 30, 0)
		table_navigation.attach(gtk.Label(), 1, 2, 5, 6, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
		table_navigation.attach(gtk.Label(), 1, 2, 6, 7, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
		table_navigation.attach(gtk.Label(), 1, 2, 7, 8, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
		table_navigation.attach(gtk.Label(), 1, 2, 8, 9, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
		table_navigation.attach(gtk.Label(), 1, 2, 9, 10, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
		table_navigation.attach(gtk.Label(), 1, 2, 10, 11, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
		table_navigation.attach(gtk.Label(), 1, 2, 11, 12, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
		table_navigation.attach(gtk.Label(), 1, 2, 12, 13, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
		# Add tabs:
		notebook = gtk.Notebook()
		notebook.append_page(table_behavior, gtk.Label(str="Behavior"))
		notebook.append_page(table_navigation, gtk.Label(str="Navigation"))
		notebook.append_page(table_settings, gtk.Label(str="Settings"))
		notebook.set_current_page(0)
		hbox = gtk.HBox()
		self.prefs_dialog.vbox.pack_start(hbox, False, False, 7)
		hbox.pack_start(notebook, False, False, 7)
		notebook.connect('switch-page', self.prefs_tab_switched)
		# Show prefs:
		self.prefs_dialog.vbox.show_all()
		self.close_button = self.prefs_dialog.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
		self.close_button.grab_focus()
		response = self.prefs_dialog.run()
		if response == gtk.RESPONSE_CLOSE or response == -4:
			if zoompref1.get_active() == True:
				self.zoom_quality = gtk.gdk.INTERP_NEAREST
			elif zoompref2.get_active() == True:
				self.zoom_quality = gtk.gdk.INTERP_TILES
			elif zoompref3.get_active() == True:
				self.zoom_quality = gtk.gdk.INTERP_BILINEAR
			elif zoompref4.get_active() == True:
				self.zoom_quality = gtk.gdk.INTERP_HYPER
			self.open_all_images = openallimages.get_active()
			if openpref1.get_active() == True:
				self.use_last_dir = True
			else:
				self.use_last_dir = False
			self.open_mode = combobox.get_active()
			self.mousewheel_nav = mousewheelnav.get_active()
			self.prefs_dialog.destroy()

	def use_fixed_dir_clicked(self, button):
		if button.get_active() == True:
			self.defaultdir.set_sensitive(True)
		else:
			self.defaultdir.set_sensitive(False)

	def defaultdir_clicked(self, button):
		getdir = gtk.FileChooserDialog(title="Choose directory",action=gtk.FILE_CHOOSER_ACTION_OPEN,buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
		getdir.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
		getdir.set_filename(self.fixed_dir)
		getdir.set_default_response(gtk.RESPONSE_OK)
		response = getdir.run()
		if response == gtk.RESPONSE_OK:
			self.fixed_dir = getdir.get_filenames()[0]
			if len(self.fixed_dir) > 25:
				button.set_label('...' + self.fixed_dir[-22:])
			else:
				button.set_label(self.fixed_dir)
			getdir.destroy()
		else:
			getdir.destroy()

	def prefs_tab_switched(self, notebook, page, page_num):
		self.close_button.grab_focus()

	def bgcolor_selected(self, widget):
		# When the user selects a color, store this color in self.bgcolor (which will
		# later be saved to .miragerc) and set this background color:
		self.bgcolor = widget.get_property('color')
		self.layout.modify_bg(gtk.STATE_NORMAL, self.bgcolor)

	def show_about(self, action):
		# Help > About
		iconname = 'mirage_large.png'
		if os.path.exists(iconname):
			icon_path = iconname
		elif os.path.exists('../share/pixmaps/' + iconname):
			icon_path = '../share/pixmaps/' + iconname
		elif os.path.exists('/usr/local/share/pixmaps/' + iconname):
			icon_path = '/usr/local/share/pixmaps/' + iconname
		elif os.path.exists('/usr/share/pixmaps/' + iconname):
			icon_path = '/usr/share/pixmaps/' + iconname
		try:
			icon_pixbuf = gtk.gdk.pixbuf_new_from_file(icon_path)
		except:
			pass
		self.about_dialog = gtk.AboutDialog()
		self.about_dialog.set_name('Mirage')
		self.about_dialog.set_version(__version__)
		self.about_dialog.set_comments('A simple GTK+ Image Viewer.')
		self.about_dialog.set_license(__license__)
		self.about_dialog.set_authors(['Scott Horowitz <stonecrest@gmail.com>'])
		self.about_dialog.set_artists(['William Rea <sillywilly@gmail.com>'])
		self.about_dialog.set_website('http://www.theskyiscrape.com/scott/mirage.html')
		self.about_dialog.set_logo(icon_pixbuf)
		self.about_dialog.connect('response', self.close_about)
		self.about_dialog.connect('delete_event', self.close_about)
		self.about_dialog.show_all()
		return

	def close_about(self, event, data=None):
		self.about_dialog.hide()
		return True

	def mousewheel_scrolled(self, widget, event):
		if event.type == gtk.gdk.SCROLL:
			# Zooming of the image by Ctrl-mousewheel
			if event.state == gtk.gdk.CONTROL_MASK:
				if event.direction == gtk.gdk.SCROLL_UP:
					self.zoom_out(None)
				elif event.direction == gtk.gdk.SCROLL_DOWN:
					self.zoom_in(None)
				return True
			# Navigation of images with mousewheel:
			elif self.mousewheel_nav == True:
				if event.direction == gtk.gdk.SCROLL_UP:
					self.prev_img_in_list(None)
				elif event.direction == gtk.gdk.SCROLL_DOWN:
					self.next_img_in_list(None)
				return True

        def mouse_moved(self, widget, event):
		# This handles the panning of the image
		if event.is_hint:
			x, y, state = event.window.get_pointer()
		else:
			state = event.state
		x, y = event.x_root, event.y_root
		if (state & gtk.gdk.BUTTON2_MASK) or (state & gtk.gdk.BUTTON1_MASK):
			xadjust = self.layout.get_hadjustment()
			newx = xadjust.value + (self.prevmousex - x)
			if newx >= xadjust.lower and newx <= xadjust.upper - xadjust.page_size:
				xadjust.set_value(newx)
				self.layout.set_hadjustment(xadjust)
			yadjust = self.layout.get_vadjustment()
			newy = yadjust.value + (self.prevmousey - y)
			if newy >= yadjust.lower and newy <= yadjust.upper - yadjust.page_size:
				yadjust.set_value(newy)
				self.layout.set_vadjustment(yadjust)
		self.prevmousex = x
		self.prevmousey = y
		if self.fullscreen_mode == True:
			# Show cursor on movement, then hide after 2 seconds of no movement
			self.change_cursor(None)
			self.timer_id = gobject.timeout_add(2000, self.hide_cursor)
		return True

	def button_pressed(self, widget, event):
		# Changes the cursor to the 'resize' cursor, like GIMP, on a middle click:
		if event.button == 2 or event.button == 1:
			self.change_cursor(gtk.gdk.Cursor(gtk.gdk.FLEUR))
			self.prevmousex = event.x_root
			self.prevmousey = event.y_root
		# Right-click popup:
		elif self.image_loaded == True and event.button == 3:
			self.UIManager.get_widget('/Popup').popup(None, None, None, event.button, event.time)
		return True

	def button_released(self, widget, event):
		# Resets the cursor when middle mouse button is released
		if event.button == 2 or event.button == 1:
			self.change_cursor(None)
		return True

	def zoom_in(self, action):
		if self.userimage != "":
			if self.zoomratio < self.min_zoomratio * self.zoomratio_for_zoom_to_fit:
				self.set_zoom_out_sensitivities(True)
			if self.zoomratio < self.max_zoomratio * self.zoomratio_for_zoom_to_fit:
				self.zoomratio = self.zoomratio * 1.25
				if self.zoomratio > self.max_zoomratio * self.zoomratio_for_zoom_to_fit:
					self.set_zoom_in_sensitivities(False)
				self.last_image_action_was_fit = False
				self.put_zoom_image_to_window()
				self.update_statusbar()
		return

	def zoom_out(self, action):
		if self.userimage != "":
			if self.zoomratio > self.max_zoomratio * self.zoomratio_for_zoom_to_fit:
				self.set_zoom_in_sensitivities(True)
			if self.zoomratio > self.min_zoomratio * self.zoomratio_for_zoom_to_fit:
				self.zoomratio = self.zoomratio * 1/1.25
				if self.zoomratio < self.min_zoomratio * self.zoomratio_for_zoom_to_fit:
					self.set_zoom_out_sensitivities(False)
				self.last_image_action_was_fit = False
				self.put_zoom_image_to_window()
				self.update_statusbar()
		return

	def zoom_to_fit_window(self, action):
		if self.userimage != "":
			if self.zoomratio < self.min_zoomratio * self.zoomratio_for_zoom_to_fit:
				self.set_zoom_out_sensitivities(True)
			if self.zoomratio > self.max_zoomratio * self.zoomratio_for_zoom_to_fit:
				self.set_zoom_in_sensitivities(True)
			self.last_mode = self.open_mode_fit
			self.last_image_action_was_fit = True
			# Calculate zoomratio needed to fit to window:
			win_width = self.available_image_width()
			win_height = self.available_image_height()
			img_width = self.originalimg.get_width()
			img_height = self.originalimg.get_height()
			if self.orientation == 1:
				# Image is rotated, swap img_width and img_height:
				img_width, img_height = img_height, img_width
			width_ratio = float(img_width)/win_width
			height_ratio = float(img_height)/win_height
			if width_ratio < height_ratio:
				max_ratio = height_ratio
			else:
				max_ratio = width_ratio
			self.zoomratio = 1/float(max_ratio)
			self.put_zoom_image_to_window()
			self.update_statusbar()
		return

	def zoom_to_fit_or_1_to_1(self, action):
		if self.userimage != "":
			if self.zoomratio < self.min_zoomratio * self.zoomratio_for_zoom_to_fit:
				self.set_zoom_out_sensitivities(True)
			if self.zoomratio > self.max_zoomratio * self.zoomratio_for_zoom_to_fit:
				self.set_zoom_in_sensitivities(True)
			self.last_image_action_was_fit = True
			# Calculate zoomratio needed to fit to window:
			win_width = self.available_image_width()
			win_height = self.available_image_height()
			img_width = self.originalimg.get_width()
			img_height = self.originalimg.get_height()
			if self.orientation == 1:
				# Image is rotated, swap img_width and img_height:
				img_width, img_height = img_height, img_width
			width_ratio = float(img_width)/win_width
			height_ratio = float(img_height)/win_height
			if width_ratio < height_ratio:
				max_ratio = height_ratio
			else:
				max_ratio = width_ratio
			self.zoomratio = 1/float(max_ratio)
			self.zoomratio_for_zoom_to_fit = self.zoomratio
			if self.first_image_load == True and self.zoomratio > 1:
				# Revert to 1:1 zoom
				self.zoom_1_to_1(action)
				self.last_image_action_was_fit = True
			else:
				self.put_zoom_image_to_window()
				self.update_statusbar()
		return

	def zoom_1_to_1(self, action):
		if self.userimage != "":
			if self.zoomratio < self.min_zoomratio * self.zoomratio_for_zoom_to_fit:
				self.set_zoom_out_sensitivities(True)
			if self.zoomratio > self.max_zoomratio * self.zoomratio_for_zoom_to_fit:
				self.set_zoom_in_sensitivities(True)
			self.last_mode = self.open_mode_1to1
			self.last_image_action_was_fit = False
			self.zoomratio = 1
			self.put_zoom_image_to_window()
			self.update_statusbar()
		return

	def rotate_left(self, action):
		if self.userimage != "":
			if self.orientation == 0:
				self.orientation = 1
			else:
				self.orientation = 0
			self.location -= 1
			if self.location == -1:
				self.location = 3
			if self.last_image_action_was_fit == True:
				self.zoom_to_fit_or_1_to_1(None)
			else:
				self.currimg_width, self.currimg_height = self.currimg_height, self.currimg_width
				self.layout.set_size(self.currimg_width, self.currimg_height)
				self.currimg = self.image_rotate(self.currimg, 90)
				self.imageview.set_from_pixbuf(self.currimg)
				self.show_scrollbars_if_needed()
				self.center_image()
		return

	def rotate_right(self, action):
		if self.userimage != "":
			if self.orientation == 0:
				self.orientation = 1
			else:
				self.orientation = 0
			self.location += 1
			if self.location == 4:
				self.location = 0
			if self.last_image_action_was_fit == True:
				self.zoom_to_fit_or_1_to_1(None)
			else:
				self.currimg_width, self.currimg_height = self.currimg_height, self.currimg_width
				self.layout.set_size(self.currimg_width, self.currimg_height)
				self.currimg = self.image_rotate(self.currimg, 270)
				self.imageview.set_from_pixbuf(self.currimg)
				self.show_scrollbars_if_needed()
				self.center_image()
		return

	def image_flip_vert(self, action):
		if self.userimage != "":
			self.last_image_action_was_fit = False
			if self.location == 0:
				self.location = 3
			elif self.location == 1:
				self.location = 2
			elif self.location == 2:
				self.location = 1
			elif self.location == 3:
				self.location = 0
			self.currimg = self.image_flip(self.currimg, True)
			self.imageview.set_from_pixbuf(self.currimg)
		return

	def image_flip_horiz(self, action):
		if self.userimage != "":
			self.last_image_action_was_fit = False
			if self.location == 0:
				self.location = 1
			elif self.location == 1:
				self.location = 0
			elif self.location == 2:
				self.location = 3
			elif self.location == 3:
				self.location = 2
			self.currimg = self.image_flip(self.currimg, False)
			self.imageview.set_from_pixbuf(self.currimg)
		return

	def prev_img_in_list(self, action):
		if len(self.image_list) > 1:
			self.randomlist = []
			if self.curr_img_in_list > 0:
				self.curr_img_in_list -= 1
			else:
				self.curr_img_in_list = len(self.image_list) - 1
			if self.fullscreen_mode == False:
				self.change_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
			gtk.main_iteration()
			self.load_new_image()
			if self.fullscreen_mode == False:
				self.change_cursor(None)

	def next_img_in_list(self, action):
		if len(self.image_list) > 1:
			self.randomlist = []
			if self.curr_img_in_list < len(self.image_list) - 1:
				self.curr_img_in_list += 1
			else:
				self.curr_img_in_list = 0
			if self.fullscreen_mode == False:
				self.change_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
			gtk.main_iteration()
			self.load_new_image()
			if self.fullscreen_mode == False:
				self.change_cursor(None)

	def random_img_in_list(self, action):
		if len(self.image_list) > 1:
			if self.randomlist == []:
				self.reinitialize_randomlist()
			else:
				# If every image has been randomly chosen once, re-initialize:
				all_items_are_true = True
				for item in self.randomlist:
					if item == False:
						all_items_are_true = False
				if all_items_are_true == True:
					self.reinitialize_randomlist()
			# Find random image that hasn't already been chosen:
			j = random.randint(0, len(self.image_list)-1)
			while self.randomlist[j] == True:
				j = random.randint(0, len(self.image_list)-1)
			self.curr_img_in_list = j
			self.randomlist[j] = True
			self.userimage = str(self.image_list[self.curr_img_in_list])
			if self.fullscreen_mode == False:
				self.change_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
			gtk.main_iteration()
			self.load_new_image()
			if self.fullscreen_mode == False:
				self.change_cursor(None)

	def first_img_in_list(self, action):
		if len(self.image_list) > 1:
			self.randomlist = []
			self.curr_img_in_list = 0
			self.change_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
			gtk.main_iteration()
			self.load_new_image()
			self.change_cursor(None)

	def last_img_in_list(self, action):
		if len(self.image_list) > 1:
			self.randomlist = []
			self.curr_img_in_list = len(self.image_list)-1
			self.change_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
			gtk.main_iteration()
			self.load_new_image()
			self.change_cursor(None)

	def reinitialize_randomlist(self):
		self.randomlist = []
		for i in range(len(self.image_list)):
			self.randomlist.append(False)
		self.randomlist[self.curr_img_in_list] = True
			
	def load_new_image(self):
		self.currimg = None
		self.userimage = str(self.image_list[self.curr_img_in_list])
		if self.verbose == True and self.userimage != "":
			print "Loading:", self.userimage
		self.originalimg = gtk.gdk.pixbuf_new_from_file(self.userimage)
		self.first_image_load = True
		self.location = 0
		self.orientation = 0
		if self.zoomratio > self.max_zoomratio * self.zoomratio_for_zoom_to_fit:
			self.set_zoom_in_sensitivities(True)
		elif self.zoomratio < self.min_zoomratio * self.zoomratio_for_zoom_to_fit:
			self.set_zoom_out_sensitivities(True)
		self.zoomratio = 1
		if self.open_mode == self.open_mode_smart:
			self.zoom_to_fit_or_1_to_1(None)
		elif self.open_mode == self.open_mode_fit:
			self.zoom_to_fit_window(None)
		elif self.open_mode == self.open_mode_1to1:
			self.zoom_1_to_1(None)
		elif self.open_mode == self.open_mode_last:
			if self.last_mode == self.open_mode_smart:
				self.zoom_to_fit_or_1_to_1(None)
			elif self.last_mode == self.open_mode_fit:
				self.zoom_to_fit_window(None)
			elif self.last_mode == self.open_mode_1to1:
				self.zoom_1_to_1(None)
		self.update_statusbar()
		self.window.set_title("Mirage - [" + str(self.curr_img_in_list+1) + " of " + str(len(self.image_list)) + "] " + os.path.basename(self.userimage))

	def change_cursor(self, type):
		for i in gtk.gdk.window_get_toplevels():
			if i.get_window_type() != gtk.gdk.WINDOW_TEMP:
				i.set_cursor(type)
		self.layout.window.set_cursor(type)
		
	def expand_filelist_and_load_image(self, inputlist):
		self.change_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
		while gtk.events_pending():
			gtk.main_iteration()
		# Takes the current list (i.e. ["pic.jpg", "pic2.gif", "../images"]) and
		# expands it into a list of all pictures found; returns new list
		first_image_found = False
		self.randomlist = []
		filelist = []
		folderlist = []
		self.image_list = []
		self.curr_img_in_list = 0
		# Clean up list (remove preceding "file://" or "file:" and trailing "/")
		for itemnum in range(len(inputlist)):
			# Strip off preceding file..
			if inputlist[itemnum].startswith('file://'):
				inputlist[itemnum] = inputlist[itemnum][7:]
			elif inputlist[itemnum].startswith('file:'):
				inputlist[itemnum] = inputlist[itemnum][5:]
			# Strip off trailing "/" if it exists:
			if inputlist[itemnum][len(inputlist[itemnum])-1] == "/":
				inputlist[itemnum] = inputlist[itemnum][:(len(inputlist[itemnum])-1)]
			inputlist[itemnum] = os.path.abspath(inputlist[itemnum])
		# If first argument is image, use for initial loading:
		if os.path.isfile(inputlist[0]):
			item_fullpath = os.path.abspath(inputlist[itemnum])
			if self.valid_image(item_fullpath) == True:
				first_image_found = True
				first_image = item_fullpath
		# If first image is dir, expand:
		if self.open_all_images == True:
			if os.path.isfile(inputlist[0]):
				for item in inputlist:
					if os.path.isfile(item):
						itempath = os.path.dirname(os.path.abspath(item))
					else:
						itempath = os.path.abspath(item)
					temp = self.recursive
					self.recursive = False
					inputlist = self.expand_directory(itempath, inputlist, False, False)
					self.recursive = temp
				# Remove any duplicates in inputlist...
				inputlist = list(set(inputlist))
		# Note: If we want case insensitive sorts, use .sort(key=str.lower)
		inputlist.sort()
		for item in inputlist:
			item_fullpath = os.path.abspath(item)
			# If the item is a filename, test to see if it's a valid image
			# that we can read; if not, discard it:
			if os.path.isfile(item_fullpath):
				if self.valid_image(item_fullpath) == True:
					if first_image_found == False:
						first_image_found = True
						first_image = item_fullpath
					filelist.append(item)
					if self.verbose == True:
						print "Found:", item_fullpath, "[" + str(len(filelist)) + "]"
			# If it's a directory that was explicitly selected or passed to
			# the program, get all the files in the dir.
			# Retrieve only images in the top directory specified by the user
			# only explicitly told to recurse (via -R or in Tools>Options)
			elif os.path.isdir(item_fullpath):
				folderlist.append(item)
		# Sort the filelist and folderlist alphabetically, and recurse into folderlist:
		if len(filelist) > 0:
			filelist = list(set(filelist))
			filelist.sort()
		if len(folderlist) > 0:
			folderlist.sort()
			folderlist = list(set(folderlist))
			for item in folderlist:
				filelist = self.expand_directory(item, filelist, False, False)
		# We now have the full list, update to full paths:
		for item in filelist:
			self.image_list.append(os.path.abspath(item))
		if len(self.image_list) <= 1:
			self.set_go_sensitivities(False)
		else:
			self.set_go_sensitivities(True)
		if len(self.image_list) > 0:
			# Find first specified image in list for updating Mirage title:
			if first_image_found == True:
				for itemnum in range(len(self.image_list)):
					if first_image == self.image_list[itemnum]:
						self.curr_img_in_list = itemnum
			if self.verbose == True and self.userimage != "":
				print "Loading:", self.userimage
			try:
				self.originalimg = gtk.gdk.pixbuf_new_from_file(str(self.image_list[self.curr_img_in_list]))
				self.load_new_image()
				self.previmg_width = self.currimg.get_width()
				self.image_loaded = True
				self.set_image_sensitivities(True)
				while gtk.events_pending():
					gtk.main_iteration(True)
			except:
				self.put_error_image_to_window()
				self.image_loaded = False
				pass
		self.change_cursor(None)

	def expand_directory(self, item, inputlist, stop_when_image_found, stop_now):
		if stop_now == False:
			filelist = []
			folderlist = []
			for item2 in os.listdir(item):
				item2 = item + "/" + item2
				item_fullpath2 = os.path.abspath(item2)
				if os.path.isfile(item_fullpath2):
					if self.valid_image(item_fullpath2) == True:
						filelist.append(item2)
						if stop_when_image_found == True:
							stop_now = True
						if self.verbose == True:
							print "Found:", item_fullpath2, "[" + str(len(self.image_list)) + "]"
				elif os.path.isdir(item_fullpath2) and self.recursive == True:
					folderlist.append(item_fullpath2)
			# Sort the filelist and folderlist alphabetically, and recurse into folderlist:
			if len(filelist) > 0:
				filelist.sort()
				inputlist = inputlist + filelist
			if len(folderlist) > 0:
				folderlist.sort()
				for item2 in folderlist:
					inputlist = self.expand_directory(item2, inputlist, stop_when_image_found, stop_now)
		return inputlist 

	def valid_image(self, file):
		test = gtk.gdk.pixbuf_get_file_info(file)
		if test == None:
			return False
		elif test[0]['name'] == "wbmp":
			# some regular files are thought to be wbmp for whatever reason,
			# so let's check further.. :(
			try:
				test2 = gtk.gdk.pixbuf_new_from_file(file)
				return True
			except:
				return False
		else:
			return True

	def image_flip(self, old_pix, vertical):
		width = old_pix.get_width()
		height = old_pix.get_height()
		d = None
		if vertical == True:
			d, w, h, rws = imgfuncs.vert(old_pix.get_pixels(), width, height, old_pix.get_rowstride(), old_pix.get_n_channels())
		else:
			d, w, h, rws = imgfuncs.horiz(old_pix.get_pixels(), width, height, old_pix.get_rowstride(), old_pix.get_n_channels())
		if d:
			new_pix = gtk.gdk.pixbuf_new_from_data(d, old_pix.get_colorspace(), old_pix.get_has_alpha(), old_pix.get_bits_per_sample(), w, h, rws)
			return new_pix
		return old_pix	

	def image_rotate(self, old_pix, full_angle):
		width = old_pix.get_width()
		height = old_pix.get_height()
		angle = full_angle - (int(full_angle) / 360) * 360
		if angle:
			d = None
			if angle % 270 == 0:
				d, w, h, rws = imgfuncs.right(old_pix.get_pixels(), width, height, old_pix.get_rowstride(), old_pix.get_n_channels())
			elif angle % 180 == 0:
				d, w, h, rws = imgfuncs.mirror(old_pix.get_pixels(), width, height, old_pix.get_rowstride(), old_pix.get_n_channels())
			elif angle % 90 == 0:
				d, w, h, rws = imgfuncs.left(old_pix.get_pixels(), width, height, old_pix.get_rowstride(), old_pix.get_n_channels())
			if d:
				new_pix = gtk.gdk.pixbuf_new_from_data(d, old_pix.get_colorspace(), old_pix.get_has_alpha(), old_pix.get_bits_per_sample(), w, h, rws)
				return new_pix
		return old_pix

	def main(self):
		gtk.main()

if __name__ == "__main__":
	base = Base()
	base.main()

#!/usr/bin/env python

__version__ = "0.7.1"

__license__ = """
Mirage, a fast GTK+ Image Viewer
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
import gettext
import locale
try:
	import gconf
except:
	pass

class Base:

        def __init__(self):
	
		try:
			gettext.install('mirage', '/usr/share/locale', unicode=1)
		except:
			gettext.install('mirage', '/usr/local/share/locale', unicode=1)
        
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
                bgcolor_found = False
                self.toolbar_show = True
                self.statusbar_show = True
                self.fullscreen_mode = False
                self.opendialogpath = ""
                self.zoom_quality = gtk.gdk.INTERP_BILINEAR
                self.recursive = False
                self.verbose = False
                self.image_loaded = False
                self.open_all_images = False		# open all images in the directory(ies)
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
                self.listwrap_mode = 0			# 0=no, 1=yes, 2=ask
		self.currimg_width = 0
                self.currimg_height = 0
                self.user_prompt_visible = False	# the "wrap?" prompt
		self.image_is_animation = False
                self.slideshow_delay = 1		# self.delayoptions[self.slideshow_delay] seconds
		self.slideshow_mode = False
                self.delayoptions = [2,3,5,10,15,30]	# in seconds
		self.slideshow_random = False
                self.slideshow_controls_visible = False	# fullscreen slideshow controls
		self.controls_moving = False
                self.zoomvalue = 3.0
                self.editor = "gimp-remote"
		self.updating_adjustments = False
		self.disable_screensaver = False

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
                        self.mousewheel_nav = conf.getboolean('prefs', 'mousewheel_nav')
                        self.listwrap_mode = conf.getint('prefs', 'listwrap_mode')
                        self.slideshow_delay = conf.getint('prefs', 'slideshow_delay')
                        self.slideshow_random = conf.getboolean('prefs', 'slideshow_random')
                        self.zoomvalue = conf.getfloat('prefs', 'zoomvalue')
                        if int(round(self.zoomvalue, 0)) == 1:
                                self.zoom_quality = gtk.gdk.INTERP_NEAREST
                        elif int(round(self.zoomvalue, 0)) == 2:
                                self.zoom_quality = gtk.gdk.INTERP_TILES
                        elif int(round(self.zoomvalue, 0)) == 3:
                                self.zoom_quality = gtk.gdk.INTERP_BILINEAR
                        elif int(round(self.zoomvalue, 0)) == 4:
                                self.zoom_quality = gtk.gdk.INTERP_HYPER
                        self.editor = conf.get('prefs', 'editor')
			self.disable_screensaver = conf.getboolean('prefs', 'disable_screensaver')
                except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
                        pass
                # slideshow_delay is the user's preference, whereas curr_slideshow_delay is
		# the current delay (which can be changed without affecting the 'default')
		self.curr_slideshow_delay = self.slideshow_delay
                # Same for randomization:
		self.curr_slideshow_random = self.slideshow_random

                # Define the main menubar and toolbar:
		actions = (  
                        ('FileMenu', None, '_File'),  
                        ('EditMenu', None, '_Edit'),
                        ('ViewMenu', None, '_View'),  
                        ('GoMenu', None, '_Go'),  
                        ('HelpMenu', None, '_Help'),  
                        ('Open Image', gtk.STOCK_OPEN, _('_Open Image...'), '<control>O', 'Open Image', self.open_file),  
                        ('Open Folder', gtk.STOCK_OPEN, _('Open _Folder...'), '<control>F', 'Open Folder', self.open_folder),  
                        ('Quit', gtk.STOCK_QUIT, _('_Quit'), '<control>Q', 'Quit', self.exit_app),  
                        ('Previous Image', gtk.STOCK_GO_BACK, _('_Previous Image'), 'Left', 'Previous Image', self.prev_img_in_list),  
                        ('Next Image', gtk.STOCK_GO_FORWARD, _('_Next Image'), 'Right', 'Next Image', self.next_img_in_list),  
                        ('Previous2', gtk.STOCK_GO_BACK, _('_Previous'), 'Left', 'Previous', self.prev_img_in_list),  
                        ('Next2', gtk.STOCK_GO_FORWARD, _('_Next'), 'Right', 'Next', self.next_img_in_list),  
                        ('Random Image', None, _('_Random Image'), 'R', 'Random Image', self.random_img_in_list),  
                        ('First Image', gtk.STOCK_GOTO_FIRST, _('_First Image'), 'Home', 'First Image', self.first_img_in_list),  
                        ('Last Image', gtk.STOCK_GOTO_LAST, _('_Last Image'), 'End', 'Last Image', self.last_img_in_list),  
                        ('In', gtk.STOCK_ZOOM_IN, _('Zoom _In'), '<Ctrl>Up', 'Zoom In', self.zoom_in),  
                        ('Out', gtk.STOCK_ZOOM_OUT, _('Zoom _Out'), '<Ctrl>Down', 'Zoom Out', self.zoom_out),  
                        ('Fit', gtk.STOCK_ZOOM_FIT, _('Zoom To _Fit'), '<Ctrl>0', 'Fit', self.zoom_to_fit_window),  
                        ('1:1', gtk.STOCK_ZOOM_100, _('_1:1'), '<Ctrl>1', '1:1', self.zoom_1_to_1),  
                        ('Rotate Left', None, _('Rotate _Left'), '<Ctrl>Left', 'Rotate Left', self.rotate_left),  
                        ('Rotate Right', None, _('Rotate _Right'), '<Ctrl>Right', 'Rotate Right', self.rotate_right),  
                        ('Flip Vertically', None, _('Flip _Vertically'), '<Ctrl>V', 'Flip Vertically', self.image_flip_vert),  
                        ('Flip Horizontally', None, _('Flip _Horizontally'), '<Ctrl>H', 'Flip Horizontally', self.image_flip_horiz),  
                        ('About', gtk.STOCK_ABOUT, _('_About'), 'F1', 'About', self.show_about),  
                        ('Preferences', gtk.STOCK_PREFERENCES, _('_Preferences'), None, 'Preferences', self.show_prefs),  
                        ('Full Screen', gtk.STOCK_FULLSCREEN, _('_Full Screen'), '<Shift>Return', 'Full Screen', self.enter_fullscreen),
                        ('Exit Full Screen', gtk.STOCK_LEAVE_FULLSCREEN, _('E_xit Full Screen'), None, 'Full Screen', self.leave_fullscreen),
                        ('Start Slideshow', gtk.STOCK_MEDIA_PLAY, _('_Start Slideshow'), 'F5', 'Start Slideshow', self.toggle_slideshow),
                        ('Stop Slideshow', gtk.STOCK_MEDIA_STOP, _('_Stop Slideshow'), 'F5', 'Stop Slideshow', self.toggle_slideshow),
                        ('Open in Editor', gtk.STOCK_EXECUTE, _('Open in _Editor'), '<Ctrl>E', 'Open in Editor', self.load_editor)
                        )
                toggle_actions = (
                        ('Status Bar', None, _('_Status Bar'), None, 'Status Bar', self.toggle_status_bar, self.statusbar_show),  
                        ('Toolbar', None, _('_Toolbar'), None, 'Toolbar', self.toggle_toolbar, self.toolbar_show),  
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
                            <separator name="FM4"/>
                            <menuitem action="Start Slideshow"/>
                            <menuitem action="Stop Slideshow"/> 
                            <separator name="FM3"/>  
                            <menuitem action="Exit Full Screen"/>
                            <menuitem action="Full Screen"/>
                          </popup>
                          <menubar name="MainMenu">
                            <menu action="FileMenu">  
                              <menuitem action="Open Image"/>  
                              <menuitem action="Open Folder"/>  
                              <separator name="FM1"/>  
                              <menuitem action="Quit"/>  
                            </menu>
                            <menu action="EditMenu">
                              <menuitem action="Rotate Left"/>
                              <menuitem action="Rotate Right"/>
                              <separator name="FM1"/>  
                              <menuitem action="Flip Vertically"/>
                              <menuitem action="Flip Horizontally"/>
                              <separator name="FM3"/>
                              <menuitem action="Open in Editor"/>
                              <separator name="FM2"/>  
                              <menuitem action="Preferences"/>  
                            </menu>
                            <menu action="ViewMenu">
                              <menuitem action="Out"/>
                              <menuitem action="In"/>
                              <menuitem action="1:1"/>
                              <menuitem action="Fit"/>
                              <separator name="FM2"/> 
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
                              <separator name="FM2"/>
                              <menuitem action="Start Slideshow"/>
                              <menuitem action="Stop Slideshow"/>
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
                self.set_window_title()
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
                self.set_slideshow_sensitivities()
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
                        self.bgcolor = gtk.gdk.Color(0, 0, 0) # Default to black
		self.layout.modify_bg(gtk.STATE_NORMAL, self.bgcolor)
                self.imageview = gtk.Image()
                self.layout.add(self.imageview)
                self.statusbar = gtk.Statusbar()
                self.statusbar.set_has_resize_grip(True)
                vbox.pack_start(self.statusbar, False, False, 0)
                self.statusbar.set_property('visible', self.statusbar_show)
                self.window.add(vbox)
                self.window.set_property('allow-shrink', False)
                self.window.set_default_size(width,height)
                # Slideshow control:
		self.slideshow_window = gtk.Window(gtk.WINDOW_POPUP)
                self.slideshow_controls = gtk.HBox()
                ss_back = gtk.Button("", gtk.STOCK_GO_BACK)
                alignment = ss_back.get_children()[0]
                hbox2 = alignment.get_children()[0]
                image, label = hbox2.get_children()
                label.set_text('')
                ss_back.set_property('can-focus', False)
                ss_back.connect('clicked', self.prev_img_in_list)
                self.ss_start = gtk.Button("", gtk.STOCK_MEDIA_PLAY)
                alignment = self.ss_start.get_children()[0]
                hbox2 = alignment.get_children()[0]
                image, label = hbox2.get_children()
                label.set_text('')
                self.ss_start.set_property('can-focus', False)
                self.ss_start.connect('clicked', self.toggle_slideshow)
                self.ss_stop = gtk.Button("", gtk.STOCK_MEDIA_STOP)
                alignment = self.ss_stop.get_children()[0]
                hbox2 = alignment.get_children()[0]
                image, label = hbox2.get_children()
                label.set_text('')
                self.ss_stop.set_property('can-focus', False)
                self.ss_stop.connect('clicked', self.toggle_slideshow)
                ss_forward = gtk.Button("", gtk.STOCK_GO_FORWARD)
                alignment = ss_forward.get_children()[0]
                hbox2 = alignment.get_children()[0]
                image, label = hbox2.get_children()
                label.set_text('')
                ss_forward.set_property('can-focus', False)
                ss_forward.connect('clicked', self.next_img_in_list)
                self.slideshow_controls.pack_start(ss_back, False, False, 0)
                self.slideshow_controls.pack_start(self.ss_start, False, False, 0)
                self.slideshow_controls.pack_start(self.ss_stop, False, False, 0)
                self.slideshow_controls.pack_start(ss_forward, False, False, 0)
                self.slideshow_window.add(self.slideshow_controls)
                self.slideshow_window.modify_bg(gtk.STATE_NORMAL, self.bgcolor)
                self.slideshow_window2 = gtk.Window(gtk.WINDOW_POPUP)
                self.slideshow_controls2 = gtk.HBox()
                self.ss_exit = gtk.Button("", gtk.STOCK_LEAVE_FULLSCREEN)
                alignment = self.ss_exit.get_children()[0]
                hbox2 = alignment.get_children()[0]
                image, label = hbox2.get_children()
                label.set_text('')
                self.ss_exit.set_property('can-focus', False)
                self.ss_exit.connect('clicked', self.leave_fullscreen)
                self.ss_randomize = gtk.ToggleButton()
		factory = gtk.IconFactory()
                iconname = 'stock_shuffle.png'
                if os.path.exists(iconname):
                        icon_path = iconname
                elif os.path.exists('../share/mirage/' + iconname):
                        icon_path = '../share/mirage/' + iconname
                elif os.path.exists('/usr/local/share/mirage/' + iconname):
                        icon_path = '/usr/local/share/mirage/' + iconname
                elif os.path.exists('/usr/share/mirage/' + iconname):
                        icon_path = '/usr/share/mirage/' + iconname
		else:
			icon_path = ''
                try:
			pixbuf = gtk.gdk.pixbuf_new_from_file(icon_path)
			iconset = gtk.IconSet(pixbuf)
			factory.add('test', iconset)
			factory.add_default()
			self.ss_randomize.set_image(gtk.image_new_from_stock('test', gtk.ICON_SIZE_MENU))
	                self.ss_randomize.set_size_request(ss_back.size_request()[0], -1)
                except:
			self.ss_randomize.set_label("Rand")
                self.ss_randomize.connect('toggled', self.random_changed)
                self.ss_delaycombo = gtk.combo_box_new_text()
                self.ss_delaycombo.append_text(str(self.delayoptions[0]) + " seconds")
                self.ss_delaycombo.append_text(str(self.delayoptions[1]) + " seconds")
                self.ss_delaycombo.append_text(str(self.delayoptions[2]) + " seconds")
                self.ss_delaycombo.append_text(str(self.delayoptions[3]) + " seconds")
                self.ss_delaycombo.append_text(str(self.delayoptions[4]) + " seconds")
                self.ss_delaycombo.append_text(str(self.delayoptions[5]) + " seconds")
                self.ss_delaycombo.connect('changed', self.delay_changed)
                self.slideshow_controls2.pack_start(self.ss_randomize, False, False, 0)
                self.slideshow_controls2.pack_start(self.ss_delaycombo, False, False, 0)
                self.slideshow_controls2.pack_start(self.ss_exit, False, False, 0)
                self.slideshow_window2.add(self.slideshow_controls2)
                self.slideshow_window2.modify_bg(gtk.STATE_NORMAL, self.bgcolor)

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
		self.imageview.connect("expose-event", self.expose_event)

		# Since GNOME does its own thing for the toolbar style...
		# Requires gnome-python installed to work (but optional)
		try:
			client = gconf.client_get_default()
			style = client.get_string('/desktop/gnome/interface/toolbar_style')
			if style == "both":
				self.toolbar.set_style(gtk.TOOLBAR_BOTH)
			elif style == "both-horiz":
				self.toolbar.set_style(gtk.TOOLBAR_BOTH_HORIZ)
			elif style == "icons":
				self.toolbar.set_style(gtk.TOOLBAR_ICONS)
			elif style == "text":
				self.toolbar.set_style(gtk.TOOLBAR_TEXT)
			client.add_dir("/desktop/gnome/interface", gconf.CLIENT_PRELOAD_NONE)
			client.notify_add("/desktop/gnome/interface/toolbar_style", self.gconf_key_changed) 
		except:
			pass

                # Show GUI:
		self.hscroll.set_no_show_all(True)
                self.vscroll.set_no_show_all(True)
                self.window.show_all()
                self.layout.set_flags(gtk.CAN_FOCUS)
                self.window.set_focus(self.layout)
                self.ss_start.set_size_request(self.ss_start.size_request()[0]*2, -1)
                self.ss_stop.set_size_request(self.ss_stop.size_request()[0]*2, -1)
                self.ss_exit.set_size_request(-1, self.ss_stop.size_request()[1])
                self.UIManager.get_widget('/Popup/Exit Full Screen').hide()

                # If arguments (filenames) were passed, try to open them:
		self.image_list = []
                if args != []:
                        for i in range(len(args)):
                                args[i] = urllib.url2pathname(args[i])
                        self.expand_filelist_and_load_image(args)
                else:
                        self.set_go_sensitivities(False)
                        self.set_image_sensitivities(False)
			
	def gconf_key_changed(self, client, cnxn_id, entry, label):
		if entry.value.type == gconf.VALUE_STRING:
			style = entry.value.to_string()
			if style == "both":
				self.toolbar.set_style(gtk.TOOLBAR_BOTH)
			elif style == "both-horiz":
				self.toolbar.set_style(gtk.TOOLBAR_BOTH_HORIZ)
			elif style == "icons":
				self.toolbar.set_style(gtk.TOOLBAR_ICONS)
			elif style == "text":
				self.toolbar.set_style(gtk.TOOLBAR_TEXT)
			if self.image_loaded == True and self.last_image_action_was_fit == True:
				self.zoom_to_fit_window(None)
			
        def topwindow_keypress(self, widget, event):
                if event.state != gtk.gdk.SHIFT_MASK and event.state != gtk.gdk.CONTROL_MASK and event.state != gtk.gdk.MOD1_MASK and event.state != gtk.gdk.CONTROL_MASK | gtk.gdk.MOD2_MASK and event.state != gtk.gdk.LOCK_MASK | gtk.gdk.CONTROL_MASK:
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
				self.leave_fullscreen(None)
			elif event.keyval == 45:     # - key
				self.zoom_out(None)
			elif event.keyval == 61 or event.keyval == 43:     # + key
				self.zoom_in(None)
                elif event.state == gtk.gdk.CONTROL_MASK or event.state == gtk.gdk.CONTROL_MASK | gtk.gdk.MOD2_MASK:
                        if event.keyval == 65456:    # "0" key on numpad
				self.zoom_to_fit_window(None)
                        if event.keyval == 65457:    # "1" key on numpad
				self.zoom_1_to_1(None)
                elif event.state == gtk.gdk.SHIFT_MASK or event.state == gtk.gdk.SHIFT_MASK | gtk.gdk.MOD2_MASK:
			if event.keyval == 43 or event.keyval == 61:     # + key
				self.zoom_in(None)
                                
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
                self.set_zoom_in_sensitivities(enable)
                self.set_zoom_out_sensitivities(enable)
                self.UIManager.get_widget('/MainMenu/ViewMenu/1:1').set_sensitive(enable)
                self.UIManager.get_widget('/MainMenu/ViewMenu/Fit').set_sensitive(enable)
                self.UIManager.get_widget('/MainMenu/EditMenu/Rotate Left').set_sensitive(enable)
                self.UIManager.get_widget('/MainMenu/EditMenu/Rotate Right').set_sensitive(enable)
                self.UIManager.get_widget('/MainMenu/EditMenu/Flip Vertically').set_sensitive(enable)
                self.UIManager.get_widget('/MainMenu/EditMenu/Flip Horizontally').set_sensitive(enable)
                self.UIManager.get_widget('/MainToolbar/1:1').set_sensitive(enable)
                self.UIManager.get_widget('/MainToolbar/Fit').set_sensitive(enable)
                self.UIManager.get_widget('/Popup/1:1').set_sensitive(enable)
                self.UIManager.get_widget('/Popup/Fit').set_sensitive(enable)
                self.UIManager.get_widget('/Popup/Rotate Left').set_sensitive(enable)
                self.UIManager.get_widget('/Popup/Rotate Right').set_sensitive(enable)
                self.UIManager.get_widget('/MainMenu/EditMenu/Open in Editor').set_sensitive(enable)
                
        def set_zoom_in_sensitivities(self, enable):
                self.UIManager.get_widget('/MainMenu/ViewMenu/In').set_sensitive(enable)
                self.UIManager.get_widget('/MainToolbar/In').set_sensitive(enable)		
                self.UIManager.get_widget('/Popup/In').set_sensitive(enable)

        def set_zoom_out_sensitivities(self, enable):
                self.UIManager.get_widget('/MainMenu/ViewMenu/Out').set_sensitive(enable)
                self.UIManager.get_widget('/MainToolbar/Out').set_sensitive(enable)		
                self.UIManager.get_widget('/Popup/Out').set_sensitive(enable)
                
        def set_next_image_sensitivities(self, enable):
                self.UIManager.get_widget('/MainToolbar/Next2').set_sensitive(enable)
                self.UIManager.get_widget('/MainMenu/GoMenu/Next Image').set_sensitive(enable)
                self.UIManager.get_widget('/Popup/Next Image').set_sensitive(enable)

        def set_previous_image_sensitivities(self, enable):
                self.UIManager.get_widget('/MainToolbar/Previous2').set_sensitive(enable)
                self.UIManager.get_widget('/MainMenu/GoMenu/Previous Image').set_sensitive(enable)
                self.UIManager.get_widget('/Popup/Previous Image').set_sensitive(enable)
                
        def set_first_image_sensitivities(self, enable):
                self.UIManager.get_widget('/MainMenu/GoMenu/First Image').set_sensitive(enable)
                
        def set_last_image_sensitivities(self, enable):
                self.UIManager.get_widget('/MainMenu/GoMenu/Last Image').set_sensitive(enable)
                
        def set_slideshow_sensitivities(self):
                if len(self.image_list) <=1:
                        self.UIManager.get_widget('/MainMenu/GoMenu/Start Slideshow').show()
                        self.UIManager.get_widget('/MainMenu/GoMenu/Start Slideshow').set_sensitive(False)
                        self.UIManager.get_widget('/MainMenu/GoMenu/Stop Slideshow').hide()
                        self.UIManager.get_widget('/MainMenu/GoMenu/Stop Slideshow').set_sensitive(False)
                elif self.slideshow_mode == True:
                        self.UIManager.get_widget('/MainMenu/GoMenu/Start Slideshow').hide()
                        self.UIManager.get_widget('/MainMenu/GoMenu/Start Slideshow').set_sensitive(False)
                        self.UIManager.get_widget('/MainMenu/GoMenu/Stop Slideshow').show()
                        self.UIManager.get_widget('/MainMenu/GoMenu/Stop Slideshow').set_sensitive(True)
                else:
                        self.UIManager.get_widget('/MainMenu/GoMenu/Start Slideshow').show()
                        self.UIManager.get_widget('/MainMenu/GoMenu/Start Slideshow').set_sensitive(True)
                        self.UIManager.get_widget('/MainMenu/GoMenu/Stop Slideshow').hide()
                        self.UIManager.get_widget('/MainMenu/GoMenu/Stop Slideshow').set_sensitive(False)
                if self.slideshow_mode == True:
                        self.UIManager.get_widget('/Popup/Start Slideshow').hide()
                        self.UIManager.get_widget('/Popup/Stop Slideshow').show()
                else:
                        self.UIManager.get_widget('/Popup/Start Slideshow').show()
                        self.UIManager.get_widget('/Popup/Stop Slideshow').hide()
                if len(self.image_list) <=1:
                        self.UIManager.get_widget('/Popup/Start Slideshow').set_sensitive(False)
                else:
                        self.UIManager.get_widget('/Popup/Start Slideshow').set_sensitive(True)

        def set_zoom_sensitivities(self):
                if self.image_is_animation == False:
                        if self.zoomratio < self.min_zoomratio * self.zoomratio_for_zoom_to_fit:
                                self.set_zoom_out_sensitivities(False)
                        else:
                                self.set_zoom_out_sensitivities(True)
                        if self.zoomratio > self.max_zoomratio * self.zoomratio_for_zoom_to_fit:
                                self.set_zoom_in_sensitivities(False)
                        else:
                                self.set_zoom_in_sensitivities(True)
                else:
                        self.set_zoom_out_sensitivities(False)
                        self.set_zoom_in_sensitivities(False)

        def print_version(self):
                print _("Version: Mirage"), __version__
                print _("Website: http://mirageiv.berlios.de")

        def print_usage(self):
                self.print_version()
                print ""
                print _("Usage: mirage [OPTION]... FILES|FOLDERS...")
                print ""
                print _("Options:")
                print _("  -h, --help                   Show this help and exit")
                print _("  -v, --version                Show version information and exit")
                print _("  -V, --verbose                Show more detailed information")
                print _("  -R, --recursive              Recursively include all images found in")
                print _("                               subdirectories of FOLDERS")

        def delay_changed(self, action):
                self.curr_slideshow_delay = self.ss_delaycombo.get_active()
                if self.slideshow_mode == True:
                        gobject.source_remove(self.timer_delay)
                        if self.curr_slideshow_random == True:
                                self.timer_delay = gobject.timeout_add(self.delayoptions[self.curr_slideshow_delay]*1000, self.random_img_in_list, "ss")
                        else:
                                self.timer_delay = gobject.timeout_add(self.delayoptions[self.curr_slideshow_delay]*1000, self.next_img_in_list, "ss")
                self.window.set_focus(self.layout)
                
        def random_changed(self, action):
                self.curr_slideshow_random = self.ss_randomize.get_active()

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
                self.currimg_width = self.imageview.size_request()[0]
                self.currimg_height = self.imageview.size_request()[1]
                self.center_image()
                self.set_go_sensitivities(False)
                self.set_image_sensitivities(False)
                self.update_statusbar()
                return

        def expose_event(self, widget, event):
		if self.updating_adjustments == True:
			return
		self.updating_adjustments = True
		if self.hscroll.get_property('visible') == True:
			try:
	                        zoomratio = float(self.currimg_width)/self.previmg_width
				newvalue = abs(self.layout.get_hadjustment().get_value() * zoomratio + (self.available_image_width()) * (zoomratio - 1) / 2)
				if newvalue >= self.layout.get_hadjustment().lower and newvalue <= (self.layout.get_hadjustment().upper - self.layout.get_hadjustment().page_size):
	                                self.layout.get_hadjustment().set_value(newvalue)
			except:
	                        pass
		if self.vscroll.get_property('visible') == True:
			try:
				newvalue = abs(self.layout.get_vadjustment().get_value() * zoomratio + (self.available_image_height()) * (zoomratio - 1) / 2)
				if newvalue >= self.layout.get_vadjustment().lower and newvalue <= (self.layout.get_vadjustment().upper - self.layout.get_vadjustment().page_size):
	                                self.layout.get_vadjustment().set_value(newvalue)
				self.previmg_width = self.currimg_width
			except:
				pass
		self.updating_adjustments = False

        def window_resized(self, widget, allocation):
                # Update the image size on window resize if the current image was last fit:
		if self.image_loaded == True:
                        if allocation.width != self.prevwinwidth or allocation.height != self.prevwinheight:
                                if self.last_image_action_was_fit == True:
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
                conf.set('prefs', 'listwrap_mode', self.listwrap_mode)
                conf.set('prefs', 'slideshow_delay', self.slideshow_delay)
                conf.set('prefs', 'slideshow_random', self.slideshow_random)
                conf.set('prefs', 'zoomvalue', self.zoomvalue)
                conf.set('prefs', 'editor', self.editor)
		conf.set('prefs', 'disable_screensaver', self.disable_screensaver)
		if os.path.exists(os.path.expanduser('~/.config/')) == False:
			os.mkdir(os.path.expanduser('~/.config/'))
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
		self.window.window.freeze_updates()
                # Always start with the original image to preserve quality!
		# Calculate image size:
		finalimg_width = int(self.originalimg.get_width() * self.zoomratio)
                finalimg_height = int(self.originalimg.get_height() * self.zoomratio)
                if self.image_is_animation  == False:
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
                else:
                        self.currimg = self.originalimg
                if self.orientation == 0:
                        self.currimg_width, self.currimg_height = finalimg_width, finalimg_height
                else:
                        self.currimg_width, self.currimg_height = finalimg_height, finalimg_width
                self.layout.set_size(self.currimg_width, self.currimg_height)
                self.center_image()
                self.show_scrollbars_if_needed()
                if self.image_is_animation  == False:
                        self.imageview.set_from_pixbuf(self.currimg)
                        self.previmage_is_animation = False
                else:
                        self.imageview.set_from_animation(self.currimg)
                        self.previmage_is_animation = True
                self.first_image_load = False
                # Clean up (free memory) because I'm lazy
		gc.collect()
		self.window.window.thaw_updates()
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
                # If isfile = True, file; If isfile = False, folder
		dialog = gtk.FileChooserDialog(title=_("Open"),action=gtk.FILE_CHOOSER_ACTION_OPEN,buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
                if isfile == True:
                        filter = gtk.FileFilter()
                        filter.set_name(_("Images"))
                        filter.add_pixbuf_formats()
                        dialog.add_filter(filter)
                        filter = gtk.FileFilter()
                        filter.set_name(_("All files"))
                        filter.add_pattern("*")
                        dialog.add_filter(filter)
                        preview = gtk.Image()
                        dialog.set_preview_widget(preview)
                        dialog.set_use_preview_label(False)
                        dialog.connect("update-preview", self.update_preview, preview)
                else:
                        dialog.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
                        recursivebutton = gtk.CheckButton(label=_("Include images in subdirectories"))
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
                        self.set_go_navigation_sensitivities()
                        self.recursive = False
                else:
                        dialog.destroy()
                return

        def exit_app(self, action):
                self.save_settings()
                gtk.main_quit()
                
        def hide_cursor(self):
                if self.fullscreen_mode == True and self.user_prompt_visible == False and self.slideshow_controls_visible == False:
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

        def enter_fullscreen(self, action):
                if self.fullscreen_mode == False:
                        self.fullscreen_mode = True
                        self.UIManager.get_widget('/Popup/Full Screen').hide()
                        self.UIManager.get_widget('/Popup/Exit Full Screen').show()
                        self.statusbar.hide()
                        self.toolbar.hide()
                        self.menubar.hide()
                        self.window.fullscreen()
                        self.timer_id = gobject.timeout_add(2000, self.hide_cursor)
                        self.set_slideshow_sensitivities()
                else:
                        self.leave_fullscreen(action)
                
        def leave_fullscreen(self, action):
                if self.fullscreen_mode == True:
                        self.slideshow_controls_visible = False
                        self.slideshow_window.hide_all()
                        self.slideshow_window2.hide_all()
                        self.fullscreen_mode = False
                        self.UIManager.get_widget('/Popup/Full Screen').show()
                        self.UIManager.get_widget('/Popup/Exit Full Screen').hide()
                        if self.toolbar_show == True:
                                self.toolbar.show()
                        self.menubar.show()
                        if self.statusbar_show == True:
                                self.statusbar.show()
                        self.window.unfullscreen()
                        self.change_cursor(None)
                        self.set_slideshow_sensitivities()

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
		try:
                        st = os.stat(self.userimage)
                        filesize = st[6]/1000
                        ratio = int(100 * self.zoomratio)
                        status_text=str(self.originalimg.get_width()) + "x" + str(self.originalimg.get_height()) + "   " + str(filesize) + "KB   " + str(ratio) + "%   "
                except:
                        status_text=_("Cannot load image.")
                self.statusbar.push(self.statusbar.get_context_id(""), status_text)
                return

        def show_prefs(self, action):
                self.prefs_dialog = gtk.Dialog(title=_("Mirage Preferences"), parent=self.window)
                self.prefs_dialog.set_has_separator(False)
                self.prefs_dialog.set_resizable(False)
                # Add "Interface" prefs:
		table_settings = gtk.Table(13, 3, False)
                table_settings.attach(gtk.Label(), 1, 3, 1, 2, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
                bglabel = gtk.Label()
                bglabel.set_markup("<b>_('Interface')</b>")
                bglabel.set_alignment(0, 1)
                table_settings.attach(bglabel, 1, 3, 2, 3, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 15, 0)
                table_settings.attach(gtk.Label(), 1, 3, 3, 4, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
		color_hbox = gtk.HBox(False, 0)
		colortext = gtk.Label("_('Background Color'):  ")
                colorbutton = gtk.ColorButton(self.bgcolor)
                colorbutton.connect('color-set', self.bgcolor_selected)
		color_hbox.pack_start(colortext, False, False, 0)
		color_hbox.pack_start(colorbutton, True, True, 0)
                table_settings.attach(color_hbox, 1, 2, 4, 5, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 30, 0)
                table_settings.attach(gtk.Label(), 1, 3, 5, 6, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
                zoomlabel = gtk.Label()
                zoomlabel.set_markup("<b>_('Zoom Quality')</b>")
                zoomlabel.set_alignment(0, 1)
                table_settings.attach(zoomlabel, 1, 3, 6, 7, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 15, 0)
                table_settings.attach(gtk.Label(), 1, 3, 7, 8,  gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 30, 0)
                zoompref = gtk.HScale()
                zoompref.set_range(1, 4)
                zoompref.set_increments(1,4)
                zoompref.set_draw_value(False)
                zoompref.set_value(self.zoomvalue)
                zoom_hbox = gtk.HBox(False, 0)
                zoom_label1 = gtk.Label()
                zoom_label1.set_markup("<i>_('Fastest')</i>")
                zoom_label1.set_alignment(0, 0)
                zoom_label2 = gtk.Label()
                zoom_label2.set_markup("<i>_('Best')</i>")
                zoom_label2.set_alignment(1, 0)
                zoom_hbox.pack_start(zoom_label1, True, True, 0)
                zoom_hbox.pack_start(zoom_label2, True, True, 0)
                table_settings.attach(zoompref, 1, 3, 8, 9,  gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 30, 0)
                table_settings.attach(zoom_hbox, 1, 3, 9, 10, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 30, 0)
                table_settings.attach(gtk.Label(), 1, 3, 10, 11,  gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 30, 0)
                table_settings.attach(gtk.Label(), 1, 3, 11, 12,  gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 30, 0)
                table_settings.attach(gtk.Label(), 1, 3, 12, 13,  gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 30, 0)
                # Add "Behavior" tab:
		table_behavior = gtk.Table(13, 2, False)
                table_behavior.attach(gtk.Label(), 1, 2, 1, 2, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
                openlabel = gtk.Label()
                openlabel.set_markup("<b>_('Open Behavior')</b>")
                openlabel.set_alignment(0, 1)
                table_behavior.attach(openlabel, 1, 2, 2, 3, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 15, 0)
                table_behavior.attach(gtk.Label(), 1, 2, 3, 4, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
                hbox_openmode = gtk.HBox()
                hbox_openmode.pack_start(gtk.Label("_('Open new image in'):"), False, False, 0)
                combobox = gtk.combo_box_new_text()
                combobox.append_text(_("Smart Mode"))
                combobox.append_text(_("Zoom To Fit Mode"))
                combobox.append_text(_("1:1 Mode"))
                combobox.append_text(_("Last Active Mode"))
                combobox.set_active(self.open_mode)
                gtk.Tooltips().set_tip(combobox, _("Smart mode uses 1:1 for images smaller than the window and Fit To Window for images larger."))
                hbox_openmode.pack_start(combobox, False, False, 5)
                table_behavior.attach(hbox_openmode, 1, 2, 4, 5, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 30, 0)
                table_behavior.attach(gtk.Label(), 1, 2, 5, 6, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
                openallimages = gtk.CheckButton(label=_("Load all images in current directory", use_underline=False))
                openallimages.set_active(self.open_all_images)
                gtk.Tooltips().set_tip(openallimages, _("If enabled, opening an image in Mirage will automatically load all images found in that image's directory."))
                table_behavior.attach(openallimages, 1, 2, 6, 7, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 30, 0)
                table_behavior.attach(gtk.Label(), 1, 2, 7, 8, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
                openpref = gtk.RadioButton()
                openpref1 = gtk.RadioButton(group=openpref, label=_("Use last chosen directory"))
                gtk.Tooltips().set_tip(openpref1, _("The default 'Open' directory will be the last directory used."))
                openpref2 = gtk.RadioButton(group=openpref, label=_("Use this fixed directory:"))
                openpref2.connect('toggled', self.use_fixed_dir_clicked)
                gtk.Tooltips().set_tip(openpref2, _("The default 'Open' directory will be this specified directory."))
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
                # Add "Navigation" tab:
		table_navigation = gtk.Table(13, 2, False)
                table_navigation.attach(gtk.Label(), 1, 2, 1, 2, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
                navlabel = gtk.Label()
                navlabel.set_markup("<b>_('Navigation')</b>")
                navlabel.set_alignment(0, 1)
                table_navigation.attach(navlabel, 1, 2, 2, 3, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 15, 0)
                mousewheelnav = gtk.CheckButton(label=_("Use mousewheel for imagelist navigation"), use_underline=False)
                mousewheelnav.set_active(self.mousewheel_nav)
                gtk.Tooltips().set_tip(mousewheelnav, _("If enabled, mousewheel-down (up) will go to the next (previous) image."))
                hbox_listwrap = gtk.HBox()
                hbox_listwrap.pack_start(gtk.Label(_("Wrap around imagelist:")), False, False, 0)
                combobox2 = gtk.combo_box_new_text()
                combobox2.append_text(_("No"))
                combobox2.append_text(_("Yes"))
                combobox2.append_text(_("Prompt User"))
                combobox2.set_active(self.listwrap_mode)
                hbox_listwrap.pack_start(combobox2, False, False, 5)
                table_navigation.attach(gtk.Label(), 1, 2, 3, 4, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
                table_navigation.attach(hbox_listwrap, 1, 2, 4, 5, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 30, 0)
                table_navigation.attach(gtk.Label(), 1, 2, 5, 6, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
                table_navigation.attach(mousewheelnav, 1, 2, 6, 7, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 30, 0)
                table_navigation.attach(gtk.Label(), 1, 2, 7, 8, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
                table_navigation.attach(gtk.Label(), 1, 2, 8, 9, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
                table_navigation.attach(gtk.Label(), 1, 2, 9, 10, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
                table_navigation.attach(gtk.Label(), 1, 2, 10, 11, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
                table_navigation.attach(gtk.Label(), 1, 2, 11, 12, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
                table_navigation.attach(gtk.Label(), 1, 2, 12, 13, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
                # Add "Slideshow" tab:
		table_slideshow = gtk.Table(13, 2, False)
                table_slideshow.attach(gtk.Label(), 1, 2, 1, 2, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
                slideshowlabel = gtk.Label()
                slideshowlabel.set_markup("<b>_('Slideshow')</b>")
                slideshowlabel.set_alignment(0, 1)
                table_slideshow.attach(slideshowlabel, 1, 2, 2, 3, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 15, 0)
                hbox_delay = gtk.HBox()
                hbox_delay.pack_start(gtk.Label(_("Delay between images:")), False, False, 0)
                delaycombo = gtk.combo_box_new_text()
                delaycombo.append_text(str(self.delayoptions[0]) + " _('seconds')")
                delaycombo.append_text(str(self.delayoptions[1]) + " _('seconds')")
                delaycombo.append_text(str(self.delayoptions[2]) + " _('seconds')")
                delaycombo.append_text(str(self.delayoptions[3]) + " _('seconds')")
                delaycombo.append_text(str(self.delayoptions[4]) + " _('seconds')")
                delaycombo.append_text(str(self.delayoptions[5]) + " _('seconds')")
                delaycombo.set_active(self.slideshow_delay)
                hbox_delay.pack_start(delaycombo, False, False, 5)
                randomize = gtk.CheckButton(_("Randomize order of images"))
                randomize.set_active(self.slideshow_random)
		disable_screensaver = gtk.CheckButton(_("Disable screensaver in slideshow mode"))
		disable_screensaver.set_active(self.disable_screensaver)
                table_slideshow.attach(gtk.Label(), 1, 2, 3, 4, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
                table_slideshow.attach(hbox_delay, 1, 2, 4, 5, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 30, 0)
                table_slideshow.attach(gtk.Label(), 1, 2, 5, 6, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
                table_slideshow.attach(disable_screensaver, 1, 2, 6, 7, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 30, 0)
                table_slideshow.attach(randomize, 1, 2, 7, 8, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 30, 0)
                table_slideshow.attach(gtk.Label(), 1, 2, 8, 9, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 30, 0)
                table_slideshow.attach(gtk.Label(), 1, 2, 9, 10, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
                table_slideshow.attach(gtk.Label(), 1, 2, 10, 11, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
                table_slideshow.attach(gtk.Label(), 1, 2, 11, 12, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
                table_slideshow.attach(gtk.Label(), 1, 2, 12, 13, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
                # Add "Editor" tab:
		table_editor = gtk.Table(13, 2, False)
                table_editor.attach(gtk.Label(), 1, 2, 1, 2, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
                editorlabel = gtk.Label()
                editorlabel.set_markup("<b>_('External Image Editor')</b>")
                editorlabel.set_alignment(0, 1)
                table_editor.attach(editorlabel, 1, 2, 2, 3, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 15, 0)
                table_editor.attach(gtk.Label(), 1, 3, 3, 4,  gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 30, 0)
                editorlabel = gtk.Label(_("The application specified below is used as the default editor. It is assumed to be in the user's PATH or can be explicitly set (e.g., \"/usr/bin/gimp-remote\")."))
                editorlabel.set_line_wrap(True)
                editorlabel.set_size_request(275, -1)
                table_editor.attach(editorlabel, 1, 3, 4, 5, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 30, 0)
                editortext = gtk.Entry()
                editortext.set_text(self.editor)
                table_editor.attach(gtk.Label(), 1, 2, 5, 6, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
                table_editor.attach(editortext, 1, 3, 7, 8, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 30, 0)
                table_editor.attach(gtk.Label(), 1, 2, 8, 9, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
                table_editor.attach(gtk.Label(), 1, 2, 9, 10, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
                table_editor.attach(gtk.Label(), 1, 2, 10, 11, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
                table_editor.attach(gtk.Label(), 1, 2, 11, 12, gtk.FILL|gtk.EXPAND, gtk.FILL|gtk.EXPAND, 0, 0)
                # Add tabs:
		notebook = gtk.Notebook()
                notebook.append_page(table_behavior, gtk.Label(str=_("Behavior")))
                notebook.append_page(table_navigation, gtk.Label(str=_("Navigation")))
                notebook.append_page(table_settings, gtk.Label(str=_("Interface")))
                notebook.append_page(table_slideshow, gtk.Label(str=_("Slideshow")))
                notebook.append_page(table_editor, gtk.Label(str=_("Editor")))
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
                        self.zoomvalue = float(zoompref.get_value())
                        if int(round(self.zoomvalue, 0)) == 1:
                                self.zoom_quality = gtk.gdk.INTERP_NEAREST
                        elif int(round(self.zoomvalue, 0)) == 2:
                                self.zoom_quality = gtk.gdk.INTERP_TILES
                        elif int(round(self.zoomvalue, 0)) == 3:
                                self.zoom_quality = gtk.gdk.INTERP_BILINEAR
                        elif int(round(self.zoomvalue, 0)) == 4:
                                self.zoom_quality = gtk.gdk.INTERP_HYPER
                        self.open_all_images = openallimages.get_active()
                        if openpref1.get_active() == True:
                                self.use_last_dir = True
                        else:
                                self.use_last_dir = False
                        self.open_mode = combobox.get_active()
                        self.mousewheel_nav = mousewheelnav.get_active()
                        self.listwrap_mode = combobox2.get_active()
                        self.set_go_navigation_sensitivities()
                        self.slideshow_delay = delaycombo.get_active()
                        self.curr_slideshow_delay = self.slideshow_delay
                        self.slideshow_random = randomize.get_active()
                        self.curr_slideshow_random = self.slideshow_random
                        self.editor = editortext.get_text()
			self.disable_screensaver = disable_screensaver.get_active()
                        self.prefs_dialog.destroy()
                        
        def use_fixed_dir_clicked(self, button):
                if button.get_active() == True:
                        self.defaultdir.set_sensitive(True)
                else:
                        self.defaultdir.set_sensitive(False)

        def defaultdir_clicked(self, button):
                getdir = gtk.FileChooserDialog(title=_("Choose directory"),action=gtk.FILE_CHOOSER_ACTION_OPEN,buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
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
                self.slideshow_window.modify_bg(gtk.STATE_NORMAL, self.bgcolor)
                self.slideshow_window2.modify_bg(gtk.STATE_NORMAL, self.bgcolor)

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
                self.about_dialog.set_comments(_('A fast GTK+ Image Viewer.'))
                self.about_dialog.set_license(__license__)
                self.about_dialog.set_authors(['Scott Horowitz <stonecrest@gmail.com>'])
                self.about_dialog.set_artists(['William Rea <sillywilly@gmail.com>'])
                self.about_dialog.set_website('http://mirageiv.berlios.de')
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
                        if self.slideshow_controls_visible == False:
                                gobject.source_remove(self.timer_id)
                                while gtk.events_pending():
                                        gtk.main_iteration()
                                self.timer_id = gobject.timeout_add(2000, self.hide_cursor)
                        if y > 0.9*self.available_image_height():
                                self.slideshow_controls_show()
                        else:
                                self.slideshow_controls_hide()
                return True

        def button_pressed(self, widget, event):
                if self.image_loaded == True:
                        # Changes the cursor to the 'resize' cursor, like GIMP, on a middle click:
			if (event.button == 2 or event.button == 1) and (self.hscroll.get_property('visible')==True or self.vscroll.get_property('visible')==True):
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
                if self.userimage != "" and self.UIManager.get_widget('/MainMenu/ViewMenu/In').get_property('sensitive') == True:
                        self.zoomratio = self.zoomratio * 1.25
                        self.set_zoom_sensitivities()
                        self.last_image_action_was_fit = False
                        self.put_zoom_image_to_window()
                        self.update_statusbar()
                return

        def zoom_out(self, action):
                if self.userimage != "" and self.UIManager.get_widget('/MainMenu/ViewMenu/Out').get_property('sensitive') == True:
                        self.zoomratio = self.zoomratio * 1/1.25
                        self.set_zoom_sensitivities()
                        self.last_image_action_was_fit = False
                        self.put_zoom_image_to_window()
                        self.update_statusbar()
                return

        def zoom_to_fit_window(self, action):
                if self.userimage != "" and (self.slideshow_mode == True or self.UIManager.get_widget('/MainMenu/ViewMenu/Fit').get_property('sensitive') == True):
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
                        self.set_zoom_sensitivities()
                        self.put_zoom_image_to_window()
                        self.update_statusbar()
                return

        def zoom_to_fit_or_1_to_1(self, action):
                if self.userimage != "":
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
                        self.set_zoom_sensitivities()
                        if self.first_image_load == True and self.zoomratio > 1:
                                # Revert to 1:1 zoom
				self.zoom_1_to_1(action)
                        else:
                                self.put_zoom_image_to_window()
                                self.update_statusbar()
                return

        def zoom_1_to_1(self, action):
                if self.userimage != "" and (self.slideshow_mode == True or self.image_is_animation == True or (self.image_is_animation == False and self.UIManager.get_widget('/MainMenu/ViewMenu/1:1').get_property('sensitive') == True)):
                        self.last_mode = self.open_mode_1to1
                        self.last_image_action_was_fit = False
                        self.zoomratio = 1
                        self.put_zoom_image_to_window()
                        self.update_statusbar()
                return

        def rotate_left(self, action):
                if self.userimage != "" and self.UIManager.get_widget('/MainMenu/EditMenu/Rotate Left').get_property('sensitive') == True:
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
                if self.userimage != "" and self.UIManager.get_widget('/MainMenu/EditMenu/Rotate Right').get_property('sensitive') == True:
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
                if self.userimage != ""  and self.UIManager.get_widget('/MainMenu/EditMenu/Flip Vertically').get_property('sensitive') == True:
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
                if self.userimage != "" and self.UIManager.get_widget('/MainMenu/EditMenu/Flip Horizontally').get_property('sensitive') == True:
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
                if self.slideshow_mode == True and action != "ss":
                        gobject.source_remove(self.timer_delay)
                if len(self.image_list) > 1:
                        self.randomlist = []
                        if self.curr_img_in_list > 0:
                                self.curr_img_in_list -= 1
                        else:
                                if self.listwrap_mode == 0:
                                        return
                                elif self.listwrap_mode == 1:
                                        self.curr_img_in_list = len(self.image_list) - 1
                                else:
                                        if self.fullscreen_mode == True:
                                                self.change_cursor(None)
                                        dialog = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO, _("You are viewing the first image in the list. Wrap around to the last image?"))
                                        dialog.set_default_response(gtk.RESPONSE_YES)
                                        self.user_prompt_visible = True
                                        response = dialog.run()
                                        if response == gtk.RESPONSE_YES:
                                                self.curr_img_in_list = len(self.image_list)-1
                                                dialog.destroy()
                                                self.user_prompt_visible = False
                                                if self.fullscreen_mode == True:
                                                        self.hide_cursor
                                        else:
                                                dialog.destroy()
                                                self.user_prompt_visible = False
                                                if self.fullscreen_mode == True:
                                                        self.hide_cursor
                                                if self.slideshow_mode == True:
                                                        self.toggle_slideshow(None)
                                                return
                        if self.fullscreen_mode == False:
                                self.change_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
                        gtk.main_iteration()
                        try:
                                self.load_new_image()
                        except:
                                self.image_load_failed()
                        self.set_go_navigation_sensitivities()
                        if self.fullscreen_mode == False:
                                self.change_cursor(None)
                        if self.slideshow_mode == True:
                                if self.curr_slideshow_random == True:
                                        self.timer_delay = gobject.timeout_add(self.delayoptions[self.curr_slideshow_delay]*1000, self.random_img_in_list, "ss")
                                else:
                                        self.timer_delay = gobject.timeout_add(self.delayoptions[self.curr_slideshow_delay]*1000, self.next_img_in_list, "ss")

        def next_img_in_list(self, action):
                if self.slideshow_mode == True and action != "ss":
                        gobject.source_remove(self.timer_delay)
                if len(self.image_list) > 1:
                        self.randomlist = []
                        if self.curr_img_in_list < len(self.image_list) - 1:
                                self.curr_img_in_list += 1
                        else:
                                if self.listwrap_mode == 0:
                                        if self.slideshow_mode == True:
                                                self.toggle_slideshow(None)
                                        return
                                elif self.listwrap_mode == 1:
                                        self.curr_img_in_list = 0
                                else:
                                        if self.fullscreen_mode == True:
                                                self.change_cursor(None)
                                        dialog = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO, _("You are viewing the last image in the list. Wrap around to the first image?"))
                                        dialog.set_default_response(gtk.RESPONSE_YES)
                                        self.user_prompt_visible = True
                                        response = dialog.run()
                                        if response == gtk.RESPONSE_YES:
                                                self.curr_img_in_list = 0
                                                dialog.destroy()
                                                self.user_prompt_visible = False
                                                if self.fullscreen_mode == True:
                                                        self.hide_cursor
                                        else:
                                                dialog.destroy()
                                                self.user_prompt_visible = False
                                                if self.fullscreen_mode == True:
                                                        self.hide_cursor
                                                if self.slideshow_mode == True:
                                                        self.toggle_slideshow(None)
                                                return
                        if self.fullscreen_mode == False and (self.slideshow_mode == False or (self.slideshow_mode == True and action != "ss")):
                                self.change_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
                        gtk.main_iteration()
                        #try:
			self.load_new_image()
                        #except:
			#	self.image_load_failed()
			if self.fullscreen_mode == False:
                                self.change_cursor(None)
                        self.set_go_navigation_sensitivities()
                        if self.slideshow_mode == True:
                                if self.curr_slideshow_random == True:
                                        self.timer_delay = gobject.timeout_add(self.delayoptions[self.curr_slideshow_delay]*1000, self.random_img_in_list, "ss")
                                else:
                                        self.timer_delay = gobject.timeout_add(self.delayoptions[self.curr_slideshow_delay]*1000, self.next_img_in_list, "ss")

        def random_img_in_list(self, action):
                if self.slideshow_mode == True and action != "ss":
                        gobject.source_remove(self.timer_delay)
                if len(self.image_list) > 1:
                        if self.randomlist == []:
                                self.reinitialize_randomlist()
                        else:
                                # check if we have seen every image; if so, reinitialize array and repeat:
				all_items_are_true = True
                                for item in self.randomlist:
                                        if item == False:
                                                all_items_are_true = False
                                if all_items_are_true == True:
                                        if self.slideshow_mode == False or (self.slideshow_mode == True and self.listwrap_mode == 1):
                                                self.reinitialize_randomlist()
                                        else:
                                                if self.listwrap_mode == 0:
                                                        self.toggle_slideshow(None)
                                                        return
                                                elif self.listwrap_mode == 2:
                                                        if self.fullscreen_mode == True:
                                                                self.change_cursor(None)
                                                        dialog = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO, _("All images have been viewed. Would you like to cycle through the images again?"))
                                                        dialog.set_default_response(gtk.RESPONSE_YES)
                                                        self.user_prompt_visible = True
                                                        response = dialog.run()
                                                        if response == gtk.RESPONSE_YES:
                                                                dialog.destroy()
                                                                self.reinitialize_randomlist()
                                                                self.user_prompt_visible = False
                                                                if self.fullscreen_mode == True:
                                                                        self.hide_cursor
                                                        else:
                                                                dialog.destroy()
                                                                self.user_prompt_visible = False
                                                                if self.fullscreen_mode == True:
                                                                        self.hide_cursor
                                                                if self.slideshow_mode == True:
                                                                        self.toggle_slideshow(None)
                                                                return
                        # Find random image that hasn't already been chosen:
			j = random.randint(0, len(self.image_list)-1)
                        while self.randomlist[j] == True:
                                j = random.randint(0, len(self.image_list)-1)
                        self.curr_img_in_list = j
                        self.randomlist[j] = True
                        self.userimage = str(self.image_list[self.curr_img_in_list])
                        if self.fullscreen_mode == False and (self.slideshow_mode == False or (self.slideshow_mode == True and action != "ss")):
                                self.change_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
                        gtk.main_iteration()
                        try:
                                self.load_new_image()
                        except:
                                self.image_load_failed()
                        if self.fullscreen_mode == False:
                                self.change_cursor(None)
                        self.set_go_navigation_sensitivities()
                        if self.slideshow_mode == True:
                                if self.curr_slideshow_random == True:
                                        self.timer_delay = gobject.timeout_add(self.delayoptions[self.curr_slideshow_delay]*1000, self.random_img_in_list, "ss")
                                else:
                                        self.timer_delay = gobject.timeout_add(self.delayoptions[self.curr_slideshow_delay]*1000, self.next_img_in_list, "ss")

        def first_img_in_list(self, action):
                if self.slideshow_mode == True and action != "ss":
                        gobject.source_remove(self.timer_delay)
                if len(self.image_list) > 1 and self.curr_img_in_list != 0:
                        self.randomlist = []
                        self.curr_img_in_list = 0
                        self.change_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
                        gtk.main_iteration()
                        try:
                                self.load_new_image()
                        except:
                                self.image_load_failed()
                        self.set_go_navigation_sensitivities()
                        self.change_cursor(None)
                        if self.slideshow_mode == True:
                                if self.curr_slideshow_random == True:
                                        self.timer_delay = gobject.timeout_add(self.delayoptions[self.curr_slideshow_delay]*1000, self.random_img_in_list, "ss")
                                else:
                                        self.timer_delay = gobject.timeout_add(self.delayoptions[self.curr_slideshow_delay]*1000, self.next_img_in_list, "ss")

        def last_img_in_list(self, action):
                if self.slideshow_mode == True and action != "ss":
                        gobject.source_remove(self.timer_delay)
                if len(self.image_list) > 1 and self.curr_img_in_list != len(self.image_list)-1:
                        self.randomlist = []
                        self.curr_img_in_list = len(self.image_list)-1
                        self.change_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
                        gtk.main_iteration()
                        try:
                                self.load_new_image()
                        except:
                                self.image_load_failed()
                        self.set_go_navigation_sensitivities()
                        self.change_cursor(None)
                        if self.slideshow_mode == True:
                                if self.curr_slideshow_random == True:
                                        self.timer_delay = gobject.timeout_add(self.delayoptions[self.curr_slideshow_delay]*1000, self.random_img_in_list, "ss")
                                else:
                                        self.timer_delay = gobject.timeout_add(self.delayoptions[self.curr_slideshow_delay]*1000, self.next_img_in_list, "ss")

        def set_go_navigation_sensitivities(self):
                if self.image_loaded == False or len(self.image_list) == 1:
                        self.set_previous_image_sensitivities(False)
                        self.set_first_image_sensitivities(False)
                        self.set_next_image_sensitivities(False)
                        self.set_last_image_sensitivities(False)
                elif self.curr_img_in_list == 0:
                        if self.listwrap_mode == 0:
                                self.set_previous_image_sensitivities(False)
                        else:
                                self.set_previous_image_sensitivities(True)
                        self.set_first_image_sensitivities(False)
                        self.set_next_image_sensitivities(True)
                        self.set_last_image_sensitivities(True)
                elif self.curr_img_in_list == len(self.image_list)-1:
                        self.set_previous_image_sensitivities(True)
                        self.set_first_image_sensitivities(True)
                        if self.listwrap_mode == 0:
                                self.set_next_image_sensitivities(False)
                        else:
                                self.set_next_image_sensitivities(True)
                        self.set_last_image_sensitivities(False)
                else:
                        self.set_previous_image_sensitivities(True)
                        self.set_first_image_sensitivities(True)
                        self.set_next_image_sensitivities(True)
                        self.set_last_image_sensitivities(True)

        def reinitialize_randomlist(self):
                self.randomlist = []
                for i in range(len(self.image_list)):
                        self.randomlist.append(False)
                self.randomlist[self.curr_img_in_list] = True
                
        def image_load_failed(self):
                self.userimage = str(self.image_list[self.curr_img_in_list])
                if self.verbose == True and self.userimage != "":
                        print _("Loading:"), self.userimage
                self.set_window_title()
                self.put_error_image_to_window()
                self.image_loaded = False
                        
        def load_new_image(self):
                self.currimg = None
                self.first_image_load = True
                self.location = 0
                self.orientation = 0
                self.zoomratio = 1
                self.userimage = str(self.image_list[self.curr_img_in_list])
                if self.verbose == True and self.userimage != "":
                        print _("Loading:"), self.userimage
                animtest = gtk.gdk.PixbufAnimation(self.userimage)
                if animtest.is_static_image() == True:
                        self.image_is_animation = False
                        self.originalimg = animtest.get_static_image()
                        self.set_image_sensitivities(True)
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
                else:
                        self.image_is_animation = True
                        self.originalimg = animtest
                        self.zoom_1_to_1(None)
                        self.set_image_sensitivities(False)
                self.update_statusbar()
                self.set_window_title()
                self.image_loaded = True
                self.set_slideshow_sensitivities()
                
        def change_cursor(self, type):
                for i in gtk.gdk.window_get_toplevels():
                        if i.get_window_type() != gtk.gdk.WINDOW_TEMP and i.get_window_type() != gtk.gdk.WINDOW_CHILD:
                                i.set_cursor(type)
                self.layout.window.set_cursor(type)
                
        def expand_filelist_and_load_image(self, inputlist):
		self.images_found = 0
                # Takes the current list (i.e. ["pic.jpg", "pic2.gif", "../images"]) and
		# expands it into a list of all pictures found; returns new list
		self.change_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
                while gtk.events_pending():
                        gtk.main_iteration()
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
                        item_fullpath = os.path.abspath(inputlist[0])
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
		inputlist.sort(locale.strcoll)
                for item in inputlist:
			if item[0] != '.':
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
							self.images_found += 1
	                                                print _("Found:"), item_fullpath, "[" + str(self.images_found) + "]"
				# If it's a directory that was explicitly selected or passed to
				# the program, get all the files in the dir.
				# Retrieve only images in the top directory specified by the user
				# only explicitly told to recurse (via -R or in Settings>Preferences)
				elif os.path.isdir(item_fullpath):
	                                folderlist.append(item)
                # Sort the filelist and folderlist alphabetically, and recurse into folderlist:
		if len(filelist) > 0:
                        filelist = list(set(filelist))
                        filelist.sort(locale.strcoll)
                if len(folderlist) > 0:
                        folderlist.sort(locale.strcoll)
                        folderlist = list(set(folderlist))
                        for item in folderlist:
				if item[0] != '.':
					filelist = self.expand_directory(item, filelist, False, False)
                # We now have the full list, update to full paths:
		for item in filelist:
                        self.image_list.append(os.path.abspath(item))
                if len(self.image_list) <= 1:
                        self.set_go_sensitivities(False)
                else:
                        self.set_go_sensitivities(True)
                if len(self.image_list) > 0:
                        if self.slideshow_mode == True:
                                self.toggle_slideshow(None)
                        # Find first specified image in list for updating Mirage title:
			if first_image_found == True:
                                for itemnum in range(len(self.image_list)):
                                        if first_image == self.image_list[itemnum]:
                                                self.curr_img_in_list = itemnum
                        if self.verbose == True and self.userimage != "":
                                print _("Loading:"), self.userimage
                        try:
                                self.originalimg = gtk.gdk.pixbuf_new_from_file(str(self.image_list[self.curr_img_in_list]))
                                self.load_new_image()
                                if self.image_is_animation == False:
                                        self.previmg_width = self.currimg.get_width()
                                else:
                                        self.previmg_width = self.currimg.get_static_image().get_width()
                                self.image_loaded = True
                                while gtk.events_pending():
                                        gtk.main_iteration(True)
                        except:
                                self.image_load_failed()
                                pass
                self.change_cursor(None)

        def expand_directory(self, item, inputlist, stop_when_image_found, stop_now):
                if stop_now == False:
                        filelist = []
                        folderlist = []
                        if os.access(item, os.R_OK) == False:
                                return inputlist
                        for item2 in os.listdir(item):
				if item2[0] != '.':
					item2 = item + "/" + item2
					item_fullpath2 = os.path.abspath(item2)
					if os.path.isfile(item_fullpath2):
	                                        if self.valid_image(item_fullpath2) == True:
							filelist.append(item2)
							if stop_when_image_found == True:
	                                                        stop_now = True
							if self.verbose == True:
								self.images_found += 1
	                                                        print _("Found:"), item_fullpath2, "[" + str(self.images_found) + "]"
					elif os.path.isdir(item_fullpath2) and self.recursive == True:
	                                        folderlist.append(item_fullpath2)
                        # Sort the filelist and folderlist alphabetically, and recurse into folderlist:
			if len(filelist) > 0:
                                filelist.sort(locale.strcoll)
                                inputlist = inputlist + filelist
                        if len(folderlist) > 0:
                                folderlist.sort(locale.strcoll)
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
                
        def toggle_slideshow(self, action):
                if len(self.image_list) > 1:
                        if self.slideshow_mode == False:
                                self.slideshow_mode = True
                                self.set_window_title()
                                self.set_slideshow_sensitivities()
                                if self.curr_slideshow_random == False:
                                        self.timer_delay = gobject.timeout_add(self.delayoptions[self.curr_slideshow_delay]*1000, self.next_img_in_list, "ss")
                                else:
                                        self.reinitialize_randomlist()
                                        self.timer_delay = gobject.timeout_add(self.delayoptions[self.curr_slideshow_delay]*1000, self.random_img_in_list, "ss")
                                self.ss_start.hide()
                                self.ss_stop.show()
				timer_screensaver = gobject.timeout_add(1000, self.disable_screensaver_in_slideshow_mode)
                        else:
                                self.slideshow_mode = False
                                gobject.source_remove(self.timer_delay)
                                self.set_window_title()
                                self.set_slideshow_sensitivities()
                                self.set_zoom_sensitivities()
                                self.ss_stop.hide()
                                self.ss_start.show()
                        
        def set_window_title(self):
                if len(self.image_list) == 0:
                        self.window.set_title("Mirage")
                else:
                        if self.slideshow_mode == True:
                                self.window.set_title("Mirage - [" + str(self.curr_img_in_list+1) + " _('of') " + str(len(self.image_list)) + "] " + os.path.basename(self.userimage) + " - _('Slideshow Mode')")
                        else:
                                self.window.set_title("Mirage - [" + str(self.curr_img_in_list+1) + " _('of') " + str(len(self.image_list)) + "] " + os.path.basename(self.userimage))
                                
        def slideshow_controls_show(self):
                if self.slideshow_controls_visible == False and self.controls_moving == False:
                        self.slideshow_controls_visible = True
                        
                        self.ss_delaycombo.set_active(self.curr_slideshow_delay)
                        self.ss_randomize.set_active(self.curr_slideshow_random)

                        if self.slideshow_mode == True:
                                self.ss_start.set_no_show_all(True)
                                self.ss_stop.set_no_show_all(False)
                        else:
                                self.ss_start.set_no_show_all(False)
                                self.ss_stop.set_no_show_all(True)
                        self.slideshow_window.show_all()
                        self.slideshow_window2.show_all()
                        while gtk.events_pending():
                                gtk.main_iteration()
                        
                        ss_winheight = self.slideshow_window.allocation.height
                        ss_win2width = self.slideshow_window2.allocation.width
                        winheight = self.window.allocation.height
                        winwidth = self.window.allocation.width
                        y = -3.0
                        self.controls_moving = True
                        while y < ss_winheight:
                                self.slideshow_window.move(2, int(winheight-y-2))
                                self.slideshow_window2.move(winwidth-ss_win2width-2, int(winheight-y-2))
                                y += 0.05
                                while gtk.events_pending():
                                        gtk.main_iteration()
                        self.controls_moving = False

        def slideshow_controls_hide(self):
                if self.slideshow_controls_visible == True and self.controls_moving == False:
                        self.slideshow_controls_visible = False
                        
                        ss_winheight = self.slideshow_window.allocation.height
                        ss_win2width = self.slideshow_window2.allocation.width
                        winheight = self.window.allocation.height
                        winwidth = self.window.allocation.width
                        y = float(self.slideshow_window.allocation.height*1.0)
                        self.controls_moving = True
                        while y > -3:
                                self.slideshow_window.move(2, int(winheight-y-2))
                                self.slideshow_window2.move(winwidth-ss_win2width-2, int(winheight-y-2))
                                y -= 0.05
                                while gtk.events_pending():
                                        gtk.main_iteration()
                        self.controls_moving = False
                        
        def load_editor(self, action):
                if self.UIManager.get_widget('/MainMenu/EditMenu/Open in Editor').get_property('sensitive') == True:
                        test = os.spawnlp(os.P_WAIT, self.editor, self.editor, self.userimage)
                        if test == 127:
                                error_dialog = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING, gtk.BUTTONS_CLOSE, "_('Unable to launch') \"" + self.editor + "\". _('Please specify a valid application from Edit > Preferences.')")
                                error_dialog.run()
                                error_dialog.destroy()
				
	def disable_screensaver_in_slideshow_mode(self):
		if self.slideshow_mode == True and self.disable_screensaver == True:
			test = os.spawnlp(os.P_WAIT, "/usr/bin/xscreensaver-command", "xscreensaver-command", "-deactivate")
			if test <> 127:
				timer_screensaver = gobject.timeout_add(1000, self.disable_screensaver_in_slideshow_mode)
	
        def main(self):
                gtk.main()

if __name__ == "__main__":
        base = Base()
        base.main()

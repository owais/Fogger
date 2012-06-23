# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# This file is in the public domain
### END LICENSE

import gettext
from gettext import gettext as _
gettext.textdomain('fogger')

from gi.repository import Gtk, Gdk, GdkPixbuf # pylint: disable=E0611
import logging
logger = logging.getLogger('fogger')
from quickly.prompts import open_image_file
from fogger_lib import Window
from fogger_lib import app_manager
from fogger_lib.errors import BaseFogAppException
from fogger.AboutFoggerDialog import AboutFoggerDialog
from fogger.PreferencesFoggerDialog import PreferencesFoggerDialog

# See fogger_lib.Window.py for more details about how this class works
class FoggerWindow(Window):
    __gtype_name__ = "FoggerWindow"

    def finish_initializing(self, builder): # pylint: disable=E1002
        """Set up the main window"""
        super(FoggerWindow, self).finish_initializing(builder)

        self.AboutDialog = AboutFoggerDialog
        self.PreferencesDialog = PreferencesFoggerDialog

        self.overlay = Gtk.Overlay()
        vbox = self.builder.get_object('vbox1')
        vbox.pack_start(self.overlay, True, True, 0)
        vbox.reorder_child(self.overlay, 5)
        bgimg = self.builder.get_object('eventbox1')
        bgimg.set_halign(Gtk.Align.CENTER)
        bgimg.set_valign(Gtk.Align.CENTER)
        self.overlay.add(bgimg)
        bgimg.show()
        self.overlay.show_all()

        self.url = self.builder.get_object('url_entry')
        self.name = self.builder.get_object('name_entry')
        self.icon = self.builder.get_object('app_icon')
        self.icon.props.pixbuf = self.icon.get_pixbuf().scale_simple(80, 80, GdkPixbuf.InterpType.BILINEAR)
        self.icon_path = None
        self.setup_drop_targets()


    def on_cancel(self, widget, data=None):
        self.destroy()

    def on_create(self, widget, data=None):
        name = self.name.get_text()
        url = self.url.get_text()
        try:
            app = app_manager.create(name, url, self.icon_path)
        except BaseFogAppException:
            logger.error("Error creating App %s" % url)
        else:
            app.run()
            self.hide()

    def setup_drop_targets(self):
        self.drag_dest_set(Gtk.DestDefaults.ALL, [], Gdk.DragAction.MOVE)
        self.connect("drag-data-received", self.on_drag_data_received)
        self.drag_dest_add_uri_targets()

    def on_drag_data_received(self, widget, context, x, y, data, info, time):
        try:
            path = data.get_uris()[0]
        except IndexError:
            return
        else:
            path = path.replace('file://', '')
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(path)
            self.icon.props.pixbuf = pixbuf.scale_simple(80, 80, GdkPixbuf.InterpType.BILINEAR)
            self.icon_path = path

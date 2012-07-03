# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# Copyright (C) 2012 Owais Lone <hello@owaislone.org>
# This program is free software: you can redistribute it and/or modify it 
# under the terms of the GNU General Public License version 3, as published 
# by the Free Software Foundation.
# 
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranties of 
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR 
# PURPOSE.  See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along 
# with this program.  If not, see <http://www.gnu.org/licenses/>.
### END LICENSE

import gettext
from gettext import gettext as _
gettext.textdomain('fogger')

from gi.repository import Gtk, Gdk, GdkPixbuf, Gio # pylint: disable=E0611
from quickly.prompts import yes_no
import logging
logger = logging.getLogger('fogger')
from fogger_lib import Window
from fogger_lib import app_manager
from fogger_lib.errors import BaseFogAppException
from fogger.AboutFoggerDialog import AboutFoggerDialog
from fogger.PreferencesFoggerDialog import PreferencesFoggerDialog


ICON_SIZE = Gtk.icon_size_register('FoggerIconSize', 80, 80)


# See fogger_lib.Window.py for more details about how this class works
class FoggerWindow(Window):
    __gtype_name__ = "FoggerWindow"

    def finish_initializing(self, builder): # pylint: disable=E1002
        """Set up the main window"""
        super(FoggerWindow, self).finish_initializing(builder)

        self.AboutDialog = AboutFoggerDialog
        self.PreferencesDialog = PreferencesFoggerDialog

        self.url = self.builder.get_object('url_entry')
        self.url.realize()
        self.name = self.builder.get_object('name_entry')
        self.icon = self.builder.get_object('app_icon')
        self.create_button = self.builder.get_object('create_button')
        #self.icon.props.pixbuf = self.icon.get_pixbuf().scale_simple(80, 80, GdkPixbuf.InterpType.BILINEAR)
        self.icon_path = 'fogger'
        self.setup_drop_targets()
        self.icon_theme = Gtk.IconTheme.get_default()

    def on_cancel(self, widget, data=None):
        self.destroy()

    def on_url_changed(self, widget, data=None):
        pass

    def validate_form(self, widget, data=None):
        url = self.url.get_text()
        name = self.name.get_text()
        sensitive = url and name
        self.create_button.set_sensitive(sensitive)

    def on_name_changed(self, widget, data=None):
        name = self.name.get_text().lower().replace(' ', '-')
        gicon = None
        if self.icon_theme.has_icon(name):
            gicon = Gio.Icon.new_for_string(name)
            self.icon_path = name
        else:
            for subname in name.split('-'):
                if self.icon_theme.has_icon(subname):
                    gicon = Gio.Icon.new_for_string(subname)
                    self.icon_path = subname
                    break
        if not gicon:
            gicon = Gio.Icon.new_for_string('foggerapp')
            self.icon_path = 'foggerapp'
        self.icon.set_from_gicon(gicon, ICON_SIZE)

    def on_create(self, widget, data=None):
        name = self.name.get_text()
        url = self.url.get_text()
        try:
            app = app_manager.create(name, url, self.icon_path)
        except BaseFogAppException:
            logger.error("Error creating App %s" % url)
        else:
            app = Gio.DesktopAppInfo.new_from_filename(app.desktop_file)
            app.launch([], Gio.AppLaunchContext())
            self.destroy()

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

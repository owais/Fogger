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


from gi.repository import Gtk, GLib, GObject # pylint: disable=E0611

import gettext
from gettext import gettext as _
gettext.textdomain('fogger')

import logging
logger = logging.getLogger('fogger')

from fogger_lib.PreferencesDialog import PreferencesDialog
from fogger_lib import ConfirmDialog
from fogger_lib.helpers import show_uri

class PreferencesFoggerDialog(PreferencesDialog):
    __gtype_name__ = "PreferencesFoggerDialog"
    __gsignals__ = {
        'fogger-autostart-changed': (GObject.SIGNAL_RUN_FIRST, None, (bool,)),
        'fogger-app-reset': (GObject.SIGNAL_RUN_FIRST, None, tuple()),
        'fogger-app-remove': (GObject.SIGNAL_RUN_FIRST, None, tuple()),
    }
    scripts_path = None
    styles_path = None

    def finish_initializing(self, builder): # pylint: disable=E1002
        """Set up the preferences dialog"""
        super(PreferencesFoggerDialog, self).finish_initializing(builder)

        # Bind each preference widget to gsettings
        #settings = Gio.Settings("net.launchpad.fogger")
        #settings.bind("example", widget, "text", Gio.SettingsBindFlags.DEFAULT)
        #widget = self.builder.get_object('example_entry')

        # Code for other initialization actions should be added here.
        #
        self.autostart = builder.get_object('autostart')
        self.space_label = builder.get_object('space')
        self.autostart.connect('notify::active', self.on_autostart_change)

    def on_reset_data(self, widget, data=None):
        d = ConfirmDialog('Reset', _('Are you sure you want to reset the app?'),
                _('This will log you out of all websites and delete all local data'),
                None, self, 'gtk-delete')
        response = d.run()
        if response == Gtk.ResponseType.YES:
            self.emit('fogger-app-reset')
            self.space_label.set_text('')
        d.destroy()

    def on_remove_app(self, widget, data=None):
        d = ConfirmDialog('Remove', _('Are you sure you want to remove the app?'),
                _('This will permanently remove the app and delete all the data associated with it.'),
                None, self, 'gtk-delete')
        response = d.run()
        if response == Gtk.ResponseType.YES:
            self.emit('fogger-app-remove')
            self.space_label.set_text('')
        d.destroy()

    def on_autostart_change(self, widget, value, data=None):
        self.emit('fogger-autostart-changed', self.autostart.props.active)

    def on_show_scripts(self, widget, data=None):
        if self.scripts_path:
            show_uri(self, GLib.filename_to_uri(self.scripts_path, 'file'))

    def on_show_styles(self, widget, data=None):
        if self.styles_path:
            show_uri(self, GLib.filename_to_uri(self.styles_path, 'file'))

    def set_autostart_widget(self, autostart):
        self.autostart.props.active = autostart

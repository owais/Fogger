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

from gi.repository import Gio, Gtk # pylint: disable=E0611
import logging
logger = logging.getLogger('fogger_lib')

import gettext
from gettext import gettext as _
gettext.textdomain('fogger')

from . helpers import get_builder, show_uri, get_help_uri


# This class is meant to be subclassed by FoggerWindow.  It provides
# common functions and some boilerplate.
class AppWindow(Gtk.Window):
    __gtype_name__ = "AppWindow"

    def __new__(cls):
        """Special static method that's automatically called by Python when
        constructing a new instance of this class.

        Returns a fully instantiated BaseFoggerWindow object.
        """
        builder = get_builder('FoggerAppWindow')
        new_object = builder.get_object("fogger_app_window")
        new_object.finish_initializing(builder)
        return new_object

    def finish_initializing(self, builder):
        """Called while initializing this instance in __new__

        finish_initializing should be called after parsing the UI definition
        and creating a FoggerWindow object with it in order to finish
        initializing the start of the new FoggerWindow instance.
        """
        # Get a reference to the builder and set up the signals.
        self.builder = builder
        self.ui = builder.get_ui(self, True)
        self.PreferencesDialog = None # class
        self.preferences_dialog = None # instance
        self.AboutDialog = None # class

        self.root = None
        self.popups = [self]
        #self.is_destroyed = False

        try:
            from gi.repository import LaunchpadIntegration # pylint: disable=E0611
            LaunchpadIntegration.add_items(self.ui.helpMenu, 1, True, True)
            LaunchpadIntegration.set_sourcepackagename('fogger')
        except ImportError:
            pass


    @property
    def is_popup(self):
        return self.root != None

    def on_mnu_contents_activate(self, widget, data=None):
        show_uri(self, "ghelp:%s" % get_help_uri())

    def on_mnu_about_activate(self, widget, data=None):
        """Display the about box for fogger."""
        if self.AboutDialog is not None:
            about = self.AboutDialog() # pylint: disable=E1102
            response = about.run()
            about.destroy()

    def on_mnu_preferences_activate(self, widget, data=None):
        """Display the preferences window for fogger."""

        """ From the PyGTK Reference manual
           Say for example the preferences dialog is currently open,
           and the user chooses Preferences from the menu a second time;
           use the present() method to move the already-open dialog
           where the user can see it."""
        if self.preferences_dialog is not None:
            logger.debug('show existing preferences_dialog')
            self.preferences_dialog.present()
        elif self.PreferencesDialog is not None:
            logger.debug('create new preferences_dialog')
            self.preferences_dialog = self.PreferencesDialog() # pylint: disable=E1102
            if hasattr(self, 'app'):
                sl = self.preferences_dialog.space_label
                sl.set_markup('<small><tt>%s</tt></small>' % (_('%s will be freed.' % self.app.data_size)))
                sl.show()
                self.preferences_dialog.set_autostart_widget(self.app.autostart)
                self.preferences_dialog.scripts_path = self.app.userscripts_path
                self.preferences_dialog.styles_path = self.app.userstyles_path
            self.preferences_dialog.connect('destroy', self.on_preferences_dialog_destroyed)
            self.preferences_dialog.connect('fogger-autostart-changed', self.on_fogger_autostart_changed)
            self.preferences_dialog.connect('fogger-app-reset', self.on_fogger_app_reset)
            self.preferences_dialog.connect('fogger-app-remove', self.on_fogger_app_remove)
            self.preferences_dialog.show()

    def on_mnu_close_activate(self, widget, data=None):
        """Signal handler for closing the FoggerWindow."""
        self.destroy()

    def on_preferences_dialog_destroyed(self, widget, data=None):
        self.preferences_dialog = None

    def on_destroy(self, widget, data=None):
        """Called when the FoggerWindow is closed."""
        # Clean up code for saving application state should be added here.
        if self.is_popup:
            self.root.popups.remove(self)
            if not self.root.popups:
                self.root.on_destroy(self.root)
            else:
                self.destroy()
        else:
            if len(self.popups) > 1:
                self.popups.remove(self)
                self.hide()
            else:
                if self.downloads:
                    self.downloads.cancel_all()
                Gtk.main_quit()
        return True

    def on_fogger_app_reset(self, widget, data=None):
        pass

    def on_fogger_autostart_changed(self, widget, data=None):
        pass

    def on_fogger_app_remove(self, widget, data=None):
        pass

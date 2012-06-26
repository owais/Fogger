# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# This file is in the public domain
### END LICENSE

from os import path as op
import gettext
from gettext import gettext as _
gettext.textdomain('fogger')

from gi.repository import Gtk, Gdk, WebKit # pylint: disable=E0611
import logging
logger = logging.getLogger('fogger')

from fogger_lib import AppWindow
from fogger_lib.helpers import get_media_file
from fogger.AboutFoggerDialog import AboutFoggerDialog
from fogger.PreferencesFoggerDialog import PreferencesFoggerDialog

# See fogger_lib.Window.py for more details about how this class works
class FoggerAppWindow(AppWindow):
    __gtype_name__ = "FoggerAppWindow"

    def finish_initializing(self, builder): # pylint: disable=E1002
        """Set up the main window"""
        super(FoggerAppWindow, self).finish_initializing(builder)

        self.AboutDialog = AboutFoggerDialog
        self.PreferencesDialog = PreferencesFoggerDialog
        self.placeholder = self.builder.get_object('placeholder')
        self.webcontainer = self.builder.get_object('webview_container')
        self.appname = self.builder.get_object('appname')
        self.statusbar = self.builder.get_object('statusbar')
        self.progressbar = self.builder.get_object('progressbar')

        # Code for other iniself.webview = WebKit.WebView()
        self.webview = WebKit.WebView()
        self.websettings = self.webview.get_settings()
        self.setup_websettings()
        self.webview.show()
        self.webview.connect('document-load-finished', self.init_dom)
        self.webview.connect('load-progress-changed', self.load_progress)
        self.webview.connect('load-finished', self.load_finished)
        self.webview.connect('load-started', self.load_started)
        self.webview.connect('download-requested', self.download_requested)
        self.userscripts = [get_media_file('userscripts/fogger.js', '')]
        self.userstyles = []
        self.webcontainer.add(self.webview)
        self.webview.show()

    def setup_websettings(self):
        self.websettings.props.enable_accelerated_compositing = True
        self.websettings.props.enable_dns_prefetching = True
        self.websettings.props.enable_fullscreen = True
        self.websettings.props.enable_html5_database = True
        self.websettings.props.enable_html5_local_storage = True
        self.websettings.enable_site_specific_quirks = True
        self.websettings.enable_spell_checking = True
        self.websettings.enable_web_audio = True
        self.websettings.enable_webgl = True
        self.websettings.enable_page_cache = True

    def do_window_state_event(self, widget, data=None):
        if self.app:
            M = Gdk.WindowState.MAXIMIZED
            self.app.maximized = self.get_window().get_state() & M == M
            self.app.save()

    def on_size_allocate(self, widget, data=None):
        self.app.window_size = self.get_size()
        self.app.save()

    def load_progress(self, widget, progress, data=None):
        self.progressbar.set_fraction(progress)

    def load_finished(self, widget, data=None):
        self.progressbar.set_fraction(0.0)
        self.progressbar.hide()

    def load_started(self, widget, data=None):
        self.progressbar.show()

    def init_dom(self, widget, data=None):
        for script in self.userscripts:
            self.webview.execute_script(open(script).read())
        self.placeholder.hide()
        self.webcontainer.show()
        self.statusbar.show()

    def download_requested(self, widget, download, data=None):
        download.set_destination_uri('file:///home/owais/Desktop/1.svg')
        return True

    def run_app(self, app):
        self.app = app
        self.websettings.user_stylesheet_uri = app.get_stylesheet()
        if op.isfile(self.app.icon):
            self.set_icon_from_file(self.app.icon)
        else:
            self.set_icon_name(self.app.icon)
        self.appname.set_text(app.name)
        self.set_title(app.name or app.url or 'FogApp')
        self.set_role('FogApp:%s' % app.name)
        self.webview.load_uri(self.app.url)
        self.set_default_size(*self.app.window_size)
        if self.app.maximized:
            self.maximize()
        self.show()

# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# This file is in the public domain
### END LICENSE

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
        self.webcontainer = self.builder.get_object('web_view_container')
        self.appname = self.builder.get_object('appname')
        self.statusbar = self.builder.get_object('statusbar')
        self.loadstatus = self.builder.get_object('load_status')

        # Code for other iniself.webview = WebKit.WebView()
        self.webview = WebKit.WebView()
        container = self.builder.get_object('web_view_container')
        container.add(self.webview)
        #self.webview.show()
        self.webview.connect('document-load-finished', self.init_dom)
        self.webview.connect('load-progress-changed', self.load_progress)
        self.webview.connect('download-requested', self.download_requested)
        self.userscripts = [get_media_file('userscripts/fogger.js', '')]
        self.userstyles = []
        self.webview.show()

    def do_window_state_event(self, widget, data=None):
        if self.app:
            M = Gdk.WindowState.MAXIMIZED
            self.app.maximized = self.get_window().get_state() & M == M
            self.app.save()

    def on_size_allocate(self, widget, data=None):
        self.app.window_size = self.get_size()
        self.app.save()

    def load_progress(self, widget, progress, data=None):
        self.loadstatus.set_text('%s' % progress + '%')

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
        self.appname.set_text(app.name)
        self.set_title(app.name or app.url or 'FogApp')
        self.set_role('FogApp:%s' % app.name)
        self.webview.load_uri(self.app.url)
        self.set_default_size(*self.app.window_size)
        if self.app.maximized:
            self.maximize()
        self.show()
        #self.connect('on-size-allocate', self.on_size_allocate)




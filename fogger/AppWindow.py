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

from os import path as op
import urllib
import gettext
from gettext import gettext as _
gettext.textdomain('fogger')

from gi.repository import Gtk, Gdk, GLib, WebKit, Soup # pylint: disable=E0611
import logging
logger = logging.getLogger('fogger')

from fogger_lib import AppWindow
from fogger_lib import DesktopBridge
from fogger_lib.helpers import get_media_file
from fogger.AboutFoggerDialog import AboutFoggerDialog
from fogger.PreferencesFoggerDialog import PreferencesFoggerDialog

DOWNLOAD_DIR = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD)
MAXIMIZED = Gdk.WindowState.MAXIMIZED


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
        self.is_popup = False
        self.extra_windows = []

    def setup_webview(self, webview=None):
        self.webview = webview or WebKit.WebView()
        self.setup_websettings()
        self.webview.show()
        self.webview.connect('document-load-finished', self.init_dom)
        self.webview.connect('notify::progress', self.load_progress)
        self.webview.connect('notify::load-status', self.load_status_changed)
        self.webview.connect('download-requested', self.download_requested)
        self.webview.connect('resource-request-starting', self.on_resource_request_starting)
        self.webview.connect('create-web-view', self.on_create_webview)
        self.userscripts = [get_media_file('userscripts/fogger.js', '')]
        self.userstyles = []
        self.webcontainer.add(self.webview)
        self.webview.show()

    def setup_websettings(self):
        self.websettings = WebKit.WebSettings()
        self.websettings.props.enable_accelerated_compositing = True
        self.websettings.props.enable_dns_prefetching = True
        self.websettings.props.enable_fullscreen = True
        self.websettings.props.enable_offline_web_application_cache = True
        self.websettings.props.javascript_can_open_windows_automatically = True
        self.websettings.props.enable_html5_database = True
        self.websettings.props.enable_html5_local_storage = True
        self.websettings.props.enable_xss_auditor = False
        self.websettings.props.enable_hyperlink_auditing = False
        self.websettings.props.enable_file_access_from_file_uris = True
        self.websettings.props.enable_universal_access_from_file_uris = True
        self.websettings.props.enable_site_specific_quirks = True
        self.websettings.props.enable_spell_checking = True
        self.websettings.props.enable_webaudio = True
        self.websettings.props.enable_webgl = True
        self.websettings.props.enable_page_cache = True
        self.websettings.props.enable_plugins = True
        self.webview.set_settings(self.websettings)

    def is_maximized(self):
        return self.get_state() & MAXIMIZED == MAXIMIZED

    def do_window_state_event(self, widget, data=None):
        if self.app and not self.is_popup:
            self.app.maximized = self.is_maximized()
            self.app.save()

    def on_size_allocate(self, widget, data=None):
        if not self.is_popup and not self.is_maximized():
            self.app.window_size = self.get_size()
            self.app.save()

    def load_progress(self, widget, propname):
        self.progressbar.set_fraction(self.webview.props.progress)

    def load_status_changed(self, widget, propname):
        if self.webview.props.load_status in \
                (WebKit.LoadStatus.FAILED, WebKit.LoadStatus.FINISHED):
            self.progressbar.hide()
        else:
            self.progressbar.show()

    def init_dom(self, widget, data=None):
        for script in self.userscripts:
            self.webview.execute_script(open(script).read())
        self.placeholder.hide()
        self.webcontainer.show()
        self.statusbar.show()

    def on_create_webview(self, widget, frame, data=None):
        webview = WebKit.WebView()
        webview.set_settings(self.webview.get_settings())
        webview.connect('web-view-ready', self.on_web_view_ready)
        return webview

    def on_web_view_ready(self, webview, data=None):
        window = self.__class__()
        app = type('FogApp', tuple(), {
            'icon': self.app.icon,
            'name': self.app.name,
            'url': webview.get_uri(),
            'uuid': self.app.uuid,
            'window_size': self.app.window_size,
            'maximized': False,
            })
        window.run_app(app, webview)
        self.popups.append(window)
        window.set_transient_for(self)

    def on_resource_request_starting(self, widget, frame, resource, request, response, data=None):
        uri = urllib.unquote(request.props.uri)
        if uri.startswith('http://fogger.local/'):
            request.props.uri = 'about:blank'
            method = uri.lstrip('http://fogger.local/')
            parts = method.split('/')
            method = parts[0]
            args = parts[1:]
            getattr(self.bridge, method)(*args)
            return True

    def download_requested(self, widget, download, data=None):
        name = download.get_suggested_filename()
        _name, ext = op.splitext(name)
        path = op.join(DOWNLOAD_DIR, name)
        i = 1
        while op.exists(path):
            path = '%s_%d%s' %(op.join(DOWNLOAD_DIR, _name), i, ext)
            i += 1
        download.set_destination_uri('file://%s' % path)
        return True

    def run_app(self, app, webview=None):
        self.setup_webview(webview)
        self.app = app
        if op.isfile(self.app.icon):
            self.set_icon_from_file(self.app.icon)
        else:
            self.set_icon_name(self.app.icon)
        self.set_title(app.name or app.url or 'FogApp')
        self.set_role('FogApp:%s' % app.name)
        self.bridge = DesktopBridge('%s.desktop' % self.app.uuid, self.app.icon)
        if not webview:
            self.appname.set_text(app.name)
            self.webview.load_uri(self.app.url)
            self.set_default_size(*self.app.window_size)
            if self.app.maximized:
                self.maximize()
        else:
            self.appname.set_text('Loading...')
            self.is_popup = True
            wf = webview.props.window_features
            if wf.props.width and wf.props.height:
                self.resize(wf.props.width, wf.props.height)
            else:
                self.resize(800, 600)
            if wf.props.fullscreen:
                self.fullscreen()
        self.show()

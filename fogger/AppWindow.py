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

import os
import urllib
import logging
import gettext
from gettext import gettext as _
gettext.textdomain('fogger')

from gi.repository import Gdk, GLib, Gtk, WebKit, Soup # pylint: disable=E0611

op = os.path
logger = logging.getLogger('fogger')

from fogger_lib import AppWindow, DesktopBridge, DownloadManager
from fogger_lib.helpers import get_media_file, get_or_create_directory
from fogger.AboutFoggerDialog import AboutFoggerDialog
from fogger.PreferencesFoggerDialog import PreferencesFoggerDialog

MAXIMIZED = Gdk.WindowState.MAXIMIZED


# TODO: Move WebView and DownloadManager to their own classes and tidy up
# FoggerAppWindow class

class FoggerAppWindow(AppWindow):
    __gtype_name__ = "FoggerAppWindow"

    def finish_initializing(self, builder): # pylint: disable=E1002
        """Set up the main window"""
        super(FoggerAppWindow, self).finish_initializing(builder)

        self.AboutDialog = AboutFoggerDialog
        self.PreferencesDialog = PreferencesFoggerDialog

        self.ui_loading = self.builder.get_object('ui_loading')
        self.ui_error = self.builder.get_object('ui_error')
        self.webcontainer = self.builder.get_object('webview_container')
        self.appname = self.builder.get_object('appname')
        self.menubar = self.builder.get_object('menubar')
        self.statusbar = self.builder.get_object('statusbar')
        self.status_text = self.builder.get_object('status_text')
        self.progressbar = self.builder.get_object('progressbar')
        self.error_message = self.builder.get_object('error_message')
        self.menu_app = self.builder.get_object('mnu_app')

        self.is_popup = False
        self.downloads = DownloadManager(self.builder)
        self.extra_windows = []

    def setup_webview(self, webview=None):
        self.webview = webview or WebKit.WebView()
        self.setup_websettings()
        self.setup_webkit_session()
        self.webview_inspector = self.webview.get_inspector()
        self.webview_inspector.connect('inspect-web-view', self.inspect_webview)
        self.inspector_window = Gtk.Window()
        self.webview.show()
        self.webview.connect('document-load-finished', self.init_dom)
        self.webview.connect('notify::progress', self.load_progress)
        #self.webview.connect('load-error', self.on_load_error)
        self.webview.connect('download-requested', self.downloads.requested)
        self.webview.connect('resource-request-starting', self.on_resource_request_starting)
        self.webview.connect('create-web-view', self.on_create_webview)
        self.webview.connect('database-quota-exceeded', self.on_database_quota_exceeded)
        self.userscripts = self.app.scripts
        self.userscripts.append(open(get_media_file('js/fogger.js', '')).read())
        self.userstyles = []
        self.webcontainer.add(self.webview)
        self.webview.show()

    def setup_webkit_session(self):
        session = WebKit.get_default_session()
        cache = get_or_create_directory(op.join(
            GLib.get_user_cache_dir(), 'fogger', self.app.uuid))
        cookie_jar = Soup.CookieJarText.new(op.join(cache, 'WebkitSession'), False)
        session.add_feature(cookie_jar)
        session.props.max_conns_per_host = 8

    def setup_websettings(self):
        self.websettings = WebKit.WebSettings()
        self.websettings.props.html5_local_storage_database_path = \
                                    get_or_create_directory(op.join(
                                            GLib.get_user_cache_dir(),
                                            'fogger/%s/db' % self.app.uuid))
        self.websettings.props.enable_accelerated_compositing = True
        self.websettings.props.enable_dns_prefetching = True
        self.websettings.props.enable_fullscreen = True
        self.websettings.props.enable_offline_web_application_cache = True
        self.websettings.props.javascript_can_open_windows_automatically = True
        self.websettings.props.enable_html5_database = True
        self.websettings.props.enable_html5_local_storage = True
        self.websettings.props.enable_hyperlink_auditing = False
        self.websettings.props.enable_file_access_from_file_uris = True
        self.websettings.props.enable_universal_access_from_file_uris = True
        self.websettings.props.enable_site_specific_quirks = True
        self.websettings.props.enable_spell_checking = True
        self.websettings.props.enable_webaudio = True
        self.websettings.props.enable_webgl = True
        self.websettings.props.enable_page_cache = True
        self.websettings.props.enable_plugins = True
        self.websettings.props.enable_developer_extras = True
        self.webview.set_settings(self.websettings)

    def inspect_webview(self, inspector, widget, data=None):
        inspector_view = WebKit.WebView()
        self.inspector_window.add(inspector_view)
        self.inspector_window.resize(800, 400)
        self.inspector_window.show_all()
        return inspector_view

    def on_download_clicked(self, *args, **kwargs):
        return self.downloads.on_download_clicked(*args, **kwargs)

    def show_download_window(self, widget, data=None):
        self.downloads.show()

    def is_maximized(self):
        if self.props.window:
            return self.props.window.get_state() & MAXIMIZED == MAXIMIZED
        else:
            return False

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
                (WebKit.LoadStatus.FINISHED,):
            #self.progressbar.hide()
            self.statusbar.hide()
        else:
            #self.progressbar.show()
            self.statusbar.show()

    def on_load_error(self, webview, frame, uri, error, data=None):
        self.error_message.set_markup('<tt>%s</tt>' % error.message)
        self.webcontainer.hide()
        self.webview.hide()
        self.statusbar.show()
        self.progressbar.hide()
        self.ui_error.show()

    def on_database_quota_exceeded(self, webview, frame, database, data=None):
        so = database.get_security_origin()
        quota = so.get_web_database_quota()
        so.set_web_database_quota(quota + 5242880) # Increase by 5mb

    def init_dom(self, webview, frame, data=None):
        for script in self.userscripts:
            self.webview.execute_script(script)
        self.ui_loading.hide()
        self.webview.connect('notify::load-status', self.load_status_changed)
        #if not frame.props.load_status == WebKit.LoadStatus.FAILED:
        #    self.webcontainer.show()
        self.webcontainer.show()

    def on_create_webview(self, widget, frame, data=None):
        webview = WebKit.WebView()
        webview.set_settings(self.webview.get_settings())
        webview.connect('web-view-ready', self.on_web_view_ready)
        return webview

    def on_zoom_in(self, widget, data=None):
        self.webview.zoom_in()

    def on_zoom_out(self, widget, data=None):
        self.webview.zoom_out()

    def on_zoom_reset(self, widget, data=None):
        self.webview.props.zoom_level = 1.0

    def on_reload(self, widget, data=None):
        self.webview.reload()

    def on_retry(self, widget, data=None):
        self.webview.reload()

    def on_go_back(self, widget, data=None):
        self.webview.go_back()

    def on_go_forward(self, widget, data=None):
        self.webview.go_forward()

    def on_remove_fog_app(self, widget, data=None):
        # TODO: COnfirmation dialog
        self.app.remove()
        self.destroy()

    def on_show_scripts(self, widget, data=None):
        os.system('xdg-open %s' % self.app.scripts_path)

    def on_web_view_ready(self, webview, data=None):
        window = self.__class__()
        app = type('FogApp', tuple(),
            {'icon': self.app.icon,
             'name': self.app.name,
             'url': webview.get_uri(),
             'uuid': self.app.uuid,
             'window_size': self.app.window_size,
             'maximized': False})
        window.run_app(app, webview)
        self.popups.append(window)
        window.set_transient_for(self)

    def on_resource_request_starting(self, widget, frame, resource, request, response, data=None):
        uri = urllib.unquote(request.props.uri)
        if uri.startswith('http://fogger.local/'):
            request.props.uri = 'about:blank'
            method = uri.replace('http://fogger.local/', '')
            action = method.split('/')
            method = action[0]
            args = action[1:]
            getattr(self.bridge, method)(*args)
            return True

    def run_app(self, app, webview=None):
        self.app = app
        self.menu_app.set_label('_%s' % self.app.name)
        self.setup_webview(webview)
        if op.isfile(self.app.icon):
            self.set_icon_from_file(self.app.icon)
        else:
            self.set_icon_name(self.app.icon)
        self.set_title(app.name or app.url or 'FogApp')
        self.set_role('FogApp:%s' % app.name)
        self.bridge = DesktopBridge(self, '%s.desktop' % self.app.uuid, self.app.icon)
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

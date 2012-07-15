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
import re
import requests
import urlparse
import tempfile
import threading
from BeautifulSoup import BeautifulSoup, SoupStrainer
import gettext
from gettext import gettext as _
gettext.textdomain('fogger')

from gi.repository import GLib, Gtk, Gdk, GdkPixbuf, GObject, Gio # pylint: disable=E0611
import logging
logger = logging.getLogger('fogger')
from fogger_lib import Window, IconChooserDialog, ConfirmDialog
from fogger_lib import FogAppManager
from fogger_lib.exceptions import BaseFogAppException
from fogger_lib.helpers import get_network_proxies
from fogger_lib.consts import DEFAULT_APP_ICON
from fogger.AboutFoggerDialog import AboutFoggerDialog


ICON_SIZE = Gtk.icon_size_register('FoggerIconSize', 80, 80)

GLib.threads_init()

# See fogger_lib.Window.py for more details about how this class works
class FoggerWindow(Window):
    __gtype_name__ = "FoggerWindow"

    def finish_initializing(self, builder): # pylint: disable=E1002
        """Set up the main window"""
        super(FoggerWindow, self).finish_initializing(builder)

        self.AboutDialog = AboutFoggerDialog

        self.url = self.builder.get_object('url_entry')
        self.name = self.builder.get_object('name_entry')
        self.image = self.builder.get_object('image')
        self.image_eb = self.builder.get_object('image_eb')
        self.create_button = self.builder.get_object('create_button')
        self.spinner = self.builder.get_object('spinner')
        self.error_message = self.builder.get_object('error')

        self.icon = DEFAULT_APP_ICON
        self.themed_icon = None
        self.icon_selected = False
        self.icon_theme = Gtk.IconTheme.get_default()

        self.setup_drop_targets()

    def validate_form(self, widget, data=None):
        url = self.url.get_text()
        name = self.name.get_text()
        sensitive = url and name
        self.create_button.set_sensitive(sensitive)

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
            self.setup_icon(path)

    def on_cancel(self, widget, data=None):
        self.destroy()

    def on_url_changed(self, widget, data=None):
        pass

    def on_icon_clicked(self, widget, data=None):
        icon_chooser = IconChooserDialog(self)
        response = icon_chooser.run()
        if response == Gtk.ResponseType.OK:
            path = icon_chooser.get_filename()
            self.setup_icon(path)
        icon_chooser.destroy()

    def on_name_changed(self, widget, data=None):
        if self.icon_selected:
            return
        name = self.name.get_text().lower().strip().replace(' ', '-')
        words = name.split('-')
        subnames = []
        for i, word in enumerate(words):
            x = '-'.join(words[:(i + 1) * -1])
            if x:
                subnames.append(x)
        search_strings = [name] + subnames
        icon = self.icon_theme.choose_icon(search_strings, 0, Gtk.IconLookupFlags.GENERIC_FALLBACK)
        if icon:
            filename = icon.get_filename()
            path, ext = op.splitext(filename)
            _, themed_icon = op.split(path)
            self.setup_icon(filename, themed_icon, False)
        else:
            self.setup_icon(DEFAULT_APP_ICON, None, False)

    def setup_icon(self, path, name=None, selected=True):
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(path)
        self.image.props.pixbuf = pixbuf.scale_simple(80, 80, GdkPixbuf.InterpType.BILINEAR)
        self.icon = path
        self.themed_icon = name
        self.icon_selected = selected

    def on_create(self, widget, data=None):
        name = self.name.get_text()
        manager = FogAppManager()
        existing = manager.get_by_name(name)
        if existing:
            confirm = ConfirmDialog('Fogger', _('There\'s an app for that!'),
                        _('A fog app already exists by that name. '\
                          'Would you like to replace it with a new one?'),
                        existing.icon, self, _('Replace'))
            response = confirm.run()
            confirm.destroy()
            if response != Gtk.ResponseType.YES:
                self.name.grab_focus()
                return
        self.set_loading_url(True)
        self.error_message.hide()
        thread = threading.Thread(target=self.verify_url)
        thread.daemon = True
        thread.start()

    def create_app(self, url, name):
        manager = FogAppManager()
        try:
            app = manager.create(name, url, self.icon, self.themed_icon)
        except BaseFogAppException:
            logger.error("Error creating App %s" % url)
        else:
            app = Gio.DesktopAppInfo.new_from_filename(app.desktop_file)
            app.launch([], Gio.AppLaunchContext())
            self.destroy()

    def set_loading_url(self, loading):
        if loading:
            self.spinner.show()
            self.create_button.hide()
            self.url.set_sensitive(False)
            self.name.set_sensitive(False)
        else:
            self.spinner.hide()
            self.create_button.show()
            self.url.set_sensitive(True)
            self.name.set_sensitive(True)

    def set_error_message(self, message):
        self.error_message.set_markup('<tt><small>%s</small></tt>' % message)
        self.error_message.show()

    def verify_url(self):
        logger.debug('Fetching url')
        url = self.url.get_text()
        name = self.name.get_text()
        verified = False
        proxies = get_network_proxies()
        try:
            if url.startswith('file://'):
                GObject.idle_add(self.set_loading_url, False)
                GObject.idle_add(self.create_app, url, name)
                return
            elif not url.startswith(('http://', 'https://',)):
                url = 'http://%s' % url

            try:
                logger.debug('starting')
                response = requests.get(url, proxies=proxies)
                verified = True
                logger.debug('finishing')
            except requests.RequestException:
                logger.debug('Error downloading url %s' % url)
                GObject.idle_add(self.set_loading_url, False)
                GObject.idle_add(self.set_error_message,
                        _('The URL %s could not be reached.\nPlease double check'\
                        ' the URL you provided and try again.' % url))
                return

            SkipIcon = type('SkipIcon', (Exception,), {})
            if self.icon != DEFAULT_APP_ICON:
                raise SkipIcon()

            # Try to find the apple-touch-icon
            logger.debug('parsing')
            soup = BeautifulSoup(response.content, parseOnlyThese=SoupStrainer('link'))
            icons = soup.findAll('link', rel=re.compile('^apple-touch-icon'))
            logger.debug('finished parsing')
            soup = BeautifulSoup(response.content)
            if not icons:
                logger.debug('No apple touch icon found')
                raise SkipIcon()
            icon = icons[0]
            href = icon.attrMap.get('href', None)
            if not href:
                logger.debug('Bad apple touch icon')
                raise SkipIcon()
            icon_url = None
            if href.startswith('/'):
                parsed = urlparse.urlparse(url)
                icon_url = urlparse.urljoin(
                        '%s://%s' % (parsed.scheme, parsed.netloc,),  href)
            else:
                parsed = urlparse.urlparse(href)
                if parsed.scheme:
                    icon_url = href
                else:
                    icon_url = urlparse.urljoin(url, href)

            ext = op.splitext(icon_url)[-1]
            tmpf = tempfile.mktemp(ext)
            logger.debug('temp file: %s' % tmpf)

            headers = {'User-Agent': 'Mozilla/5.0 (iPad; U; CPU OS 3_2 like'\
                ' Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko)'\
                ' Version/4.0.4 Mobile/7B334b Safari/531.21.10'}
            try:
                icon_bytes = requests.get(icon_url, headers=headers,
                                          proxies=proxies).content
            except requests.RequestException:
                logger.debug('Error dowloading apple touch icon')
            else:
                handle = open(tmpf, 'w')
                handle.write(icon_bytes)
                handle.close()
                self.setup_icon(tmpf)
        except Exception, e:
            logger.debug("Error", e)
        finally:
            GObject.idle_add(self.set_loading_url, False)
            if verified:
                GObject.idle_add(self.create_app, url, name)

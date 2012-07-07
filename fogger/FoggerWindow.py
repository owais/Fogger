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
import re
#import urllib2
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

        self.icon = 'foggerapp'
        self.icon_selected = False
        self.setup_drop_targets()
        self.icon_theme = Gtk.IconTheme.get_default()

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

    def setup_icon(self, path):
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(path)
        self.image.props.pixbuf = pixbuf.scale_simple(80, 80, GdkPixbuf.InterpType.BILINEAR)
        self.icon = path
        self.icon_selected = True

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
        name = self.name.get_text().lower().replace(' ', '-')
        gicon = None
        if self.icon_theme.has_icon(name):
            gicon = Gio.Icon.new_for_string(name)
            self.icon= name
        else:
            for subname in name.split('-'):
                if self.icon_theme.has_icon(subname):
                    gicon = Gio.Icon.new_for_string(subname)
                    self.icon = subname
                    break
        if not gicon:
            gicon = Gio.Icon.new_for_string('foggerapp')
            self.icon = 'foggerapp'
        self.image.set_from_gicon(gicon, ICON_SIZE)

    def create_app(self, url):
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
                return
        try:
            app = manager.create(name, url, self.icon)
        except BaseFogAppException:
            logger.error("Error creating App %s" % url)
        else:
            app = Gio.DesktopAppInfo.new_from_filename(app.desktop_file)
            app.launch([], Gio.AppLaunchContext())
            self.destroy()

    def on_create(self, widget, data=None):
        self.set_loading_url(True)
        self.error_message.hide()
        thread = threading.Thread(target=self.verify_url)
        thread.daemon = True
        thread.start()

    def set_loading_url(self, loading):
        if loading:
            self.spinner.show()
            #self.create_button.set_sensitive(False)
            self.create_button.hide()
            self.url.set_sensitive(False)
        else:
            self.spinner.hide()
            self.create_button.show()
            #self.create_button.set_sensitive(True)
            self.url.set_sensitive(True)

    def set_error_message(self, message):
        self.error_message.set_markup('<tt><small>%s</small></tt>' % message)
        self.error_message.show()

    def verify_url(self):
        logger.debug('Fetching url')
        url = self.url.get_text()
        verified = False
        try:
            if url.startswith('file://'):
                GObject.idle_add(self.set_loading_url, False)
                GObject.idle_add(self.create_app, url)
                return
            elif not url.startswith(('http://', 'https://',)):
                url = 'http://%s' % url

            try:
                logger.debug('starting')
                #response = urllib2.urlopen(url)
                response = requests.get(url)
                verified = True
                logger.debug('finishing')
            #except urllib2.URLError:
            except requests.RequestException:
                logger.debug('Error downloading url %s' % url)
                GObject.idle_add(self.set_loading_url, False)
                GObject.idle_add(self.set_error_message,
                        _('The URL %s could not be reached.\nPlease double check'\
                        ' the URL you provided and try again.' % url))
                return

            SkipIcon = type('SkipIcon', (BaseException,), {})
            if self.icon != "foggerapp":
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
                logger.debug(parsed.scheme, parsed.netloc)
                icon_url = urlparse.urljoin(
                        '%s://%s' % (parsed.scheme, parsed.netloc,),  href)
                logger.debug(icon_url, '<<< icon url')
            else:
                parsed = urlparse.urlparse(href)
                if parsed.scheme:
                    icon_url = href
                else:
                    icon_url = urlparse.urljoin(url, href)

            ext = os.path.splitext(icon_url)[-1]
            tmpf = tempfile.mktemp(ext)
            logger.debug('temp file: %s' % tmpf)

            headers = {'User-Agent': 'Mozilla/5.0 (iPad; U; CPU OS 3_2 like'\
                ' Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko)'\
                ' Version/4.0.4 Mobile/7B334b Safari/531.21.10'}
            #req = urllib2.Request(icon_url, None, headers)
            try:
                #icon_bytes = urllib2.urlopen(req).read()
                icon_bytes = requests.get(icon_url, headers=headers).content
            #except urllib2.URLError:
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
                GObject.idle_add(self.create_app, url)

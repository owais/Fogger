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
import optparse

import gettext
from gettext import gettext as _
gettext.textdomain('fogger')

from gi.repository import Gtk, Gio # pylint: disable=E0611

from fogger import FoggerWindow
from fogger_lib import FogAppManager, set_up_logging, get_version


def parse_options():
    """Support for command line options"""
    parser = optparse.OptionParser(version="%%prog %s" % get_version())
    parser.add_option(
        "-v", "--verbose", action="count", dest="verbose",
        help=_("Show debug messages (-vv debugs fogger_lib also)"))
    parser.add_option(
        "-l", "--list", action="store_true", dest="list",
        help=_("List all fogapps"))
    parser.add_option(
        "-r", "--remove", action="store", dest="remove",
        help=_("Remove a fogapp"))
    parser.add_option(
        "-R", "--remove-all", action="store_true", dest="remove_all",
        help=_("Remove all fogapp"))
    parser.add_option(
        "-c", "--clean", action="store_true", dest="clean",
        help=_("Remove all fogapps"))
    (options, args) = parser.parse_args()
    set_up_logging(options)
    return (options, args)


def main():
    options, args = parse_options()

    option_selected = False
    if options.list:
        option_selected = True
        manager = FogAppManager()
        apps = manager.get_all()
        for app in apps:
            print '\033[1m%s\033[0m' % app.name, '\t', app.uuid, '\n'

    if options.remove:
        option_selected = True
        manager = FogAppManager()
        app = manager.get(options.remove)
        if app:
            app.remove()
            print 'Removed app %s (%s)' % (app.name, app.uuid)

    if options.remove_all:
        option_selected = True
        manager = FogAppManager()
        for app in manager.get_all():
            app.remove()
            print 'Removed app %s (%s)' % (app.name, app.uuid)

    if options.clean:
        import os
        option_selected = True
        manager = FogAppManager()
        apps = [app.desktop_file for app in  manager.get_all()]
        all_apps = [app for app in Gio.AppInfo.get_all() if 'fogapp' in app.get_keywords()]
        for app in all_apps:
            if not app.props.filename in apps:
                try:
                    os.remove(app.props.filename)
                except:
                    print 'Could not delete file %s' % app.props.filename
                else:
                    print 'Cleaned stale file: %s' % app.props.filename

    if option_selected:
        return

    # Run the application.
    if len(args) > 0:
        def activate_application(application):
            try:
                window.present()
            except NameError:
                pass

        gapp_name = 'net.launchpad.fogger%s' % args[0]
        g_app = Gtk.Application.new(gapp_name, Gio.ApplicationFlags.FLAGS_NONE)
        g_app.connect('activate', activate_application)
        g_app.run(args)
        if g_app.get_is_remote():
            return
        manager = FogAppManager()
        app = manager.get(args[0]) or manager.get_by_name(args[0])
        if app:
            app.run()
            Gtk.main()
    else:
        window = FoggerWindow.FoggerWindow()
        window.show()
        Gtk.main()

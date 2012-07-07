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
        "-c", "--clean", action="store_true", dest="clean",
        help=_("Remove all fogapps"))
    (options, args) = parser.parse_args()
    set_up_logging(options)
    return (options, args)


def main():
    options, args = parse_options()

    if options.list:
        manager = FogAppManager()
        apps = manager.get_all()
        for app in apps:
            print '\033[1m%s\033[0m' % app.name, '\t', app.uuid, '\n'
        return

    if options.remove:
        manager = FogAppManager()
        app = manager.get(options.remove)
        if app:
            app.remove()
            print 'Removed app %s (%s)' % (app.name, app.uuid)
        return

    if options.clean:
        manager = FogAppManager()
        for app in manager.get_all():
            app.remove()
            print 'Removed app %s (%s)' % (app.name, app.uuid)
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
        app = manager.get(args[0])
        if app:
            app.run()
            window = app.window
        else:
            return
    else:
        window = FoggerWindow.FoggerWindow()
        window.show()

    Gtk.main()

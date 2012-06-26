# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# This file is in the public domain
### END LICENSE
import optparse

import gettext
from gettext import gettext as _
gettext.textdomain('fogger')

from gi.repository import Gtk, Gio # pylint: disable=E0611

from fogger import FoggerWindow

from fogger_lib import app_manager, set_up_logging, get_version


def parse_options():
    """Support for command line options"""
    parser = optparse.OptionParser(version="%%prog %s" % get_version())
    parser.add_option(
        "-v", "--verbose", action="count", dest="verbose",
        help=_("Show debug messages (-vv debugs fogger_lib also)"))
    (options, args) = parser.parse_args()
    set_up_logging(options)
    return (options, args)


def main():
    options, args = parse_options()
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

        app = app_manager.get(args[0])
        if app:
            app.run()
            window = app.window
        else:
            return
    else:
        window = FoggerWindow.FoggerWindow()
        window.show()

    Gtk.main()

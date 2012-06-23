# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# This file is in the public domain
### END LICENSE
import os
import optparse

import gettext
from gettext import gettext as _
gettext.textdomain('fogger')

from gi.repository import Gtk, WebKit, Soup, GLib # pylint: disable=E0611

from fogger import FoggerWindow

from fogger_lib import app_manager, set_up_logging, get_version
from fogger_lib.helpers import get_or_create_directory

USERNAME = GLib.get_user_name()
CACHE = get_or_create_directory(os.path.join(GLib.get_user_cache_dir(), 'fogger'))
COOKIE_JAR = os.path.join(CACHE, 'cookies.txt')


def setup_webkit_session():
    session = WebKit.get_default_session()
    cookie_jar = Soup.CookieJarText.new(COOKIE_JAR, False)
    session.add_feature(cookie_jar)


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
    setup_webkit_session()
    options, args = parse_options()

    # Run the application.
    if len(args) > 0:
        print args
        app = app_manager.get(args[0])
        if app:
            app.run()
        else:
            return
    else:
        window = FoggerWindow.FoggerWindow()
        window.show()

    Gtk.main()

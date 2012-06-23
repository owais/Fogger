# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# This file is in the public domain
### END LICENSE

import gettext
from gettext import gettext as _
gettext.textdomain('fogger')

from gi.repository import Gtk # pylint: disable=E0611
import logging
logger = logging.getLogger('fogger')

from fogger_lib import Window
from fogger.AboutFoggerDialog import AboutFoggerDialog
from fogger.PreferencesFoggerDialog import PreferencesFoggerDialog

# See fogger_lib.Window.py for more details about how this class works
class FoggerWindow(Window):
    __gtype_name__ = "FoggerWindow"
    
    def finish_initializing(self, builder): # pylint: disable=E1002
        """Set up the main window"""
        super(FoggerWindow, self).finish_initializing(builder)

        self.AboutDialog = AboutFoggerDialog
        self.PreferencesDialog = PreferencesFoggerDialog

        # Code for other initialization actions should be added here.


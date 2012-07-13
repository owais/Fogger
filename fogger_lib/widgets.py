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
from gi.repository import Gtk, GObject

class DownloadCancelButton(Gtk.CellRendererPixbuf):
    __gsignals__ = {
        'cancel-download': (GObject.SIGNAL_RUN_FIRST, None, tuple())
    }

    def __init__(self):
        Gtk.CellRendererPixbuf.__init__(self)
        self.set_property('mode', Gtk.CellRendererMode.ACTIVATABLE)
        self.props.stock_id = Gtk.STOCK_CANCEL
        self.props.width = 100

    def do_activate(self, *args, **kwargs):
        self.emit('cancel-download')





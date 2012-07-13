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
import gettext
from gettext import gettext as _
gettext.textdomain('fogger')

from gi.repository import Gtk, GdkPixbuf

ICON_SIZE = Gtk.icon_size_register('FoggerDialogIconSize', 80, 80)

class ConfirmDialog(Gtk.MessageDialog):
    def __init__(self, appname, title, message, icon=None, parent=None, ok='gtk-ok', cancel='gtk-cancel'):
        Gtk.MessageDialog.__init__(self, parent,
                Gtk.DialogFlags.MODAL & Gtk.DialogFlags.DESTROY_WITH_PARENT,
                Gtk.MessageType.QUESTION,
                Gtk.ButtonsType.YES_NO,
                title)
        if icon:
            image = self.get_content_area().get_children()[0].get_children()[0]
            if icon.startswith('/'):
                pixbuf = GdkPixbuf.Pixbuf.new_from_file(icon)
                image.props.pixbuf = pixbuf.scale_simple(80, 80, GdkPixbuf.InterpType.BILINEAR)
            else:
                image.set_from_icon_name(icon, ICON_SIZE)
        self.format_secondary_text(message)
        buttons = self.action_area.get_children()
        for b in buttons:
            if b.get_label() == 'gtk-yes':
                b.set_label(ok)
                b.set_image(Gtk.Image.new_from_stock(Gtk.STOCK_REMOVE, Gtk.IconSize.BUTTON))
            elif b.get_label() == 'gtk-no':
                b.set_label(cancel)
                b.set_image(Gtk.Image.new_from_stock(Gtk.STOCK_CANCEL, Gtk.IconSize.BUTTON))


class IconChooserDialog(Gtk.FileChooserDialog):
    def __init__(self, parent):
        Gtk.FileChooserDialog.__init__(self, _("Please choose an icon"), parent,
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OK, Gtk.ResponseType.OK))
        self.set_default_size(800, 400)
        fltr = Gtk.FileFilter()
        fltr.set_name('Images')
        for mime in ['image/png', 'image/svg', 'image/jpeg', 'image/xpm']:
            fltr.add_mime_type(mime)
        self.add_filter(fltr)


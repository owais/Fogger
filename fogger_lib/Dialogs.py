import gettext
from gettext import gettext as _
gettext.textdomain('fogger')

from gi.repository import Gtk


class ConfirmDialog(Gtk.MessageDialog):
    def __init__(self, appname, title, message, parent=None, ok='gtk-ok', cancel='gtk-cancel'):
        Gtk.MessageDialog.__init__(self, parent,
                Gtk.DialogFlags.MODAL & Gtk.DialogFlags.DESTROY_WITH_PARENT,
                Gtk.MessageType.QUESTION,
                Gtk.ButtonsType.YES_NO,
                title)
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


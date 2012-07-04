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





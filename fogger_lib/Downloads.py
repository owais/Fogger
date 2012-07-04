from os import path as op

from gi.repository import GLib, GObject

from fogger_lib.widgets import DownloadCancelButton


DOWNLOAD_DIR = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD)


class DownloadManager:
    def __init__(self, builder):
        self.builder = builder
        self.window = self.builder.get_object('DownloadWindow')
        self.store = self.builder.get_object('downloadstore')
        download_cancel_column = self.builder.get_object('download_cancel_column')
        download_cancel_button = DownloadCancelButton()
        download_cancel_column.pack_start(download_cancel_button, True)
        self.download_view = self.builder.get_object('download_view')
        self.window.connect('delete-event', self.on_delete)

    def show(self):
        self.window.show()

    def on_delete(self, widget, data=None):
        self.window.hide()
        return True

    def requested(self, widget, download, data=None):
        # TODO: Confirmation, progress, notifications
        name = download.get_suggested_filename()
        _name, ext = op.splitext(name)
        path = op.join(DOWNLOAD_DIR, name)
        i = 1
        while op.exists(path):
            path = '%s_%d%s' %(op.join(DOWNLOAD_DIR, _name), i, ext)
            i += 1
        download.set_destination_uri('file://%s' % path)
        self.add_download(download)
        return True

    def add_download(self, download):
        name = op.split(download.props.destination_uri)[-1]
        self.store.prepend([name, 0.0, None, download])
        download.connect('notify::progress', self.on_download_progress)

    def on_download_clicked(self, tree, event, data=None):
        x, y = event.get_coords()
        path, column, _, _ = tree.get_path_at_pos(x, y)
        if column.get_name() == 'download_cancel_column':
            _iter = self.store.get_iter(path)
            download = self.store.get_value(_iter, 3)
            download.cancel()
            self.store.remove(_iter)

    def on_download_progress(self, download, progress, data=None):
        #print download, progress
        #print dir(progress)
        def update_progress(download, progress):
            for d in self.store:
                if d[3] == download:
                    d[1] = download.props.progress * 100
        GObject.idle_add(update_progress, download, progress)

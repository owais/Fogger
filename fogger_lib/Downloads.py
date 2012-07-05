import os

import gettext
from gettext import gettext as _
gettext.textdomain('fogger')

from gi.repository import GLib, WebKit, Notify


#from fogger_lib.widgets import DownloadCancelButton

op = os.path
DOWNLOAD_DIR = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD)
FINISHED = WebKit.DownloadStatus.FINISHED


class DownloadManager:
    def __init__(self, root_window):
        self.R = root_window
        self.window = self.R.builder.get_object('DownloadWindow')
        self.store = self.R.builder.get_object('downloadstore')
        self.download_view = self.R.builder.get_object('download_view')
        self.download_view.get_column(0).props.expand = True

        self.window.connect('delete-event', self.on_delete)

    def show(self):
        self.window.show()

    def on_delete(self, widget, data=None):
        self.window.hide()
        return True

    def open_folder(self, widget, data=None):
        os.system('xdg-open %s' % DOWNLOAD_DIR)

    def cancel_all(self):
        for row in self.store:
            download = row[3]
            if download.props.status != FINISHED:
                download.cancel()

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
        treeiter = self.store.prepend([name, 0.0, 'Unknown Size', download])
        download.connect('notify::progress', self.on_download_progress)
        download.connect('notify::status', self.on_status_changed)
        download.connect('error', self.on_download_error, treeiter)
        if not self.window.props.visible:
            self.window.present()

    def on_download_clicked(self, tree, event, data=None):
        if len(self.store) < 1:
            return
        x, y = event.get_coords()
        ret = tree.get_path_at_pos(x, y)
        if ret:
            path, column, _, _ = tree.get_path_at_pos(x, y)
        else:
            return
        if column.get_name() == 'download_cancel_column':
            _iter = self.store.get_iter(path)
            download = self.store.get_value(_iter, 3)
            download.cancel()
            self.store.remove(_iter)
        elif event.get_click_count()[1] == 2:
            _iter = self.store.get_iter(path)
            download = self.store.get_value(_iter, 3)
            if download.props.status == WebKit.DownloadStatus.FINISHED:
                os.system('xdg-open %s' % download.props.destination_uri)

    def on_download_progress(self, download, progress, data=None):
        for d in self.store:
            if d[3] == download:
                d[1] = download.props.progress * 100
                d[2] = '%s MB' % str(download.props.total_size / (1024 * 1024))

    def on_download_error(self, download, code, detail, reason, treeiter, data=None):
        path = download.props.destination_uri.replace('file://', '')
        if download.props.status != FINISHED and os.path.exists(path):
            os.remove(path)
        if detail != WebKit.DownloadError.CANCELLED_BY_USER:
            self.store[treeiter][2] = _('Error')

    def on_status_changed(self, download, status, data=None):
        if download.props.status == FINISHED:
            name = op.split(download.props.destination_uri)[-1]
            Notify.Notification.new(name, _('Download Complete'), self.R.app.icon).show()

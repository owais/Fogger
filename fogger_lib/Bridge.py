from gi.repository import Unity, Notify

Notify.init('fogger')

class DesktopBridge:
    icon_name = None
    desktop_file = None

    def __init__(self, desktop_file, icon_name=None):
        self.desktop_file = desktop_file
        self.icon_name = icon_name
        self.launcher_entry = Unity.LauncherEntry.get_for_desktop_file(self.desktop_file)

    def notify(self, title, body):
        Notify.Notification.new(title, body, self.icon_name).show()

    def set_progress(self, progress):
        self.launcher_entry.props.progress = float(progress)

    def set_progress_visible(self):
        self.launcher_entry.props.progress_visible = True

    def set_progress_invisible(self):
        self.launcher_entry.props.progress_visible = False

    def set_count(self, count):
        self.launcher_entry.props.count = int(count)

    def set_count_visible(self):
        self.launcher_entry.props.count_visible = True

    def set_count_invisible(self):
        self.launcher_entry.props.count_visible = False

    def set_urgent(self):
        self.launcher_entry.props.urgent = True

    def unset_urgent(self):
        self.launcher_entry.props.urgent = False

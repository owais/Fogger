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
from gi.repository import Gtk, Unity, Notify, Dbusmenu, TelepathyGLib

Notify.init('fogger')


TELEPATHY_PRESENCE_MAP = {
    TelepathyGLib.ConnectionPresenceType.AVAILABLE: 'available',
    TelepathyGLib.ConnectionPresenceType.AWAY: 'away',
    TelepathyGLib.ConnectionPresenceType.EXTENDED_AWAY: 'away',
    TelepathyGLib.ConnectionPresenceType.BUSY: 'busy',
    TelepathyGLib.ConnectionPresenceType.OFFLINE: 'offline',
}


class DesktopBridge:
    icon_name = None
    desktop_file = None
    actions = {}
    launcher_actions = {}

    def __init__(self, root, desktop_file, icon_name=None):
        self.W = root
        self.desktop_file = desktop_file
        self.icon_name = icon_name
        self.launcher_entry = Unity.LauncherEntry.get_for_desktop_file(self.desktop_file)
        self.quicklist = Dbusmenu.Menuitem.new()
        self.launcher_entry.set_property("quicklist", self.quicklist)
        self.indicator = None
        self._rename_methods = {
            Dbusmenu.Menuitem: self._rename_dbus_menu_item,
            Gtk.MenuItem: self._rename_gtk_menu_item,
        }
        self.telepathy_account_manager = TelepathyGLib.AccountManager.new(
                                             TelepathyGLib.DBusDaemon.dup())
        self.telepathy_account_manager.connect(
            'most-available-presence-changed', self.notify_presence_change)
        self.W.connect('notify::is-active', self.notify_window_state)

    def _js(self, W, jscode):
        if W:
            windows = [W]
            W.webview.execute_script(jscode)
        else:
            windows = self.W.popups
        for win in windows:
            win.webview.execute_script(jscode)

    def _dispatch_dom_event(self, W, event, params):
        js = 'var e = document.createEvent("Event"); e.initEvent("%s"); var params={};' % event
        for k,v in params.items():
            js = js + 'params.%s = "%s";' % (k, v,)
        js = js + 'e.foggerData = params; document.dispatchEvent(e);'
        self._js(W, js)

    def _rename_gtk_menu_item(self, item, name):
        item.props.label = name

    def _rename_dbus_menu_item(self, item, name):
        item.property_set(Dbusmenu.MENUITEM_PROP_LABEL, name)

    def rename_item(self, W, data):
        widget_id = data['id'][0]
        item = self.widgets.get(widget_id)
        rename = self._rename_methods.get(item.__class__)
        if rename:
            rename(item, data['name'][0])

    def notify_window_state(self, window, active):
        self._dispatch_dom_event(self.W, 'foggerWindowStateChange', {
                'active': self.W.props.is_active})

    def notify_presence_change(self, manager, presence, status, message):
        self._dispatch_dom_event(None, 'foggerPresenceChange',
                {'presence': TELEPATHY_PRESENCE_MAP.get(presence, 'offline')})

    def get_presence(self, W, data):
        presence = self.telepathy_account_manager.get_most_available_presence()
        print W

    def notify(self, W, data):
        Notify.Notification.new(data.get('summary', [''])[0], data.get('body', [''])[0], self.icon_name).show()

    def set_progress(self, W, data):
        self.launcher_entry.props.progress = float(data['progress'][0])
        self.launcher_entry.props.progress_visible = True

    def clear_progress(self, W, data):
        self.launcher_entry.props.progress_visible = False

    def set_count(self, W, data):
        self.launcher_entry.props.count = int(data['count'][0])
        self.launcher_entry.props.count_visible = True

    def clear_count(self, W, data):
        self.launcher_entry.props.count_visible = False

    def set_urgent(self, W, data):
        self.launcher_entry.props.urgent = True

    def clear_urgent(self, W, data):
        self.launcher_entry.props.urgent = False

    def add_launcher_action(self, W, data):
        name = data['name'][0]
        if name in self.launcher_actions:
            return
        item = self.launcher_actions[name] = Dbusmenu.Menuitem.new()
        item.property_set(Dbusmenu.MENUITEM_PROP_LABEL, name)
        item.property_set_bool(Dbusmenu.MENUITEM_PROP_VISIBLE, True)
        item.connect('item-activated', lambda *a, **kw:
                self._dispatch_dom_event(None, 'foggerQLCallbackEvent',
                    {'name': name}))
        self.quicklist.child_append(item)

    def remove_launcher_action(self, W, data):
        name = data['name'][0]
        action = self.launcher_actions.get(name)
        if action:
            self.quicklist.child_delete(action)
            del self.launcher_actions[name]

    def remove_launcher_actions(self, W, data):
        for action in self.launcher_actions.values():
            self.quicklist.child_delete(action)
        self.launcher_actions = {}

    def add_action(self, W, data):
        action_path = data['name'][0]
        if action_path in self.actions:
            return
        action_items = []
        action_parts = [X for X in action_path.split('/') if X]
        parent = self.W.menubar
        length = len(action_parts)
        for i, action in enumerate(action_parts, 1):
            if i == length:
                prepend = False
                if i == 1:
                    parent = self.W.menubar.get_children()[0].get_submenu()
                    prepend = True
                if [X for X in parent.get_children() if X.props.label == action]:
                    return
                item = Gtk.MenuItem(action)
                item.props.use_underline = True
                if prepend:
                    parent.prepend(item)
                else:
                    parent.append(item)
                item.connect('activate', lambda *a, **kw:
                        self._dispatch_dom_event(W, 'foggerActionCallbackEvent',
                            {'name': action_path}))
                item.show()
                action_items.append(item)
            else:
                children = [X.props.label for X in parent.get_children()]
                if action in children:
                    parent = [X for X in parent.get_children() if X.props.label == action][0].get_submenu()
                    action_items.append(parent)
                else:
                    menu = Gtk.MenuItem(action)
                    menu.props.use_underline = True
                    menu.set_submenu(Gtk.Menu())
                    parent.append(menu)
                    parent = menu.get_submenu()
                    menu.show()
                    action_items.append(menu)
        self.actions[action_path] = action_items

    def remove_action(self, W, data):
        action_path = data['name'][0]
        action_items = self.actions.get(action_path)
        if action_items:
            for item in reversed(action_items):
                if isinstance(item, Gtk.MenuItem):
                    submenu = item.get_submenu()
                else:
                    submenu = item
                if not submenu or not submenu.get_children():
                    action_items.remove(item)
                    item.destroy()
            del self.actions[action_path]

    def remove_actions(self, W, data):
        for value in self.actions.values():
            root = value[0]
            root.destroy()
        self.actions = {}

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
from gi.repository import Gtk, Unity, Notify, Dbusmenu

Notify.init('fogger')


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
        self.W.connect('notify::is-active', self.notify_window_state)

    def _js(self, W, jscode):
        if W:
            W.webview.execute_script(jscode)
        else:
            for win in self.W.popups:
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
                'active': self.W.props.is_active
            })

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
            else:
                children = [X.props.label for X in parent.get_children()]
                if action in children:
                    parent = [X for X in parent.get_children() if X.props.label == action][0].get_submenu()
                else:
                    menu = Gtk.MenuItem(action)
                    menu.set_submenu(Gtk.Menu())
                    parent.append(menu)
                    parent = menu.get_submenu()
                    menu.show()

    def add_menu(self, W, data):
        name = data['name'][0]
        if name in [c.props.label for c in W.menubar.get_children()]:
            return
        widget_id = data['id'][0]
        menu_item = self.widgets[widget_id] = self.widgets.get(widget_id, Gtk.MenuItem(name))
        menu = Gtk.Menu()
        menu.set_title(name)
        menu.show()
        menu_item.set_submenu(menu)
        menu_item.show()
        menu_item.props.use_underline = True
        W.menubar.append(menu_item)

    def remove_menu(self, W, data):
        widget_id = data['id'][0]
        menu = self.widgets.get(widget_id)
        if menu:
            menu.destroy()
            del self.widgets[widget_id]

    def add_menu_item(self, W, data):
        menu_id = data['menu_id'][0]
        item_id = data['id'][0]
        item_name = data['name'][0]
        widget_name = data.get('type', ['MenuItem'])[0]
        if hasattr(Gtk, widget_name):
            WidgetClass = getattr(Gtk, widget_name)
        else:
            WidgetClass = Gtk.MenuItem
        menu_item = self.widgets.get(menu_id)
        if not menu_item:
            return
        menu = menu_item.get_submenu()
        item = self.widgets[item_id] = self.widgets.get(item_id, WidgetClass(item_name))
        item.props.use_underline = True
        menu.append(item)
        item.connect('activate', lambda *a, **kw:
                self._dispatch_dom_event(W, 'foggerMenuCallbackEvent',
                    {'menu_id': menu_id, 'item_id': item_id}))
        item.show()

    def remove_menu_item(self, W, data):
        widget_id = data['id'][0]
        item = self.widgets.get(widget_id)
        if item:
            item.destroy()
            del self.widgets[widget_id]

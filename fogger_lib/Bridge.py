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
    menus = {}
    widgets = {}

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

    def set_progress_visible(self, W, data):
        self.launcher_entry.props.progress_visible = data['visible'][0] == 'true'

    def set_count(self, W, data):
        self.launcher_entry.props.count = int(data['count'][0])

    def set_count_visible(self, W, data):
        self.launcher_entry.props.count_visible = data['visible'][0] == 'true'

    def set_urgent(self, W, data):
        self.launcher_entry.props.urgent = data['urgent'][0] == 'true'

    def add_quicklist_item(self, W, data):
        widget_id = data['id'][0]
        name = data['name'][0]
        item = self.widgets[widget_id] = self.widgets.get(
                                                    widget_id,
                                                    Dbusmenu.Menuitem.new())
        item.property_set(Dbusmenu.MENUITEM_PROP_LABEL, name)
        item.property_set_bool(Dbusmenu.MENUITEM_PROP_VISIBLE, True)
        item.connect('item-activated', lambda *a, **kw:
                self._dispatch_dom_event(None, 'foggerQLCallbackEvent',
                    {'name': name}))
        self.quicklist.child_append(item)

    def remove_quicklist_item(self, W, data):
        widget_id = data['id'][0]
        item = self.widgets.get(widget_id)
        if item:
            self.quicklist.child_delete(item)
            del self.widgets[widget_id]

    def add_menu(self, W, data):
        widget_id = data['id'][0]
        name = data['name'][0]
        menu_item = self.widgets[widget_id] = self.widgets.get(widget_id, Gtk.MenuItem(name))
        menu = Gtk.Menu()
        menu.set_title(name)
        menu.show()
        menu_item.set_submenu(menu)
        menu_item.show()
        menu_item.props.use_underline = True
        W.menubar.append(menu_item)
        #menus[name] = {'menu': menu, 'menu_item': menu_item, 'items': {}}
        #self.menus[W] = menus

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

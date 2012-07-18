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

    widget_callback_data = {


    }

    def __init__(self, root, desktop_file, icon_name=None):
        self.W = root
        self.desktop_file = desktop_file
        self.icon_name = icon_name
        self.launcher_entry = Unity.LauncherEntry.get_for_desktop_file(self.desktop_file)
        self.quicklist = Dbusmenu.Menuitem.new()
        self.launcher_entry.set_property("quicklist", self.quicklist)
        self.quicklist_items = {}
        self.indicator = None

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
        name = data['name'][0]
        if name in self.quicklist_items:
            return
        item = Dbusmenu.Menuitem.new()
        item.property_set(Dbusmenu.MENUITEM_PROP_LABEL, name)
        item.property_set_bool(Dbusmenu.MENUITEM_PROP_VISIBLE, True)
        item.connect('item-activated', lambda *a, **kw:
                self._dispatch_dom_event(None, 'foggerQLCallbackEvent',
                    {'name': name}))
        self.quicklist.child_append(item)
        self.quicklist_items[name] = item

    def remove_quicklist_item(self, W, data):
        name = data['name'][0]
        item = self.quicklist_items.get(name)
        if item:
            self.quicklist.child_delete(item)
            del self.quicklist_items[name]

    def add_menu(self, W, data):
        name = data['name'][0]
        menus = self.menus.get(W, {})
        if name in menus:
            return
        menu = Gtk.Menu()
        menu.set_title(name)
        menu.show()
        menu_item = Gtk.MenuItem(name)
        menu_item.set_submenu(menu)
        menu_item.show()
        menu_item.props.use_underline = True
        W.menubar.append(menu_item)
        menus[name] = {'menu': menu, 'menu_item': menu_item, 'items': {}}
        self.menus[W] = menus

    def remove_menu(self, W, data):
        name = data['name'][0]
        menus = self.menus.get(W)
        if name not in menus:
            return
        menu = menus[name]['menu_item']
        W.menubar.remove(menu)
        del menus[name]

    def add_menu_item(self, W, data):
        menu_name = data['menu_name'][0]
        item_name = data['item_name'][0]
        widget_name = data.get('type', ['MenuItem'])[0]
        if hasattr(Gtk, widget_name):
            WidgetClass = getattr(Gtk, widget_name)
        else:
            WidgetClass = Gtk.MenuItem
        _menu = self.menus.get(W, {}).get(menu_name)
        if not _menu:
            return
        if _menu['items'].get(item_name):
            return
        gmenu = _menu['menu']
        #item = Gtk.MenuItem(item_name)
        item = WidgetClass(item_name)
        item.props.use_underline = True
        gmenu.append(item)
        _menu['items'][item_name] = item
        item.connect('activate', lambda *a, **kw:
                self._dispatch_dom_event(W, 'foggerMenuCallbackEvent',
                    {'menu': menu_name, 'name': item_name}))
        item.show()

    def remove_menu_item(self, W, data):
        menu_name = data['menu_name'][0]
        item_name = data['item_name'][0]
        _menu = self.menus.get(W, {}).get(menu_name)
        if not _menu and item_name not in _menu['items']:
            return
        gmenu = _menu['menu']
        item = _menu['items'][item_name]
        gmenu.remove(item)
        del _menu['items'][item_name]
        item.destroy()


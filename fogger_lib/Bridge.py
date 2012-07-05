from gi.repository import Gtk, Unity, Notify, Dbusmenu

Notify.init('fogger')

class DesktopBridge:
    icon_name = None
    desktop_file = None
    menus = {}

    def __init__(self, window, desktop_file, icon_name=None):
        self.W = window
        self.web = window.webview
        self.desktop_file = desktop_file
        self.icon_name = icon_name
        self.launcher_entry = Unity.LauncherEntry.get_for_desktop_file(self.desktop_file)
        self.quicklist = Dbusmenu.Menuitem.new()
        self.launcher_entry.set_property("quicklist", self.quicklist)
        self.quicklist_items = {}
        self.indicator = None

    def _js(self, jscode):
        self.web.execute_script(jscode)

    def _dispatch_dom_event(self, event, params):
        js = 'var e = document.createEvent("Event"); e.initEvent("%s"); var params={};' % event
        for k,v in params.items():
            js = js + 'params.%s = "%s";' % (k, v,)
        js = js + 'e.foggerData = params; document.dispatchEvent(e);'
        self._js(js)

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

    def add_quicklist_item(self, name):
        if name in self.quicklist_items:
            return
        item = Dbusmenu.Menuitem.new()
        item.property_set(Dbusmenu.MENUITEM_PROP_LABEL, name)
        item.property_set_bool(Dbusmenu.MENUITEM_PROP_VISIBLE, True)
        item.connect('item-activated', lambda *a, **kw:
                self._dispatch_dom_event('foggerQLCallbackEvent',
                    {'name': name}))
        self.quicklist.child_append(item)
        self.quicklist_items[name] = item

    def remove_quicklist_item(self, name):
        item = self.quicklist_items.get(name)
        if item:
            self.quicklist.child_delete(item)
            del self.quicklist_items[name]

    def add_menu(self, name):
        if name in self.menus:
            return
        menu = Gtk.Menu()
        menu.set_title(name)
        menu.show()
        menu_item = Gtk.MenuItem(name)
        menu_item.set_submenu(menu)
        menu_item.show()
        menu_item.props.use_underline = True
        self.W.menubar.append(menu_item)
        self.menus[name] = {'menu': menu, 'menu_item': menu_item, 'items': {}}

    def remove_menu(self, name):
        if not name in self.menus:
            return
        menu = self.menus[name]['menu_item']
        self.W.menubar.remove(menu)
        del self.menus[name]

    def add_menu_item(self, menu_name, item_name):
        _menu = self.menus.get(menu_name)
        if not _menu and _menu['items'].get(item_name):
            return
        gmenu = _menu['menu']
        item = Gtk.MenuItem(item_name)
        item.props.use_underline = True
        gmenu.append(item)
        _menu['items'][item_name] = item
        item.connect('activate', lambda *a, **kw:
                self._dispatch_dom_event('foggerMenuCallbackEvent',
                    {'menu': menu_name, 'name': item_name}))
        item.show()

    def remove_menu_item(self, menu_name, item_name):
        _menu = self.menus.get(menu_name)
        if not _menu and item_name not in _menu['items']:
            return
        gmenu = _menu['menu']
        item = _menu['items'][item_name]
        gmenu.remove(item)
        del _menu['items'][item_name]
        item.destroy()


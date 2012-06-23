import urllib2
import urlparse
import os
import simplejson as json

from gi.repository import GLib

from fogger import AppWindow
from fogger_lib.helpers import get_or_create_directory, get_media_file
from . foggerconfig import get_data_file


__all__ = ('FogApp', 'FogAppManager', 'app_manager')
op = os.path
APP_PATH = op.join(GLib.get_user_data_dir(), 'fogapps')
CONF_PATH = op.join(GLib.get_user_config_dir(), 'fogger')


class FogApp:
    name = None
    url = None
    window_size = (800, 600,)
    maximized = False
    path = ''

    def __init__(self, path=None):
        if not path:
            return
        self.path = path
        if op.exists(self.path):
            state = json.loads(open(op.join(self.path, 'app.json'), 'r').read())
            self.name = state['name']
            self.url = state['url']
            self.window_size = state['window_size']
            self.maximized = state['maximized']

    def set_url(self, url):
        self.url = url
        purl = urlparse.urlparse(self.url)
        if not purl.scheme:
           self.url = 'https://%s' % (self.url,)
        #try:
        #    urllib2.urlopen(self.url)
        #except urllib2.URLError:
        #    raise BadFogAppException()

    def save(self):
        state = {
            'name': self.name,
            'url': self.url,
            'window_size': self.window_size,
            'maximized': self.maximized,
        }
        serialized = json.dumps(state)
        handle = open(op.join(self.path, 'app.json'), 'w')
        handle.write(serialized)
        handle.close()

    def run(self):
        self.window = AppWindow.AppWindow()
        self.window.run_app(self)


class FogAppManager:
    apps = {}

    def __init__(self):
        path = op.join(CONF_PATH, 'apps.json')
        if op.exists(path):
            self.apps = json.loads(open(path, 'r').read())

    def get(self, name):
        path = self.apps.get(name)
        if path:
            return FogApp(path)
        else:
            return None

    def create(self, name, url, icon):
        path = self._setup_app_dir(name)
        app = FogApp()
        app.name = name
        app.path = path
        app.set_url(url)
        app.save()
        icon = self._setup_icon(name, icon)
        self._create_desktop_file(name, icon)
        self.apps[name] = path
        self.save()
        return app

    def _setup_icon(self, name, icon):
        _, ext = op.splitext(icon)
        path = op.join(APP_PATH, name, 'icon%s' % ext)
        data = open(icon).read()
        open(path, 'w').write(data)
        return path

    def _create_desktop_file(self, name, icon):
        print get_data_file('templates/fogapp.desktop.in'), '<<<<<<'
        desktop_tmpl = open(get_data_file('templates/fogapp.desktop.in')).read()
        desktop_tmpl = desktop_tmpl % {'name': name, 'icon': icon}
        desktop_file_path = op.join(GLib.get_user_data_dir(), 'applications', '%s.desktop' % name)
        desktop_file = open(desktop_file_path, 'w')
        desktop_file.write(desktop_tmpl)
        desktop_file.close()
        os.chmod(desktop_file_path, 0755)

    def _setup_app_dir(self, name):
        path = get_or_create_directory(op.join(APP_PATH, name))
        get_or_create_directory(op.join(path, 'scripts'))
        get_or_create_directory(op.join(path, 'styles'))
        return path

    def save(self):
        path = get_or_create_directory(CONF_PATH)
        serialized = json.dumps(self.apps)
        open(op.join(path, 'apps.json'), 'w').write(serialized)


app_manager = FogAppManager()

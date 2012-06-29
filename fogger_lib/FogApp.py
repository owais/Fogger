import urllib2
import urlparse
import os
import logging
import simplejson as json
from hashlib import md5

from gi.repository import GLib, WebKit, Soup

from fogger import AppWindow
from fogger_lib.helpers import get_or_create_directory
from . foggerconfig import get_data_file

logger = logging.getLogger('fogger_lib')


__all__ = ('FogApp', 'FogAppManager', 'app_manager')
op = os.path

APP_PATH = op.join(GLib.get_user_data_dir(), 'fogapps')
CONF_PATH = op.join(GLib.get_user_config_dir(), 'fogger')


class FogApp:
    name = None
    url = None
    window_size = (800, 600,)
    maximized = False
    icon = None
    uuid = None
    path = ''

    def __init__(self, path=None):
        if not path:
            return
        self.path = path
        if op.exists(self.path):
            state = json.loads(open(op.join(self.path, 'app.json'), 'r').read())
            self.name = state['name']
            self.url = state['url']
            self.uuid = state['uuid']
            self.icon = state['icon']
            self.window_size = state['window_size']
            self.maximized = state['maximized']

    def get_stylesheet(self):
        return op.join(self.path, 'styles', 'style.css')

    def get_desktop_file(self):
        return op.join(GLib.get_user_data_dir(), 'applications', '%s.desktop' % self.uuid)

    def setup_webkit_session(self):
        session = WebKit.get_default_session()
        cache = get_or_create_directory(os.path.join(GLib.get_user_cache_dir(), 'fogger', self.uuid))
        cookie_jar = Soup.CookieJarText.new(op.join(cache, 'WebkitSession'), False)
        session.add_feature(cookie_jar)
        session.props.max_conns_per_host = 8

    def set_url(self, url):
        self.url = url
        purl = urlparse.urlparse(self.url)
        if not purl.scheme:
           self.url = 'http://%s' % (self.url,)
        #try:
        #    urllib2.urlopen(self.url)
        #except urllib2.URLError:
        #    raise BadFogAppException()

    def save(self):
        state = {
            'name': self.name,
            'url': self.url,
            'uuid': self.uuid,
            'icon': self.icon,
            'window_size': self.window_size,
            'maximized': self.maximized,
        }
        serialized = json.dumps(state)
        handle = open(op.join(self.path, 'app.json'), 'w')
        handle.write(serialized)
        handle.close()

    def run(self):
        self.setup_webkit_session()
        self.window = AppWindow.AppWindow()
        self.window.run_app(self)


class FogAppManager:
    apps = {}

    def __init__(self):
        path = op.join(CONF_PATH, 'apps.json')
        if op.exists(path):
            self.apps = json.loads(open(path, 'r').read())

    def get(self, uuid):
        #path = self.apps.get(uuid)
        path = op.join(APP_PATH, uuid)
        if op.exists(path):
            return FogApp(path)
        else:
            logger.error('No such app: %s' % uuid)
            return None

    def create(self, name, url, icon):
        uuid = md5(name).hexdigest()
        path = self._setup_app_dir(uuid)
        app = FogApp()
        app.name = name
        app.path = path
        app.uuid = uuid
        app.icon = icon
        app.set_url(url)
        app.save()
        icon = self._setup_icon(uuid, icon)
        self._create_desktop_file(name, uuid, icon)
        #self.apps[uuid] = path
        #self.save()
        return app

    def _setup_icon(self, uuid, icon):
        if op.exists(icon):
            _, ext = op.splitext(icon)
            path = op.join(APP_PATH, uuid, 'icon%s' % ext)
            data = open(icon).read()
            open(path, 'w').write(data)
            return path
        else:
            return icon

    def _create_desktop_file(self, name, uuid, icon):
        desktop_tmpl = open(get_data_file('templates/fogapp.desktop.tmpl')).read()
        desktop_tmpl = desktop_tmpl % {'name': name, 'icon': icon, 'uuid': uuid}
        desktop_file_path = op.join(GLib.get_user_data_dir(), 'applications', '%s.desktop' % uuid)
        desktop_file = open(desktop_file_path, 'w')
        desktop_file.write(desktop_tmpl)
        desktop_file.close()
        os.chmod(desktop_file_path, 0755)

    def _setup_app_dir(self, uuid):
        path = get_or_create_directory(op.join(APP_PATH, uuid))
        get_or_create_directory(op.join(path, 'scripts'))
        get_or_create_directory(op.join(path, 'styles'))
        return path

    def save(self):
        path = get_or_create_directory(CONF_PATH)
        serialized = json.dumps(self.apps)
        open(op.join(path, 'apps.json'), 'w').write(serialized)


app_manager = FogAppManager()

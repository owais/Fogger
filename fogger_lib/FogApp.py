import urlparse
import os
import logging
from shutil import rmtree
import simplejson as json
from hashlib import md5

from gi.repository import GLib

from fogger import AppWindow
from fogger_lib.helpers import get_or_create_directory
from fogger_lib.exceptions import BadFogAppException
from . foggerconfig import get_data_file


__all__ = ('FogApp', 'FogAppManager', 'app_manager')

op = os.path
logger = logging.getLogger('fogger_lib')
DESKTOP_DIR = op.join(GLib.get_user_data_dir(), 'applications')
APP_PATH = op.join(GLib.get_user_data_dir(), 'fogapps')
CONF_PATH = op.join(GLib.get_user_config_dir(), 'fogger')
CACHE_PATH = op.join(GLib.get_user_cache_dir(), 'fogger')
DEFAULT_SIZE = (800, 600,)
DEFAULT_STATE = False # True if maximized

class FogApp:
    name = None
    url = None
    window_size = DEFAULT_SIZE
    maximized = DEFAULT_STATE
    icon = None
    uuid = None
    path = ''

    def __init__(self, path=None):
        if not path:
            return
        self.path = path
        if op.exists(self.path):
            try:
                state = json.loads(open(op.join(self.path, 'app.json'), 'r').read())
            except:
                raise BadFogAppException()
            try:
                self.name = state['name']
                self.url = state['url']
                self.uuid = state['uuid']
                self.icon = state['icon']
                self.window_size = state.get('window_size') or DEFAULT_SIZE
                self.maximized = state.get('maximized') or DEFAULT_STATE
            except KeyError:
                raise BadFogAppException()

    @property
    def scripts(self):
        scripts = []
        path = self.scripts_path
        for item in os.listdir(path):
            scripts.append(open(op.join(path, item)).read())
        return scripts

    @property
    def scripts_path(self):
        return op.join(self.path, 'scripts')

    @property
    def desktop_file(self):
        return op.join(DESKTOP_DIR, '%s.desktop' % self.uuid)

    def save(self):
        state = {
            'name': self.name,
            'url': self.url,
            'uuid': self.uuid,
            'icon': self.icon,
            'window_size': self.window_size or DEFAULT_SIZE,
            'maximized': self.maximized or DEFAULT_STATE,
        }
        serialized = json.dumps(state)
        handle = open(op.join(self.path, 'app.json'), 'w')
        handle.write(serialized)
        handle.close()

    def run(self):
        self.window = AppWindow.AppWindow()
        self.window.run_app(self)

    def disable(self):
        if op.exists(self.desktop_file):
            os.remove(self.desktop_file)

    def enable(self):
        create_desktop_files(self.name, self.uuid, self.icon, self.path)

    def remove(self, soft=False):
        self.disable()
        if soft:
            return
        else:
            for directory in (op.join(CONF_PATH, self.uuid),
                              op.join(APP_PATH, self.uuid),
                              op.join(CACHE_PATH, self.uuid),):
                if op.exists(directory):
                    rmtree(directory)


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
        path = setup_app_dir(uuid)
        icon = setup_icon(icon, path)
        create_desktop_files(name, uuid, icon, path)
        app = FogApp()
        app.name = name
        app.path = path
        app.uuid = uuid
        app.icon = icon
        app.url = url
        app.save()
        #self.apps[uuid] = path
        #self.save()
        return app

    def save(self):
        path = get_or_create_directory(CONF_PATH)
        serialized = json.dumps(self.apps)
        open(op.join(path, 'apps.json'), 'w').write(serialized)


def setup_icon(icon, path):
    if icon.startswith('/') and op.exists(icon):
        _, ext = op.splitext(icon)
        path = op.join(path, 'icon%s' % ext)
        data = open(icon).read()
        open(path, 'w').write(data)
        return path
    else:
        return icon

def create_desktop_files(name, uuid, icon, path):
    desktop_tmpl = open(get_data_file('templates/fogapp.desktop.tmpl')).read()
    desktop_tmpl = desktop_tmpl % {'name': name, 'icon': icon, 'uuid': uuid}
    for P in (DESKTOP_DIR, path,):
        base_dir = get_or_create_directory(P)
        desktop_file_path = op.join(base_dir, '%s.desktop' % uuid)
        desktop_file = open(desktop_file_path, 'w')
        desktop_file.write(desktop_tmpl)
        desktop_file.close()
        os.chmod(desktop_file_path, 0755)

def setup_app_dir(uuid):
    path = get_or_create_directory(op.join(APP_PATH, uuid))
    get_or_create_directory(op.join(path, 'scripts'))
    get_or_create_directory(op.join(path, 'styles'))
    return path



app_manager = FogAppManager()

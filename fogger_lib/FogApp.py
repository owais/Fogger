import os
from shutil import rmtree
import simplejson as json
from hashlib import md5
import logging

from gi.repository import GLib

from fogger_lib.helpers import get_or_create_directory
from fogger_lib.exceptions import BadFogAppException
from . foggerconfig import get_data_file, get_data_path


__all__ = ('FogApp', 'FogAppManager',)

op = os.path
logger = logging.getLogger('fogger_lib')
DESKTOP_DIR = op.join(GLib.get_user_data_dir(), 'applications')
CONF_PATH = op.join(GLib.get_user_config_dir(), 'fogger')
CACHE_PATH = op.join(GLib.get_user_cache_dir(), 'fogger')
AUTOSTART_PATH = op.join(GLib.get_user_config_dir(), 'autostart')

BASE_APP_PATHS = [GLib.get_user_data_dir(), get_data_path()]
BASE_APP_PATHS += list(GLib.get_system_data_dirs())
APP_PATHS = [op.join(P, 'fogapps') for P in BASE_APP_PATHS]
USER_APP_PATH = op.join(GLib.get_user_data_dir(), 'fogapps')

DEFAULT_SIZE = (800, 600,)
DEFAULT_STATE = False # True if maximized


class FogApp(object):
    name = None
    url = None
    window_size = DEFAULT_SIZE
    maximized = DEFAULT_STATE
    icon = None
    uuid = None
    path = ''
    __style_cache = __script_cache = ''
    DEBUG = False

    def __init__(self, path=None):
        self.DEBUG = logging.getLogger('fogger').level == logging.DEBUG
        if not path:
            return
        self.path = path
        if op.exists(self.path):
            try:
                state = json.loads(open(op.join(self.path, 'app.json'), 'r').read())
            except:
                logger.error('Could not read app configuration: %s' % path)
                raise BadFogAppException()
            else:
                try:
                    self.name = state['name']
                    self.url = state['url']
                    self.uuid = state['uuid']
                    self.icon = state['icon']
                    self.window_size = state.get('window_size') or DEFAULT_SIZE
                    self.maximized = state.get('maximized') or DEFAULT_STATE
                except KeyError:
                    logger.error('Could not read app configuration: %s' % path)
                    raise BadFogAppException()

    @property
    def scripts(self):
        if self.DEBUG or not self.__script_cache:
            scripts = []
            path = self.scripts_path
            for item in os.listdir(path):
                try:
                    scripts.append(open(op.join(path, item)).read())
                    logger.info('READING %s' % item)
                except:
                    logger.error('Error reading file: %s', op.join(path, item))
                self.__script_cache = scripts
        return self.__script_cache

    @property
    def styles(self):
        if self.DEBUG or not self.__style_cache:
            styles = []
            path = self.styles_path
            for item in os.listdir(path):
                try:
                    lines = [line.replace("'", "\\'")
                            for line in open(op.join(path, item)).readlines()]
                    logger.info('READING %s' % item)
                except Exception, e:
                    raise e
                    logger.error('Error reading file: %s\n %s' % \
                                  (op.join(path, item), e))
                else:
                    styles.append('\n'.join([l for l in lines]))
                self.__style_cache = styles

        return self.__style_cache

    @property
    def scripts_path(self):
        return op.join(self.path, 'scripts')

    @property
    def styles_path(self):
        return op.join(self.path, 'styles')

    @property
    def desktop_file(self):
        return op.join(DESKTOP_DIR, 'fogger-%s.desktop' % self.uuid)

    @property
    def desktop_file_name(self):
        return 'fogger-%s.desktop' % self.uuid

    @property
    def autostart(self):
        filename = '%s.%s' %(self.uuid, 'desktop',)
        autostart_file = op.join(get_or_create_directory(AUTOSTART_PATH), filename)
        return op.exists(autostart_file)

    @autostart.setter
    def autostart(self, autostart):
        filename = '%s.%s' %(self.uuid, 'desktop',)
        autostart_file = op.join(AUTOSTART_PATH, filename)
        if autostart:
            os.link(self.desktop_file, autostart_file)
        else:
            if op.exists(autostart_file):
                os.remove(autostart_file)

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
        # TODO: Move all inter object communication to GSignals and stop
        # passing around object references
        from fogger import AppWindow
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
                              op.join(USER_APP_PATH, self.uuid),
                              op.join(CACHE_PATH, self.uuid),):
                if op.exists(directory):
                    rmtree(directory)

    def reset(self):
        app_data = op.join(CACHE_PATH, self.uuid)
        if op.exists(app_data):
            for child in os.listdir(app_data):
                child = op.join(app_data, child)
                if op.isfile(child):
                    os.remove(child)
                else:
                    rmtree(child)

    @property
    def data_size(self):
        size = 0
        path = op.join(CACHE_PATH, self.uuid)
        if not op.exists(path):
            return
        for _path, _dirs, _files in os.walk(path):
            for _file in _files:
                size += op.getsize(op.join(_path, _file))
        size = size / 1000.0 #1024 returns wrong size. Probably ubuntu uses 1000
        if size > 1000:
            return '%d MB' % (size / 1000.0)
        else:
            return '%d KB' % (size)


class FogAppManager(object):
    apps = {}

    def __init__(self):
        path = op.join(CONF_PATH, 'apps.json')
        if op.exists(path):
            self.apps = json.loads(open(path, 'r').read())

    def get(self, uuid):
        #path = self.apps.get(uuid)
        for app_path in APP_PATHS:
            path = op.join(app_path, uuid)
            if op.exists(path):
                return FogApp(path)
        logger.debug('No such app: %s' % uuid)
        return None

    def get_by_name(self, name):
        return self.get(md5(name.lower()).hexdigest())

    def get_all(self):
        apps = []
        for app_path in APP_PATHS:
            if not op.exists(app_path):
                continue
            dirs = os.listdir(app_path)
            for path in dirs:
                try:
                    apps.append(FogApp(op.join(app_path, path)))
                except BadFogAppException:
                    pass
        return apps

    def create(self, name, url, icon):
        uuid = md5(name.lower()).hexdigest()
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

    get_by_uuid = get


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
        desktop_file_path = op.join(base_dir, 'fogger-%s.desktop' % uuid)
        desktop_file = open(desktop_file_path, 'w')
        desktop_file.write(desktop_tmpl)
        desktop_file.close()
        os.chmod(desktop_file_path, 0755)

def setup_app_dir(uuid):
    path = get_or_create_directory(op.join(USER_APP_PATH, uuid))
    get_or_create_directory(op.join(path, 'scripts'))
    get_or_create_directory(op.join(path, 'styles'))
    return path

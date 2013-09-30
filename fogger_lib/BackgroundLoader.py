from gi.repository import Rsvg, Gdk
from Xlib import Xatom
from Xlib.display import Display

from . helpers import get_media_file


def __patch_svg_data__(data):
    display = Display()
    screen = display.screen()
    atom = display.get_atom('_GNOME_BACKGROUND_REPRESENTATIVE_COLORS')
    result = screen.root.get_property(atom, Xatom.STRING, 0, 100)
    if result:
        color = result.value.strip('\x00')
        rgba = Gdk.RGBA()
        rgba.parse(color)
        color = rgba.to_color().to_string()
        data = data.replace('#000000', color)
    return data


def get_chameleonic_pixbuf_from_svg(filename):
    # Note: Experimental!!!!
    # TODO: Fix or Remove completely
    data = open(get_media_file(filename, '/'), 'r').read()
    try:
        data = __patch_svg_data__(data)
    except:
        # this shouldn't crash the app. fail silently
        pass
    h = Rsvg.Handle.new_from_data(data)
    return h.get_pixbuf()

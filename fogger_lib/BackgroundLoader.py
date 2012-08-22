from gi.repository import Rsvg
from Xlib import Xatom
from Xlib.display import Display

from . helpers import get_media_file

def get_chameleonic_pixbuf_from_svg(filename):
    # Note: Experimental!!!!
    # TODO: Fix or Remove completely
    data = open(get_media_file(filename, '/'), 'r').read()
    display = Display()
    screen = display.screen()
    atom = display.get_atom('_GNOME_BACKGROUND_REPRESENTATIVE_COLORS')
    result = screen.root.get_property(atom, Xatom.STRING, 1, 3)
    if result:
        color = result.value.strip('\x00')
        data = data.replace('#000000', color)
    h = Rsvg.Handle.new_from_data(data)
    return h.get_pixbuf()

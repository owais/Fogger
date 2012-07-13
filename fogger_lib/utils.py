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
from gi.repository import Gio

SEARCH_FIELDS = ['get_display_name',
                 'get_name',
                 'get_filename',
                 'get_description',]


def search_fogapps(search):
    # TODO: Add application/fogapp mimetype and use get_all_for_type
    fogapps = []
    for app in Gio.AppInfo.get_all():
        if 'fogapp' in app.get_keywords():
            fogapps.append(app)

    results = []
    if not search:
        return fogapps

    if not results:
        for app in fogapps:
            for field in SEARCH_FIELDS:
                field_value = getattr(app, field)().lower()
                if search in field_value:
                    results.append(app)
                    app.weight = field_value.index(search)
                    break
        return sorted(results, key=lambda app: app.weight)

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
        results = fogapps

    if not results:
        for app in fogapps:
            for field in SEARCH_FIELDS:
                field_value = getattr(app, field)().lower()
                if search in field_value:
                    results.append(app)
                    app.weight = field_value.index(search)
                    break
    return sorted(results, key=lambda app: app.weight)

# Settings -> Screens: which view each page opens in.
# Saved on the server (not in the browser), so every browser and phone opens the same way.
# The switch on a page saves the same setting, so a switch there sticks too.

DETAILS_VIEWS = ('poster', 'hero', 'classic')
DETAILS_BACKDROPS = ('full', 'small', 'none')
HOME_VIEWS = ('classic', 'sections', 'dashboard')
LIST_VIEWS = ('classic', 'posters', 'list')  # Wanted and Manage
ACTIVITY_VIEWS = ('table', 'cards')  # a new page: no Classic
SNATCHED_VIEWS = ('classic', 'cards', 'table')  # Home's Snatched & Available list

config = [{
    'name': 'screens',
    'order': 3,
    'groups': [
        {
            'tab': 'screens',
            'name': 'home',
            'label': 'Home',
            'description': 'The first page. The switch at the top right of Home changes this too.',
            'options': [
                {
                    'name': 'home_view',
                    'label': 'Opens in',
                    'default': 'classic',
                    'type': 'dropdown',
                    'values': [('Classic', 'classic'), ('Sections', 'sections'), ('Dashboard', 'dashboard')],
                    'description': 'Classic: the old CouchPotato look. Sections: each list as a row of posters. Dashboard: counts on top, then every list as a compact card.',
                },
            ],
        },
        {
            'tab': 'screens',
            'name': 'wanted',
            'label': 'Wanted',
            'description': 'Movies → Wanted. The switch at the top of that page changes this too.',
            'options': [
                {
                    'name': 'wanted_view',
                    'label': 'Opens in',
                    'default': 'classic',
                    'type': 'dropdown',
                    'values': [('Classic', 'classic'), ('Posters', 'posters'), ('List', 'list')],
                    'description': 'Classic: the old CouchPotato look. Posters: a poster grid with search and A-Z always shown. List: one line per movie.',
                },
            ],
        },
        {
            'tab': 'screens',
            'name': 'manage',
            'label': 'Manage',
            'description': 'Movies → Manage (your library). The switch at the top of that page changes this too.',
            'options': [
                {
                    'name': 'manage_view',
                    'label': 'Opens in',
                    'default': 'classic',
                    'type': 'dropdown',
                    'values': [('Classic', 'classic'), ('Posters', 'posters'), ('List', 'list')],
                    'description': 'Classic: the old CouchPotato look. Posters: a poster grid with search and A-Z always shown. List: one line per movie.',
                },
            ],
        },
        {
            'tab': 'screens',
            'name': 'snatched',
            'label': 'Snatched & Available',
            'description': 'The Snatched & Available list on Home. The switch next to its title changes this too.',
            'options': [
                {
                    'name': 'snatched_view',
                    'label': 'Opens in',
                    'default': 'classic',
                    'type': 'dropdown',
                    'values': [('Classic', 'classic'), ('Cards', 'cards'), ('Table', 'table')],
                    'description': 'Classic: the old CouchPotato look. Cards: one card per release with its state, progress and buttons. Table: release, status, quality, size, age, score and provider.',
                },
            ],
        },
        {
            'tab': 'screens',
            'name': 'activity',
            'label': 'Activity',
            'description': 'What is downloading now. The switch at the top right of Activity changes this too.',
            'options': [
                {
                    'name': 'activity_view',
                    'label': 'Opens in',
                    'default': 'table',
                    'type': 'dropdown',
                    'values': [('Table', 'table'), ('Cards', 'cards')],
                    'description': 'Table: one row per download with progress and time left. Cards: one card per download, problems on top with a fix button.',
                },
            ],
        },
        {
            'tab': 'screens',
            'name': 'movie_details',
            'label': 'Movie details',
            'description': 'The page that opens when you click a movie. The switch at the top right of that page changes these too.',
            'options': [
                {
                    'name': 'details_view',
                    'label': 'Opens in',
                    'default': 'poster',
                    'type': 'dropdown',
                    'values': [('Poster', 'poster'), ('Hero', 'hero'), ('Classic', 'classic')],
                    'description': 'Poster: poster and facts on the left. Hero: a wide banner on top. Classic: the old CouchPotato look.',
                },
                {
                    'name': 'details_backdrop',
                    'label': 'Backdrop',
                    'default': 'full',
                    'type': 'dropdown',
                    'values': [('Full', 'full'), ('Small', 'small'), ('None', 'none')],
                    'description': 'The movie\'s backdrop picture behind the whole page, as a band on top, or not at all. Not used in Classic.',
                },
            ],
        },
        {
            'tab': 'screens',
            'name': 'labels',
            'label': 'Labels',
            'options': [
                {
                    'name': 'show_new_tags',
                    'label': 'Show NEW tags',
                    'default': True,
                    'type': 'bool',
                    'description': 'On: a small NEW tag marks things added in recent updates. Off: hidden everywhere. Saves as soon as you click.',
                },
            ],
        },
    ],
}]


def frontendOptions(get_setting):
    """What the page needs at start. Unknown values fall back to the defaults."""
    view = get_setting('details_view', section = 'screens', default = 'poster')
    backdrop = get_setting('details_backdrop', section = 'screens', default = 'full')
    show_new = get_setting('show_new_tags', section = 'screens', default = True)
    home = get_setting('home_view', section = 'screens', default = 'classic')
    wanted = get_setting('wanted_view', section = 'screens', default = 'classic')
    manage = get_setting('manage_view', section = 'screens', default = 'classic')
    activity = get_setting('activity_view', section = 'screens', default = 'table')
    snatched = get_setting('snatched_view', section = 'screens', default = 'classic')
    return {
        'home_view': home if home in HOME_VIEWS else 'classic',
        'wanted_view': wanted if wanted in LIST_VIEWS else 'classic',
        'manage_view': manage if manage in LIST_VIEWS else 'classic',
        'activity_view': activity if activity in ACTIVITY_VIEWS else 'table',
        'snatched_view': snatched if snatched in SNATCHED_VIEWS else 'classic',
        'details_view': view if view in DETAILS_VIEWS else 'poster',
        'details_backdrop': backdrop if backdrop in DETAILS_BACKDROPS else 'full',
        'show_new_tags': asBool(show_new, True),
    }


def asBool(value, default):
    """The settings file holds text ('1', 'True', '0'...); getBool only applies once the option type is known."""
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in ('1', 'true', 'yes', 'on'):
        return True
    if text in ('0', 'false', 'no', 'off'):
        return False
    return default

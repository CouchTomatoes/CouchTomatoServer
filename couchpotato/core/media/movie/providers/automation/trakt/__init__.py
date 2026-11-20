from .main import Trakt


def autoload():
    return Trakt()


config = [{
    'name': 'trakt',
    'groups': [
        {
            'tab': 'automation',
            'list': 'watchlist_providers',
            'name': 'trakt_automation',
            'label': 'Trakt',
            'description': 'Import movies from your own watchlist',
            'options': [
                {
                    'name': 'automation_enabled',
                    'default': False,
                    'type': 'enabler',
                },
                {
                    'name': 'automation_oauth_token',
                    'label': 'Auth Token',
                    'advanced': 1
                },
                {
                    'name': 'automation_oauth_refresh',
                    'label': 'Refresh Token',
                    'description': 'Renews the auth token before it expires. Filled in when you sign in.',
                    'advanced': 1
                },
                {
                    'name': 'automation_oauth_expires',
                    'label': 'Token Expires',
                    'description': 'When the auth token runs out (Unix time). Empty means an old sign-in: sign in again.',
                    'advanced': 1
                },
            ],
        },
    ],
}]

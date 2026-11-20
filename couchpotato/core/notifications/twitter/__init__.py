from .main import Twitter


def autoload():
    return Twitter()

config = [{
    'name': 'twitter',
    'groups': [
        {
            'tab': 'notifications',
            'list': 'notification_providers',
            'name': 'twitter',
            'label': 'X (Twitter)',
            'description': 'Posts or DMs through <a href="https://developer.x.com/en/portal/dashboard" target="_blank">your own X developer app</a>. '
                           'X charges per post (about $0.015 each, since February 2026), billed to that app.',
            'options': [
                {
                    'name': 'enabled',
                    'default': 0,
                    'type': 'enabler',
                },
                {
                    'name': 'consumer_key',
                    'label': 'API key',
                    'description': 'From your app\'s "Keys and tokens" page on developer.x.com (Consumer Keys).',
                },
                {
                    'name': 'consumer_secret',
                    'label': 'API key secret',
                    'type': 'password',
                },
                {
                    'name': 'access_token_key',
                    'label': 'Access token',
                    'description': ('Same page, "Access Token and Secret". Set the app\'s permissions to "Read and write" '
                                    '(and "Direct message" for DMs) BEFORE generating these, or X refuses the post.'),
                },
                {
                    'name': 'access_token_secret',
                    'label': 'Access token secret',
                    'type': 'password',
                },
                {
                    'name': 'screen_name',
                    'description': 'Your X username. Direct messages go here.',
                    'advanced': True,
                },
                {
                    'name': 'mention',
                    'description': 'Add a mention to this user to the tweet.',
                },
                {
                    'name': 'on_snatch',
                    'default': 0,
                    'type': 'bool',
                    'advanced': True,
                    'description': 'Also send message when movie is snatched.',
                },
                {
                    'name': 'direct_message',
                    'default': 0,
                    'type': 'bool',
                    'advanced': True,
                    'description': 'Use direct messages for the notifications (Also applies to the mentioned users).',
                },
            ],
        }
    ],
}]

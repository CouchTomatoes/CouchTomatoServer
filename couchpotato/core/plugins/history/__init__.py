from .main import History


def autoload():
    return History()


config = [{
    'name': 'history',
    'order': 2,
    'groups': [
        {
            'tab': 'general',
            'name': 'history',
            'label': 'History',
            'description': 'What happened to your movies, on the History page.',
            'options': [
                {
                    'name': 'keep',
                    'label': 'Keep history',
                    'default': '90',
                    'type': 'dropdown',
                    'values': [('90 days', '90'), ('1 year', '365'), ('Forever', 'forever')],
                    'description': 'Older events go into an archive file each night, then leave the database. Forever never archives.',
                },
                {
                    'name': 'folder',
                    'label': 'Archive folder',
                    'default': '',
                    'type': 'directory',
                    'description': 'Empty = the "history" folder inside your data folder, so it is copied with your backups.',
                },
            ],
        },
    ],
}]

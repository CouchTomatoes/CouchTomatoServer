import traceback

from couchpotato.core.event import addEvent
from couchpotato.core.helpers.encoding import tryUrlencode
from couchpotato.core.helpers.variable import tryInt, getIdentifier, cleanHost
from couchpotato.core.logger import CPLog
from couchpotato.core.media._base.providers.torrent.base import TorrentMagnetProvider


log = CPLog(__name__)

# Trackers added to magnets built from apibay's info_hash (clients with DHT find peers without them)
TRACKERS = [
    'udp://tracker.opentrackr.org:1337/announce',
    'udp://open.demonii.com:1337/announce',
    'udp://open.stealth.si:80/announce',
    'udp://tracker.torrent.eu.org:451/announce',
    'udp://exodus.desync.com:6969/announce',
    'udp://explodie.org:6969/announce',
    'udp://tracker.openbittorrent.com:6969/announce',
]


class Base(TorrentMagnetProvider):
    """
    ThePirateBay through apibay, the JSON API behind thepiratebay.org. The HTML proxy sites this
    provider used to scrape are gone; apibay sits behind Cloudflare, so it needs a FlareSolverr
    host in Settings > General (the same approach SickGear uses).
    """

    urls = {
        'api': 'https://apibay.org',
        'search': '%s/q.php?q=%s',
        'info': '%s/t.php?id=%s',
        'detail': 'https://thepiratebay.org/description.php?id=%s',
    }

    cat_backup_id = 200
    disable_provider = False
    http_time_between_calls = 0

    # apibay's uploader status, and the score it adds (the old HTML badges: Trusted, VIP, Helpers, Moderator)
    trust_scores = {'trusted': 10, 'vip': 20, 'helper': 30, 'moderator': 50, 'supermod': 50, 'admin': 50}

    def __init__(self):
        super(Base, self).__init__()

        addEvent('app.test', self.doTest)

    def getDomain(self, url = ''):
        domain = self.conf('domain')
        return (cleanHost(domain).rstrip('/') if domain else self.urls['api']) + url

    def _search(self, media, quality, results):

        cats = [str(cat) for cat in self.getCatId(quality)]
        imdb_id = getIdentifier(media)

        data = self.getJsonData(self.urls['search'] % (self.getDomain(), tryUrlencode(self.buildQuery(media))))
        if not isinstance(data, list):
            return

        try:
            for item in data:
                # an empty search answers with one placeholder row, id 0
                if tryInt(item.get('id')) == 0 or not item.get('info_hash'):
                    continue

                category = str(item.get('category', ''))
                if not (category in cats or ('200' in cats and category.startswith('2'))):
                    continue

                if imdb_id and item.get('imdb') and item['imdb'] != imdb_id:
                    log.debug('Skipped %s, it is for %s', (item.get('name'), item['imdb']))
                    continue

                status = (item.get('status') or '').lower()
                if self.conf('trusted_only') and status not in self.trust_scores:
                    log.info('Skipped torrent %s, untrusted.', item.get('name'))
                    continue

                results.append({
                    'id': item['id'],
                    'name': item['name'],
                    'url': self.magnet(item['info_hash'], item['name']),
                    'detail_url': self.urls['detail'] % item['id'],
                    'size': tryInt(item.get('size')) / 1024 / 1024,
                    'seeders': tryInt(item.get('seeders')),
                    'leechers': tryInt(item.get('leechers')),
                    'extra_score': lambda x, score = self.trust_scores.get(status, 0): score,
                    'get_more_info': self.getMoreInfo,
                })
        except:
            log.error('Failed getting results from %s: %s', (self.getName(), traceback.format_exc()))

    def magnet(self, info_hash, name):
        return 'magnet:?xt=urn:btih:%s&dn=%s&tr=%s' % (info_hash.lower(), tryUrlencode(name), '&tr='.join(tryUrlencode(tr) for tr in TRACKERS))

    def getMoreInfo(self, item):
        info = self.getJsonData(self.urls['info'] % (self.getDomain(), item['id']), cache_timeout = 25920000)
        item['description'] = (info or {}).get('descr', '') if isinstance(info, dict) else ''
        return item

    def doTest(self):
        try:
            data = self.getJsonData(self.urls['search'] % (self.getDomain(), 'test'), cache_timeout = 0)
            if isinstance(data, list):
                log.info('Success %s', self.getDomain())
            else:
                log.error('%s answered no search results list; is a FlareSolverr host set?', self.getDomain())
        except:
            log.error('%s', traceback.format_exc(0))


config = [{
    'name': 'thepiratebay',
    'groups': [
        {
            'tab': 'searcher',
            'list': 'torrent_providers',
            'name': 'ThePirateBay',
            'description': 'The world\'s largest bittorrent tracker. <a href="https://thepiratebay.org/" target="_blank">ThePirateBay</a>, searched through its apibay API. Needs a FlareSolverr host (Settings > General).',
            'wizard': True,
            'icon': 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAAAAAA6mKC9AAAA3UlEQVQY02P4DwT/YADIZvj//7qnozMYODmtAAusZoCDELDAegYGViZhAWZmRoYoqIDupfhNN1M3dTBEggXWMZg9jZRXV77YxhAOFpjDwMAPMoCXmcHsF1SAQZ6bQY2VgUEbKHClcAYzg3mINEO8jSCD478/DPsZmvqWblu1bOmStes3Pp0ezVDF4Gif0Hfx9///74/ObRZ2YNiZ47C8XIRBxFJR0jbSSUud4f9zAQWn8NTuziAt2zy5xIMM/z8LFX0E+fD/x0MRDCeA1v7Z++Y/FDzyvAtyBxIA+h8A8ZKLeT+lJroAAAAASUVORK5CYII=',
            'options': [
                {
                    'name': 'enabled',
                    'type': 'enabler',
                    'default': False
                },
                {
                    'name': 'domain',
                    'advanced': True,
                    'label': 'API server',
                    'description': 'An apibay-compatible API to search, keep empty for apibay.org.',
                },
                {
                    'name': 'seed_ratio',
                    'label': 'Seed ratio',
                    'type': 'float',
                    'default': 1,
                    'description': 'Will not be (re)moved until this seed ratio is met.',
                },
                {
                    'name': 'seed_time',
                    'label': 'Seed time',
                    'type': 'int',
                    'default': 40,
                    'description': 'Will not be (re)moved until this seed time (in hours) is met.',
                },
                {
                    'name': 'extra_score',
                    'advanced': True,
                    'label': 'Extra Score',
                    'type': 'int',
                    'default': 0,
                    'description': 'Starting score for each release found via this provider.',
                },
                {
                    'name': 'trusted_only',
                    'advanced': True,
                    'label': 'Trusted/VIP Only',
                    'type': 'bool',
                    'default': False,
                    'description': 'Only download releases marked as Trusted or VIP'
                }
            ],
        }
    ]
}]

"""Torznab indexers: Prowlarr, Jackett and anything else that speaks the Torznab API.

One entry per feed. In Prowlarr, open an indexer and copy its Torznab URL
(http://<prowlarr>:9696/<id>/api) plus Prowlarr's API key (Settings -> General).
In Jackett, use the indexer's "Copy Torznab Feed" link and Jackett's API key.
"""
from urllib.parse import urlparse
import time
import traceback

from couchpotato.core.helpers.encoding import toUnicode
from couchpotato.core.helpers.rss import RSS
from couchpotato.core.helpers.variable import splitString, tryInt, tryFloat
from couchpotato.core.logger import CPLog
from couchpotato.core.media._base.providers.base import ResultList
from couchpotato.core.media._base.providers.torrent.base import TorrentProvider
from couchpotato.core.media._base.providers.torrent.yts import makeMagnet
from couchpotato.environment import Env
from dateutil.parser import parse


log = CPLog(__name__)


class Base(TorrentProvider, RSS):

    urls = {}
    http_time_between_calls = 1  # Seconds

    def search(self, media, quality):
        # Never trust a feed's result as "this is the movie": some indexers behind Prowlarr
        # ignore imdbid, so every result still goes through the title + year checks.
        results = ResultList(self, media, quality, imdb_results = False)

        for host in self.getHosts():
            if self.isDisabled(host):
                continue
            try:
                self._searchOnHost(host, media, quality, results)
            except:
                log.error('Failed searching %s: %s', (self.hostLabel(host), traceback.format_exc()))

        return results

    def _searchOnHost(self, host, media, quality, results):
        found = 0
        for query in self.buildQueries(media, host):
            url = self.feedUrl(host['host'], query)
            items = self.getRSSData(url, cache_timeout = 1800, headers = {'User-Agent': Env.getIdentifier()})
            for item in items or []:
                result = self.parseItem(item, host)
                if result:
                    results.append(result)
                    found += 1
            if found:
                break  # the IMDb search answered; the title search is only a fallback

    @staticmethod
    def feedUrl(feed, query):
        feed = feed.strip()
        if '://' not in feed:
            feed = 'http://' + feed
        if '?' in feed:
            return '%s&%s' % (feed.rstrip('&'), query)
        return '%s?%s' % (feed, query)

    def buildQueries(self, media, host):
        """ Override in the media provider; returns url-encoded query strings, best first """
        return []

    @staticmethod
    def attrs(item):
        out = {}
        for child in list(item):
            tag = child.tag if isinstance(child.tag, str) else ''
            if tag.endswith('}attr') or tag == 'attr':
                name = child.attrib.get('name')
                if name and name not in out:
                    out[name] = child.attrib.get('value')
        return out

    def parseItem(self, item, host):
        name = self.getTextElement(item, 'title')
        if not name:
            return None

        a = self.attrs(item)

        link = None
        enclosure = self.getElement(item, 'enclosure')
        if enclosure is not None:
            link = enclosure.attrib.get('url')
        if not link:
            link = self.getTextElement(item, 'link')

        # Prowlarr's download link answers either a .torrent (200) or a 301 to a magnet:, which a
        # 'torrent' download can't follow. So: the feed's own magnet first; for a public indexer, a
        # magnet from the infohash; private indexers keep the .torrent (its announce URL holds the passkey).
        magnet = a.get('magneturl')
        if not magnet and link and link.startswith('magnet:'):
            magnet = link
        if not magnet and a.get('infohash') and self.isPublic(item):
            magnet = makeMagnet(a['infohash'], name)

        if magnet:
            url, protocol = magnet, 'torrent_magnet'
        elif link:
            url, protocol = link, 'torrent'
        else:
            return None

        size = tryInt(a.get('size')) or tryInt(self.getTextElement(item, 'size'))
        if not size and enclosure is not None:
            size = tryInt(enclosure.attrib.get('length'))

        seeders = tryInt(a.get('seeders'))
        peers = tryInt(a.get('peers'))
        leechers = max(peers - seeders, 0) if peers else tryInt(a.get('leechers'))

        guid = self.getTextElement(item, 'guid') or link
        detail_url = self.getTextElement(item, 'comments') or (guid if guid and guid.startswith('http') else '')

        age = 0
        pub = self.getTextElement(item, 'pubDate')
        if pub:
            try: age = max(int((time.time() - parse(pub).timestamp()) / 86400), 0)
            except (ValueError, OverflowError): log.debug('Unreadable pubDate %s', pub)

        return {
            'id': a.get('infohash') or guid,
            'protocol': protocol,
            'provider_extra': self.hostLabel(host),
            'name': toUnicode(name),
            'url': url,
            'detail_url': detail_url,
            'size': size / 1024 / 1024 if size else 0,
            'age': age,
            'seeders': seeders,
            'leechers': leechers,
            'score': host['extra_score'],
            'seed_ratio': host['seed_ratio'],
            'seed_time': host['seed_time'],
        }

    @staticmethod
    def isPublic(item):
        # Prowlarr marks each item <prowlarrindexer type="public|private|semiPrivate">. Jackett doesn't
        # (it sends magneturl for magnet-only sites instead), so an unmarked item counts as private.
        for child in list(item):
            tag = child.tag if isinstance(child.tag, str) else ''
            if tag.endswith('prowlarrindexer'):
                return (child.attrib.get('type') or '').lower() == 'public'
        return False

    @staticmethod
    def hostLabel(host):
        if host.get('name'):
            return host['name']
        feed = host.get('host') or ''
        parsed = urlparse(feed if '://' in feed else 'http://' + feed)
        return parsed.hostname or feed

    def getHosts(self):
        uses = splitString(str(self.conf('use')), clean = False)
        hosts = splitString(self.conf('host'), clean = False)
        api_keys = splitString(self.conf('api_key'), clean = False)
        names = splitString(self.conf('name'), clean = False)
        extra_score = splitString(self.conf('extra_score'), clean = False)
        seed_ratios = splitString(self.conf('seed_ratio'), clean = False)
        seed_times = splitString(self.conf('seed_time'), clean = False)
        categories = splitString(self.conf('custom_categories'), clean = False)

        def at(lst, nr, default = ''):
            try: return lst[nr]
            except IndexError: return default

        out = []
        for nr in range(len(hosts)):
            out.append({
                'use': at(uses, nr, '0'),
                'host': at(hosts, nr),
                'api_key': at(api_keys, nr),
                'name': at(names, nr).strip(),
                'extra_score': tryInt(at(extra_score, nr, 0)),
                'seed_ratio': tryFloat(at(seed_ratios, nr, 1)),
                'seed_time': tryInt(at(seed_times, nr, 40)),
                'custom_category': at(categories, nr).strip().replace(' ', ','),
            })
        return out

    def belongsTo(self, url, provider = None, host = None):
        for host in self.getHosts():
            result = super(Base, self).belongsTo(url, host = host['host'], provider = provider)
            if result:
                return result

    def isDisabled(self, host = None):
        return not self.isEnabled(host)

    def isEnabled(self, host = None):
        if host is None:
            for h in self.getHosts():
                if self.isEnabled(h):
                    return True
            return False

        return TorrentProvider.isEnabled(self) and bool(host['host']) and tryInt(host['use']) == 1


config = [{
    'name': 'torznab',
    'groups': [
        {
            'tab': 'searcher',
            'list': 'torrent_providers',
            'name': 'Torznab',
            'order': 5,
            'description': 'Search your <a href="https://prowlarr.com/" target="_blank">Prowlarr</a> or '
                           '<a href="https://github.com/Jackett/Jackett" target="_blank">Jackett</a> indexers '
                           '(any Torznab feed). One row per indexer: the indexer\'s Torznab URL, e.g. '
                           '<code>http://prowlarr:9696/1/api</code>, and the Prowlarr or Jackett API key.',
            'wizard': True,
            'icon': 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQAgMAAABinRfyAAAACVBMVEX/xQBEMjL///+R5qO4AAAAM0lEQVQI12NgYGBgDA1lYGBgcGBgYGBgZWBgYGRiYGBgYmFgYGBgZmBgYAhlYGBgYGAAAEdmAyEB+AviAAAAAElFTkSuQmCC',
            'options': [
                {
                    'name': 'enabled',
                    'type': 'enabler',
                    'default': False,
                },
                {
                    'name': 'use',
                    'default': '',
                },
                {
                    'name': 'host',
                    'default': '',
                    'label': 'Torznab URL',
                    'description': 'The indexer\'s Torznab feed URL',
                },
                {
                    'name': 'name',
                    'label': 'Name',
                    'default': '',
                    'description': 'Shown next to results (optional)',
                },
                {
                    'name': 'seed_ratio',
                    'label': 'Seed ratio',
                    'default': '',
                    'description': 'Will not be (re)moved until this seed ratio is met.',
                },
                {
                    'name': 'seed_time',
                    'label': 'Seed time',
                    'default': '',
                    'description': 'Will not be (re)moved until this seed time (in hours) is met.',
                },
                {
                    'name': 'extra_score',
                    'advanced': True,
                    'label': 'Extra Score',
                    'default': '',
                    'description': 'Starting score for each release found via this indexer.',
                },
                {
                    'name': 'custom_categories',
                    'advanced': True,
                    'label': 'Categories',
                    'default': '',
                    'description': 'Leave empty for all movies (2000). E.g. "2040 2045" for HD and UHD only.',
                },
                {
                    'name': 'api_key',
                    'default': '',
                    'label': 'API key',
                    'description': 'Prowlarr: Settings → General. Jackett: top of its dashboard.',
                    'type': 'combined',
                    'combine': ['use', 'host', 'api_key', 'name', 'seed_ratio', 'seed_time', 'extra_score', 'custom_categories'],
                },
            ],
        },
    ],
}]

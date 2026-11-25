"""
Torznab provider (Prowlarr / Jackett): parsing real Prowlarr feeds (tests/fixtures/torznab, captured
2026-11-25 from Prowlarr's YTS and Knaben indexers), magnet vs .torrent choice, the IMDb-then-title
fallback, and per-row settings.
"""
import os
import sys
import unittest
import xml.etree.ElementTree as XMLTree
from unittest import mock
from urllib.parse import urlparse, parse_qs

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)
sys.path.insert(0, os.path.join(root, 'libs'))

from couchpotato.core.media.movie.providers.torrent.torznab import Torznab

FIX = os.path.join(root, 'tests', 'fixtures', 'torznab')

HOST = {'use': '1', 'host': 'http://prowlarr:9696/1/api', 'api_key': 'K', 'name': '', 'extra_score': 5,
        'seed_ratio': 1.0, 'seed_time': 40, 'custom_category': ''}

MATRIX = {'identifiers': {'imdb': 'tt0133093'}, 'info': {'year': 1999, 'titles': ['The Matrix']}, 'title': 'The Matrix'}


def items(name):
    with open(os.path.join(FIX, name), 'rb') as f:
        return XMLTree.fromstring(f.read()).findall('channel/item')


def provider(conf = None):
    p = Torznab.__new__(Torznab)
    values = {'enabled': True}
    values.update(conf or {})
    p.conf = lambda key, *a, **kw: values.get(key)
    return p


class ParseTest(unittest.TestCase):

    def test_public_prowlarr_item_becomes_a_magnet_with_trackers(self):
        r = provider().parseItem(items('prowlarr_knaben_search.xml')[0], HOST)
        self.assertEqual(r['protocol'], 'torrent_magnet')
        q = parse_qs(urlparse(r['url']).query)
        self.assertEqual(q['xt'], ['urn:btih:3950B0923106A7457D3AB8340A929F38C636B1A0'])
        self.assertEqual(q['dn'], ['The Matrix 1999 2160p UHD BDRip HEVC 10bit DV HDR TrueHD.7.1 Atmos MUSHR00M'])
        self.assertTrue(q['tr'])
        self.assertEqual(r['seeders'], 55)
        self.assertEqual(r['leechers'], 14)          # peers 69 - seeders 55
        self.assertEqual(int(r['size']), 23788)      # 24944353313 bytes in MB
        self.assertEqual(r['score'], 5)
        self.assertEqual(r['provider_extra'], 'prowlarr')
        self.assertTrue(r['detail_url'].startswith('https://knaben.xyz/'))
        self.assertGreater(r['age'], 0)

    def test_private_item_keeps_the_torrent_link(self):
        item = items('prowlarr_yts_movie.xml')[0]
        for child in item:
            if child.tag == 'prowlarrindexer':
                child.set('type', 'private')
        r = provider().parseItem(item, HOST)
        self.assertEqual(r['protocol'], 'torrent')
        self.assertTrue(r['url'].startswith('http://localhost:19696/1/download?apikey=TESTKEY'))

    def test_unmarked_item_without_magneturl_counts_as_private(self):
        item = items('prowlarr_yts_movie.xml')[0]
        for child in list(item):
            if child.tag == 'prowlarrindexer':
                item.remove(child)
        self.assertEqual(provider().parseItem(item, HOST)['protocol'], 'torrent')

    def test_feed_magneturl_wins(self):
        item = items('prowlarr_yts_movie.xml')[0]
        attr = XMLTree.SubElement(item, '{http://torznab.com/schemas/2015/feed}attr')
        attr.set('name', 'magneturl')
        attr.set('value', 'magnet:?xt=urn:btih:FEEDMAGNET')
        r = provider().parseItem(item, HOST)
        self.assertEqual((r['protocol'], r['url']), ('torrent_magnet', 'magnet:?xt=urn:btih:FEEDMAGNET'))

    def test_name_label_shown(self):
        r = provider().parseItem(items('prowlarr_yts_movie.xml')[0], dict(HOST, name = 'YTS via Prowlarr'))
        self.assertEqual(r['provider_extra'], 'YTS via Prowlarr')


class QueryTest(unittest.TestCase):

    def test_imdb_first_then_title_year(self):
        qs = [parse_qs(q) for q in provider().buildQueries(MATRIX, HOST)]
        self.assertEqual(qs[0]['t'], ['movie'])
        self.assertEqual(qs[0]['imdbid'], ['tt0133093'])
        self.assertEqual(qs[0]['cat'], ['2000'])
        self.assertEqual(qs[0]['apikey'], ['K'])
        self.assertEqual(qs[1]['t'], ['search'])
        self.assertEqual(qs[1]['q'], ['The Matrix 1999'])

    def test_custom_categories(self):
        q = parse_qs(provider().buildQueries(MATRIX, dict(HOST, custom_category = '2040,2045'))[0])
        self.assertEqual(q['cat'], ['2040,2045'])

    def test_feed_url_joins(self):
        self.assertEqual(Torznab.feedUrl('http://p:9696/1/api', 't=movie'), 'http://p:9696/1/api?t=movie')
        self.assertEqual(Torznab.feedUrl('p:9117/api/v2.0/indexers/x/results/torznab/?x=1', 't=movie'),
                         'http://p:9117/api/v2.0/indexers/x/results/torznab/?x=1&t=movie')

    def test_title_search_only_when_imdb_finds_nothing(self):
        p = provider()
        calls = []

        def rss(url, **kw):
            calls.append(parse_qs(urlparse(url).query)['t'][0])
            return [] if len(calls) == 1 else items('prowlarr_knaben_search.xml')

        results = []
        with mock.patch.object(p, 'getRSSData', side_effect = rss):
            p._searchOnHost(HOST, MATRIX, None, results)
        self.assertEqual(calls, ['movie', 'search'])
        self.assertEqual(len(results), 3)

        calls[:] = []
        results = []
        with mock.patch.object(p, 'getRSSData', side_effect = lambda url, **kw: calls.append(1) or items('prowlarr_yts_movie.xml')):
            p._searchOnHost(HOST, MATRIX, None, results)
        self.assertEqual(len(calls), 1)
        self.assertEqual(len(results), 3)


class HostsTest(unittest.TestCase):

    def test_rows_and_enabled(self):
        p = provider({'use': '1,0', 'host': 'http://a/1/api,http://a/2/api', 'api_key': 'k1,k2', 'name': 'A,',
                      'extra_score': '10,', 'seed_ratio': ',', 'seed_time': ',', 'custom_categories': '2040 2045,'})
        hosts = p.getHosts()
        self.assertEqual(len(hosts), 2)
        self.assertEqual(hosts[0]['custom_category'], '2040,2045')
        self.assertEqual(hosts[0]['extra_score'], 10)
        with mock.patch('couchpotato.core.media._base.providers.torrent.base.TorrentProvider.isEnabled', return_value = True):
            self.assertTrue(p.isEnabled(hosts[0]))
            self.assertFalse(p.isEnabled(hosts[1]))
            self.assertTrue(p.isEnabled())


if __name__ == '__main__':
    unittest.main()

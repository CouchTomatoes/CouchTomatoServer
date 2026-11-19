"""
Tests for the YTS magnet link (couchpotato/core/media/_base/providers/torrent/yts.py): every
tracker must parse back to a clean udp:// URL. The old string had a '%0A' newline before each
tracker and a stray ']' on the last one.
Run from the repo root:  python3 -m unittest discover -s tests
"""
import os
import sys
import unittest
from urllib.parse import urlparse, parse_qs

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)
sys.path.insert(0, os.path.join(root, 'libs'))

from couchpotato.core.media._base.providers.torrent.yts import makeMagnet, TRACKERS


class YtsMagnetTest(unittest.TestCase):

    def setUp(self):
        self.magnet = makeMagnet('ABCDEF0123456789ABCDEF0123456789ABCDEF01', 'The Rage (2026) [1080p]')
        self.params = parse_qs(urlparse(self.magnet).query)

    def test_trackers_are_clean_urls(self):
        self.assertEqual(self.params['tr'], TRACKERS)
        for tracker in self.params['tr']:
            u = urlparse(tracker)
            self.assertEqual(u.scheme, 'udp')
            self.assertTrue(u.port)
            self.assertNotIn(']', tracker)
            self.assertNotIn('\n', tracker)

    def test_hash_and_name(self):
        self.assertEqual(self.params['xt'], ['urn:btih:ABCDEF0123456789ABCDEF0123456789ABCDEF01'])
        self.assertEqual(self.params['dn'], ['The Rage (2026) [1080p]'])


if __name__ == '__main__':
    unittest.main()

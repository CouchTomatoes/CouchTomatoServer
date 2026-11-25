"""
Tests for Wanted's status chips and List columns (card #104 part 2): media.list's no_release_status filter
("Still wanted") and the added / last_search times. Run from the repo root:
PYTHONHASHSEED=0 python3 -m unittest discover -s tests
"""
import os
import sys
import unittest
from unittest import mock

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)
sys.path.insert(0, os.path.join(root, 'libs'))

from couchpotato.core.media._base.media import main as media_main
from couchpotato.core.media._base.media.main import MediaPlugin, addTimes

# m1 snatched, m2 available, m3 nothing yet, m4 snatched AND available
RELEASES = [
    {'media_id': 'm1', 'status': 'snatched'},
    {'media_id': 'm2', 'status': 'available'},
    {'media_id': 'm4', 'status': 'snatched'},
    {'media_id': 'm4', 'status': 'available'},
]
IDS = ['m1', 'm2', 'm3', 'm4']


class FakeDb(object):

    def all(self, index):
        return [{'_id': x} for x in IDS]  # 'media' and 'media_title' (already in title order)


def fakeFire(name, *args, **kwargs):
    if name == 'release.with_status':
        return [r for r in RELEASES if r['status'] in args[0]]
    if name == 'media.with_status':
        return [{'_id': x} for x in IDS]
    if name == 'media.get':
        return {'_id': args[0]}
    raise AssertionError('unexpected event %s' % name)


def titles(**kwargs):
    with mock.patch.object(media_main, 'get_db', return_value = FakeDb()), \
            mock.patch.object(media_main, 'fireEvent', side_effect = fakeFire):
        total, medias = MediaPlugin.list(None, status = ['active'], **kwargs)
    return total, [m['_id'] for m in medias]


class ChipFilterTest(unittest.TestCase):

    def test_all(self):
        self.assertEqual(titles(), (4, IDS))

    def test_snatched_and_available_chips(self):
        self.assertEqual(titles(release_status = ['snatched', 'downloaded', 'seeding', 'missing']), (2, ['m1', 'm4']))
        self.assertEqual(titles(release_status = ['available']), (2, ['m2', 'm4']))

    def test_still_wanted_leaves_out_anything_snatched_or_available(self):
        self.assertEqual(titles(no_release_status = ['snatched', 'downloaded', 'seeding', 'missing', 'available']), (1, ['m3']))

    def test_still_wanted_accepts_a_single_string(self):
        self.assertEqual(titles(no_release_status = 'snatched'), (2, ['m2', 'm3']))

    def test_total_is_counted_before_the_limit(self):
        # the chip counts ask with limit_offset=1 and read total
        total, ids = titles(no_release_status = ['available'], limit_offset = '1')
        self.assertEqual((total, ids), (2, ['m1']))


class TimesTest(unittest.TestCase):

    def test_times_from_doc_and_property(self):
        props = {'last_search.abc': '1795649268'}
        with mock.patch.object(media_main.Env, 'prop', side_effect = lambda k, *a, **kw: props.get(k)):
            m = addTimes({'_id': b'abc', 'added': 1795217203})  # the database gives bytes ids
        self.assertEqual((m['added'], m['last_search']), (1795217203, 1795649268))

    def test_unknown_is_none(self):
        # movies added before this change have no 'added', never-searched ones no property
        with mock.patch.object(media_main.Env, 'prop', return_value = None):
            m = addTimes({'_id': 'x'})
        self.assertEqual((m['added'], m['last_search']), (None, None))


if __name__ == '__main__':
    unittest.main()

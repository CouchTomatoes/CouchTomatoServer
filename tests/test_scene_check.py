"""
Tests for SceneCheck (backlog §10, replaces the CouchTomato API's /validate/). The fixtures are real
predb.net and srrdb answers recorded 2026-11-19/20.
Run from the repo root:  python3 -m unittest discover -s tests
"""
import json
import os
import sys
import unittest
from unittest import mock

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)
sys.path.insert(0, os.path.join(root, 'libs'))

from couchpotato.core.plugins import scenecheck
from couchpotato.core.plugins.scenecheck import SceneCheck
from couchpotato.core.plugins.score import scores

FIXTURES = os.path.join(root, 'couchpotato', 'core', 'plugins', 'fixtures')

FOUND = 'the.matrix.1999.2160p.uhd.bluray.h265-wou'
NUKED = 'avatar.2009.extended.2160p.uhd.bluray.x265-guacamole'
UNNUKED = 'the.matrix.1999.multi.2160p.uhd.bluray.x265-seskapile'
UNKNOWN = 'joker.2019.1080p.bluray.x264-fake99'


def recorded(name):
    with open(os.path.join(FIXTURES, 'scenecheck_%s.json' % name), 'rb') as f:
        return f.read()


def checker(predb = None, srrdb = None):
    """ A SceneCheck whose sites answer with the given bytes; an Exception instance means that site failed """
    plugin = SceneCheck.__new__(SceneCheck)  # skip __init__: no event registration
    cache = {}
    plugin.getCache = lambda key: cache.get(key)
    plugin.setCache = lambda key, value, timeout = 0: cache.__setitem__(key, value)
    plugin.cache = cache

    def urlopen(url, **kwargs):
        answer = predb if 'predb.net' in url else srrdb
        if isinstance(answer, Exception):
            raise answer
        return answer

    plugin.urlopen = mock.Mock(side_effect = urlopen)
    return plugin


class SceneCheckTest(unittest.TestCase):

    def test_scene_release(self):
        plugin = checker(recorded('predb_found'))
        self.assertEqual(plugin.validate(FOUND), {'score': 40, 'reasons': ['scene']})
        # A short connect timeout, so predb's dead IPv6 address can't eat the whole budget (see TIMEOUT)
        connect, read = plugin.urlopen.call_args.kwargs['timeout']
        self.assertLessEqual(connect, 3)

    def test_nuked_release_with_a_known_reason(self):
        # predb reason "bad.subs_get.rerip": -10 for the nuke, -40 for get.rerip
        self.assertEqual(checker(recorded('predb_nuked')).validate(NUKED),
                         {'score': -50, 'reasons': ['nuke', 'get.rerip']})

    def test_unnuked_counts_as_scene(self):
        self.assertEqual(checker(recorded('predb_unnuked')).validate(UNNUKED)['score'], 40)

    def test_name_is_matched_case_insensitively(self):
        # The app lowercases names before asking; the old orlydb check compared case-sensitively and never matched
        self.assertEqual(checker(recorded('predb_found')).validate(FOUND.upper())['score'], 40)

    def test_only_an_exact_name_counts(self):
        self.assertEqual(checker(recorded('predb_found')).validate(FOUND + '.proper')['score'], 0)

    def test_unknown_release_scores_nothing_and_is_cached(self):
        plugin = checker(recorded('predb_notfound'))
        self.assertEqual(plugin.validate(UNKNOWN), {'score': 0, 'reasons': []})
        self.assertEqual(plugin.urlopen.call_count, 1)  # predb answered, so srrdb is not asked
        self.assertTrue(plugin.cache)

    def test_answer_is_cached(self):
        plugin = checker(recorded('predb_found'))
        plugin.validate(FOUND)
        plugin.validate(FOUND)
        self.assertEqual(plugin.urlopen.call_count, 1)

    def test_predb_down_falls_back_to_srrdb(self):
        plugin = checker(IOError('429 Too Many Requests'), recorded('srrdb_found'))
        self.assertEqual(plugin.validate(FOUND), {'score': 40, 'reasons': ['scene']})

    def test_predb_rate_limit_page_falls_back_to_srrdb(self):
        # predb's 429 body is plain text, not JSON
        plugin = checker(b'Too Many Requests', recorded('srrdb_notfound'))
        self.assertEqual(plugin.validate(UNKNOWN), {'score': 0, 'reasons': []})
        self.assertTrue(plugin.cache)

    def test_both_down_scores_nothing_and_is_not_cached(self):
        plugin = checker(IOError('down'), '')
        self.assertEqual(plugin.validate(FOUND), {'score': 0, 'reasons': []})
        self.assertFalse(plugin.cache)

    def test_no_name(self):
        self.assertIsNone(checker().validate(''))

    def test_nuke_penalties(self):
        self.assertEqual(scenecheck.scoreNuke('blended.frames'), (-50, ['nuke', 'blended.frames']))
        self.assertEqual(scenecheck.scoreNuke('dupe.DARM.2010-11-27'), (-10, ['nuke']))
        self.assertEqual(scenecheck.scoreNuke(None), (-10, ['nuke']))


class SceneScoreTest(unittest.TestCase):
    """ The search scoring path end to end: sceneScore -> release.validate -> SceneCheck """

    def score(self, release_name, predb):
        plugin = checker(predb)
        with mock.patch.object(scores, 'fireEvent', side_effect = lambda event, name, single: plugin.validate(name)):
            return scores.sceneScore(release_name)

    def test_scene_release_in_a_search(self):
        self.assertEqual(self.score('The.Matrix.1999.2160p.UHD.BluRay.H265-WOU.mkv', recorded('predb_found')), 40)

    def test_nuked_release_in_a_search(self):
        self.assertEqual(self.score('Avatar.2009.EXTENDED.2160p.UHD.BluRay.x265-GUACAMOLE', recorded('predb_nuked')), -50)


if __name__ == '__main__':
    unittest.main()

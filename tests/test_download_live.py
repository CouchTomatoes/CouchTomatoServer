"""
Tests for the live download status behind Movie details (couchpotato/core/plugins/download_live.py and the
progress / eta fields every downloader now reports). Run from the repo root:
python3 -m unittest discover -s tests
"""
import os
import sys
import unittest
from unittest import mock

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)
sys.path.insert(0, os.path.join(root, 'libs'))

from couchpotato.core._base.downloader.main import toProgress, toEta, clockToSeconds
from couchpotato.core.plugins import download_live
from couchpotato.core.plugins.download_live import mergeStatus, DownloadLive


def rel(rid, dl_id, downloader = 'Transmission', media_id = 'm1'):
    return {'_id': rid, 'media_id': media_id, 'download_info': {'id': dl_id, 'downloader': downloader}}


def rd(dl_id, progress, eta = None, status = 'busy', downloader = 'Transmission', **extra):
    d = {'id': dl_id, 'downloader': downloader, 'status': status, 'progress': progress, 'eta': eta}
    d.update(extra)
    return d


class ProgressParsingTest(unittest.TestCase):

    def test_fraction_percent_and_per_mille(self):
        self.assertEqual(toProgress(0.64), 64)  # Transmission percentDone, qBittorrent progress
        self.assertEqual(toProgress(64.9, whole = 100), 64)  # Deluge, SABnzbd, put.io: never rounds up to a false 100
        self.assertEqual(toProgress(640, whole = 1000), 64)  # uTorrent
        self.assertEqual(toProgress(1), 100)
        self.assertEqual(toProgress('45', whole = 100), 45)  # SABnzbd sends a string

    def test_unknown_is_none_never_a_made_up_number(self):
        for value in (None, '', 'n/a', -1):
            self.assertIsNone(toProgress(value))
        self.assertIsNone(toProgress(5, whole = 0))  # rTorrent before it knows the size

    def test_clamped(self):
        self.assertEqual(toProgress(1.2), 100)

    def test_eta(self):
        self.assertEqual(toEta(1080), 1080)
        self.assertIsNone(toEta(-1))  # Transmission: not available
        self.assertIsNone(toEta(-2))  # Transmission: unknown
        self.assertIsNone(toEta(8640000, unknown_from = 8640000))  # qBittorrent: infinity
        self.assertIsNone(toEta(None))

    def test_sabnzbd_clock(self):
        self.assertEqual(clockToSeconds('1:02:03'), 3723)
        self.assertEqual(clockToSeconds('0:18:00'), 1080)
        self.assertIsNone(clockToSeconds('soon'))


class MergeTest(unittest.TestCase):

    def test_first_answer_is_sent(self):
        live = {}
        changed = mergeStatus(live, [rel('r1', 'h1')], [rd('h1', 64, 1080)], now = 1000)
        self.assertEqual(len(changed), 1)
        self.assertEqual(live['r1']['progress'], 64)
        self.assertEqual(live['r1']['eta'], 1080)

    def test_only_changes_are_sent(self):
        live = {}
        mergeStatus(live, [rel('r1', 'h1')], [rd('h1', 64, 1075)], now = 1000)
        # Same %, ETA a few seconds lower in the same minute -> nothing to send
        self.assertEqual(mergeStatus(live, [rel('r1', 'h1')], [rd('h1', 64, 1070)], now = 1010), [])
        # One point more -> sent
        self.assertEqual(len(mergeStatus(live, [rel('r1', 'h1')], [rd('h1', 65, 1070)], now = 1020)), 1)
        # Same %, but the minute of the ETA changed -> sent
        self.assertEqual(len(mergeStatus(live, [rel('r1', 'h1')], [rd('h1', 65, 1000)], now = 1030)), 1)

    def test_matches_by_id_and_downloader(self):
        live = {}
        changed = mergeStatus(live, [rel('r1', 'h1', downloader = 'Deluge')], [rd('h1', 50)], now = 1)
        self.assertEqual(changed, [])
        self.assertEqual(live, {})

    def test_completed_without_progress_counts_as_100_and_remembers_when(self):
        live = {}
        mergeStatus(live, [rel('r1', 'h1')], [rd('h1', None, status = 'completed')], now = 500)
        self.assertEqual(live['r1']['progress'], 100)
        self.assertEqual(live['r1']['done'], 500)
        self.assertIsNone(live['r1']['eta'])
        # Later checks keep the first time 100 % was seen
        mergeStatus(live, [rel('r1', 'h1')], [rd('h1', 100, status = 'seeding')], now = 900)
        self.assertEqual(live['r1']['done'], 500)

    def test_downloader_done_date_wins(self):
        live = {}
        mergeStatus(live, [rel('r1', 'h1')], [rd('h1', 100, done = 420, added = 100)], now = 500)
        self.assertEqual(live['r1']['done'], 420)
        self.assertEqual(live['r1']['added'], 100)

    def test_unknown_progress_stays_unknown(self):
        live = {}
        mergeStatus(live, [rel('r1', 'h1', downloader = 'Hadouken')], [rd('h1', None, downloader = 'Hadouken')], now = 1)
        self.assertIsNone(live['r1']['progress'])

    def test_full_check_drops_releases_no_longer_snatched(self):
        live = {}
        mergeStatus(live, [rel('r1', 'h1'), rel('r2', 'h2')], [rd('h1', 10), rd('h2', 20)], now = 1)
        mergeStatus(live, [rel('r1', 'h1')], [rd('h1', 11)], now = 2, full = True)
        self.assertEqual(list(live.keys()), ['r1'])
        # A fast-lane check (not full) never drops others
        mergeStatus(live, [rel('r2', 'h2')], [rd('h2', 30)], now = 3)
        self.assertEqual(sorted(live.keys()), ['r1', 'r2'])


class FastLaneTest(unittest.TestCase):

    def setUp(self):
        self.fired = []

        def fake_fire(name, *args, **kwargs):
            self.fired.append((name, args, kwargs))
            if name == 'release.for_media':
                return [dict(rel('r1', 'h1'), status = 'snatched'), dict(rel('r9', 'h9'), status = 'done')]
            if name == 'download.status':
                return [rd('h1', 64, 1080)]
            return None

        patches = [
            mock.patch.object(download_live, 'fireEvent', side_effect = fake_fire),
            mock.patch.object(download_live, 'addEvent'),
            mock.patch.object(download_live, 'addApiView'),
        ]
        db = mock.Mock()
        db.get.side_effect = lambda index, key: {'_id': key}
        patches.append(mock.patch.object(download_live, 'get_db', return_value = db))
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        self.plugin = DownloadLive()

    def names(self):
        return [f[0] for f in self.fired]

    def test_watch_starts_the_fast_lane_once(self):
        self.plugin.watchView(media_id = 'm1')
        self.plugin.watchView(media_id = 'm1')
        self.assertEqual(self.names().count('schedule.interval'), 1)
        sched = [f for f in self.fired if f[0] == 'schedule.interval'][0]
        self.assertEqual(sched[2]['seconds'], 10)

    def test_fast_lane_asks_only_about_watched_downloading_releases(self):
        self.plugin.watchView(media_id = 'm1')
        self.plugin.fastLane()
        status_call = [f for f in self.fired if f[0] == 'download.status'][0]
        self.assertEqual(status_call[1][0], [{'id': 'h1', 'downloader': 'Transmission'}])  # not the 'done' one
        pushed = [f for f in self.fired if f[0] == 'notify.frontend']
        self.assertEqual(pushed[0][2]['type'], 'release.progress')
        self.assertEqual(pushed[0][2]['data'][0]['progress'], 64)

    def test_no_heartbeat_for_60s_stops_it(self):
        with mock.patch.object(download_live.time, 'time', return_value = 1000):
            self.plugin.watchView(media_id = 'm1')
        with mock.patch.object(download_live.time, 'time', return_value = 1059):
            self.plugin.fastLane()
        self.assertNotIn('schedule.remove', self.names())
        with mock.patch.object(download_live.time, 'time', return_value = 1061):
            self.plugin.fastLane()
        self.assertIn('schedule.remove', self.names())
        self.assertFalse(self.plugin.fast_on)
        # A new watch starts it again
        self.plugin.watchView(media_id = 'm1')
        self.assertEqual(self.names().count('schedule.interval'), 2)

    def test_live_view_filters_by_movie(self):
        self.plugin.update([rel('r1', 'h1', media_id = 'm1'), rel('r2', 'h2', media_id = 'm2')], [rd('h1', 5), rd('h2', 6)])
        out = self.plugin.liveView(media_id = 'm2')
        self.assertEqual([x['release_id'] for x in out['releases']], ['r2'])
        self.assertEqual(len(self.plugin.liveView()['releases']), 2)


if __name__ == '__main__':
    unittest.main()

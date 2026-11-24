"""
Tests for the History page's backend (couchpotato/core/plugins/history): events, the rolling archive for
"Keep history" = 90 days / 1 year / Forever, importing a file back, and filling History from the notifications
and releases an existing install already has. Runs against a real CodernityDB database in a temp folder.
Run from the repo root:  python3 -m unittest discover -s tests
"""
import datetime
import hashlib
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from unittest import mock

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)
sys.path.insert(0, os.path.join(root, 'libs'))

from CodernityDB.database import Database

from couchpotato.core.media._base.media.index import MediaIndex
from couchpotato.core.notifications.core.index import NotificationIndex
from couchpotato.core.plugins.history import main as history_main
from couchpotato.core.plugins.history.index import HistoryIndex, HistoryEventIndex
from couchpotato.core.plugins.history.main import History, parseNotification, blockFor, FILE_RE
from couchpotato.core.plugins.release.index import ReleaseIndex

DAY = 86400
NOW = int(time.mktime((2026, 11, 20, 12, 0, 0, 0, 0, -1)))


class Base(unittest.TestCase):
    """ A History plugin on a real database, with settings and Env.prop kept in dicts """

    keep = '90'

    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix = 'ct-history-')
        self.db = Database(os.path.join(self.dir, 'db'))
        self.db.create()
        for name, klass in (('history', HistoryIndex), ('history_eid', HistoryEventIndex), ('media', MediaIndex),
                            ('notification', NotificationIndex), ('release', ReleaseIndex)):
            self.db.add_index(klass(self.db.path, name))

        self.settings = {'keep': self.keep, 'folder': os.path.join(self.dir, 'history')}
        self.props = {}

        self.patches = [
            mock.patch.object(history_main, 'get_db', return_value = self.db),
            mock.patch.object(history_main.Env, 'prop', side_effect = self.prop),
            mock.patch.object(history_main, 'fireEvent'),
        ]
        for p in self.patches:
            p.start()

        h = History.__new__(History)
        h.lock = __import__('threading').RLock()
        h.conf = lambda name, value = None, default = None: self.settings.get(name, default)
        self.h = h

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.db.close()
        shutil.rmtree(self.dir)

    def prop(self, identifier, value = None, default = None):
        if value is None:
            return self.props.get(identifier, default)
        self.props[identifier] = value

    def event(self, days_ago, type = 'snatched', title = 'The Odyssey', **kw):
        self.assertTrue(self.h.add(type, title = title, year = 2026, event_time = NOW - days_ago * DAY, **kw))

    def live(self):
        return [e for e in self.h.allEvents() if not e.get('archive')]

    def files(self):
        folder = self.settings['folder']
        return sorted(os.listdir(folder)) if os.path.isdir(folder) else []

    def lines(self, name):
        with open(os.path.join(self.settings['folder'], name), encoding = 'utf-8') as f:
            return [json.loads(l) for l in f if l.strip()]


class EventsAndList(Base):

    def test_add_and_list_newest_first(self):
        self.event(3, 'snatched', quality = '1080p', source = 'YTS')
        self.event(2, 'downloaded')
        self.event(1, 'moved')
        self.event(0, 'updated', title = None)
        r = self.h.listView()
        self.assertTrue(r['success'])
        self.assertEqual([e['type'] for e in r['events']], ['updated', 'moved', 'downloaded', 'snatched'])
        self.assertEqual(r['events'][-1]['source'], 'YTS')
        self.assertNotIn('_rev', r['events'][0])
        self.assertEqual(r['keep'], '90')

    def test_filters(self):
        for t in ('added', 'snatched', 'downloaded', 'moved', 'failed', 'subfail', 'updated', 'signin'):
            self.event(1, t)
        types = lambda f: sorted(e['type'] for e in self.h.listView(filter = f)['events'])
        self.assertEqual(types('snatched'), ['snatched'])
        self.assertEqual(types('failed'), ['failed', 'subfail'])
        self.assertEqual(types('library'), ['added', 'moved', 'subfail'])
        self.assertEqual(types('app'), ['signin', 'updated'])
        self.assertEqual(len(types('all')), 8)

    def test_range(self):
        self.event(5)
        self.event(40)
        with mock.patch.object(history_main.time, 'time', return_value = NOW):
            self.assertEqual(self.h.listView(days = '30')['total'], 1)
            self.assertEqual(self.h.listView(days = 'all')['total'], 2)

    def test_unknown_type_is_refused(self):
        self.assertFalse(self.h.add('exploded'))
        self.assertEqual(self.h.allEvents(), [])

    def test_same_event_id_is_stored_once(self):
        self.assertTrue(self.h.add('snatched', eid = 'x1'))
        self.assertFalse(self.h.add('snatched', eid = 'x1'))
        self.assertEqual(len(self.h.allEvents()), 1)

    def test_media_fills_title_year_identifier(self):
        m = self.db.insert({'_t': 'media', 'type': 'movie', 'title': 'Despatch', 'info': {'year': 2024, 'titles': ['Despatch']},
                            'identifiers': {'imdb': 'tt1234567'}})
        self.h.add('moved', media_id = m['_id'])
        e = self.h.allEvents()[0]
        self.assertEqual((e['title'], e['year'], e['identifier']), ('Despatch', 2024, 'tt1234567'))


    def test_update_failure_with_a_previous_version_is_a_rollback(self):
        # Both updater paths that reset to the previous commit send it in data
        self.h.onUpdateFailed('rolled back', data = {'version': 'b', 'previous': 'a', 'reason': 'installing its packages failed'})
        self.h.onUpdateFailed('Failed updating: no network')
        self.assertEqual(sorted(e['type'] for e in self.h.allEvents()), ['failed', 'rollback'])

    def test_renamed_group_gives_movie_quality_and_folder(self):
        m = self.db.insert({'_t': 'media', 'type': 'movie', 'title': 'Arrival', 'info': {'year': 2016, 'titles': ['Arrival']},
                            'identifiers': {'imdb': 'tt2543164'}})
        self.h.onRenamed('Downloaded Arrival', group = {'media': self.db.get('id', m['_id']),
                                                        'meta_data': {'quality': {'label': '1080p'}},
                                                        'destination_dir': '/media/Movies/Arrival (2016)'})
        e = self.h.allEvents()[0]
        self.assertEqual((e['type'], e['title'], e['quality'], e['detail']), ('moved', 'Arrival', '1080p', '/media/Movies/Arrival (2016)'))


class Archive90(Base):

    def test_old_events_move_to_their_block_file_and_leave_the_db(self):
        self.event(200, title = 'A')   # first event: the blocks start on its date
        self.event(150, title = 'B')
        self.event(95, title = 'C')
        self.event(10, title = 'D')
        r = self.h.archive(now = NOW)
        self.assertTrue(r['success'])
        self.assertEqual(r['archived'], 3)
        self.assertEqual([e['title'] for e in self.live()], ['D'])

        first = datetime.date.fromtimestamp(NOW - 200 * DAY)
        self.assertEqual(self.props['history.anchor'], first.isoformat())
        names = self.files()
        self.assertEqual(len(names), 2)
        for name in names:
            m = FILE_RE.match(name)
            start, end = datetime.date.fromisoformat(m.group(1)), datetime.date.fromisoformat(m.group(2))
            self.assertEqual((end - start).days, 89)
            self.assertEqual((start - first).days % 90, 0)
        self.assertEqual([e['title'] for e in self.lines(names[0])], ['A', 'B'])
        self.assertEqual([e['title'] for e in self.lines(names[1])], ['C'])
        self.assertNotIn('_rev', self.lines(names[0])[0])

    def test_nothing_old_writes_nothing(self):
        self.event(10)
        self.assertEqual(self.h.archive(now = NOW)['archived'], 0)
        self.assertEqual(self.files(), [])

    def test_file_is_written_before_anything_is_deleted(self):
        self.event(120)
        self.event(100)
        with mock.patch.object(history_main.os, 'replace', side_effect = OSError('disk full')):
            r = self.h.archive(now = NOW)
        self.assertFalse(r['success'])
        self.assertEqual(len(self.live()), 2)  # nothing removed when the file could not be saved

    def test_archiving_twice_does_not_duplicate_lines(self):
        self.event(120, eid = 'e1')
        self.h.archive(now = NOW)
        # The same event shows up again (for example from an old backup) and is archived again
        self.event(120, eid = 'e1')
        self.h.archive(now = NOW)
        name = self.files()[0]
        self.assertEqual([e['eid'] for e in self.lines(name)], ['e1'])
        self.assertEqual(self.live(), [])

    def test_existing_file_content_is_kept(self):
        self.event(120, title = 'A')
        self.h.archive(now = NOW)
        self.event(110, title = 'B')
        self.h.archive(now = NOW)
        self.assertEqual([e['title'] for e in self.lines(self.files()[0])], ['A', 'B'])

    def test_anchor_stays_put(self):
        self.event(120)
        self.h.archive(now = NOW)
        anchor = self.props['history.anchor']
        self.event(30)
        self.h.archive(now = NOW + 70 * DAY)
        self.assertEqual(self.props['history.anchor'], anchor)


class Archive365(Base):
    keep = '365'

    def test_yearly_blocks(self):
        self.event(800, title = 'A')
        self.event(400, title = 'B')
        self.event(200, title = 'C')
        self.h.archive(now = NOW)
        self.assertEqual([e['title'] for e in self.live()], ['C'])
        names = self.files()
        self.assertEqual(len(names), 2)
        for name in names:
            m = FILE_RE.match(name)
            self.assertEqual((datetime.date.fromisoformat(m.group(2)) - datetime.date.fromisoformat(m.group(1))).days, 364)


class ArchiveForever(Base):
    keep = 'forever'

    def test_forever_never_archives(self):
        self.event(3000)
        self.event(400)
        r = self.h.archive(now = NOW)
        self.assertEqual(r['archived'], 0)
        self.assertIn('Forever', r['message'])
        self.assertEqual(len(self.live()), 2)
        self.assertEqual(self.files(), [])


class Import(Base):

    def archived_file(self):
        self.event(120, title = 'A', eid = 'a')
        self.event(100, title = 'B', eid = 'b')
        self.event(5, title = 'C', eid = 'c')
        self.h.archive(now = NOW)
        name = self.files()[0]
        return name, os.path.join(self.settings['folder'], name)

    def digest(self, path):
        with open(path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()

    def test_round_trip(self):
        name, path = self.archived_file()
        before = self.digest(path)

        r = self.h.importView(file = name)
        self.assertEqual((r['added'], r['skipped']), (2, 0))
        back = [e for e in self.h.allEvents() if e.get('archive') == name]
        self.assertEqual(sorted(e['title'] for e in back), ['A', 'B'])
        self.assertEqual(self.digest(path), before)  # the file is not changed

        # Importing again adds nothing
        self.assertEqual(self.h.importView(file = name)['added'], 0)
        self.assertEqual(len(self.h.allEvents()), 3)

        # The nightly job leaves imported events alone and does not duplicate them in the file
        self.h.archive(now = NOW + DAY)
        self.assertEqual(len([e for e in self.h.allEvents() if e.get('archive')]), 2)
        self.assertEqual(self.digest(path), before)

        listed = self.h.listView()
        self.assertEqual(listed['imported'], {name: 2})
        self.assertEqual([f['on_page'] for f in listed['files']], [2])

        # Remove from page
        self.assertEqual(self.h.unimportView(file = name)['removed'], 2)
        self.assertEqual([e['title'] for e in self.h.allEvents()], ['C'])
        self.assertEqual(self.digest(path), before)

    def test_began_is_the_oldest_day_anywhere(self):
        """ The page's "History began here" must not move to the oldest LIVE day once older days are archived """
        self.archived_file()
        day = lambda days_ago: datetime.date.fromtimestamp(NOW - days_ago * DAY).isoformat()
        listed = self.h.listView()
        self.assertEqual(listed['began'], self.files_from()[0])
        self.assertLessEqual(listed['began'], day(120))
        self.assertEqual(datetime.date.fromtimestamp(listed['first_time']).isoformat(), day(5))
        # Each file says which days it really holds, not just its 90-day block
        f = listed['files'][0]
        self.assertEqual((f['first'], f['last']), (day(120), day(100)))
        self.assertLess(f['last'], f['to'])

    def files_from(self):
        return sorted(f['from'] for f in self.h.files())

    def test_upload_from_elsewhere(self):
        name, path = self.archived_file()
        with open(path, 'rb') as f:
            body = f.read()
        request = mock.Mock()
        request.request.files = {'file': [{'filename': 'my-backup.jsonl', 'body': body + b'not json\n\n'}]}
        r = self.h.importView(_request = request)
        self.assertEqual((r['added'], r['name']), (2, 'my-backup.jsonl'))
        self.assertEqual(self.h.listView()['imported'], {'my-backup.jsonl': 2})

    def test_only_files_in_the_archive_folder(self):
        self.assertFalse(self.h.importView(file = '../../etc/passwd')['success'])
        self.assertFalse(self.h.importView(file = 'history-2026-01-01_to_2026-03-31.jsonl')['success'])


class Simulate(Base):
    """ Every day for 400 days: a few events, then the nightly job. Checked for each Keep setting. """

    def run_days(self, keep):
        self.settings['keep'] = keep
        written = []
        start = NOW - 400 * DAY
        for d in range(400):
            day = start + d * DAY
            for k, t in enumerate(('snatched', 'downloaded', 'moved')):
                eid = 'd%03d-%d' % (d, k)
                self.assertTrue(self.h.add(t, title = 'Movie %d' % d, event_time = day + 3600 * (k + 1), eid = eid))
                written.append(eid)
            self.h.archive(now = day + 23 * 3600)
        return written

    def all_in_files(self):
        out = []
        for name in self.files():
            out += [e['eid'] for e in self.lines(name)]
        return out

    def check(self, keep, days):
        written = self.run_days(keep)
        in_db = [e['eid'] for e in self.live()]
        in_files = self.all_in_files()
        self.assertEqual(len(in_files), len(set(in_files)), 'an event is in the files twice')
        self.assertEqual(sorted(in_db + in_files), sorted(written), 'an event was lost')
        self.assertFalse(set(in_db) & set(in_files))
        if days:
            oldest = min(e['time'] for e in self.live())
            self.assertLessEqual((NOW - oldest) / DAY, days + 1)
            names = self.files()
            spans = [(datetime.date.fromisoformat(FILE_RE.match(n).group(1)), datetime.date.fromisoformat(FILE_RE.match(n).group(2))) for n in names]
            for a, b in zip(spans, spans[1:]):
                self.assertEqual((b[0] - a[1]).days, 1, 'blocks are not back to back')
            for a, b in spans:
                self.assertEqual((b - a).days, days - 1)
        return in_db, in_files

    def test_90_days(self):
        in_db, in_files = self.check('90', 90)
        self.assertEqual(len(self.files()), 4)   # 310 archived days = 3 whole blocks + part of a 4th
        self.assertEqual(len(in_db), 90 * 3)

    def test_1_year(self):
        in_db, in_files = self.check('365', 365)
        self.assertEqual(len(self.files()), 1)
        self.assertEqual(len(in_db), 365 * 3)

    def test_forever(self):
        in_db, in_files = self.check('forever', None)
        self.assertEqual(in_files, [])
        self.assertEqual(len(in_db), 400 * 3)

    def test_switching_90_then_forever_then_1_year(self):
        self.settings['keep'] = '90'
        self.event(200, eid = 'old')
        self.event(100, eid = 'mid')
        self.event(10, eid = 'new')
        self.h.archive(now = NOW)
        self.assertEqual(sorted(e['eid'] for e in self.live()), ['new'])
        # Forever: everything archived comes back on the page, and the files go
        self.settings['keep'] = 'forever'
        self.event(500, eid = 'older')
        self.h.archive(now = NOW)
        self.assertEqual(sorted(e['eid'] for e in self.live()), ['mid', 'new', 'old', 'older'])
        self.assertEqual(self.files(), [])
        self.settings['keep'] = '365'
        self.h.archive(now = NOW)
        self.assertEqual(sorted(e['eid'] for e in self.live()), ['mid', 'new', 'old'])
        self.assertEqual(sorted(self.all_in_files()), ['older'])

    def spans(self):
        out = []
        for n in self.files():
            m = FILE_RE.match(n)
            out.append((datetime.date.fromisoformat(m.group(1)), datetime.date.fromisoformat(m.group(2))))
        return out

    def seed51(self):
        """ The real-boot scenario: 5 movies x 12 ages x 4 kinds, + 3 more = 63 events, all kept somewhere """
        eids = []
        for m in range(5):
            for d in (0.2, 1, 3, 10, 45, 89, 95, 130, 200, 300, 370, 400):
                for k, t in enumerate(('snatched', 'downloaded', 'moved', 'subtitle')):
                    eid = 's%d-%s-%d' % (m, d, k)
                    self.assertTrue(self.h.add(t, title = 'Movie %d' % m, event_time = NOW - d * DAY + k * 60, eid = eid))
                    eids.append(eid)
        return eids

    def check_whole(self, eids):
        in_db, in_files = [e['eid'] for e in self.live()], self.all_in_files()
        self.assertEqual(len(in_files), len(set(in_files)), 'an event is in the files twice')
        self.assertFalse(set(in_db) & set(in_files), 'an event is both on the page and in a file')
        self.assertEqual(sorted(in_db + in_files), sorted(eids), 'an event was lost')
        spans = self.spans()
        for (a1, b1), (a2, b2) in zip(spans, spans[1:]):
            self.assertLess(b1, a2, 'files %s..%s and %s..%s overlap' % (a1, b1, a2, b2))
        return in_db, in_files

    def test_1_year_then_90_days_makes_no_overlapping_files(self):
        self.settings['keep'] = '365'
        eids = self.seed51()
        self.h.archive(now = NOW)
        self.assertEqual(len(self.files()), 1)
        year = self.files()[0]
        self.settings['keep'] = '90'
        self.h.archive(now = NOW)
        in_db, in_files = self.check_whole(eids)
        # Everything 95-300 days old falls inside the year file's dates, so it went there
        self.assertEqual(self.files(), [year])
        self.assertEqual(len(in_db), 5 * 6 * 4)

    def test_90_days_then_1_year_brings_events_back(self):
        self.settings['keep'] = '90'
        eids = self.seed51()
        self.h.archive(now = NOW)
        self.assertEqual(len(self.live()), 5 * 6 * 4)
        before = len(self.files())
        self.settings['keep'] = '365'
        self.h.restore(now = NOW)
        in_db, in_files = self.check_whole(eids)
        self.assertEqual(len(in_db), 5 * 10 * 4)          # 95-300 days are back on the page
        self.assertEqual(len(in_files), 5 * 2 * 4)        # 370 and 400 stay archived
        self.assertLess(len(self.files()), before)        # files that emptied are gone
        self.assertFalse([e for e in self.h.allEvents() if e.get('archive')])

    def test_restore_turns_an_imported_copy_live(self):
        self.settings['keep'] = '90'
        self.event(100, eid = 'mid')
        self.h.archive(now = NOW)
        name = self.files()[0]
        self.h.importEvents(self.lines(name), name)
        self.assertEqual([e.get('archive') for e in self.h.allEvents()], [name])
        self.settings['keep'] = '365'
        self.h.restore(now = NOW)
        docs = self.h.allEvents()
        self.assertEqual([(e['eid'], e.get('archive')) for e in docs], [('mid', None)])
        self.assertEqual(self.files(), [])


class Seed(Base):
    """ Filling History on upgrade from what the Pi4 really has (notification text copied from it, 2026-11-20) """

    def test_parse_real_messages(self):
        e = parseNotification('Snatched "The Rage (2026) YTS 1080p BR-Rip": The Uprising (2026) in 1080p from Yts')
        self.assertEqual((e['type'], e['title'], e['year'], e['quality'], e['source'], e['detail']),
                         ('snatched', 'The Uprising', 2026, '1080p', 'Yts', 'The Rage (2026) YTS 1080p BR-Rip'))
        e = parseNotification('Snatched "Resident Evil 2026 2026 1080p AMZN WEB-DL DDP5 1 H 264-KyoGo": Resident Evil (2026) in brrip from ThePirateBay')
        self.assertEqual((e['title'], e['quality'], e['source']), ('Resident Evil', 'brrip', 'ThePirateBay'))
        e = parseNotification('Downloaded Brahmāstra Part One: Shiva (1080p)')
        self.assertEqual((e['type'], e['title'], e['quality']), ('moved', 'Brahmāstra Part One: Shiva', '1080p'))
        self.assertEqual(parseNotification('CouchTomato: updated to 8e193854, and it answers.')['type'], 'updated')
        self.assertEqual(parseNotification('CouchTomato: the update to abc was rolled back to def, because x.')['type'], 'rollback')
        self.assertIsNone(parseNotification('ZOMG Lazors Pewpewpew!'))

    def test_seed_from_notifications_and_releases(self):
        odyssey = self.db.insert({'_t': 'media', 'type': 'movie', 'title': 'The Odyssey', 'info': {'year': 2026, 'titles': ['The Odyssey']}, 'identifiers': {'imdb': 'tt1'}})
        wall_e = self.db.insert({'_t': 'media', 'type': 'movie', 'title': 'WALL·E', 'info': {'year': 2008, 'titles': ['WALL·E']}, 'identifiers': {'imdb': 'tt2'}})
        self.db.insert({'_t': 'notification', 'time': NOW - 2 * DAY, 'message': 'Snatched "The Odyssey (2026) YTS 1080p BR-Rip": The Odyssey (2026) in 1080p from Yts'})
        self.db.insert({'_t': 'notification', 'time': NOW - 2 * DAY + 2800, 'message': 'Downloaded The Odyssey (1080p)'})
        self.db.insert({'_t': 'notification', 'time': NOW - DAY, 'message': 'CouchTomato: updated to 8e193854, and it answers.'})
        # The Odyssey's release: its "moved" is already in the notifications, so it is not added twice
        self.db.insert({'_t': 'release', 'media_id': odyssey['_id'], 'status': 'done', 'last_edit': NOW - 2 * DAY + 2810, 'quality': '1080p'})
        # WALL·E finished long before the notifications began (they only last 4 weeks)
        self.db.insert({'_t': 'release', 'media_id': wall_e['_id'], 'status': 'done', 'last_edit': NOW - 60 * DAY, 'quality': '1080p',
                        'info': {'name': 'WALL·E (2008) YTS 1080p BR-Rip', 'provider': 'YTS'}})
        self.db.insert({'_t': 'release', 'media_id': wall_e['_id'], 'status': 'ignored', 'last_edit': NOW - 61 * DAY})

        self.h.seed()
        got = sorted((e['type'], e.get('title')) for e in self.h.allEvents())
        self.assertEqual(got, [('moved', 'The Odyssey'), ('moved', 'WALL·E'), ('snatched', 'The Odyssey'), ('updated', None)])
        snatched = [e for e in self.h.allEvents() if e['type'] == 'snatched'][0]
        self.assertEqual(snatched['identifier'], 'tt1')
        self.assertEqual(snatched['time'], NOW - 2 * DAY)

        # Only once
        self.h.seed()
        self.assertEqual(len(self.h.allEvents()), 4)
        # and even if it ran again, the same ids mean nothing is added twice
        self.assertEqual(self.h.seedFrom(self.db), 0)

class BytesFields(unittest.TestCase):
    """ Pi4 2026-11-23: an event field came back from the database as bytes and the nightly archive crashed """

    def test_write_block_decodes_bytes(self):
        d = tempfile.mkdtemp(prefix = 'ct-history-bytes-')
        try:
            path = os.path.join(d, 'block.jsonl')
            e = {'eid': 'e1', 'time': 1, 'type': 'snatched', 'media_id': b'abc123', 'title': 'Dune'}
            self.assertEqual(history_main.writeBlock(path, [e]), 1)
            with open(path, encoding = 'utf-8') as f:
                self.assertEqual(json.loads(f.readline())['media_id'], 'abc123')
        finally:
            shutil.rmtree(d)



if __name__ == '__main__':
    unittest.main()


"""
Tests for Movie details -> Subtitles (board #95 part 3): the subtitle.search / subtitle.choose APIs in
couchpotato/core/plugins/subtitle.py, and the language matching they rely on.
The fixture is the real yts-subs.com page for Oppenheimer (tt15398776), subtitle table only, 2026-11-25.
Run from the repo root:  python3 -m unittest discover -s tests
"""
import io
import os
import shutil
import sys
import tempfile
import unittest
import zipfile
from unittest import mock

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)
sys.path.insert(0, os.path.join(root, 'libs'))

from couchpotato.core.plugins import subtitle
from couchpotato.core.plugins.subtitle import Subtitle, parseSubtitles, languageCode, languageName, madeFor

FIXTURE = os.path.join(root, 'tests', 'fixtures', 'yts_subs_oppenheimer_2026.html')
SRT_NEW = b'1\r\n00:00:01,000 --> 00:00:02,000\r\nNew\r\n'
SRT_OLD = b'1\r\n00:00:01,000 --> 00:00:02,000\r\nOld\r\n'
YTS_RELEASE = 'Oppenheimer.2023.1080p.BluRay.x264.AAC5.1-[YTS.MX]'


def page():
    with open(FIXTURE) as f:
        return f.read()


def makeZip(data):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        z.writestr('Oppenheimer.srt', data)
    return buf.getvalue()


class LanguageTest(unittest.TestCase):

    def test_site_names_to_codes(self):
        self.assertEqual(languageCode('English'), 'en')
        self.assertEqual(languageCode('Spanish'), 'es')  # subliminal's name is 'Spanish; Castilian'
        self.assertEqual(languageCode('Greek'), 'el')  # 'Greek, Modern (1453-)'
        self.assertEqual(languageCode('Farsi/Persian'), 'fa')
        self.assertEqual(languageCode('Brazillian Portuguese'), 'pt')  # the site's spelling
        self.assertEqual(languageCode('ur'), 'ur')
        self.assertIsNone(languageCode('Klingon'))
        self.assertIsNone(languageCode(''))

    def test_codes_to_names(self):
        self.assertEqual(languageName('es'), 'Spanish')
        self.assertEqual(languageName('el'), 'Greek')
        self.assertEqual(languageName('ur'), 'Urdu')
        self.assertIsNone(languageName('xx'))

    def test_every_language_on_the_page_has_a_code(self):
        self.assertEqual([r['language'] for r in parseSubtitles(page()) if not r['code']], [])

    def test_spanish_rows_are_found_by_code(self):
        # Before: rows were matched to Language('es').name == 'Spanish; Castilian', so Spanish never matched
        rows = parseSubtitles(page(), 'es')
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(r['language'] == 'Spanish' for r in rows))
        self.assertEqual(len(parseSubtitles(page(), 'Spanish')), 4)
        self.assertEqual(parseSubtitles(page(), 'Klingon'), [])

    def test_made_for(self):
        self.assertEqual(madeFor(['Oppenheimer.2023.720p.BluRay.x264.AAC-[YTS.MX]']), 'YIFY')
        self.assertEqual(madeFor(['Oppenheimer.2023.1080p.BluRay.DDP5.1.x264-Kitsune']), 'Kitsune')
        self.assertEqual(madeFor(['Oppenheimer.2023.1080p.MA.WEB-DL.DDP5.1.Atmos.H.264']), 'WEB')
        self.assertEqual(madeFor(['Oppenheimer.2023.720p.BluRay.999MB.x264-GalaxyRG.Sdh']), 'GalaxyRG · SDH')
        self.assertEqual(madeFor([]), '')
        # A YTS name further down the list doesn't make a FraMeSToR subtitle 'made for YIFY'
        self.assertEqual(madeFor(['Oppenheimer.2023.BluRay.1080p.REMUX-FraMeSToR', 'Oppenheimer.2023.720p.BluRay.x264.[YTS.MX]']), 'FraMeSToR, YIFY')


class ApiTest(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.movie = os.path.join(self.dir, 'Oppenheimer (2023).mkv')
        open(self.movie, 'wb').close()

        self.media = {'_id': b'abc123', 'identifiers': {'imdb': 'tt15398776'}, 'title': 'Oppenheimer'}
        self.releases = []
        self.db = mock.Mock()
        self.db.get.side_effect = lambda index, key: self.media
        self.events = []

        def fire(name, *args, **kwargs):
            self.events.append((name, args, kwargs))
            if name == 'release.for_media':
                self.assertEqual(args[0], b'abc123')  # the id as the database gives it, not the API's str
                return self.releases
        patches = [
            mock.patch.object(subtitle, 'get_db', return_value = self.db),
            mock.patch.object(subtitle, 'fireEvent', side_effect = fire),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

        self.plugin = Subtitle.__new__(Subtitle)  # no events or API views
        self.plugin.conf = lambda name, **kw: {'languages': 'en, ur', 'force': False}.get(name)
        self.plugin.getCache = mock.Mock(return_value = page())
        self.plugin.urlopen = mock.Mock(return_value = makeZip(SRT_NEW))

    def tearDown(self):
        shutil.rmtree(self.dir)

    def inLibrary(self):
        self.releases = [{'status': 'done', 'files': {'movie': [self.movie]}, 'info': {'name': YTS_RELEASE}, 'last_edit': 2}]

    def downloading(self):
        self.releases = [{'status': 'snatched', 'files': {}, 'info': {'name': YTS_RELEASE}, 'last_edit': 1}]

    def test_search_lists_english_with_one_match_first(self):
        self.downloading()
        r = self.plugin.searchView(id = 'abc123')
        self.assertTrue(r['success'])
        self.assertEqual(r['language'], 'en')  # first language in Settings
        self.assertEqual(len(r['subtitles']), 24)
        self.assertEqual([s['matches'] for s in r['subtitles']].count(True), 1)
        self.assertTrue(r['subtitles'][0]['matches'])
        self.assertIn('YIFY', r['subtitles'][0]['made_for'])
        self.assertFalse(r['in_library'])
        self.assertIsNone(r['chosen'])
        # Menu: Settings languages first (Urdu even before the site's count), then the rest of the page
        codes = [l['code'] for l in r['languages']]
        self.assertEqual(codes[:2], ['en', 'ur'])
        self.assertIn('ar', codes)
        self.assertEqual(r['languages'][0]['count'], 24)

    def test_search_reads_the_bytes_getcache_really_returns(self):
        # toUnicode(bytes) gave the b'...' repr: literal \n in every name and every rating 0
        self.plugin.getCache.return_value = page().encode('utf-8')
        subs = self.plugin.searchView(id = 'abc123')['subtitles']
        self.assertEqual(len(subs), 24)
        self.assertTrue(any(s['rating'] > 0 for s in subs))
        self.assertFalse(any('\\n' in n for s in subs for n in s['releases']))

    def test_search_a_language_with_nothing(self):
        self.downloading()
        r = self.plugin.searchView(id = 'abc123', language = 'de')
        self.assertEqual(len(r['subtitles']), 1)
        r = self.plugin.searchView(id = 'abc123', language = 'sw')
        self.assertTrue(r['success'])
        self.assertEqual(r['subtitles'], [])
        self.assertEqual(r['language_name'], 'Swahili')
        self.assertEqual(r['languages'][0]['code'], 'sw')  # the asked language stays in the menu

    def test_search_without_a_release_marks_no_match(self):
        r = self.plugin.searchView(id = 'abc123')
        self.assertFalse(any(s['matches'] for s in r['subtitles']))

    def test_choose_while_downloading_only_remembers(self):
        self.downloading()
        r = self.plugin.chooseView(id = 'abc123', language = 'en', slug = 'oppenheimer-2023-english-yify-1')
        self.assertEqual(r, {'success': True, 'saved': False, 'language': 'en', 'slug': 'oppenheimer-2023-english-yify-1', 'filename': None})
        self.assertEqual(self.media['subtitle_choice'], {'en': 'oppenheimer-2023-english-yify-1'})
        self.db.update.assert_called_once_with(self.media)
        self.assertFalse(self.plugin.urlopen.called)
        self.assertEqual(self.plugin.searchView(id = 'abc123')['chosen'], 'oppenheimer-2023-english-yify-1')

    def test_choose_in_library_replaces_and_keeps_a_backup(self):
        self.inLibrary()
        target = os.path.join(self.dir, 'Oppenheimer (2023).en.srt')
        with open(target, 'wb') as f:
            f.write(SRT_OLD)

        r = self.plugin.chooseView(id = 'abc123', language = 'en', slug = 'oppenheimer-2023-english-yify-1')
        self.assertTrue(r['saved'])
        self.assertEqual(r['filename'], 'Oppenheimer (2023).en.srt')
        self.plugin.urlopen.assert_called_once_with(Subtitle.download_url % 'oppenheimer-2023-english-yify-1', show_error = False)
        with open(target, 'rb') as f:
            self.assertEqual(f.read(), SRT_NEW)
        with open(target + '.bak', 'rb') as f:
            self.assertEqual(f.read(), SRT_OLD)

        pushed = [e for e in self.events if e[0] == 'notify.frontend']
        self.assertEqual(len(pushed), 1)
        self.assertEqual(pushed[0][2]['type'], 'subtitle.saved')
        self.assertEqual(pushed[0][2]['data']['media_id'], 'abc123')  # str for the page, not bytes
        self.assertTrue(any(e[0] == 'history.add' for e in self.events))
        self.assertEqual(self.plugin.searchView(id = 'abc123')['has_file'], True)

    def test_choose_fails_cleanly_when_the_download_fails(self):
        self.inLibrary()
        self.plugin.urlopen.side_effect = IOError('down')
        r = self.plugin.chooseView(id = 'abc123', language = 'en', slug = 'oppenheimer-2023-english-yify-1')
        self.assertFalse(r['success'])
        self.assertNotIn('subtitle_choice', self.media)
        self.assertEqual(os.listdir(self.dir), ['Oppenheimer (2023).mkv'])

    def test_choose_rejects_bad_input(self):
        for kw in ({'language': 'en', 'slug': '../../etc'}, {'language': 'Klingon', 'slug': 'x'}, {'language': 'en'}):
            self.assertFalse(self.plugin.chooseView(id = 'abc123', **kw)['success'])
        self.assertFalse(self.db.update.called)

    def test_renamer_uses_the_chosen_subtitle(self):
        self.media['subtitle_choice'] = {'en': 'oppenheimer-2023-english-yify-1'}
        self.plugin.isDisabled = lambda: False
        group = {
            'media': self.media, 'identifier': 'tt15398776', 'dirname': 'Oppenheimer (2023) [1080p] [YTS.MX]',
            'files': {'movie': [self.movie], 'subtitle': []}, 'subtitle_language': {}, 'before_rename': [],
        }
        self.assertTrue(self.plugin.searchSingle(group))
        self.plugin.urlopen.assert_any_call(Subtitle.download_url % 'oppenheimer-2023-english-yify-1', show_error = False)


if __name__ == '__main__':
    unittest.main()

import io
import os
import shutil
import tempfile
import zipfile
from unittest import TestCase, mock

from couchpotato.core.plugins import subtitle
from couchpotato.core.plugins.subtitle import Subtitle, parseSubtitles, matchScore, extractSrt
from subliminal.videos import hash_opensubtitles

FIXTURES = os.path.join(os.path.dirname(__file__), 'fixtures')
OBSESSION_RELEASE = 'Obsession (2025) [720p] [BluRay] [YTS.MX] Obsession.2025.720p.BluRay.x264.AAC-[YTS.MX].mp4'
SRT = b'1\r\n00:00:47,160 --> 00:00:51,060\r\nHello\r\n'


def obsessionPage():
    """ yts-subs.com/movie-imdb/tt37287335, subtitle table only, recorded 2026-10-27 """
    with open(os.path.join(FIXTURES, 'yts_subs_obsession_2026.html')) as f:
        return f.read()


def makeZip(files):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        for name, data in files.items():
            z.writestr(name, data)
    return buf.getvalue()


class ParseTest(TestCase):

    def test_english_rows(self):
        found = parseSubtitles(obsessionPage(), 'English')
        self.assertEqual(len(found), 11)
        self.assertTrue(all(c['slug'].startswith('obsession-2025-english-') for c in found))
        self.assertTrue(all(c['releases'] for c in found))

    def test_other_language_and_empty_page(self):
        self.assertTrue(parseSubtitles(obsessionPage(), 'Arabic'))
        self.assertEqual(parseSubtitles(obsessionPage(), 'Klingon'), [])
        self.assertEqual(parseSubtitles('', 'English'), [])

    def test_picks_the_subtitle_made_for_the_yts_720p_release(self):
        found = parseSubtitles(obsessionPage(), 'English')
        best = max(found, key = lambda c: matchScore(c, OBSESSION_RELEASE))
        self.assertEqual(best['slug'], 'obsession-2025-english-yify-2162652')
        self.assertIn('720p', best['releases'][0])


class ExtractTest(TestCase):

    def test_largest_srt(self):
        data = makeZip({'readme.txt': b'x' * 5000, 'small.srt': b'1', 'Movie-English.srt': SRT})
        self.assertEqual(extractSrt(data), SRT)

    def test_no_srt(self):
        self.assertIsNone(extractSrt(makeZip({'readme.txt': b'x'})))


class HashTest(TestCase):

    def test_opensubtitles_hash_on_python3(self):
        # 65536 / 8 is a float in Python 3: range() raised TypeError, which made every subtitle scan fail
        with tempfile.NamedTemporaryFile(suffix = '.mkv') as f:
            f.write(b'\x01' * 200000)
            f.flush()
            self.assertRegex(hash_opensubtitles(f.name), r'^[0-9a-f]{16}$')


class SearchSingleTest(TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.movie = os.path.join(self.dir, 'Obsession.2025.720p.BluRay.x264.AAC-[YTS.MX].mp4')
        open(self.movie, 'wb').close()

        self.plugin = Subtitle.__new__(Subtitle)  # skip __init__: no events or API views
        self.plugin.isDisabled = lambda: False
        self.plugin.conf = lambda name, **kw: {'languages': 'en', 'force': False}.get(name)
        self.plugin.getCache = mock.Mock(return_value = obsessionPage())
        self.plugin.urlopen = mock.Mock(return_value = makeZip({'Obsession-English.srt': SRT}))

    def tearDown(self):
        shutil.rmtree(self.dir)

    def group(self, languages = None):
        return {
            'identifier': 'tt37287335',
            'dirname': 'Obsession (2025) [720p] [BluRay] [YTS.MX]',
            'files': {'movie': [self.movie], 'subtitle': []},
            'subtitle_language': languages or {},
            'before_rename': [],
        }

    def test_downloads_english_next_to_the_movie(self):
        group = self.group()
        self.assertTrue(self.plugin.searchSingle(group))

        target = os.path.splitext(self.movie)[0] + '.en.srt'
        with open(target, 'rb') as f:
            self.assertEqual(f.read(), SRT)
        self.assertEqual(group['files']['subtitle'], [target])
        self.assertEqual(group['before_rename'], [target])
        self.assertEqual(group['subtitle_language'][target], ['en'])  # so the renamer names it "<movie>.en.srt"
        self.plugin.urlopen.assert_called_once_with(subtitle.Subtitle.download_url % 'obsession-2025-english-yify-2162652', show_error = False)

    def test_skips_a_language_the_release_already_has(self):
        group = self.group({'/x/Obsession.srt': ['en']})
        self.plugin.searchSingle(group)
        self.assertFalse(self.plugin.urlopen.called)
        self.assertEqual(group['files']['subtitle'], [])

    def test_nothing_found_or_site_down_changes_nothing(self):
        self.plugin.getCache.return_value = None
        group = self.group()
        self.assertTrue(self.plugin.searchSingle(group))
        self.assertEqual(group['files']['subtitle'], [])
        self.assertEqual(os.listdir(self.dir), [os.path.basename(self.movie)])

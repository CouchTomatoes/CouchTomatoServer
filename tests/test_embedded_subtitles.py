"""
Tests for embedded subtitle detection (libs/enzyme + libs/subliminal), used by the subtitle
backfill to skip movies that already carry a subtitle. enzyme.parse used Python 2's
__import__(level=-1) and ord() on bytes, so on Python 3 it always failed and every MKV looked
subtitle-free (board #42). The fixtures are 2-second MKVs made with ffmpeg.
Run from the repo root:  python3 -m unittest discover -s tests
"""
import os
import sys
import unittest

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)
sys.path.insert(0, os.path.join(root, 'libs'))

import enzyme
from subliminal.subtitles import EmbeddedSubtitle
from subliminal.videos import Video

fixtures = os.path.join(root, 'tests', 'fixtures')


class EmbeddedSubtitleTest(unittest.TestCase):

    def embedded(self, name):
        return [s for s in Video.from_path(os.path.join(fixtures, name)).scan() if isinstance(s, EmbeddedSubtitle)]

    def test_enzyme_parses_mkv(self):
        mkv = enzyme.parse(os.path.join(fixtures, 'embedded-text-eng.mkv'))
        self.assertEqual([s.language for s in mkv.subtitles], ['eng'])

    def test_text_track_counts(self):
        subs = self.embedded('embedded-text-eng.mkv')
        self.assertEqual([s.language.alpha2 for s in subs], ['en'])
        self.assertTrue(subs[0].is_text)

    def test_image_track_is_not_text(self):
        # VobSub/PGS: Plex has to burn these in, so the backfill still adds an .srt
        subs = self.embedded('embedded-image-eng.mkv')
        self.assertEqual([s.language.alpha2 for s in subs], ['en'])
        self.assertFalse(subs[0].is_text)


if __name__ == '__main__':
    unittest.main()

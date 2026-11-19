"""
Tests for subtitleTagsFromName in couchpotato/core/plugins/renamer.py: subtitles the scanner
can't place next to the movie (a Subs/ folder of "English.srt", "SDH.eng.srt", ...) used to
all be renamed to the same "<movie>.srt", so all but one ended up as "<movie>.srt.random-XXXX".
Run from the repo root:  python3 -m unittest discover -s tests
"""
import os
import sys
import unittest

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)
sys.path.insert(0, os.path.join(root, 'libs'))

from couchpotato.core.plugins.renamer import subtitleTagsFromName


class SubtitleTagsFromNameTest(unittest.TestCase):

    def test_subs_folder_names_seen_on_the_pi4(self):
        # The exact files that collided on 2026-11-07 (The Rage / The Uprising)
        self.assertEqual(subtitleTagsFromName('/dl/The Rage (2026)/Subs/English.srt'), ['en'])
        self.assertEqual(subtitleTagsFromName('/dl/The Rage (2026)/Subs/SDH.eng.srt'), ['en', 'sdh'])
        self.assertEqual(subtitleTagsFromName('/dl/The Rage (2026)/Subs/Canadian.fre.srt'), ['fr'])

    def test_they_no_longer_collide(self):
        names = ['English.srt', 'SDH.eng.srt', 'Canadian.fre.srt']
        tags = ['.'.join(subtitleTagsFromName(n)) for n in names]
        self.assertEqual(len(set(tags)), 3)

    def test_release_name_without_language(self):
        self.assertEqual(subtitleTagsFromName('The.Rage.2026.1080p.WEBRip.x265.10bit.AAC5.1-[YTS.GG - YTS.BZ].srt'), [])

    def test_short_words_in_a_title_are_not_languages(self):
        # "It" / "Up" are ISO codes but only count as the last token
        self.assertEqual(subtitleTagsFromName('It.Follows.2014.1080p.srt'), [])
        self.assertEqual(subtitleTagsFromName('Up.2009.720p.BluRay.srt'), [])

    def test_trailing_code(self):
        self.assertEqual(subtitleTagsFromName('Movie.2020.1080p.es.srt'), ['es'])
        self.assertEqual(subtitleTagsFromName('Movie.2020.1080p.English.forced.srt'), ['en', 'forced'])


if __name__ == '__main__':
    unittest.main()

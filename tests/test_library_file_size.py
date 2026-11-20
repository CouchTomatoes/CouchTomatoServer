"""
Tests for libraryFileSize in couchpotato/core/plugins/release/main.py: the renamer's 'done'
release row only stores file paths, so the movie page's releases table showed Size 'n/a'.
Run from the repo root:  python3 -m unittest discover -s tests
"""
import os
import sys
import tempfile
import unittest

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)
sys.path.insert(0, os.path.join(root, 'libs'))

from couchpotato.core.plugins.release.main import libraryFileSize


class LibraryFileSizeTest(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.movie = os.path.join(self.dir, 'The Odyssey (2026).mkv')
        with open(self.movie, 'wb') as f:
            f.truncate(3 * 1048576)

    def test_done_row_gets_the_movie_file_size(self):
        release = {'status': 'done', 'files': {'movie': [self.movie], 'subtitle': ['/x.srt']}}
        self.assertEqual(libraryFileSize(release), 3.0)

    def test_missing_file_gives_none_not_an_error(self):
        release = {'status': 'done', 'files': {'movie': [os.path.join(self.dir, 'gone.mkv')]}}
        self.assertIsNone(libraryFileSize(release))

    def test_rows_without_files(self):
        self.assertIsNone(libraryFileSize({'status': 'available', 'info': {'size': 1400}}))
        self.assertIsNone(libraryFileSize({'files': []}))


if __name__ == '__main__':
    unittest.main()

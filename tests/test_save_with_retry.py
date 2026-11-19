"""
Tests for saveWithRetry in couchpotato/core/media/movie/_base/main.py, against the real
codernitydb3 engine. movie.update and updateReleaseDate read a movie, fetch info from the
network for seconds, then saved the revision they had read: if anything saved the movie
meanwhile, that raised RevConflict and the update was lost (board #36).
Run from the repo root:  python3 -m unittest discover -s tests
"""
import os
import shutil
import sys
import tempfile
import unittest

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)
sys.path.insert(0, os.path.join(root, 'libs'))

from CodernityDB.database import Database, RevConflict
from couchpotato.core.media.movie._base.main import saveWithRetry


class SaveWithRetryTest(unittest.TestCase):

    def setUp(self):
        self.path = tempfile.mkdtemp()
        self.db = Database(os.path.join(self.path, 'db'))
        self.db.create()
        self.media_id = self.db.insert({'_t': 'media', 'title': 'The Matrix', 'info': {}})['_id']

    def tearDown(self):
        self.db.close()
        shutil.rmtree(self.path)

    def someone_else_saves(self):
        other = self.db.get('id', self.media_id)
        other['status'] = 'active'
        self.db.update(other)

    def test_stale_write_conflicts(self):
        # What the old code did: write back the copy read before the slow fetch
        stale = self.db.get('id', self.media_id)
        self.someone_else_saves()
        stale['info'] = {'year': 1999}
        self.assertRaises(RevConflict, self.db.update, stale)

    def test_save_with_retry_keeps_both_changes(self):
        self.db.get('id', self.media_id)
        self.someone_else_saves()

        saveWithRetry(self.db, self.media_id, lambda doc: doc.update({'info': {'year': 1999}}))

        saved = self.db.get('id', self.media_id)
        self.assertEqual(saved['info'], {'year': 1999})
        self.assertEqual(saved['status'], 'active')


if __name__ == '__main__':
    unittest.main()

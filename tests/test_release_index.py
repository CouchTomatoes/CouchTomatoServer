"""
The 'release' tree index (release.for_media) on a real CodernityDB: a str media id used to crash the tree search with
"'<' not supported between instances of 'str' and 'bytes'", so "Try another release" (movie.searcher.try_next) and the
renamer's automatic retry failed. Needs enough releases for the tree to split into several nodes.
Run from the repo root:  PYTHONHASHSEED=0 python3 -m unittest discover -s tests
"""
import os
import shutil
import sys
import tempfile
import unittest
import uuid

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)
sys.path.insert(0, os.path.join(root, 'libs'))

from CodernityDB.database import Database

from couchpotato.core.plugins.release.index import ReleaseIndex


class ReleaseIndexTest(unittest.TestCase):

    def setUp(self):
        self.path = tempfile.mkdtemp()
        self.db = Database(os.path.join(self.path, 'db'))
        self.db.create()
        self.db.add_index(ReleaseIndex(self.db.path, 'release'))

        self.media_ids = [uuid.uuid4().hex for _ in range(60)]
        for media_id in self.media_ids:
            for nr in range(5):
                self.db.insert({'_t': 'release', 'media_id': media_id, 'identifier': '%s-%s' % (media_id, nr)})

    def tearDown(self):
        self.db.close()
        shutil.rmtree(self.path)

    def test_str_media_id_finds_its_releases(self):
        for media_id in (self.media_ids[0], self.media_ids[31], self.media_ids[-1]):
            found = list(self.db.get_many('release', media_id))
            self.assertEqual(len(found), 5, media_id)

    def test_bytes_media_id_still_works(self):
        found = list(self.db.get_many('release', self.media_ids[7].encode('utf-8')))
        self.assertEqual(len(found), 5)

    def test_unknown_media_id_finds_nothing(self):
        self.assertEqual(list(self.db.get_many('release', uuid.uuid4().hex)), [])


OLD_INDEX = '''
from CodernityDB.tree_index import TreeBasedIndex


class ReleaseIndex(TreeBasedIndex):
    _version = 1

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = '32s'
        super(ReleaseIndex, self).__init__(*args, **kwargs)

    def make_key(self, key):
        return key

    def make_key_value(self, data):
        return None
'''


class IndexUpgradeInSameRunTest(unittest.TestCase):
    """couchpotato/core/database.py upgrades an index (destroy + add) right after opening the DB. codernitydb3 used to
    build the new index from the class it had already loaded, so the upgrade only worked after a second restart."""

    def setUp(self):
        self.path = tempfile.mkdtemp()
        old_file = os.path.join(self.path, 'old_release_index.py')
        with open(old_file, 'w') as f:
            f.write(OLD_INDEX)
        import importlib.util
        spec = importlib.util.spec_from_file_location('old_release_index', old_file)
        self.old = importlib.util.module_from_spec(spec)
        sys.modules['old_release_index'] = self.old
        spec.loader.exec_module(self.old)

    def tearDown(self):
        sys.modules.pop('old_release_index', None)
        shutil.rmtree(self.path)

    def test_upgraded_index_runs_new_code_without_restart(self):
        db = Database(os.path.join(self.path, 'db'))
        db.create()
        db.add_index(self.old.ReleaseIndex(db.path, 'release'))
        db.close()

        db = Database(os.path.join(self.path, 'db'))
        db.open()
        self.assertEqual(db.indexes_names['release']._version, 1)

        db.destroy_index(db.indexes_names['release'])
        db.add_index(ReleaseIndex(db.path, 'release'))
        db.reindex_index('release')

        upgraded = db.indexes_names['release']
        self.assertEqual(upgraded._version, 2)
        self.assertEqual(upgraded.make_key('a' * 32), b'a' * 32)
        db.close()


if __name__ == '__main__':
    unittest.main()

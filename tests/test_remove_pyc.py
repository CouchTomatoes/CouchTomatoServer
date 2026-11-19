"""
Tests for removePyc in couchpotato/core/helpers/variable.py (runs at every start): it must keep
Python 3 __pycache__ files whose .py still exists, drop orphans, and never touch .git.
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

from couchpotato.core.helpers.variable import removePyc


def touch(path):
    os.makedirs(os.path.dirname(path), exist_ok = True)
    open(path, 'w').close()


class RemovePycTest(unittest.TestCase):

    def setUp(self):
        self.app = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.app)

    def test_keeps_live_cache_and_drops_orphans(self):
        touch(os.path.join(self.app, 'pkg', 'alive.py'))
        live = os.path.join(self.app, 'pkg', '__pycache__', 'alive.cpython-311.pyc')
        orphan = os.path.join(self.app, 'pkg', '__pycache__', 'gone.cpython-311.pyc')
        touch(live)
        touch(orphan)

        removePyc(self.app, show_logs = False)

        self.assertTrue(os.path.isfile(live))
        self.assertFalse(os.path.isfile(orphan))

    def test_leaves_git_alone(self):
        refs = os.path.join(self.app, '.git', 'refs', 'tags')
        os.makedirs(refs)

        removePyc(self.app, show_logs = False)

        self.assertTrue(os.path.isdir(refs))


if __name__ == '__main__':
    unittest.main()

"""
Tests for the updater inside the official Docker image (2026-11-24).

The code is part of the image, so a self-update would be lost on the next container re-create.
Inside Docker (COUCHTOMATO_DOCKER=1) the app uses DockerUpdater: it reads the commit baked in at
build time, still checks GitHub, never overwrites itself, and tells the user to pull the new image.

Run from the repo root:  python3 -m unittest discover -s tests
"""
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)
sys.path.insert(0, os.path.join(root, 'libs'))

from couchpotato.core._base.updater import main as updater


class DockerUpdaterTest(unittest.TestCase):

    def baked(self, data):
        f = tempfile.NamedTemporaryFile('w', suffix = '.json', delete = False)
        json.dump(data, f)
        f.close()
        self.addCleanup(os.remove, f.name)
        return f.name

    def make(self, data):
        path = self.baked(data)
        with mock.patch.object(updater.DockerUpdater, 'baked_file', path):
            return updater.DockerUpdater()

    def test_baked_file_is_at_the_app_root(self):
        self.assertEqual(updater.DockerUpdater.baked_file, os.path.join(root, 'docker-version.json'))

    def test_version_comes_from_the_baked_commit(self):
        d = self.make({'hash': 'abcdef1234567890', 'date': 1795562184})
        v = d.getVersion()
        self.assertEqual(v['type'], 'docker')
        self.assertEqual(v['hash'], 'abcdef1234567890')
        self.assertTrue(v['repr'].startswith('docker:(CouchTomatoes:CouchTomatoServer main) abcdef12'), v['repr'])

    def test_never_overwrites_itself(self):
        d = self.make({'hash': 'a', 'date': 1})
        with mock.patch.object(updater.SourceUpdater, 'replaceWith') as replace:
            self.assertFalse(d.doUpdate())
        replace.assert_not_called()
        self.assertFalse(d.can_update)

    def test_still_finds_a_newer_release(self):
        d = self.make({'hash': 'old', 'date': 100})
        with mock.patch.object(d, 'latestCommit', return_value = {'hash': 'new', 'date': 200}):
            self.assertTrue(d.check())
        self.assertEqual(d.update_version['hash'], 'new')

    def test_automatic_is_off_and_the_notice_says_how_to_update(self):
        u = updater.Updater.__new__(updater.Updater)   # skip __init__: it registers events and crons
        u.updater = self.make({'hash': 'old', 'date': 100})
        u.available_notified = False
        conf = {'automatic': True, 'notification': True, 'enabled': True}
        with mock.patch.object(updater.Updater, 'conf', side_effect = lambda k, **kw: conf.get(k)), \
                mock.patch.object(updater.Updater, 'isDisabled', return_value = False), \
                mock.patch.object(u.updater, 'latestCommit', return_value = {'hash': 'new', 'date': 200}), \
                mock.patch.object(updater, 'fireEvent') as fire:
            self.assertFalse(u.automatic())
            self.assertTrue(u.check())
        message = fire.call_args[1]['message']
        self.assertIn('docker compose pull', message)

    def test_chosen_only_inside_docker(self):
        with open(os.path.join(root, 'couchpotato', 'core', '_base', 'updater', 'main.py')) as f:
            src = f.read()
        self.assertIn("os.environ.get('COUCHTOMATO_DOCKER')", src)
        with open(os.path.join(root, 'Dockerfile')) as f:
            dockerfile = f.read()
        self.assertIn('COUCHTOMATO_DOCKER=1', dockerfile)
        self.assertIn('GIT_PYTHON_REFRESH=quiet', dockerfile)   # no git in the image; GitPython must still import


if __name__ == '__main__':
    unittest.main()

"""
Tests for the updater's repo and its daily check (2026-11-19).

- Source installs downloaded and compared against the dead upstream CouchPotato/CouchPotatoServer on
  `master`, and asked the CouchTomato API for the download link. They now use this repo's `main` and
  build GitHub's tarball link themselves.
- The git updater's daily check logged only "Checking for new version" and then nothing when there was
  nothing new, which read like a stuck updater. It now says "Up to date" or "New version".

Run from the repo root:  python3 -m unittest discover -s tests
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)
sys.path.insert(0, os.path.join(root, 'libs'))

import git
import version
from couchpotato.core._base.updater import main as updater
from couchpotato.environment import Env


def run(cwd, *args):
    subprocess.run(['git', '-c', 'user.name=t', '-c', 'user.email=t@t', '-c', 'commit.gpgsign=false'] + list(args),
                   cwd = cwd, check = True, capture_output = True)


class RepoTest(unittest.TestCase):

    def test_points_at_this_repo_on_main(self):
        self.assertEqual((updater.BaseUpdater.repo_user, updater.BaseUpdater.repo_name), ('CouchTomatoes', 'CouchTomatoServer'))
        self.assertEqual(version.BRANCH, 'main')

    def test_source_url_is_built_in_the_app(self):
        source = updater.SourceUpdater.__new__(updater.SourceUpdater)  # skip __init__: it fetches from GitHub
        self.assertEqual(source.sourceUrl(), {
            'url': 'https://codeload.github.com/CouchTomatoes/CouchTomatoServer/tar.gz/main',
            'type': 'tar.gz',
        })

    def test_no_longer_asks_the_api(self):
        with open(os.path.join(root, 'couchpotato', 'core', '_base', 'updater', 'main.py')) as f:
            self.assertNotIn('cp.source_url', f.read())


class GitCheckTest(unittest.TestCase):
    """ A real git checkout with a real 'origin' on disk, driven the way the daily check drives it. """

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.origin = os.path.join(self.tmp, 'origin.git')
        self.work = os.path.join(self.tmp, 'work')      # where commits are made and pushed
        self.app = os.path.join(self.tmp, 'app')        # the install being updated
        run(self.tmp, 'init', '-q', '--bare', '-b', 'main', self.origin)
        run(self.tmp, 'clone', '-q', self.origin, self.work)
        run(self.work, 'checkout', '-q', '-b', 'main')
        self.commit('first', 1700000000)
        run(self.tmp, 'clone', '-q', '-b', 'main', self.origin, self.app)

        self.get = mock.patch.object(Env, 'get', side_effect = lambda key, *a, **k: {'app_dir': self.app, 'dev': False}.get(key))
        self.get.start()

        self.updater = updater.GitUpdater.__new__(updater.GitUpdater)  # skip __init__: no settings/events
        self.updater.repo = git.Repo(self.app)
        self.updater.update_version = None

    def tearDown(self):
        self.get.stop()
        shutil.rmtree(self.tmp, ignore_errors = True)

    def commit(self, name, when):
        with open(os.path.join(self.work, name), 'w') as f:
            f.write(name)
        run(self.work, 'add', name)
        env = dict(os.environ, GIT_AUTHOR_DATE = '%d +0000' % when, GIT_COMMITTER_DATE = '%d +0000' % when)
        subprocess.run(['git', '-c', 'user.name=t', '-c', 'user.email=t@t', '-c', 'commit.gpgsign=false',
                        'commit', '-q', '-m', name], cwd = self.work, env = env, check = True)
        run(self.work, 'push', '-q', 'origin', 'main')

    def test_up_to_date_says_so(self):
        with mock.patch.object(updater.log, 'info') as info:
            self.assertFalse(self.updater.check())
        said = [c.args[0] for c in info.call_args_list]
        self.assertTrue(any(s.startswith('Up to date') for s in said), said)

    def test_new_commit_on_origin_is_found(self):
        self.assertFalse(self.updater.check())
        self.commit('second', 1700086400)
        head = git.Repo(self.work).head.commit.hexsha[:8]

        with mock.patch.object(updater.log, 'info') as info:
            self.assertTrue(self.updater.check())
        self.assertEqual(self.updater.update_version['hash'], head)
        said = [c.args[0] for c in info.call_args_list]
        self.assertTrue(any(s.startswith('New version') for s in said), said)


if __name__ == '__main__':
    unittest.main()

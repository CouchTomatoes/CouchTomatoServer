"""
Tests for update_guard.py, the rollback safety net of the git updater.

Each test builds a throwaway git repo with two commits (the version before an update and
the update itself) and drives the guard the way CouchPotato.py and the updater do.
Run from the repo root:  python3 -m unittest discover -s tests
"""
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import update_guard


def git(repo, *args):
    return subprocess.run(['git', '-C', repo, '-c', 'user.name=t', '-c', 'user.email=t@t'] + list(args),
                          check = True, capture_output = True, text = True).stdout.strip()


class UpdateGuardTest(unittest.TestCase):

    def setUp(self):
        self.app = tempfile.mkdtemp(prefix = 'ct-guard-')
        git(self.app, 'init', '-q', '-b', 'main')
        self.write('version.txt', 'old')
        git(self.app, 'add', '-A')
        git(self.app, 'commit', '-qm', 'before the update')
        self.previous = git(self.app, 'rev-parse', 'HEAD')
        self.write('version.txt', 'new')
        git(self.app, 'commit', '-qam', 'the update')
        self.current = git(self.app, 'rev-parse', 'HEAD')

        self.confirm_seconds = update_guard.CONFIRM_SECONDS
        update_guard.CONFIRM_SECONDS = 3600  # keep the watchdog asleep unless a test wants it

    def tearDown(self):
        update_guard.CONFIRM_SECONDS = self.confirm_seconds
        shutil.rmtree(self.app, ignore_errors = True)

    def write(self, name, text):
        with open(os.path.join(self.app, name), 'w') as f:
            f.write(text)

    def read(self, name):
        with open(os.path.join(self.app, name)) as f:
            return f.read()

    def test_no_pending_update_does_nothing(self):
        update_guard.on_start(self.app, [])
        self.assertEqual(git(self.app, 'rev-parse', 'HEAD'), self.current)
        self.assertIsNone(update_guard.pending(self.app))

    def test_rolls_back_after_max_boots_without_confirmation(self):
        update_guard.mark_pending(self.app, self.previous, self.current, False)

        for boot in range(update_guard.MAX_BOOTS):
            update_guard.on_start(self.app, [])
            self.assertEqual(git(self.app, 'rev-parse', 'HEAD'), self.current, 'rolled back too early, at boot %d' % (boot + 1))
            self.assertEqual(update_guard.pending(self.app)['boots'], boot + 1)

        update_guard.on_start(self.app, [])

        self.assertEqual(git(self.app, 'rev-parse', 'HEAD'), self.previous)
        self.assertEqual(self.read('version.txt'), 'old')
        self.assertIsNone(update_guard.pending(self.app))
        self.assertTrue(update_guard.is_bad(self.app, self.current))

        note = update_guard.take_rollback(self.app)
        self.assertEqual(note['version'], self.current)
        self.assertEqual(note['previous'], self.previous)
        self.assertIn('did not start', note['reason'])
        self.assertIsNone(update_guard.take_rollback(self.app), 'the note is reported once')

    def test_confirmed_update_stays(self):
        update_guard.mark_pending(self.app, self.previous, self.current, False)
        update_guard.on_start(self.app, [])

        state = update_guard.confirm(self.app)

        self.assertEqual(state['version'], self.current)
        self.assertIsNone(update_guard.pending(self.app))
        for i in range(update_guard.MAX_BOOTS + 1):
            update_guard.on_start(self.app, [])
        self.assertEqual(git(self.app, 'rev-parse', 'HEAD'), self.current)
        self.assertFalse(update_guard.is_bad(self.app, self.current))

    def test_head_moved_by_hand_drops_the_pending_update(self):
        update_guard.mark_pending(self.app, self.previous, self.current, False)
        git(self.app, 'reset', '-q', '--hard', self.previous)

        update_guard.on_start(self.app, [])

        self.assertIsNone(update_guard.pending(self.app))
        self.assertIsNone(update_guard.take_rollback(self.app))
        self.assertFalse(update_guard.is_bad(self.app, self.current))

    def test_watchdog_rolls_back_a_start_that_never_confirms(self):
        update_guard.mark_pending(self.app, self.previous, self.current, False)
        update_guard.CONFIRM_SECONDS = 0.5
        restarted = threading.Event()
        real_execv = update_guard.os.execv
        update_guard.os.execv = lambda *args: restarted.set()
        try:
            update_guard.on_start(self.app, ['CouchPotato.py'])
            self.assertTrue(restarted.wait(10), 'the watchdog never re-executed')
        finally:
            update_guard.os.execv = real_execv

        self.assertEqual(git(self.app, 'rev-parse', 'HEAD'), self.previous)
        self.assertIn('no healthy reply within', update_guard.take_rollback(self.app)['reason'])

    def test_watchdog_leaves_a_confirmed_update_alone(self):
        update_guard.mark_pending(self.app, self.previous, self.current, False)
        update_guard.CONFIRM_SECONDS = 0.5
        restarted = threading.Event()
        real_execv = update_guard.os.execv
        update_guard.os.execv = lambda *args: restarted.set()
        try:
            update_guard.on_start(self.app, ['CouchPotato.py'])
            update_guard.confirm(self.app)
            self.assertFalse(restarted.wait(2), 'the watchdog re-executed after a confirmation')
        finally:
            update_guard.os.execv = real_execv

        self.assertEqual(git(self.app, 'rev-parse', 'HEAD'), self.current)

    def test_failed_pip_install_is_reported(self):
        self.write('requirements.txt', 'this is !! not a requirement\n')
        self.assertFalse(update_guard.install_requirements(self.app))

    def test_bad_version_is_remembered(self):
        self.assertFalse(update_guard.is_bad(self.app, self.current))
        update_guard.mark_bad(self.app, self.current)
        self.assertTrue(update_guard.is_bad(self.app, self.current))
        self.assertFalse(update_guard.is_bad(self.app, self.previous))

    def test_install_without_git_is_left_alone(self):
        plain = tempfile.mkdtemp(prefix = 'ct-guard-plain-')
        try:
            update_guard.on_start(plain, [])
            self.assertIsNone(update_guard.pending(plain))
            self.assertIsNone(update_guard.confirm(plain))
            self.assertIsNone(update_guard.take_rollback(plain))
        finally:
            shutil.rmtree(plain, ignore_errors = True)

    def test_durations_read_naturally(self):
        self.assertEqual(update_guard._duration(40), '40 seconds')
        self.assertEqual(update_guard._duration(600), '10 minutes')


if __name__ == '__main__':
    unittest.main()

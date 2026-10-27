"""
Keeps an automatic update from leaving the app unable to start.

The git updater pulls `main` and restarts. Before the restart it records the update as
pending (the previous and the new commit) in the clone's .git directory. CouchPotato.py
calls on_start() before it imports anything from the app, so this still runs when the
new code can't even be imported:

- each start of the new version counts as a boot; after MAX_BOOTS starts that never
  confirmed (the app crashed and systemd restarted it), roll back to the previous commit;
- a watchdog rolls back and re-executes when a start doesn't confirm within
  CONFIRM_SECONDS (the app came up but hangs);
- the app confirms once its own API answers over HTTP (Updater.confirmUpdate).

A rolled-back commit is remembered, so the daily check doesn't install it again.
Standard library only, on purpose: the code it guards may be what's broken.
"""
import json
import os
import subprocess
import sys
import threading
import time

PENDING = 'couchtomato-update.json'
ROLLED_BACK = 'couchtomato-rollback.json'
BAD_VERSION = 'couchtomato-bad-version'

MAX_BOOTS = 3
CONFIRM_SECONDS = 600


def _git_dir(app_dir):
    path = os.path.join(app_dir, '.git')
    return path if os.path.isdir(path) else None


def _read(app_dir, name):
    git_dir = _git_dir(app_dir)
    try:
        with open(os.path.join(git_dir, name)) as f:
            return json.load(f)
    except Exception:
        return None


def _write(app_dir, name, data):
    path = os.path.join(_git_dir(app_dir), name)
    with open(path + '.tmp', 'w') as f:
        json.dump(data, f)
    os.replace(path + '.tmp', path)


def _remove(app_dir, name):
    try:
        os.remove(os.path.join(_git_dir(app_dir), name))
    except OSError:
        pass


def _git(app_dir, *args):
    return subprocess.run(['git', '-C', app_dir] + list(args), check = True, capture_output = True, text = True).stdout.strip()


def head(app_dir):
    return _git(app_dir, 'rev-parse', 'HEAD')


def install_requirements(app_dir):
    """ pip install -r requirements.txt into the interpreter running the app. True when it worked. """
    try:
        p = subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', '-r', os.path.join(app_dir, 'requirements.txt')],
                           capture_output = True, text = True, timeout = 1800)
        if p.returncode != 0:
            sys.stderr.write('update_guard: pip install failed:\n%s\n' % p.stderr[-2000:])
        return p.returncode == 0
    except Exception as e:
        sys.stderr.write('update_guard: pip install failed: %s\n' % e)
        return False


def mark_pending(app_dir, previous, version, requirements_changed):
    _write(app_dir, PENDING, {
        'previous': previous,
        'version': version,
        'requirements_changed': requirements_changed,
        'updated_at': time.time(),
        'boots': 0,
    })


def mark_bad(app_dir, version):
    with open(os.path.join(_git_dir(app_dir), BAD_VERSION), 'w') as f:
        f.write(version)


def is_bad(app_dir, version):
    try:
        with open(os.path.join(_git_dir(app_dir), BAD_VERSION)) as f:
            return f.read().strip() == version
    except OSError:
        return False


def rollback(app_dir, state, reason):
    """ Go back to the commit before the update, and leave a note for the app to report. """
    _git(app_dir, 'reset', '--hard', state['previous'])
    if state.get('requirements_changed'):
        install_requirements(app_dir)
    mark_bad(app_dir, state['version'])
    _write(app_dir, ROLLED_BACK, {
        'version': state['version'],
        'previous': state['previous'],
        'reason': reason,
        'at': time.time(),
    })
    _remove(app_dir, PENDING)


def pending(app_dir):
    """ The update waiting for its first healthy start, or None. """
    return _read(app_dir, PENDING) if _git_dir(app_dir) else None


def confirm(app_dir):
    """ The new version answered: the update stands. Returns the pending record, or None. """
    if not _git_dir(app_dir):
        return None
    state = _read(app_dir, PENDING)
    _remove(app_dir, PENDING)
    return state


def take_rollback(app_dir):
    """ The note left by a rollback, removed once read. None when there wasn't one. """
    if not _git_dir(app_dir):
        return None
    note = _read(app_dir, ROLLED_BACK)
    _remove(app_dir, ROLLED_BACK)
    return note


def on_start(app_dir, argv):
    """ Called by CouchPotato.py before the app is imported. argv re-executes this process. """
    if not _git_dir(app_dir):
        return

    state = _read(app_dir, PENDING)
    if not state:
        return

    try:
        if head(app_dir) != state['version']:
            # HEAD moved by hand since the update; nothing of ours to guard
            _remove(app_dir, PENDING)
            return

        state['boots'] = state.get('boots', 0) + 1
        _write(app_dir, PENDING, state)

        if state['boots'] > MAX_BOOTS:
            rollback(app_dir, state, 'it did not start (%d attempts)' % MAX_BOOTS)
            return
    except Exception as e:
        sys.stderr.write('update_guard: %s\n' % e)
        return

    def watchdog():
        time.sleep(CONFIRM_SECONDS)
        current = _read(app_dir, PENDING)
        if current and current.get('version') == state['version']:
            try:
                rollback(app_dir, current, 'no healthy reply within %d minutes' % (CONFIRM_SECONDS // 60))
            except Exception as e:
                sys.stderr.write('update_guard: rollback failed: %s\n' % e)
                return
            os.execv(sys.executable, [sys.executable] + argv)

    t = threading.Thread(target = watchdog, name = 'update_guard')
    t.daemon = True
    t.start()

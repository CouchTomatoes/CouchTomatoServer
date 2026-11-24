"""
History: what happened to your movies (added, snatched, downloaded, moved, replaced, failed, subtitles) and to the
app (updated, rolled back, signed in), shown on the History page as a dated timeline.

Keeping it small: with "Keep history" at 90 days (or 1 year), a nightly job moves events older than that into a
plain-text archive file, one per 90-day (or 1-year) block, and only then removes them from the database. Import puts
a file's events back on the page, tagged with the file's name; importing twice adds nothing twice.
"""
import datetime
import json
import os
import re
import threading
import time
import traceback
import uuid

from couchpotato import get_db
from couchpotato.api import addApiView
from couchpotato.core.event import addEvent, fireEvent
from couchpotato.core.helpers.encoding import toUnicode
from couchpotato.core.helpers.variable import tryInt, getTitle, getIdentifier
from couchpotato.core.logger import CPLog
from couchpotato.core.plugins.base import Plugin
from couchpotato.environment import Env
from .index import HistoryIndex, HistoryEventIndex


log = CPLog(__name__)

TYPES = ['added', 'snatched', 'downloaded', 'moved', 'replaced', 'failed', 'subtitle', 'subfail',
         'updated', 'rollback', 'signin']

# The page's filter chips
FILTERS = {
    'snatched': ['snatched'],
    'downloaded': ['downloaded'],
    'failed': ['failed', 'subfail', 'rollback'],
    'library': ['added', 'moved', 'replaced', 'subtitle', 'subfail'],
    'app': ['updated', 'rollback', 'signin'],
}

# What goes into an archive file, per event
FIELDS = ['eid', 'time', 'type', 'title', 'year', 'identifier', 'media_id', 'quality', 'source', 'detail']

FILE_RE = re.compile(r'^history-(\d{4}-\d{2}-\d{2})_to_(\d{4}-\d{2}-\d{2})\.jsonl$')
DAY = 86400


def keepDays(keep):
    """ '90' -> 90, '365' -> 365, 'forever' -> None """
    if toUnicode(keep or '').strip().lower() == 'forever':
        return None
    return tryInt(keep, 90) or 90


def blockFor(day, anchor, length):
    """ The (first, last) date of the block that `day` falls in; blocks are `length` days, starting at `anchor` """
    start = anchor + datetime.timedelta(days = ((day - anchor).days // length) * length)
    return start, start + datetime.timedelta(days = length - 1)


def fileName(start, end):
    return 'history-%s_to_%s.jsonl' % (start.isoformat(), end.isoformat())


def fileRanges(folder):
    """ (first day, last day, name) of every archive file in the folder """
    out = []
    if os.path.isdir(folder):
        for name in os.listdir(folder):
            m = FILE_RE.match(name)
            if m:
                try:
                    out.append((datetime.date.fromisoformat(m.group(1)), datetime.date.fromisoformat(m.group(2)), name))
                except ValueError:
                    pass
    return sorted(out)


def nameFor(day, anchor, length, ranges):
    """
    The file an event of `day` goes into. A file already covering that day wins (so changing "Keep history" never
    makes files whose dates overlap); otherwise its block, cut short where it would run into an existing file.
    """
    for first, last, name in ranges:
        if first <= day <= last:
            return name
    start, end = blockFor(day, anchor, length)
    for first, last, name in ranges:
        if last < day:
            start = max(start, last + datetime.timedelta(days = 1))
        elif first > day:
            end = min(end, first - datetime.timedelta(days = 1))
    return fileName(start, end)


def replaceFile(path, lines):
    """ Write lines into path in one rename (fsync first); no lines left removes the file """
    if not lines:
        os.remove(path)
    else:
        tmp = path + '.tmp'
        with open(tmp, 'w', encoding = 'utf-8') as f:
            f.writelines(lines)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)

    try:
        fd = os.open(os.path.dirname(path), os.O_RDONLY)
        try: os.fsync(fd)
        finally: os.close(fd)
    except OSError:
        pass  # not every platform can fsync a folder


def removeEvents(path, eids):
    """ Take these events out of an archive file (the file goes when it is empty). Returns how many are left. """
    kept = []
    with open(path, 'r', encoding = 'utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                eid = json.loads(line).get('eid')
            except (ValueError, AttributeError):
                eid = None
            if eid not in eids:
                kept.append(line if line.endswith('\n') else line + '\n')
    replaceFile(path, kept)
    return len(kept)


def readEvents(path):
    """ The events in an archive file, skipping blank or broken lines """
    events = []
    with open(path, 'r', encoding = 'utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if isinstance(e, dict) and e.get('eid') and e.get('type'):
                events.append(e)
    return events


def eventDoc(e):
    """ An event's FIELDS as a JSON-safe dict: values the database handed back as bytes become str """
    doc = {}
    for k in FIELDS:
        v = e.get(k)
        if isinstance(v, bytes):
            v = v.decode('utf-8', 'replace')
        if v is not None:
            doc[k] = v
    return doc


def writeBlock(path, new_events):
    """
    Add events to an archive file, skipping any already in it, then fsync. The old content is kept as it was;
    the new file replaces it in one rename, so a crash leaves the old file or the new one, never half of one.
    Returns how many were written.
    """
    existing, lines = set(), []
    if os.path.isfile(path):
        with open(path, 'r', encoding = 'utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                lines.append(line if line.endswith('\n') else line + '\n')
                try:
                    existing.add(json.loads(line).get('eid'))
                except (ValueError, AttributeError):
                    pass

    added = 0
    for e in sorted(new_events, key = lambda x: x.get('time', 0)):
        if e.get('eid') in existing:
            continue
        existing.add(e.get('eid'))
        lines.append(json.dumps(eventDoc(e), ensure_ascii = False) + '\n')
        added += 1

    replaceFile(path, lines)
    return added


# Notifications kept before History existed (4 weeks), read once to fill the page on upgrade
SNATCHED_RE = re.compile(r'^Snatched "(?P<name>.*)": (?P<title>.*) \((?P<year>\d{4})\) in (?P<quality>\S+) from (?P<source>.*)$')
DOWNLOADED_RE = re.compile(r'^Downloaded (?P<title>.*) \((?P<quality>[^)]*)\)$')
UPDATED_RE = re.compile(r'updated to (?P<version>\w+)')


def parseNotification(message):
    """ An old notification's text -> an event dict (without time/eid), or None """
    message = toUnicode(message or '').strip()
    m = SNATCHED_RE.match(message)
    if m:
        return {'type': 'snatched', 'title': m.group('title'), 'year': tryInt(m.group('year')) or None,
                'quality': m.group('quality'), 'source': m.group('source'), 'detail': m.group('name')}
    m = DOWNLOADED_RE.match(message)
    if m:
        return {'type': 'moved', 'title': m.group('title'), 'quality': m.group('quality'), 'detail': message}
    if 'rolled back' in message:
        return {'type': 'rollback', 'detail': message}
    m = UPDATED_RE.search(message)
    if m and message.startswith('CouchTomato'):
        return {'type': 'updated', 'detail': message}
    return None


class History(Plugin):

    _database = {
        'history': HistoryIndex,
        'history_eid': HistoryEventIndex,
    }

    def __init__(self):
        self.lock = threading.RLock()

        addEvent('history.add', self.add)
        addEvent('history.archive', self.archive)
        addEvent('renamer.after', self.onRenamed)
        addEvent('updater.updated', self.onUpdated)
        addEvent('updater.failed', self.onUpdateFailed)
        addEvent('app.load', self.seed)
        addEvent('setting.save.history.keep.after', self.restore)

        addApiView('history.list', self.listView, docs = {
            'desc': 'History events, newest first',
            'params': {
                'filter': {'desc': 'all (default), snatched, downloaded, failed, library or app'},
                'days': {'desc': 'Only the last N days; "all" for everything in the database'},
                'limit_offset': {'desc': 'Limit and offset, for example "500" or "500,500"'},
            },
            'return': {'type': 'object', 'example': """{'success': True, 'events': [...], 'total': 120, 'keep': '90', 'files': [...], 'imported': {...}}"""}
        })
        addApiView('history.files', self.filesView, docs = {
            'desc': 'The archive files in the archive folder',
        })
        addApiView('history.archive', self.archiveView, docs = {
            'desc': 'Archive now: move events older than "Keep history" into their archive files',
        })
        addApiView('history.import', self.importView, docs = {
            'desc': 'Put an archive file\'s events back on the History page. POST a "file" upload to import one from elsewhere',
            'params': {'file': {'desc': 'Name of a file in the archive folder'}},
        })
        addApiView('history.unimport', self.unimportView, docs = {
            'desc': 'Take an imported file\'s events off the History page again (the file is not changed)',
            'params': {'file': {'desc': 'The name the events were imported under'}},
        })

        fireEvent('schedule.cron', 'history.archive', self.archive, hour = 3, minute = 17)

    # Settings

    def keep(self):
        keep = toUnicode(self.conf('keep') or '90').strip().lower()
        return keep if keep in ('90', '365', 'forever') else '90'

    def folder(self):
        folder = toUnicode(self.conf('folder') or '').strip()
        return folder or os.path.join(Env.get('data_dir'), 'history')

    # Writing events

    def add(self, type, media = None, media_id = None, title = None, year = None, quality = None, source = None,
            detail = None, event_time = None, eid = None):
        if type not in TYPES:
            log.error('Unknown history event type: %s', type)
            return False

        try:
            db = get_db()
            if not media and media_id:
                try: media = db.get('id', media_id)
                except: media = None

            e = {
                '_t': 'history',
                'eid': eid or uuid.uuid4().hex,
                'time': int(event_time or time.time()),
                'type': type,
            }
            if media:
                e['media_id'] = media.get('_id')
                e['title'] = getTitle(media)
                e['year'] = (media.get('info') or {}).get('year')
                e['identifier'] = getIdentifier(media)
            for k, v in (('title', title), ('year', year), ('quality', quality), ('source', source), ('detail', detail)):
                if v not in (None, ''):
                    e[k] = toUnicode(v) if k != 'year' else tryInt(v) or None
            e = dict((k, v) for k, v in e.items() if v is not None)

            with self.lock:
                if self.hasEvent(db, e['eid']):
                    return False
                db.insert(e)

            fireEvent('notify.frontend', type = 'history.add', data = e)
            return True
        except:
            log.error('Failed adding history event %s: %s', (type, traceback.format_exc()))
        return False

    def hasEvent(self, db, eid):
        try:
            db.get('history_eid', eid)
            return True
        except:
            return False

    def onRenamed(self, message = None, group = None):
        group = group or {}
        quality = ((group.get('meta_data') or {}).get('quality') or {}).get('label')
        where = group.get('destination_dir') or ''
        self.add('moved', media = group.get('media'), quality = quality, detail = where or message)

    def onUpdated(self, message = None, data = None):
        self.add('updated', detail = message)

    def onUpdateFailed(self, message = None, data = None):
        self.add('rollback' if data and data.get('previous') else 'failed', detail = message)

    # Reading

    def allEvents(self):
        db = get_db()
        return [x['doc'] for x in db.all('history', with_doc = True)]

    def listView(self, filter = 'all', days = None, limit_offset = None, **kwargs):
        events = self.allEvents()
        live = [e for e in events if not e.get('archive')]

        types = FILTERS.get(toUnicode(filter or 'all').lower())
        if types:
            events = [e for e in events if e.get('type') in types]

        days_n = None if toUnicode(days or '').lower() in ('', 'all') else tryInt(days)
        if days_n:
            since = time.time() - days_n * DAY
            events = [e for e in events if e.get('time', 0) >= since or e.get('archive')]

        events.sort(key = lambda e: e.get('time', 0), reverse = True)
        total = len(events)

        limit, offset = 1000, 0
        if limit_offset:
            parts = toUnicode(limit_offset).split(',')
            limit = tryInt(parts[0]) or limit
            offset = tryInt(parts[1]) if len(parts) > 1 else 0
        events = events[offset:offset + limit]

        imported = {}
        all_events = self.allEvents()
        for e in all_events:
            if e.get('archive'):
                imported[e['archive']] = imported.get(e['archive'], 0) + 1

        files = self.files()

        # Where history really began: the oldest event in the database (live or imported) or archive file
        starts = [datetime.date.fromtimestamp(e['time']).isoformat() for e in all_events if e.get('time')]
        starts += [f['from'] for f in files]

        return {
            'success': True,
            'events': [self.clean(e) for e in events],
            'total': total,
            'keep': self.keep(),
            'first_time': min([e.get('time', 0) for e in live]) if live else None,
            'began': min(starts) if starts else None,
            'files': files,
            'imported': imported,
            'folder': self.folder(),
        }

    def clean(self, e):
        return dict((k, v) for k, v in e.items() if k not in ('_rev', '_t'))

    def files(self):
        folder = self.folder()
        out = []
        if not os.path.isdir(folder):
            return out

        imported = {}
        try:
            for e in self.allEvents():
                if e.get('archive'):
                    imported[e['archive']] = imported.get(e['archive'], 0) + 1
        except:
            pass

        for name in sorted(os.listdir(folder), reverse = True):
            m = FILE_RE.match(name)
            if not m:
                continue
            path = os.path.join(folder, name)
            try:
                events = readEvents(path)
                count = len(events)
                size = os.path.getsize(path)
                times = [tryInt(e.get('time')) for e in events if e.get('time')]
            except:
                log.error('Failed reading history file %s: %s', (path, traceback.format_exc()))
                continue
            day = lambda t: datetime.date.fromtimestamp(t).isoformat()
            out.append({'name': name, 'from': m.group(1), 'to': m.group(2), 'events': count, 'size': size,
                        'on_page': imported.get(name, 0),
                        # The days the file really holds events for (its block can reach past them)
                        'first': day(min(times)) if times else None, 'last': day(max(times)) if times else None})
        return out

    def filesView(self, **kwargs):
        return {'success': True, 'files': self.files(), 'folder': self.folder(), 'keep': self.keep()}

    # Archiving

    def anchor(self, events):
        """ Blocks start on the date of the first event ever recorded, and stay there """
        saved = Env.prop('history.anchor')
        if saved:
            try:
                return datetime.date.fromisoformat(toUnicode(saved))
            except ValueError:
                pass
        first = datetime.date.fromtimestamp(min(e['time'] for e in events))
        Env.prop('history.anchor', value = first.isoformat())
        return first

    def archive(self, now = None):
        """ Move events older than "Keep history" into their block's file. Each file is on disk before any delete. """
        restored = self.restore(now = now).get('restored', 0)

        keep = keepDays(self.keep())
        if keep is None:
            return {'success': True, 'archived': 0, 'files': [], 'restored': restored,
                    'message': 'Keep history is Forever: nothing is archived.'}

        with self.lock:
            try:
                db = get_db()
                events = self.allEvents()
                live = [e for e in events if not e.get('archive')]
                cutoff = (now or time.time()) - keep * DAY
                old = [e for e in live if e.get('time', 0) < cutoff]
                if not old:
                    return {'success': True, 'archived': 0, 'files': [], 'restored': restored}

                anchor = self.anchor(live)
                folder = self.folder()
                ranges = fileRanges(folder)
                blocks = {}
                for e in old:
                    name = nameFor(datetime.date.fromtimestamp(e['time']), anchor, keep, ranges)
                    blocks.setdefault(name, []).append(e)

                if not os.path.isdir(folder):
                    os.makedirs(folder)

                archived, written = 0, []
                for name in sorted(blocks):
                    path = os.path.join(folder, name)
                    added = writeBlock(path, blocks[name])

                    # Only delete what the file now holds
                    in_file = set(e['eid'] for e in readEvents(path))
                    for e in blocks[name]:
                        if e['eid'] in in_file:
                            db.delete(e)
                            archived += 1
                    written.append({'name': name, 'added': added})
                    log.info('History: archived %s events into %s', (len(blocks[name]), path))

                return {'success': True, 'archived': archived, 'files': written, 'restored': restored}
            except:
                log.error('Failed archiving history: %s', traceback.format_exc())
                return {'success': False, 'error': 'Archiving failed, see the log'}

    def restore(self, now = None, **kwargs):
        """
        "Keep history" got longer (or Forever): events in the files that are now inside the limit go back on the
        page, live, and leave their file, so an event is never both. Each is in the database before its file shrinks.
        """
        keep = keepDays(self.keep())
        cutoff = None if keep is None else (now or time.time()) - keep * DAY

        with self.lock:
            try:
                db = get_db()
                restored = 0
                for first, last, name in fileRanges(self.folder()):
                    path = os.path.join(self.folder(), name)
                    back = [e for e in readEvents(path) if cutoff is None or tryInt(e.get('time')) >= cutoff]
                    if not back:
                        continue

                    done = set()
                    for e in back:
                        if e.get('type') not in TYPES:
                            continue
                        try:
                            doc = db.get('history_eid', e['eid'], with_doc = True)['doc']
                        except:
                            doc = None
                        if doc is None:
                            new = eventDoc(e)
                            new['time'] = tryInt(new.get('time'))
                            new['_t'] = 'history'
                            db.insert(new)
                        elif doc.get('archive'):
                            # Imported earlier: it stops being an imported copy and is simply on the page again
                            del doc['archive']
                            db.update(doc)
                        done.add(e['eid'])
                        restored += 1

                    left = removeEvents(path, done)
                    log.info('History: %s events from %s are back on the page (%s left in the file)', (len(done), name, left))

                return {'success': True, 'restored': restored}
            except:
                log.error('Failed bringing history back from the archive: %s', traceback.format_exc())
                return {'success': False, 'restored': 0}

    def archiveView(self, **kwargs):
        return self.archive()

    # Import

    def importEvents(self, events, name):
        db = get_db()
        added = skipped = 0
        with self.lock:
            for e in events:
                if e.get('type') not in TYPES or not e.get('eid') or self.hasEvent(db, e['eid']):
                    skipped += 1
                    continue
                doc = eventDoc(e)
                doc['time'] = tryInt(doc.get('time'))
                doc['_t'] = 'history'
                doc['archive'] = name
                db.insert(doc)
                added += 1
        log.info('History: imported %s events from %s (%s already there)', (added, name, skipped))
        return {'success': True, 'added': added, 'skipped': skipped, 'name': name}

    def importView(self, file = None, _request = None, **kwargs):
        try:
            upload = None
            if _request is not None:
                upload = (_request.request.files.get('file') or [None])[0]

            if upload:
                name = os.path.basename(toUnicode(upload.get('filename') or 'imported.jsonl'))
                events = []
                for line in upload['body'].decode('utf-8', 'replace').splitlines():
                    try:
                        e = json.loads(line)
                        if isinstance(e, dict) and e.get('eid'):
                            events.append(e)
                    except ValueError:
                        pass
                return self.importEvents(events, name)

            name = os.path.basename(toUnicode(file or ''))
            path = os.path.join(self.folder(), name)
            if not FILE_RE.match(name) or not os.path.isfile(path):
                return {'success': False, 'error': 'No archive file called "%s" in %s' % (name, self.folder())}
            return self.importEvents(readEvents(path), name)
        except:
            log.error('Failed importing history: %s', traceback.format_exc())
            return {'success': False, 'error': 'Import failed, see the log'}

    def unimportView(self, file = None, **kwargs):
        name = os.path.basename(toUnicode(file or ''))
        db = get_db()
        removed = 0
        with self.lock:
            for e in self.allEvents():
                if e.get('archive') == name:
                    db.delete(e)
                    removed += 1
        return {'success': True, 'removed': removed}

    # Filling the page on upgrade, from what the app already kept

    def seed(self):
        if Env.prop('history.seeded'):
            return
        try:
            added = self.seedFrom(get_db())
            Env.prop('history.seeded', value = int(time.time()))
            log.info('History: filled with %s earlier events (notifications and finished downloads)', added)
        except:
            log.error('Failed filling history from earlier events: %s', traceback.format_exc())

    def seedFrom(self, db):
        media = {}
        for x in db.all('media', with_doc = True):
            m = x['doc']
            media[m['_id']] = m
        by_title = {}
        for m in media.values():
            by_title.setdefault(toUnicode(getTitle(m) or '').lower(), m)

        added = 0
        moved_at = {}  # media id -> times a "moved" event was seeded from notifications

        for x in db.all('notification', with_doc = True):
            n = x['doc']
            e = parseNotification(n.get('message'))
            if not e:
                continue
            m = by_title.get(toUnicode(e.get('title') or '').lower())
            if m and e['type'] == 'moved':
                moved_at.setdefault(m['_id'], []).append(n.get('time', 0))
            if self.add(e.pop('type'), media = m, event_time = n.get('time'), eid = 'seed-n-%s' % n['_id'], **e):
                added += 1

        # Finished downloads older than the notifications (which only last 4 weeks), and failed ones
        for x in db.all('release', with_doc = True):
            r = x['doc']
            when = r.get('last_edit')
            m = media.get(r.get('media_id'))
            if not when or not m:
                continue
            if r.get('status') == 'done':
                if any(abs(t - when) < 3 * DAY for t in moved_at.get(m['_id'], [])):
                    continue
                kind, detail = 'moved', 'In your library'
            elif r.get('status') == 'failed':
                kind, detail = 'failed', 'Marked failed'
            else:
                continue
            name = (r.get('info') or {}).get('name')
            if self.add(kind, media = m, quality = r.get('quality'), source = (r.get('info') or {}).get('provider'),
                        detail = name or detail, event_time = when, eid = 'seed-r-%s' % r['_id']):
                added += 1

        return added

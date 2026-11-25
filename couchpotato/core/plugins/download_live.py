"""
Live download status for Movie details: the % and time left change on screen without a reload.

- Kept in memory only (never the database): it is worthless once the download ends, and writing CodernityDB every
  10 s would grow the files and wear a Pi's SD card.
- The renamer's normal check (every renamer.run_every minutes) refreshes it for every snatched release.
- A page that shows a movie sends download.watch every 30 s. While any watch is fresh (< 60 s) a "fast lane" asks the
  downloader about only those movies every 10 s. No watch for 60 s -> the fast lane is removed from the scheduler,
  so nothing runs faster than before when nobody is looking.
- Only what changed is pushed to the browser, over the existing notification channel ('release.progress').
"""
import threading
import time
import traceback

from couchpotato import get_db
from couchpotato.api import addApiView
from couchpotato.core.event import addEvent, fireEvent
from couchpotato.core.helpers.variable import splitString
from couchpotato.core.logger import CPLog
from couchpotato.core.plugins.base import Plugin

log = CPLog(__name__)

autoload = 'DownloadLive'

FAST_SECONDS = 10
WATCH_SECONDS = 60
WATCHED_STATUSES = ['snatched', 'missing', 'seeding', 'downloaded']


def toStr(value):
    # The database gives ids as bytes; the page asks with str ids and the push is JSON
    return value.decode('utf-8') if isinstance(value, bytes) else value


def mergeStatus(live, rels, release_downloads, now, full = False):
    """ Fold a downloader answer into `live` ({release_id: item}).

    :param rels: release docs that were asked about
    :param release_downloads: what the downloaders returned (ReleaseDownloadList items)
    :param full: True when `rels` is every snatched release, so anything else in `live` is stale and goes
    :return: the items that changed enough to tell the browser about
    """
    changed = []
    seen = set()

    for rel in rels:
        info = rel.get('download_info') or {}
        if not isinstance(info, dict) or not info.get('id') or not info.get('downloader'):
            continue

        found = None
        for rd in release_downloads or []:
            if rd.get('id') == info.get('id') and rd.get('downloader') == info.get('downloader'):
                found = rd
                break
        if not found:
            continue

        rid = toStr(rel.get('_id'))
        seen.add(rid)
        old = live.get(rid) or {}

        progress = found.get('progress')
        if progress is None and found.get('status') in ['completed', 'seeding']:
            progress = 100

        done = found.get('done') or old.get('done')
        if not done and progress == 100:
            done = now  # the downloader doesn't say when; the first time we saw 100 %

        item = {
            'release_id': rid,
            'media_id': toStr(rel.get('media_id')),
            'progress': progress,
            'eta': found.get('eta') if progress != 100 else None,
            'status': found.get('status'),
            'added': found.get('added') or old.get('added'),
            'done': done,
            'checked_at': now,
        }

        is_new = not old
        moved = (old.get('progress') is None) != (progress is None) or \
            (progress is not None and old.get('progress') is not None and abs(progress - old['progress']) >= 1)
        eta_moved = (old.get('eta') is None) != (item['eta'] is None) or \
            (item['eta'] is not None and old.get('eta') is not None and item['eta'] // 60 != old['eta'] // 60)

        live[rid] = item
        if is_new or moved or eta_moved or old.get('status') != item['status'] or old.get('done') != item['done']:
            changed.append(item)

    if full:
        for rid in list(live.keys()):
            if rid not in seen:
                del live[rid]

    return changed


class DownloadLive(Plugin):

    def __init__(self):
        self.live = {}
        self.watches = {}  # media_id -> time of the last download.watch
        self.lock = threading.Lock()
        self.fast_on = False

        addEvent('download.live.update', self.update)

        addApiView('download.live', self.liveView, docs = {
            'desc': 'Download %, time left and dates for releases being downloaded (from memory, no downloader call)',
            'params': {
                'media_id': {'desc': 'Optional, comma separated: only these movies'},
            },
            'return': {'type': 'object', 'example': """{
    'success': True,
    'releases': [{'release_id': '...', 'media_id': '...', 'progress': 64, 'eta': 1080, 'status': 'busy',
                  'added': 1795570000, 'done': None, 'checked_at': 1795574000}],
    'interval': 10
}"""}
        })
        addApiView('download.watch', self.watchView, docs = {
            'desc': 'A page is showing these movies: check their downloads every 10 s for the next 60 s. Send again every 30 s.',
            'params': {
                'media_id': {'desc': 'Comma separated movie ids'},
            },
            'return': {'type': 'object', 'example': 'Same as download.live, for these movies'}
        })

    # Called by the renamer after its normal check of every snatched release
    def update(self, rels, release_downloads, full = False):
        try:
            with self.lock:
                changed = mergeStatus(self.live, rels, release_downloads, int(time.time()), full = full)
            if changed:
                fireEvent('notify.frontend', type = 'release.progress', data = changed)
            return changed
        except:
            log.error('Failed updating live download status: %s', traceback.format_exc())
            return []

    def itemsFor(self, media_ids = None):
        with self.lock:
            items = list(self.live.values())
        if media_ids:
            items = [x for x in items if x.get('media_id') in media_ids]
        return items

    def liveView(self, media_id = None, **kwargs):
        return {
            'success': True,
            'releases': self.itemsFor(splitString(media_id) if media_id else None),
            'interval': FAST_SECONDS,
        }

    def watchView(self, media_id = None, **kwargs):
        media_ids = splitString(media_id) if media_id else []
        if media_ids:
            now = time.time()
            with self.lock:
                for mid in media_ids:
                    self.watches[mid] = now
                start = not self.fast_on
                self.fast_on = True
            if start:
                log.info('Live download status: fast lane on (every %ss while a page is open)', FAST_SECONDS)
                fireEvent('schedule.interval', 'download.live.fast', self.fastLane, seconds = FAST_SECONDS, single = True)

        return {
            'success': True,
            'releases': self.itemsFor(media_ids),
            'interval': FAST_SECONDS,
        }

    def freshWatches(self, now):
        with self.lock:
            for mid, at in list(self.watches.items()):
                if now - at > WATCH_SECONDS:
                    del self.watches[mid]
            return list(self.watches.keys())

    def stopFastLane(self):
        with self.lock:
            was_on = self.fast_on
            self.fast_on = False
        if was_on:
            fireEvent('schedule.remove', 'download.live.fast', single = True)
            log.info('Live download status: fast lane off (no page has asked for %ss)', WATCH_SECONDS)

    def fastLane(self):
        try:
            media_ids = self.freshWatches(time.time())
            if not media_ids:
                self.stopFastLane()
                return

            rels = []
            db = get_db()
            for mid in media_ids:
                try:
                    media = db.get('id', mid)
                except Exception:
                    continue  # removed meanwhile
                # The release index wants the id exactly as the database gives it (bytes), not the API's str
                for rel in fireEvent('release.for_media', media['_id'], single = True) or []:
                    if rel.get('status') in WATCHED_STATUSES and isinstance(rel.get('download_info'), dict) \
                            and rel['download_info'].get('id'):
                        rels.append(rel)
            if not rels:
                return

            download_ids = [rel['download_info'] for rel in rels]
            release_downloads = fireEvent('download.status', download_ids, merge = True) or []
            self.update(rels, release_downloads)
        except:
            log.error('Live download status check failed: %s', traceback.format_exc())

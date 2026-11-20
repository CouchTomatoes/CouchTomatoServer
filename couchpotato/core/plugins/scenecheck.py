"""
Scene check: answers `release.validate`, which the search scoring (scores.sceneScore) asks for every
release name that has a year and a -GROUP. It used to be answered by the CouchPotato API's /validate/,
which looked the name up on orlydb and scored it. That API is gone, so this asks the public pre databases
directly and scores the answer the same way (CouchPotatoAPI libs/providers/orlydb.js):

  a scene release, not nuked   +40  'scene'
  nuked                        -10  'nuke', plus a penalty for each known nuke reason found in it

predb.net is asked first (it knows nukes). When it can't answer (down, 429), srrdb is asked instead,
which only knows whether the release exists, so it can give +40 but never a nuke.
Answers are cached for 3 days like the API did; a failed lookup is not cached.
"""
import json
import traceback

from couchpotato.core.event import addEvent
from couchpotato.core.helpers.encoding import toUnicode, tryUrlencode
from couchpotato.core.helpers.variable import tryInt
from couchpotato.core.logger import CPLog
from couchpotato.core.plugins.base import Plugin


log = CPLog(__name__)

autoload = 'SceneCheck'

# The API's orlydb scoring, unchanged ('blended.frames, ' was a typo there that could never match)
NUKE_PENALTIES = {
    'bad.ivtc': -20, 'no.ivtc': -20, 'interlaced': -20, 'bad.pack': -20, 'bad.fps': -20,

    'mislabeled': -40, 'grp.req': -40, 'oos': -40, 'out.of.sync': -40, 'ghosting': -40,
    'field.shifted': -40, 'dupe.frames': -40, 'blended.frames': -40, 'custom.quant.matrix': -40,
    'divx.not.allowed': -40, 'no.audio': -40, 'missing.audio': -40, 'get.rerip': -40, 'get.proper': -40,
}

# predb.net row status
PRE, NUKED, UNNUKED, DELPRE = 0, 1, 2, 3

CACHE_SECONDS = 259200  # 3 days, as the API cached it

# (connect, read). predb.net publishes an IPv6 address that does not answer from his network (measured
# 2026-11-20: v6 connect timed out at 15 s, v4 connected in 0.1 s, on the Mac and the Pi4 alike). Python
# tries v6 first and only moves to v4 when the connect times out, so a single 10 s timeout spent all 10 s
# on v6 and the first lookup of every run failed over to srrdb. A short connect timeout costs 3 s once,
# then the kept-alive v4 connection answers in ~0.2 s.
TIMEOUT = (3, 10)


def scoreNuke(reason):
    score, reasons = -10, ['nuke']
    reason = (reason or '').lower()
    for tag, penalty in NUKE_PENALTIES.items():
        if tag in reason:
            reasons.append(tag)
            score += penalty
    return score, reasons


class SceneCheck(Plugin):

    predb_url = 'https://api.predb.net/?type=pre&%s'
    srrdb_url = 'https://api.srrdb.com/v1/search/r:%s'

    def __init__(self):
        addEvent('release.validate', self.validate)

    def validate(self, name = None):
        """ {'score': int, 'reasons': [str]} for a release name; score 0 when nothing is known """
        if not name:
            return

        name = toUnicode(name).strip()
        cache_key = 'scenecheck.%s' % name.lower()
        cached = self.getCache(cache_key)
        if cached:
            return json.loads(cached)

        result = self.askPredb(name)
        if result is None:
            result = self.askSrrdb(name)
        if result is None:
            return {'score': 0, 'reasons': []}  # nobody could answer: score nothing, try again next time

        self.setCache(cache_key, json.dumps(result), timeout = CACHE_SECONDS)
        if result['score']:
            log.debug('Scene check %s: %s %s', (name, result['score'], result['reasons']))
        return result

    def fetchJson(self, url):
        """ The decoded answer, or None when the site could not answer """
        try:
            data = self.urlopen(url, timeout = TIMEOUT, show_error = False)
            if isinstance(data, bytes):
                data = data.decode('utf-8', 'replace')  # not toUnicode(): it turns bytes into their b'...' repr
            return json.loads(data) if data else None
        except Exception as e:
            log.debug('Scene check could not ask %s: %s', (url, e))
            return None

    def askPredb(self, name):
        answer = self.fetchJson(self.predb_url % tryUrlencode({'release': name}))
        if not isinstance(answer, dict) or answer.get('status') != 'success':
            return None

        # The match is case-insensitive there; only an exact name counts, like the old check
        rows = [row for row in (answer.get('data') or [])
                if toUnicode(row.get('release', '')).lower() == name.lower()]

        score, reasons = 0, []
        for row in rows:
            status = tryInt(row.get('status'))
            if status in (PRE, UNNUKED):
                score, reasons = 40, ['scene']
            elif status == NUKED:
                score, reasons = scoreNuke(row.get('reason'))
            # DELPRE: the group deleted the pre, so it says nothing either way
            break

        return {'score': score, 'reasons': reasons}

    def askSrrdb(self, name):
        answer = self.fetchJson(self.srrdb_url % name)
        if not isinstance(answer, dict) or 'resultsCount' not in answer:
            return None

        found = any(toUnicode(row.get('release', '')).lower() == name.lower()
                    for row in (answer.get('results') or []))
        return {'score': 40, 'reasons': ['scene']} if found else {'score': 0, 'reasons': []}

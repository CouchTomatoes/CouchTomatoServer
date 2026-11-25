import io
import os
import re
import time
import traceback
import zipfile

from couchpotato import get_db
from couchpotato.api import addApiView
from couchpotato.core.event import addEvent, fireEvent
from couchpotato.core.helpers.encoding import toUnicode, sp
from couchpotato.core.helpers.variable import splitString, getIdentifier, getTitle
from couchpotato.core.logger import CPLog
from couchpotato.core.plugins.base import Plugin
from subliminal.language import Language, LANGUAGES
from subliminal.videos import Video


log = CPLog(__name__)

autoload = 'Subtitle'


class Subtitle(Plugin):
    """
    Subtitles from yts-subs.com: searched by IMDb id, no account needed, and timed for the YIFY/YTS releases
    this app mostly downloads. The services subliminal used (OpenSubtitles' old XML-RPC API, TheSubDB, Podnapisi,
    ...) are all gone or behind Cloudflare. Each subtitle is saved as "<movie file>.<lang>.srt", the name Plex
    and Kodi pick up next to the video.
    """

    search_url = 'https://yts-subs.com/movie-imdb/%s'
    download_url = 'https://subtitles.yts-subs.com/subtitles/%s.zip'

    def __init__(self):
        addEvent('renamer.before', self.searchSingle)

        addApiView('subtitle.library', self.libraryView, docs = {
            'desc': 'Download missing subtitles for every movie already in the library',
            'return': {'type': 'object', 'example': """{'success': True, 'added': 3, 'checked': 20}"""}
        })
        addApiView('subtitle.search', self.searchView, docs = {
            'desc': 'The subtitles yts-subs.com has for a movie in one language (Movie details -> Subtitles)',
            'params': {
                'id': {'desc': 'Media id'},
                'language': {'desc': '2 letter code; default = the first language in Settings'},
            },
            'return': {'type': 'object', 'example': """{'success': True, 'language': 'en', 'subtitles': [{'slug': ..., 'matches': True}], 'chosen': None, 'in_library': True}"""}
        })
        addApiView('subtitle.choose', self.chooseView, docs = {
            'desc': 'Use this subtitle for the movie. In the library: written next to the file now (the old one kept as .srt.bak). '
                    'Still downloading: remembered and written when the movie reaches the library.',
            'params': {
                'id': {'desc': 'Media id'},
                'language': {'desc': '2 letter code'},
                'slug': {'desc': 'Subtitle id from subtitle.search'},
            },
            'return': {'type': 'object', 'example': """{'success': True, 'saved': True, 'filename': 'Movie (2023).en.srt'}"""}
        })

    def searchSingle(self, group):
        """ Called by the renamer before it moves a download; subtitles added here are renamed with the movie """
        if self.isDisabled(): return

        try:
            movie_files = group['files']['movie']
            identifier = group.get('identifier') or getIdentifier(group.get('media') or {})
            if len(movie_files) != 1 or not identifier:
                return False  # multi-part releases have no single file to name the subtitle after

            movie_file = sp(toUnicode(movie_files[0]))
            have = set(sum(list(group['subtitle_language'].values()), []))
            release_name = '%s %s' % (group.get('dirname') or '', os.path.basename(movie_file))

            for lang in self.getLanguages():
                if lang in have and not self.conf('force'):
                    continue

                chosen = (group.get('media') or {}).get('subtitle_choice', {}).get(lang)
                path = self.download(identifier, lang, movie_file, release_name, slug = chosen)
                if path:
                    group['files']['subtitle'].append(path)
                    group['before_rename'].append(path)
                    group['subtitle_language'][path] = [lang]
                language = languageName(lang) or lang
                fireEvent('history.add', 'subtitle' if path else 'subfail', media = group.get('media'),
                          detail = ('%s from yts-subs.com' if path else 'No %s subtitle on yts-subs.com yet') % language)

            return True
        except:
            log.error('Failed searching for subtitle: %s', traceback.format_exc())

        return False

    def libraryView(self, **kwargs):
        if self.isDisabled():
            return {'success': False, 'error': 'Subtitles are disabled'}

        checked = added = 0
        for media in fireEvent('media.with_status', 'done', types = 'movie', single = True) or []:
            identifier = getIdentifier(media)
            for release in fireEvent('release.for_media', media['_id'], single = True) or []:
                movie_files = (release.get('files') or {}).get('movie') or []
                if release.get('status') != 'done' or len(movie_files) != 1 or not os.path.isfile(movie_files[0]):
                    continue

                checked += 1
                movie_file = sp(movie_files[0])
                have = self.existingLanguages(movie_file)
                chosen = media.get('subtitle_choice') or {}
                for lang in self.getLanguages():
                    if lang not in have and self.download(identifier, lang, movie_file, os.path.basename(movie_file), slug = chosen.get(lang)):
                        added += 1

        log.info('Library subtitles: %s added, %s movies checked', (added, checked))
        return {'success': True, 'added': added, 'checked': checked}

    def existingLanguages(self, movie_file):
        """ Languages of the subtitles already next to, or embedded in, a movie file """
        try:
            # An embedded image track (PGS/VobSub) still gets an .srt: Plex would have to burn it in
            return set(s.language.alpha2 for s in Video.from_path(movie_file).scan()
                       if s.language and getattr(s, 'is_text', True))
        except:
            log.debug('Failed scanning %s for subtitles: %s', (movie_file, traceback.format_exc()))
            return set()

    def download(self, identifier, lang, movie_file, release_name, slug = None, replace = False):
        """ Save a subtitle as "<movie file>.<lang>.srt"; returns its path or None.

        :param slug: this exact yts-subs subtitle (chosen on Movie details), else the best match for the release
        :param replace: write over an existing subtitle, keeping it as "<name>.srt.bak"
        """
        target = '%s.%s.srt' % (os.path.splitext(movie_file)[0], lang)
        if os.path.isfile(target) and not replace:
            return target

        if not slug:
            candidates = self.candidates(identifier, lang)
            if not candidates:
                log.info('No %s subtitle on yts-subs for %s', (lang, identifier))
                return None
            best = max(candidates, key = lambda c: matchScore(c, release_name))
            slug = best['slug']
            name = best['releases'][0] if best['releases'] else slug
        else:
            name = slug

        try:
            data = self.urlopen(self.download_url % slug, show_error = False)
            srt = extractSrt(data)
        except:
            log.info('Failed downloading subtitle %s: %s', (slug, traceback.format_exc()))
            return None

        if not srt:
            log.info('No .srt inside subtitle %s', slug)
            return None

        if os.path.isfile(target):
            os.replace(target, target + '.bak')
        with open(target, 'wb') as f:
            f.write(srt)

        log.info('Found subtitle (%s) for %s: %s', (lang, os.path.basename(movie_file), name))
        return target

    def candidates(self, identifier, lang):
        """ The yts-subs rows for a movie in one language; None when the page could not be read """
        try:
            page = self.getCache('yts-subs.%s' % identifier, self.search_url % identifier, show_error = False)
        except Exception as e:
            # 404 = yts-subs has no page for this movie yet (common for new releases)
            log.info('No subtitle page on yts-subs for %s: %s', (identifier, e))
            return None
        return parseSubtitles(toUnicode(page or ''), lang)

    # ----- Movie details -> Subtitles -----

    def libraryFile(self, media):
        """ (movie file, release name) when the movie is in the library as one file, else (None, release name) """
        release_name = ''
        newest = 0
        for release in fireEvent('release.for_media', media['_id'], single = True) or []:
            status = release.get('status')
            if status not in ('snatched', 'downloaded', 'done', 'seeding'):
                continue
            movie_files = (release.get('files') or {}).get('movie') or []
            if status == 'done' and len(movie_files) == 1 and os.path.isfile(sp(movie_files[0])):
                movie_file = sp(movie_files[0])
                return movie_file, '%s %s' % ((release.get('info') or {}).get('name') or '', os.path.basename(movie_file))
            if (release.get('last_edit') or 0) >= newest:
                newest = release.get('last_edit') or 0
                release_name = (release.get('info') or {}).get('name') or ''
        return None, release_name

    def searchView(self, id = None, language = None, **kwargs):
        try:
            media = get_db().get('id', id)
        except:
            return {'success': False, 'error': 'Movie not found'}

        identifier = getIdentifier(media)
        lang = languageCode(language) if language else (self.getLanguages() or ['en'])[0]
        settings_langs = [l for l in self.getLanguages() if languageName(l)]
        movie_file, release_name = self.libraryFile(media)

        rows = None
        if identifier:
            try:
                page = self.getCache('yts-subs.%s' % identifier, self.search_url % identifier, show_error = False)
                rows = parseSubtitles(toUnicode(page or ''))
            except Exception as e:
                log.info('No subtitle page on yts-subs for %s: %s', (identifier, e))
                rows = []

        # Languages for the menu: Settings first, then whatever the site has for this movie
        languages = [{'code': l, 'name': languageName(l), 'count': 0} for l in settings_langs]
        by_code = dict((l['code'], l) for l in languages)
        for row in rows or []:
            if not row['code']:
                continue
            if row['code'] not in by_code:
                by_code[row['code']] = {'code': row['code'], 'name': row['language'], 'count': 0}
                languages.append(by_code[row['code']])
            by_code[row['code']]['count'] += 1
        if lang and lang not in by_code and languageName(lang):
            languages.insert(0, {'code': lang, 'name': languageName(lang), 'count': 0})

        mine = [r for r in rows or [] if r['code'] == lang]
        best = max(mine, key = lambda c: matchScore(c, release_name)) if mine and release_name else None
        subtitles = [{
            'slug': r['slug'],
            'name': r['releases'][0] if r['releases'] else r['slug'],
            'releases': r['releases'],
            'uploader': r['uploader'],
            'rating': r['rating'],
            'made_for': madeFor(r['releases']),
            'matches': bool(best is r and matchBonus(r, release_name) > 0),
        } for r in sorted(mine, key = lambda c: -matchScore(c, release_name))]

        target = '%s.%s.srt' % (os.path.splitext(movie_file)[0], lang) if movie_file else None
        return {
            'success': rows is not None,
            'error': None if rows is not None else 'This movie has no IMDb id',
            'language': lang,
            'language_name': languageName(lang) or lang,
            'languages': languages,
            'subtitles': subtitles,
            'chosen': (media.get('subtitle_choice') or {}).get(lang),
            'in_library': bool(movie_file),
            'has_file': bool(target and os.path.isfile(target)),
            'filename': os.path.basename(target) if target else '%s.%s.srt' % (getTitle(media) or 'Movie', lang),
        }

    def chooseView(self, id = None, language = None, slug = None, **kwargs):
        lang = languageCode(language or '')
        if not lang or not slug or not re.match(r'^[a-z0-9-]+$', slug):
            return {'success': False, 'error': 'Pick a language and a subtitle'}

        db = get_db()
        try:
            media = db.get('id', id)
        except:
            return {'success': False, 'error': 'Movie not found'}

        movie_file, release_name = self.libraryFile(media)
        path = None
        if movie_file:
            path = self.download(getIdentifier(media), lang, movie_file, release_name, slug = slug, replace = True)
            if not path:
                return {'success': False, 'error': 'Could not download that subtitle from yts-subs.com, try another one'}

        # Remember it: the renamer uses it when the movie arrives, and the page shows "chosen"
        media = db.get('id', media['_id'])
        choice = media.get('subtitle_choice') or {}
        choice[lang] = slug
        media['subtitle_choice'] = choice
        db.update(media)

        media_id = media['_id'].decode('utf-8') if isinstance(media['_id'], bytes) else media['_id']
        if path:
            fireEvent('history.add', 'subtitle', media = media,
                      detail = '%s chosen on Movie details, from yts-subs.com' % (languageName(lang) or lang))
            fireEvent('notify.frontend', type = 'subtitle.saved', data = {
                'media_id': media_id, 'language': lang, 'slug': slug, 'filename': os.path.basename(path), 'at': int(time.time())
            })

        return {
            'success': True,
            'saved': bool(path),
            'language': lang,
            'slug': slug,
            'filename': os.path.basename(path) if path else None,
        }

    def getLanguages(self):
        return splitString(self.conf('languages'))


# yts-subs names that are not plain language names
SITE_LANGUAGES = {
    'farsi/persian': 'fa',
    'brazillian portuguese': 'pt',
    'brazilian portuguese': 'pt',
    'chinese bg code': 'zh',
    'big 5 code': 'zh',
}


def languageCode(name):
    """ 'Arabic' / 'ar' / 'Farsi/Persian' / 'Greek' -> 'ar' / 'ar' / 'fa' / 'el'; None when unknown """
    name = (name or '').strip().lower()
    if not name:
        return None
    if name in SITE_LANGUAGES:
        return SITE_LANGUAGES[name]
    if not NAME_CODES:
        for alpha3, _, alpha2, english, _ in LANGUAGES:
            if not alpha2:
                continue
            NAME_CODES.setdefault(alpha2, alpha2)
            NAME_CODES.setdefault(alpha3, alpha2)
            # 'Spanish; Castilian', 'Greek, Modern (1453-)': every part before ; , ( is a name
            for part in re.split(r'[;(]', english):
                part = part.strip().lower()
                if part:
                    NAME_CODES.setdefault(part, alpha2)
                    NAME_CODES.setdefault(part.split(',')[0].strip(), alpha2)
    for part in [name] + re.split(r'[/;,]', name):
        code = NAME_CODES.get(part.strip())
        if code:
            return code
    return None


NAME_CODES = {}


def languageName(code):
    """ 'es' -> 'Spanish' (subliminal says 'Spanish; Castilian') """
    try:
        return re.split(r'[;,(]', Language(code).name)[0].strip()
    except:
        return None


def parseSubtitles(html, language = None):
    """ The subtitle rows of a yts-subs movie page: [{'slug', 'rating', 'releases', 'language', 'code', 'uploader'}].

    :param language: only rows in this language, as a name ('English') or a code ('en')
    """
    want = languageCode(language) if language else None
    found = []
    for row in re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.S):
        lang = re.search(r'class="sub-lang">([^<]+)<', row)
        slug = re.search(r'href="/subtitles/([^"/]+)"', row)
        if not lang or not slug:
            continue
        name = lang.group(1).strip()
        code = languageCode(name)
        if language and not (want and code == want) and name.lower() != language.lower():
            continue

        rating = re.search(r'class="rating-cell">\s*<span[^>]*>(-?\d+)<', row)
        names = re.search(r'</span>(.*?)</a>', row[slug.start():], re.S)
        uploader = re.search(r'class="uploader-cell">([^<]*)<', row)
        releases = [re.sub(r'\s+', ' ', n).strip() for n in re.split(r'<br\s*/?>', names.group(1) if names else '')]
        found.append({
            'slug': slug.group(1),
            'rating': int(rating.group(1)) if rating else 0,
            'releases': [n for n in releases if n],
            'language': name,
            'code': code,
            'uploader': uploader.group(1).strip() if uploader else '',
        })

    return found


def madeFor(releases):
    """ What a subtitle was timed for, in a word: YIFY, a release group, WEB or BluRay; '+ SDH' for hearing impaired """
    words = set(re.split(r'[\W_]+', ' '.join(releases).lower()))
    if words & {'yify', 'yts'}:
        kind = 'YIFY'
    else:
        group = re.search(r'-([A-Za-z0-9]+)(?:\.[A-Za-z]{2,4})*$', releases[0]) if releases else None
        if group and not group.group(1).isdigit():
            kind = group.group(1)
        elif words & {'web', 'webrip', 'webdl'}:
            kind = 'WEB'
        elif words & {'bluray', 'brrip', 'bdrip'}:
            kind = 'BluRay'
        else:
            kind = ''
    if words & {'sdh', 'hi'}:
        kind = (kind + ' · SDH').strip(' ·')
    return kind


def matchScore(candidate, release_name):
    """ Prefer a subtitle made for the same kind of release (group, resolution, source), so it is in sync """
    return candidate['rating'] + matchBonus(candidate, release_name)


def matchBonus(candidate, release_name):
    """ How well a subtitle's release names fit ours (0 = nothing in common) """
    ours = set(re.split(r'[\W_]+', release_name.lower()))
    theirs = set(re.split(r'[\W_]+', ' '.join(candidate['releases']).lower()))

    score = 0
    if ours & {'yify', 'yts'} and theirs & {'yify', 'yts'}:
        score += 10
    for group in ({'2160p'}, {'1080p'}, {'720p'}, {'bluray', 'brrip', 'bdrip'}, {'web', 'webrip', 'webdl'}):
        if ours & group and theirs & group:
            score += 3
    return score


def extractSrt(data):
    """ The largest .srt inside a subtitle zip """
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        srts = [i for i in z.infolist() if i.filename.lower().endswith('.srt')]
        if not srts:
            return None
        return z.read(max(srts, key = lambda i: i.file_size))


config = [{
    'name': 'subtitle',
    'groups': [
        {
            'tab': 'renamer',
            'name': 'subtitle',
            'label': 'Download subtitles',
            'description': 'after rename, from yts-subs.com',
            'options': [
                {
                    'name': 'enabled',
                    'label': 'Search and download subtitles',
                    'default': False,
                    'type': 'enabler',
                },
                {
                    'name': 'languages',
                    'description': ('Comma separated, 2 letter country code.', 'Example: en, nl. See the codes at <a href="http://en.wikipedia.org/wiki/List_of_ISO_639-1_codes" target="_blank">on Wikipedia</a>'),
                },
                {
                    'advanced': True,
                    'name': 'force',
                    'label': 'Force',
                    'description': ('Force download all languages (including embedded).', 'This will also <strong>overwrite</strong> all existing subtitles.'),
                    'default': False,
                    'type': 'bool',
                },
            ],
        },
    ],
}]

import io
import os
import re
import traceback
import zipfile

from couchpotato.api import addApiView
from couchpotato.core.event import addEvent, fireEvent
from couchpotato.core.helpers.encoding import toUnicode, sp
from couchpotato.core.helpers.variable import splitString, getIdentifier
from couchpotato.core.logger import CPLog
from couchpotato.core.plugins.base import Plugin
from subliminal.language import Language
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

                path = self.download(identifier, lang, movie_file, release_name)
                if path:
                    group['files']['subtitle'].append(path)
                    group['before_rename'].append(path)
                    group['subtitle_language'][path] = [lang]

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
                for lang in self.getLanguages():
                    if lang not in have and self.download(identifier, lang, movie_file, os.path.basename(movie_file)):
                        added += 1

        log.info('Library subtitles: %s added, %s movies checked', (added, checked))
        return {'success': True, 'added': added, 'checked': checked}

    def existingLanguages(self, movie_file):
        """ Languages of the subtitles already next to, or embedded in, a movie file """
        try:
            return set(s.language.alpha2 for s in Video.from_path(movie_file).scan() if s.language)
        except:
            log.debug('Failed scanning %s for subtitles: %s', (movie_file, traceback.format_exc()))
            return set()

    def download(self, identifier, lang, movie_file, release_name):
        """ Save the best matching subtitle as "<movie file>.<lang>.srt"; returns its path or None """
        target = '%s.%s.srt' % (os.path.splitext(movie_file)[0], lang)
        if os.path.isfile(target):
            return target

        page = self.getCache('yts-subs.%s' % identifier, self.search_url % identifier, show_error = False)
        candidates = parseSubtitles(toUnicode(page or ''), Language(lang).name)
        if not candidates:
            log.info('No %s subtitle on yts-subs for %s', (lang, identifier))
            return None

        best = max(candidates, key = lambda c: matchScore(c, release_name))
        try:
            data = self.urlopen(self.download_url % best['slug'], show_error = False)
            srt = extractSrt(data)
        except:
            log.info('Failed downloading subtitle %s: %s', (best['slug'], traceback.format_exc()))
            return None

        if not srt:
            log.info('No .srt inside subtitle %s', best['slug'])
            return None

        with open(target, 'wb') as f:
            f.write(srt)

        log.info('Found subtitle (%s) for %s: %s', (lang, os.path.basename(movie_file), best['releases'][0] if best['releases'] else best['slug']))
        return target

    def getLanguages(self):
        return splitString(self.conf('languages'))


def parseSubtitles(html, language_name):
    """ The subtitle rows of a yts-subs movie page in one language: [{'slug', 'rating', 'releases'}] """
    found = []
    for row in re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.S):
        lang = re.search(r'class="sub-lang">([^<]+)<', row)
        slug = re.search(r'href="/subtitles/([^"/]+)"', row)
        if not lang or not slug or lang.group(1).strip().lower() != language_name.lower():
            continue

        rating = re.search(r'class="rating-cell">\s*<span[^>]*>(-?\d+)<', row)
        names = re.search(r'</span>(.*?)</a>', row[slug.start():], re.S)
        releases = [re.sub(r'\s+', ' ', n).strip() for n in re.split(r'<br\s*/?>', names.group(1) if names else '')]
        found.append({
            'slug': slug.group(1),
            'rating': int(rating.group(1)) if rating else 0,
            'releases': [n for n in releases if n],
        })

    return found


def matchScore(candidate, release_name):
    """ Prefer a subtitle made for the same kind of release (group, resolution, source), so it is in sync """
    ours = set(re.split(r'[\W_]+', release_name.lower()))
    theirs = set(re.split(r'[\W_]+', ' '.join(candidate['releases']).lower()))

    score = candidate['rating']
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

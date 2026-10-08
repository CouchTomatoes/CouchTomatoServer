import json
import re
import traceback

import requests

from couchpotato import Env
from couchpotato.core.event import addEvent, fireEvent
from couchpotato.core.helpers.encoding import tryUrlencode
from couchpotato.core.helpers.variable import tryInt, tryFloat, splitString
from couchpotato.core.logger import CPLog
from couchpotato.core.media.movie.providers.base import MovieProvider


log = CPLog(__name__)

autoload = 'OMDBAPI'


class OMDBAPI(MovieProvider):

    urls = {
        'search': 'https://www.omdbapi.com/?apikey=%s&type=movie&%s',
        'info': 'https://www.omdbapi.com/?apikey=%s&type=movie&i=%s',
    }

    http_time_between_calls = 0

    key_rejected = None  # the key OMDb answered 401 for

    def __init__(self):
        addEvent('info.search', self.search)
        addEvent('movie.search', self.search)
        addEvent('movie.info', self.getInfo)

        addEvent('app.load', self.checkKey)
        addEvent('setting.save.omdbapi.api_key.after', self.checkKey)

    def checkKey(self):
        """ Ask OMDb once whether the key works, instead of failing every lookup quietly """
        self.key_rejected = None
        key = self.getApiKey()
        if not key:
            return

        try:
            # The app's own opener: same proxy/SSL settings as every other call
            self.urlopen(self.urls['info'] % (key, 'tt0133093'), show_error = False,
                         headers = {'User-Agent': Env.getIdentifier()})
            return
        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else None
        except Exception:
            log.debug('Could not reach OMDb to check the API key: %s', traceback.format_exc(0))
            return  # network trouble says nothing about the key

        if status == 401:
            self.key_rejected = key
            message = 'OMDb rejected its API key, so IMDb ratings and OMDb lookups are off. ' \
                      'Get a free key at https://www.omdbapi.com/apikey.aspx (activate it from the email) ' \
                      'and enter it in Settings > Searcher > OMDb.'
            log.error(message)
            fireEvent('notify', message = message, data = {'important': True})

    def search(self, q, limit = 12):
        if self.isDisabled():
            return []

        name_year = fireEvent('scanner.name_year', q, single = True)

        if not name_year or (name_year and not name_year.get('name')):
            name_year = {
                'name': q
            }

        cache_key = 'omdbapi.cache.%s' % q
        url = self.urls['search'] % (self.getApiKey(), tryUrlencode({'t': name_year.get('name'), 'y': name_year.get('year', '')}))
        cached = self.getCache(cache_key, url, timeout = 3, headers = {'User-Agent': Env.getIdentifier()})

        if cached:
            result = self.parseMovie(cached)
            if result.get('titles') and len(result.get('titles')) > 0:
                log.info('Found: %s', result['titles'][0] + ' (' + str(result.get('year')) + ')')
                return [result]

            return []

        return []

    def getInfo(self, identifier = None, **kwargs):
        if self.isDisabled() or not identifier:
            return {}

        cache_key = 'omdbapi.cache.%s' % identifier
        url = self.urls['info'] % (self.getApiKey(), identifier)
        cached = self.getCache(cache_key, url, timeout = 3, headers = {'User-Agent': Env.getIdentifier()})

        if cached:
            result = self.parseMovie(cached)
            if result.get('titles') and len(result.get('titles')) > 0:
                log.info('Found: %s', result['titles'][0] + ' (' + str(result['year']) + ')')
                return result

        return {}

    def parseMovie(self, movie):

        movie_data = {}
        try:

            try:
                # The HTTP helper returns bytes in Python 3; json.loads takes either
                if isinstance(movie, (bytes, str)):
                    movie = json.loads(movie)
            except ValueError:
                log.info('No proper json to decode')
                return movie_data

            if movie.get('Response') == 'Parse Error' or movie.get('Response') == 'False':
                return movie_data

            if movie.get('Type').lower() != 'movie':
                return movie_data

            tmp_movie = movie.copy()
            for key in tmp_movie:
                tmp_movie_elem = tmp_movie.get(key)
                if not isinstance(tmp_movie_elem, str) or tmp_movie_elem.lower() == 'n/a':
                    del movie[key]

            year = tryInt(movie.get('Year', ''))

            movie_data = {
                'type': 'movie',
                'via_imdb': True,
                'titles': [movie.get('Title')] if movie.get('Title') else [],
                'original_title': movie.get('Title'),
                'images': {
                    'poster': [movie.get('Poster', '')] if movie.get('Poster') and len(movie.get('Poster', '')) > 4 else [],
                },
                'rating': {
                    'imdb': (tryFloat(movie.get('imdbRating', 0)), tryInt(movie.get('imdbVotes', '').replace(',', ''))),
                    #'rotten': (tryFloat(movie.get('tomatoRating', 0)), tryInt(movie.get('tomatoReviews', '').replace(',', ''))),
                },
                'imdb': str(movie.get('imdbID', '')),
                'mpaa': str(movie.get('Rated', '')),
                'runtime': self.runtimeToMinutes(movie.get('Runtime', '')),
                'released': movie.get('Released'),
                'year': year if isinstance(year, int) else None,
                'plot': movie.get('Plot'),
                'genres': splitString(movie.get('Genre', '')),
                'directors': splitString(movie.get('Director', '')),
                'writers': splitString(movie.get('Writer', '')),
                'actors': splitString(movie.get('Actors', '')),
            }
            movie_data = dict((k, v) for k, v in list(movie_data.items()) if v)
        except:
            log.error('Failed parsing IMDB API json: %s', traceback.format_exc())

        return movie_data

    def isDisabled(self):
        key = self.getApiKey()
        # Optional provider: no key, or a key OMDb rejected, just means it sits out (checkKey said why)
        return not key or key == self.key_rejected

    def getApiKey(self):
        apikey = self.conf('api_key')
        return apikey

    def runtimeToMinutes(self, runtime_str):
        runtime = 0

        regex = '(\d*.?\d+).(h|hr|hrs|mins|min)+'
        matches = re.findall(regex, runtime_str)
        for match in matches:
            nr, size = match
            runtime += tryInt(nr) * (60 if 'h' == str(size)[0] else 1)

        return runtime


config = [{
    'name': 'omdbapi',
    'groups': [
        {
            'tab': 'searcher',
            'name': 'omdbapi',
            'label': 'OMDb',
            'description': 'Optional. Adds IMDb ratings and a second lookup source. Needs a free key from '
                           '<a href="https://www.omdbapi.com/apikey.aspx" target="_blank">omdbapi.com</a> '
                           '(activate it from the email).',
            'options': [
                {
                    'name': 'api_key',
                    'default': '',  # the old shared default (bbc0e412) was never activated
                    'label': 'Api Key',
                },
            ],
        },
    ],
}]

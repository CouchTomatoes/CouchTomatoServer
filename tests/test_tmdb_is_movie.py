"""
Tests for TheMovieDb.isMovie (board #31, backlog §10 PR 1). "Is this IMDb id a movie?" used to be asked of
the CouchTomato API; it now asks TMDB's /find directly, so no API server is needed. The fixtures are real
/find answers recorded 2026-11-19.
Run from the repo root:  python3 -m unittest discover -s tests
"""
import json
import os
import sys
import unittest
from unittest import mock

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)
sys.path.insert(0, os.path.join(root, 'libs'))

from couchpotato.core.media.movie.providers.info import couchpotatoapi
from couchpotato.core.media.movie.providers.info.themoviedb import TheMovieDb

FIXTURES = os.path.join(root, 'couchpotato', 'core', 'media', 'movie', 'providers', 'info', 'fixtures')


def recorded(name):
    with open(os.path.join(FIXTURES, 'tmdb_find_%s.json' % name)) as f:
        return json.load(f)


def tmdb(response):
    provider = TheMovieDb.__new__(TheMovieDb)  # skip __init__: no event registration or settings needed
    provider.isDisabled = lambda: False
    provider.request = mock.Mock(return_value = response)
    return provider


class IsMovieTest(unittest.TestCase):

    def test_movie(self):
        provider = tmdb(recorded('matrix_1999'))
        self.assertIs(provider.isMovie('tt0133093'), True)
        provider.request.assert_called_once_with('find/tt0133093', {'external_source': 'imdb_id'})

    def test_tv_show_is_not_a_movie(self):
        self.assertIs(tmdb(recorded('breaking_bad_tv')).isMovie('tt0903747'), False)

    def test_tv_episode_is_not_a_movie(self):
        self.assertIs(tmdb(recorded('breaking_bad_episode')).isMovie('tt0959621'), False)

    def test_id_tmdb_does_not_know_is_allowed(self):
        # The old API answered True when it didn't know; a gap in TMDB must not block an add
        self.assertIs(tmdb(recorded('unknown')).isMovie('tt9999999999'), True)

    def test_failed_lookup_is_allowed(self):
        self.assertIs(tmdb(None).isMovie('tt0133093'), True)  # network error / 401
        self.assertIs(tmdb({'success': False, 'status_code': 7}).isMovie('tt0133093'), True)  # error body

    def test_no_identifier(self):
        provider = tmdb(None)
        self.assertIs(provider.isMovie(None), True)
        self.assertFalse(provider.request.called)

    def test_adding_keyword_is_accepted(self):
        # movie.add fires movie.is_movie with adding = True
        self.assertIs(tmdb(recorded('matrix_1999')).isMovie(identifier = 'tt0133093', adding = True), True)


class ApiNoLongerAnswersTest(unittest.TestCase):

    def test_api_does_not_register_is_movie_or_release_dates(self):
        registered = []
        with mock.patch.object(couchpotatoapi, 'addEvent', side_effect = lambda name, *a, **k: registered.append(name)):
            couchpotatoapi.CouchPotatoApi()
        self.assertNotIn('movie.is_movie', registered)
        self.assertNotIn('movie.info.release_date', registered)


if __name__ == '__main__':
    unittest.main()

"""
Tests for TheMovieDb.getSuggestions (board #31, backlog section 10, PR 2). Suggestions used to come from the
CouchTomato API's shared-votes store; they now come from TMDB's recommendations for each library movie.
Fixtures are real TMDB answers recorded 2026-11-19 (The Matrix = 603, The Matrix Reloaded = 604).
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
from couchpotato.core.media.movie.providers.info.themoviedb import TheMovieDb, rankRecommendations

FIXTURES = os.path.join(root, 'couchpotato', 'core', 'media', 'movie', 'providers', 'info', 'fixtures')

MATRIX, RELOADED, GENISYS = 603, 604, 87101
LIBRARY = {'tt0133093': MATRIX, 'tt0234215': RELOADED}


def recommendations(tmdb_id):
    with open(os.path.join(FIXTURES, 'tmdb_recommendations_%s.json' % tmdb_id)) as f:
        return json.load(f)['results']


def fakeTmdb(calls):
    """ A provider whose request() answers from the fixtures and records every call """
    def request(call, params = None, return_key = None):
        calls.append(call)
        if call.startswith('find/'):
            tmdb_id = LIBRARY.get(call.split('/')[1])
            return {'movie_results': [{'id': tmdb_id}] if tmdb_id else []}
        if call.endswith('/recommendations'):
            return recommendations(int(call.split('/')[1]))
        if call == 'movie/popular':
            return [{'id': 1}, {'id': 2}]
        return None

    provider = TheMovieDb.__new__(TheMovieDb)
    provider.isDisabled = lambda: False
    provider.request = request
    provider.parseMovie = lambda movie, extended = True: {'imdb': 'tt%07d' % movie['id'], 'tmdb_id': movie['id'], 'titles': ['x']}
    return provider


class RankTest(unittest.TestCase):

    def test_recommended_by_both_ranks_first(self):
        ranked = rankRecommendations([recommendations(MATRIX), recommendations(RELOADED)], exclude = {MATRIX, RELOADED})
        self.assertEqual(ranked[0], GENISYS)  # #2 on both lists

    def test_library_movies_are_excluded(self):
        ranked = rankRecommendations([recommendations(MATRIX), recommendations(RELOADED)], exclude = {MATRIX, RELOADED})
        self.assertNotIn(MATRIX, ranked)
        self.assertNotIn(RELOADED, ranked)
        self.assertEqual(len(ranked), len(set(ranked)))

    def test_bad_input(self):
        self.assertEqual(rankRecommendations([None, [None, {}, {'id': 5}]]), [5])


class SuggestTest(unittest.TestCase):

    def test_top_ten_full_info_without_library_or_ignored(self):
        calls = []
        ignored = 'tt%07d' % GENISYS
        found = fakeTmdb(calls).getSuggestions(movies = list(LIBRARY), ignore = [ignored])
        imdbs = [m['imdb'] for m in found]
        self.assertEqual(len(found), 10)
        self.assertNotIn(ignored, imdbs)
        self.assertFalse(set(LIBRARY) & set(imdbs))
        self.assertTrue(all(m.get('titles') for m in found))  # full info, as the suggestion page needs

    def test_empty_library_uses_popular(self):
        calls = []
        found = fakeTmdb(calls).getSuggestions(movies = [], ignore = [])
        self.assertIn('movie/popular', calls)
        self.assertEqual([m['tmdb_id'] for m in found], [1, 2])

    def test_unknown_library_movie_is_skipped(self):
        calls = []
        found = fakeTmdb(calls).getSuggestions(movies = ['tt0000001'])
        self.assertEqual(found, [])

    def test_api_no_longer_answers_suggest(self):
        registered = []
        with mock.patch.object(couchpotatoapi, 'addEvent', side_effect = lambda name, *a, **k: registered.append(name)):
            couchpotatoapi.CouchPotatoApi()
        self.assertNotIn('movie.suggest', registered)


class ForgetCachedTest(unittest.TestCase):
    """ The suggestion list is cached for weeks; adding or deleting a movie must clear it """

    def test_forget_deletes_the_cached_list(self):
        from couchpotato.core.helpers.variable import md5
        from couchpotato.core.media.movie import suggestion
        from couchpotato.environment import Env

        cache = mock.Mock()
        plugin = suggestion.Suggestion.__new__(suggestion.Suggestion)
        with mock.patch.object(Env, 'get', side_effect = lambda key, *a, **k: cache if key == 'cache' else None):
            self.assertTrue(plugin.forgetCached())
        cache.delete.assert_called_once_with(md5('suggestion_cached'))

    def test_add_and_delete_fire_forget(self):
        for path in ('couchpotato/core/media/movie/_base/main.py', 'couchpotato/core/media/_base/media/main.py'):
            with open(os.path.join(root, path)) as f:
                self.assertIn("fireEvent('suggestion.forget')", f.read(), path)


if __name__ == '__main__':
    unittest.main()

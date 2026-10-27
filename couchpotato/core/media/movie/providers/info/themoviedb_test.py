import calendar
import json
import os
import time
from unittest import TestCase, mock

from couchpotato.core.media.movie._base import main as movie_main
from couchpotato.core.media.movie.providers.info.couchpotatoapi import CouchPotatoApi
from couchpotato.core.media.movie.providers.info import themoviedb
from couchpotato.core.media.movie.providers.info.themoviedb import TheMovieDb

FIXTURES = os.path.join(os.path.dirname(__file__), 'fixtures')

# Fixed "now" so the recorded responses always give the same answer: 2026-10-27
NOW = calendar.timegm((2026, 10, 27, 0, 0, 0))
DAY = 86400


def recorded(name):
    """ TMDB /movie/{id}/release_dates responses, recorded 2026-10-27 """
    with open(os.path.join(FIXTURES, 'tmdb_release_dates_%s.json' % name)) as f:
        return json.load(f)['results']


def stamp(ymd):
    return calendar.timegm(time.strptime(ymd, '%Y-%m-%d'))


def releaseDates(countries, now):
    return themoviedb.releaseDates(countries, now = now)


def tmdb(response):
    provider = TheMovieDb.__new__(TheMovieDb)  # skip __init__: no event registration or settings needed
    provider.isDisabled = lambda: False
    provider.request = mock.Mock(return_value = response)
    return provider


class ReleaseDatesTest(TestCase):

    def test_new_movie_gets_us_dates(self):
        # Obsession (2026): US theatrical 05-15, digital 06-30 (earlier than physical 07-14)
        dates = releaseDates(recorded('obsession_2026'), now = NOW)
        self.assertEqual(dates['theater'], stamp('2026-05-15'))
        self.assertEqual(dates['dvd'], stamp('2026-06-30'))
        self.assertEqual(dates['bluray'], False)
        self.assertEqual(dates['expires'], NOW + 21 * DAY)  # out on digital for months: settled

    def test_old_movie(self):
        dates = releaseDates(recorded('wall_e_2008'), now = NOW)
        self.assertEqual(dates['theater'], stamp('2008-06-27'))
        self.assertEqual(dates['dvd'], stamp('2008-11-18'))
        self.assertEqual(dates['expires'], NOW + 21 * DAY)

    def test_movie_without_cinema_or_home_dates(self):
        # Only a premiere (type 1) is listed: nothing the searcher can use, and checked again in 3 days, not 3 weeks
        dates = releaseDates(recorded('no_release_dates'), now = NOW)
        self.assertEqual(dates, {'theater': 0, 'dvd': 0, 'bluray': False, 'expires': NOW + 3 * DAY})

    def test_no_us_date_uses_earliest_anywhere(self):
        countries = [
            {'iso_3166_1': 'GB', 'release_dates': [{'type': 3, 'release_date': '2026-03-02T00:00:00.000Z'}]},
            {'iso_3166_1': 'FR', 'release_dates': [{'type': 3, 'release_date': '2026-02-20T00:00:00.000Z'}]},
        ]
        self.assertEqual(releaseDates(countries, now = NOW)['theater'], stamp('2026-02-20'))

    def test_future_movie_is_rechecked_soon(self):
        countries = [{'iso_3166_1': 'US', 'release_dates': [{'type': 3, 'release_date': '2027-01-08T00:00:00.000Z'}]}]
        dates = releaseDates(countries, now = NOW)
        self.assertEqual(dates['theater'], stamp('2027-01-08'))
        self.assertEqual(dates['expires'], NOW + 3 * DAY)


class TheMovieDbReleaseDateTest(TestCase):

    def test_asks_tmdb_by_imdb_id(self):
        provider = tmdb(recorded('obsession_2026'))
        dates = provider.getReleaseDate('tt37287335')
        provider.request.assert_called_once_with('movie/tt37287335/release_dates', return_key = 'results')
        self.assertEqual(dates['theater'], stamp('2026-05-15'))

    def test_failing_upstream_returns_nothing(self):
        # request() returns None on a network error or a 401/404 from TMDB
        self.assertEqual(tmdb(None).getReleaseDate('tt37287335'), {})
        # ... and the bare error body when TMDB answers without 'results'
        self.assertEqual(tmdb({'status_code': 34, 'status_message': 'not found'}).getReleaseDate('tt0000001'), {})


class CouchPotatoApiReleaseDateTest(TestCase):

    def test_zeros_from_the_api_are_dropped(self):
        # What the self-hosted API answered for Obsession on 2026-10-26. Kept as-is, these zeros would
        # overwrite TMDB's dates when the two answers are merged.
        api = CouchPotatoApi.__new__(CouchPotatoApi)
        api.getRequestHeaders = lambda: {}
        api.getJsonData = mock.Mock(return_value = {'dvd': 0, 'theater': 0, 'bluray': False, 'expires': 1793254638})
        self.assertEqual(api.getReleaseDate('tt37287335'), {'expires': 1793254638})


class UpdateReleaseDateTest(TestCase):

    def update(self, stored, fetched):
        media = {'_id': 'm1', 'identifiers': {'imdb': 'tt37287335'}, 'info': {'release_date': stored}}
        db = mock.Mock()
        db.get.return_value = media
        with mock.patch.object(movie_main, 'get_db', return_value = db), \
                mock.patch.object(movie_main, 'fireEvent', return_value = fetched) as fire:
            dates = movie_main.MovieBase.updateReleaseDate(mock.Mock(), 'm1')
        return dates, fire

    def test_stored_zeros_are_looked_up_again_before_they_expire(self):
        # Zeros the old API cached for 3 weeks: the movie must not wait for them to expire
        stored = {'dvd': 0, 'theater': 0, 'bluray': False, 'expires': time.time() + 20 * DAY}
        fetched = {'theater': stamp('2026-05-15'), 'dvd': stamp('2026-06-30'), 'bluray': False, 'expires': time.time() + 21 * DAY}
        dates, fire = self.update(stored, fetched)
        self.assertTrue(fire.called)
        self.assertEqual(dates['theater'], stamp('2026-05-15'))

    def test_known_dates_are_not_looked_up_again(self):
        stored = {'dvd': stamp('2026-06-30'), 'theater': stamp('2026-05-15'), 'bluray': False, 'expires': time.time() + 3 * DAY}
        dates, fire = self.update(stored, {})
        self.assertFalse(fire.called)
        self.assertEqual(dates, stored)

    def test_every_source_failing_gives_zeros_not_an_error(self):
        dates, fire = self.update({}, {})
        self.assertTrue(fire.called)
        self.assertEqual(dates, {'dvd': 0, 'theater': 0, 'bluray': False})

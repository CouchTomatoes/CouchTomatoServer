"""
Tests for pickSearchResult in couchpotato/core/plugins/scanner.py. The scanner used the first
search hit, which linked 'Race (2008)' to Death Race and 'Mrs (2025)' to Mrs. Doubtfire on the
Pi4 (board #40). The result lists below are what movie.search returned on 2026-11-19.
Run from the repo root:  python3 -m unittest discover -s tests
"""
import os
import sys
import unittest

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)
sys.path.insert(0, os.path.join(root, 'libs'))

from couchpotato.core.plugins.scanner import pickSearchResult


def movie(imdb, title, year):
    return {'imdb': imdb, 'titles': [title], 'year': year}


RACE_2008 = [movie('tt0452608', 'Death Race', 2008), movie('tt1017456', 'Race', 2008),
             movie('tt1037011', 'Ben 10: Race Against Time', 2008), movie('tt0969240', 'African Race', 2008)]
MRS_2025 = [movie('tt0107614', 'Mrs. Doubtfire', 1993), movie('tt0067411', 'McCabe & Mrs. Miller', 1971),
            movie('tt27032419', 'Mrs.', 2023), movie('tt6614198', 'And Mrs.', 2024),
            movie('tt36061838', 'Mrs. Christmas', 2025), movie('tt37526897', 'Mrs.', 2026)]


class PickSearchResultTest(unittest.TestCase):

    def test_race(self):
        self.assertEqual(pickSearchResult(RACE_2008, 'race', 2008)['imdb'], 'tt1017456')

    def test_death_race_still_matches_itself(self):
        self.assertEqual(pickSearchResult(RACE_2008, 'death race', 2008)['imdb'], 'tt0452608')

    def test_mrs(self):
        # Exact title within 2 years, first in search order (the 2023 festival film released 2025)
        self.assertEqual(pickSearchResult(MRS_2025, 'mrs', 2025)['imdb'], 'tt27032419')

    def test_same_year_when_no_exact_title(self):
        self.assertEqual(pickSearchResult(MRS_2025, 'mrs christmas special', 2025)['imdb'], 'tt36061838')

    def test_falls_back_to_first_hit(self):
        self.assertEqual(pickSearchResult(RACE_2008, 'something else', 1990)['imdb'], 'tt0452608')
        self.assertIsNone(pickSearchResult([], 'race', 2008))


if __name__ == '__main__':
    unittest.main()

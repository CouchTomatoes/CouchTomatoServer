"""
Tests for stripCollectionIndex in couchpotato/core/plugins/scanner.py: numbered collection files
("1 harry potter and the sorcerers stone 2001") found nothing on TMDB because of the leading index.
Run from the repo root:  python3 -m unittest discover -s tests
"""
import os
import sys
import unittest

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)
sys.path.insert(0, os.path.join(root, 'libs'))

from couchpotato.core.plugins.scanner import stripCollectionIndex


class StripCollectionIndexTest(unittest.TestCase):

    def test_numbered_collection_names(self):
        self.assertEqual(stripCollectionIndex('1 harry potter and the sorcerers stone'), 'harry potter and the sorcerers stone')
        self.assertEqual(stripCollectionIndex('07 - harry potter and the deathly hallows part 1'), 'harry potter and the deathly hallows part 1')
        self.assertEqual(stripCollectionIndex('3. the dark knight rises'), 'the dark knight rises')

    def test_no_index(self):
        self.assertIsNone(stripCollectionIndex('harry potter and the sorcerers stone'))
        self.assertIsNone(stripCollectionIndex(None))
        self.assertIsNone(stripCollectionIndex(''))

    def test_number_only_titles_are_left_alone(self):
        # "1917", "300" and "2 1" have nothing left after an index, so there is no fallback
        self.assertIsNone(stripCollectionIndex('1917'))
        self.assertIsNone(stripCollectionIndex('300'))
        self.assertIsNone(stripCollectionIndex('2 12'))


if __name__ == '__main__':
    unittest.main()

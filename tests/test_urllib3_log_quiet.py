"""Debug logging must not write urllib3's request lines: they carry indexer API keys and passkeys unmasked."""
import logging
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'libs'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from couchpotato.runner import quietNoisyLoggers


class TestUrllib3LogQuiet(unittest.TestCase):

    def test_urllib3_debug_lines_are_dropped(self):
        root = logging.getLogger()
        old = root.level
        root.setLevel(logging.DEBUG)
        try:
            quietNoisyLoggers()
            pool = logging.getLogger('urllib3.connectionpool')
            self.assertFalse(pool.isEnabledFor(logging.DEBUG))
            self.assertTrue(pool.isEnabledFor(logging.ERROR))
        finally:
            root.setLevel(old)


if __name__ == '__main__':
    unittest.main()

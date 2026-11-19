"""
Tests for describeUrlError in couchpotato/core/plugins/base.py: a failed request is logged as
one readable line (the real cause and host) instead of urllib3's chained traceback.
Run from the repo root:  python3 -m unittest discover -s tests
"""
import os
import socket
import sys
import unittest

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)
sys.path.insert(0, os.path.join(root, 'libs'))

import requests
from couchpotato.core.plugins.base import describeUrlError


class DescribeUrlErrorTest(unittest.TestCase):

    def test_unresolvable_host_names_the_host(self):
        # The Pi4's real failure: pi5.local (FlareSolverr) not resolving
        try:
            requests.get('http://no-such-host.invalid:8191/v1', timeout = 5)
        except requests.ConnectionError as e:
            text = describeUrlError(e)
        self.assertIn('no-such-host.invalid', text)
        self.assertIn('gaierror', text)
        self.assertNotIn('\n', text)

    def test_http_status(self):
        response = requests.Response()
        response.status_code = 521
        response.reason = 'Web Server Is Down'
        e = requests.HTTPError('521 Server Error', response = response)
        self.assertEqual(describeUrlError(e), 'HTTP 521 Web Server Is Down')

    def test_plain_ioerror(self):
        self.assertEqual(describeUrlError(IOError('FlareSolverr could not open x')), 'OSError: FlareSolverr could not open x')


if __name__ == '__main__':
    unittest.main()

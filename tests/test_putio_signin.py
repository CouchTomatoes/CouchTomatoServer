"""
Tests for the put.io code-link sign-in (backlog §10, replaces the CouchTomato API's /authorize/putio route).
The replies are put.io's real answers recorded 2026-11-20 (oob/code, a pending poll, an unknown code).
Run from the repo root:  python3 -m unittest discover -s tests
"""
import os
import sys
import time
import unittest
from unittest import mock

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)
sys.path.insert(0, os.path.join(root, 'libs'))

from couchpotato.core.downloaders.putio.main import PutIO

CODE = {'code': 'CBQWDH', 'qr_code_url': 'https://api.put.io/v2/oauth2/oob/qr/CBQWDH', 'status': 'OK'}
PENDING = {'oauth_token': None, 'status': 'OK'}
LINKED = {'oauth_token': 'TOKEN123', 'status': 'OK'}
UNKNOWN = {'error_type': 'NotFound', 'status': 'ERROR', 'status_code': 404}


class Reply(object):
    def __init__(self, status, body):
        self.status_code = status
        self.body = body
        self.content = b'x'

    def json(self):
        return self.body


def putio(replies, app_id = '1234'):
    plugin = PutIO.__new__(PutIO)  # skip __init__: no event registration
    plugin.device = None
    plugin.app_id = app_id
    store = {}
    plugin.conf = lambda name, value = None, default = None: store.__setitem__(name, value) if value is not None else store.get(name, default)
    plugin.store = store
    plugin.opener = mock.Mock()
    plugin.opener.get.side_effect = lambda url, **kwargs: replies.pop(0)
    return plugin


class PutIOSignInTest(unittest.TestCase):

    def setUp(self):
        patcher = mock.patch('couchpotato.core.downloaders.putio.main.Env')
        self.env = patcher.start()
        self.addCleanup(patcher.stop)

    def use(self, plugin):
        self.env.get.side_effect = lambda key: plugin.opener if key == 'http_opener' else None
        return plugin

    def test_without_app_id_sign_in_says_so(self):
        plugin = self.use(putio([], app_id = ''))
        self.assertFalse(plugin.startSignIn()['success'])
        plugin.opener.get.assert_not_called()

    def test_full_link(self):
        plugin = self.use(putio([Reply(200, CODE), Reply(200, PENDING), Reply(200, LINKED)]))

        started = plugin.startSignIn()
        self.assertEqual((started['user_code'], started['verification_url']), ('CBQWDH', 'https://put.io/link'))
        self.assertEqual(plugin.opener.get.call_args.kwargs['params'], {'app_id': '1234'})

        self.assertEqual(plugin.pollSignIn()['status'], 'pending')
        self.assertTrue(plugin.opener.get.call_args.args[0].endswith('/oob/code/CBQWDH'))
        self.assertEqual(plugin.pollSignIn(), {'success': True, 'status': 'connected'})

        self.assertEqual(plugin.store['oauth_token'], 'TOKEN123')
        self.assertIsNone(plugin.device)
        connect, read = plugin.opener.get.call_args.kwargs['timeout']
        self.assertLessEqual(connect, 3)

    def test_code_put_io_no_longer_knows_ends_the_link(self):
        plugin = self.use(putio([Reply(404, UNKNOWN)]))
        plugin.device = {'code': 'ZZZZZZ', 'expires': time.time() + 60}
        self.assertEqual(plugin.pollSignIn()['status'], 'expired')
        self.assertIsNone(plugin.device)
        self.assertNotIn('oauth_token', plugin.store)

    def test_poll_after_the_code_ran_out_does_not_call_put_io(self):
        plugin = self.use(putio([]))
        plugin.device = {'code': 'c', 'expires': time.time() - 1}
        self.assertEqual(plugin.pollSignIn()['status'], 'expired')
        plugin.opener.get.assert_not_called()


if __name__ == '__main__':
    unittest.main()

"""
Tests for the Trakt device-code sign-in (backlog §10, replaces the CouchTomato API's /authorize/trakt routes).
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

from couchpotato.core.media.movie.providers.automation.trakt.main import Trakt


class Reply(object):
    def __init__(self, status, body = None):
        self.status_code = status
        self.body = body
        self.content = b'x' if body is not None else b''

    def json(self):
        return self.body


def trakt(replies, settings = None, keys = True):
    """ A Trakt plugin whose api.trakt.tv answers with `replies` (path -> Reply, or a list used in order) """
    plugin = Trakt.__new__(Trakt)  # skip __init__: no event registration
    plugin.device = None
    if keys:
        plugin.client_id, plugin.client_secret = 'id', 'secret'
    store = dict(settings or {})
    plugin.conf = lambda name, value = None, default = None: store.__setitem__(name, value) if value is not None else store.get(name, default)
    plugin.store = store

    def post(url, **kwargs):
        answer = replies[url.split('api.trakt.tv/')[1]]
        return answer.pop(0) if isinstance(answer, list) else answer

    plugin.opener = mock.Mock()
    plugin.opener.post.side_effect = post
    return plugin


class TraktSignInTest(unittest.TestCase):

    def setUp(self):
        patcher = mock.patch('couchpotato.core.media.movie.providers.automation.trakt.main.Env')
        self.env = patcher.start()
        self.addCleanup(patcher.stop)

    def use(self, plugin):
        self.env.get.side_effect = lambda key: plugin.opener if key == 'http_opener' else None
        return plugin

    def test_without_app_keys_sign_in_says_so(self):
        plugin = self.use(trakt({}, keys = False))
        self.assertFalse(plugin.startSignIn()['success'])
        plugin.opener.post.assert_not_called()

    def test_full_sign_in(self):
        plugin = self.use(trakt({
            'oauth/device/code': Reply(200, {'device_code': 'secret-device', 'user_code': 'ABCD1234',
                                             'verification_url': 'https://trakt.tv/activate', 'expires_in': 600, 'interval': 5}),
            'oauth/device/token': [Reply(400), Reply(429), Reply(200, {
                'access_token': 'tok', 'refresh_token': 'ref', 'created_at': 1000, 'expires_in': 86400})],
        }))

        started = plugin.startSignIn()
        self.assertEqual(started['user_code'], 'ABCD1234')
        self.assertEqual(started['interval'], 5)
        self.assertNotIn('secret-device', str(started))  # the device code stays on the server

        self.assertEqual(plugin.pollSignIn()['status'], 'pending')
        self.assertEqual(plugin.pollSignIn()['status'], 'slow_down')
        self.assertEqual(plugin.pollSignIn(), {'success': True, 'status': 'connected'})

        self.assertEqual(plugin.store['automation_oauth_token'], 'tok')
        self.assertEqual(plugin.store['automation_oauth_refresh'], 'ref')
        self.assertEqual(plugin.store['automation_oauth_expires'], 87400)
        self.assertIsNone(plugin.device)

        payload = plugin.opener.post.call_args.kwargs['data']
        self.assertIn('"code": "secret-device"', payload)
        connect, read = plugin.opener.post.call_args.kwargs['timeout']
        self.assertLessEqual(connect, 3)

    def test_denied_and_expired_end_the_sign_in(self):
        for status, answer in ((418, 'denied'), (410, 'expired'), (404, 'invalid'), (409, 'used')):
            plugin = self.use(trakt({'oauth/device/token': Reply(status)}))
            plugin.device = {'code': 'c', 'expires': time.time() + 60}
            self.assertEqual(plugin.pollSignIn()['status'], answer)
            self.assertIsNone(plugin.device)

    def test_poll_after_the_code_ran_out_does_not_call_trakt(self):
        plugin = self.use(trakt({}))
        plugin.device = {'code': 'c', 'expires': time.time() - 1}
        self.assertEqual(plugin.pollSignIn()['status'], 'expired')
        plugin.opener.post.assert_not_called()

    def test_token_far_from_expiry_is_left_alone(self):
        plugin = self.use(trakt({}, {'automation_oauth_token': 't', 'automation_oauth_refresh': 'r',
                                     'automation_oauth_expires': int(time.time()) + 30 * 86400}))
        self.assertTrue(plugin.refreshToken())
        plugin.opener.post.assert_not_called()

    def test_token_near_expiry_is_renewed(self):
        plugin = self.use(trakt({'oauth/token': Reply(200, {
            'access_token': 'new', 'refresh_token': 'new-ref', 'created_at': 5000, 'expires_in': 100})},
            {'automation_oauth_token': 't', 'automation_oauth_refresh': 'r',
             'automation_oauth_expires': int(time.time()) + 3600}))
        self.assertTrue(plugin.refreshToken())
        self.assertEqual(plugin.store['automation_oauth_token'], 'new')
        self.assertEqual(plugin.store['automation_oauth_expires'], 5100)
        self.assertIn('"grant_type": "refresh_token"', plugin.opener.post.call_args.kwargs['data'])

    def test_old_couchpotato_token_is_reported_not_refreshed(self):
        # Signed in through the old API: no expiry stored, and its app no longer exists on Trakt
        plugin = self.use(trakt({}, {'automation_oauth_token': 't', 'automation_oauth_refresh': 'r'}))
        self.assertFalse(plugin.refreshToken())
        plugin.opener.post.assert_not_called()

    def test_refused_renewal_keeps_the_old_token(self):
        plugin = self.use(trakt({'oauth/token': Reply(401, {'error': 'invalid_grant'})},
                                {'automation_oauth_token': 't', 'automation_oauth_refresh': 'r',
                                 'automation_oauth_expires': int(time.time()) - 10}))
        self.assertFalse(plugin.refreshToken())
        self.assertEqual(plugin.store['automation_oauth_token'], 't')


if __name__ == '__main__':
    unittest.main()

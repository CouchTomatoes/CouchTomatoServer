"""
Tests for the X (Twitter) notifier on X's v2 API with the user's own app keys (backlog §10, step 4).
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

import requests

from couchpotato.core.notifications.twitter import main as twitter_main
from couchpotato.core.notifications.twitter.main import Twitter, oauthHeader


KEYS = {'consumer_key': 'ck', 'consumer_secret': 'cs', 'access_token_key': 'at', 'access_token_secret': 'ats'}


class Reply(object):
    def __init__(self, status, body = None):
        self.status_code = status
        self.body = body
        self.text = json.dumps(body) if body is not None else ''

    def json(self):
        if self.body is None:
            raise ValueError('no body')
        return self.body


def plugin(settings = None, replies = None):
    """ A Twitter plugin without event registration; X answers from `replies` (list, in order) """
    p = Twitter.__new__(Twitter)
    p.request_token = None
    p.default_title = 'CouchTomato'
    store = dict(settings if settings is not None else KEYS)
    p.conf = lambda name, value = None, default = None: store.__setitem__(name, value) if value is not None else store.get(name, default)
    p.sent = []

    def request(method, url, headers = None, data = None, timeout = None):
        p.sent.append((method, url, headers, json.loads(data) if data else None))
        return replies.pop(0) if replies else Reply(201, {'data': {'id': '1', 'text': 'x'}})

    p.patcher = mock.patch.object(twitter_main.requests, 'request', side_effect = request)
    p.patcher.start()
    return p


class OAuthSignature(unittest.TestCase):

    def test_matches_x_documented_example(self):
        """ X's "Creating a signature" page: these inputs must give hCtSmYh+iHYCEqBWrE7C7hYmtUk= """
        header = oauthHeader(
            'POST', 'https://api.twitter.com/1.1/statuses/update.json',
            'xvz1evFS4wEEPTGEFPHBog', 'kAcSOqF21Fu85e7zjz7ZN2U4ZRhfV3WpwPAoE3Z7kBw',
            '370773112-GmHxMAgYyLbNEtIKZeRNFsMKPR9EyMZeS9weJAEb', 'LswwdoUaIvS8ltyTt5jkRh4J50vUPVVHtR2YPi5kE',
            params = {'status': 'Hello Ladies + Gentlemen, a signed OAuth request!', 'include_entities': 'true'},
            nonce = 'kYjzVBB8Y0ZFabxSWbWovY3uYSQ2pTgmZeNu2VS4cg', timestamp = 1318622958)
        self.assertIn('oauth_signature="hCtSmYh%2BiHYCEqBWrE7C7hYmtUk%3D"', header)

    def test_header_carries_keys_but_never_secrets(self):
        header = oauthHeader('POST', 'https://api.x.com/2/tweets', 'ck', 'consumer-secret', 'at', 'token-secret')
        self.assertTrue(header.startswith('OAuth '))
        self.assertIn('oauth_consumer_key="ck"', header)
        self.assertIn('oauth_token="at"', header)
        self.assertNotIn('consumer-secret', header)
        self.assertNotIn('token-secret', header)


class Posting(unittest.TestCase):

    def tearDown(self):
        self.p.patcher.stop()

    def test_posts_to_v2_tweets(self):
        self.p = plugin()
        self.assertTrue(self.p.notify('Odyssey (2026) snatched'))
        method, url, headers, body = self.p.sent[0]
        self.assertEqual((method, url), ('POST', 'https://api.x.com/2/tweets'))
        self.assertEqual(body, {'text': '[CouchTomato] Odyssey (2026) snatched'})
        self.assertTrue(headers['Authorization'].startswith('OAuth '))

    def test_long_message_splits_in_two_posts_of_at_most_280(self):
        self.p = plugin(dict(KEYS, mention = 'friend'))
        self.assertTrue(self.p.notify('x' * 400))
        texts = [s[3]['text'] for s in self.p.sent]
        self.assertEqual(len(texts), 2)
        self.assertTrue(all(len(t) <= 280 for t in texts))
        self.assertTrue(texts[0].endswith('@friend 1/2') and texts[1].endswith('@friend 2/2'))
        self.assertEqual(''.join(t.rsplit(' @friend', 1)[0] for t in texts), '[CouchTomato] ' + 'x' * 400)

    def test_280_exactly_is_one_post(self):
        self.p = plugin()
        self.p.notify('y' * (280 - len('[CouchTomato] ')))
        self.assertEqual(len(self.p.sent), 1)

    def test_mention_is_added_to_a_short_post(self):
        self.p = plugin(dict(KEYS, mention = '@friend'))
        self.p.notify('Done')
        self.assertEqual(self.p.sent[0][3]['text'], '[CouchTomato] Done @friend')

    def test_missing_keys_fail_without_calling_x(self):
        self.p = plugin({'consumer_key': 'ck'})
        with mock.patch.object(twitter_main.log, 'error', autospec = True) as error:
            self.assertFalse(self.p.notify('x'))
        self.assertEqual(self.p.sent, [])
        self.assertIn('API key secret, Access token, Access token secret', error.call_args[0][1][0])

    def test_out_of_credits_is_logged_with_x_reason(self):
        self.p = plugin(replies = [Reply(402, {'title': 'Payment Required', 'detail': 'Your enrolled account does not have any credits'})])
        with mock.patch.object(twitter_main.log, 'error', autospec = True) as error:
            self.assertFalse(self.p.notify('x'))
        logged = str(error.call_args[0][1][1])
        self.assertIn('402', logged)
        self.assertIn('does not have any credits', logged)
        self.assertIn('out of credits', logged)
        self.assertNotIn('ats', logged.replace('credits', ''))

    def test_network_error_is_caught(self):
        self.p = plugin()
        self.p.patcher.stop()
        self.p.patcher = mock.patch.object(twitter_main.requests, 'request', side_effect = requests.ConnectionError('down'))
        self.p.patcher.start()
        with mock.patch.object(twitter_main.log, 'error', autospec = True):
            self.assertFalse(self.p.notify('x'))


class DirectMessages(unittest.TestCase):

    def tearDown(self):
        self.p.patcher.stop()

    def test_dm_looks_up_each_user_then_sends(self):
        self.p = plugin(dict(KEYS, direct_message = True, screen_name = 'me', mention = '@friend'),
                        [Reply(200, {'data': {'id': '11', 'username': 'me'}}), Reply(201, {'data': {}}),
                         Reply(200, {'data': {'id': '22', 'username': 'friend'}}), Reply(201, {'data': {}})])
        self.assertTrue(self.p.notify('Done'))
        urls = [(s[0], s[1].replace('https://api.x.com', '')) for s in self.p.sent]
        self.assertEqual(urls, [('GET', '/2/users/by/username/me'), ('POST', '/2/dm_conversations/with/11/messages'),
                                ('GET', '/2/users/by/username/friend'), ('POST', '/2/dm_conversations/with/22/messages')])
        self.assertEqual(self.p.sent[1][3], {'text': '[CouchTomato] Done'})

    def test_dm_to_unknown_user_fails_cleanly(self):
        self.p = plugin(dict(KEYS, direct_message = True, screen_name = 'nobody'), [Reply(200, {'errors': [{'detail': 'Could not find user'}]})])
        with mock.patch.object(twitter_main.log, 'error', autospec = True):
            self.assertFalse(self.p.notify('x'))

    def test_dm_without_screen_name_fails_cleanly(self):
        self.p = plugin(dict(KEYS, direct_message = True))
        with mock.patch.object(twitter_main.log, 'error', autospec = True):
            self.assertFalse(self.p.notify('x'))
        self.assertEqual(self.p.sent, [])


if __name__ == '__main__':
    unittest.main()

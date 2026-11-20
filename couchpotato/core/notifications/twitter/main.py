import base64
import hashlib
import hmac
import json
import time
import uuid
from urllib.parse import parse_qsl, quote

import requests

from couchpotato.api import addApiView
from couchpotato.core.helpers.variable import cleanHost
from couchpotato.core.logger import CPLog
from couchpotato.core.notifications.base import Notification
from couchpotato.environment import Env


log = CPLog(__name__)


def _enc(value):
    """ RFC 3986 percent-encoding, as OAuth 1.0a requires (only A-Z a-z 0-9 - . _ ~ stay as they are) """
    return quote(str(value), safe = '~')


def oauthHeader(method, url, consumer_key, consumer_secret, token = '', token_secret = '',
                params = None, nonce = None, timestamp = None, extra = None):
    """ The OAuth 1.0a (HMAC-SHA1) Authorization header for one request.

    `params` are the query string or form-body parameters, which are part of the signature.
    A JSON body is not (X signs only the oauth_* values for those). `extra` adds oauth_* values
    such as oauth_callback or oauth_verifier. """
    oauth = {
        'oauth_consumer_key': consumer_key,
        'oauth_nonce': nonce or uuid.uuid4().hex,
        'oauth_signature_method': 'HMAC-SHA1',
        'oauth_timestamp': str(timestamp or int(time.time())),
        'oauth_version': '1.0',
    }
    if token:
        oauth['oauth_token'] = token
    oauth.update(extra or {})

    signed = dict(params or {})
    signed.update(oauth)
    param_string = '&'.join('%s=%s' % pair for pair in sorted((_enc(k), _enc(v)) for k, v in signed.items()))
    base = '&'.join([method.upper(), _enc(url), _enc(param_string)])
    key = '%s&%s' % (_enc(consumer_secret), _enc(token_secret))
    oauth['oauth_signature'] = base64.b64encode(hmac.new(key.encode('utf-8'), base.encode('utf-8'), hashlib.sha1).digest()).decode('ascii')

    return 'OAuth ' + ', '.join('%s="%s"' % (_enc(k), _enc(v)) for k, v in sorted(oauth.items()))


class Twitter(Notification):
    """ Posts (or DMs) through X's v2 API, with the user's own X developer app.

    Since February 2026 the X API is pay-per-use with no free tier, so the project cannot ship
    a shared app the way it does for Trakt: every user's posts would be billed to the project.
    Each user pastes the four values from their app's "Keys and tokens" page instead. """

    api = 'https://api.x.com'
    max_length = 280
    timeout = (3, 15)

    request_token = None

    urls = {
        'request': 'https://api.x.com/oauth/request_token',
        'access': 'https://api.x.com/oauth/access_token',
        'authorize': 'https://api.x.com/oauth/authorize',
    }

    def __init__(self):
        super(Twitter, self).__init__()

        addApiView('notify.%s.auth_url' % self.getName().lower(), self.getAuthorizationUrl)
        addApiView('notify.%s.credentials' % self.getName().lower(), self.getCredentials)

    # Keys

    def appKeys(self):
        return (self.conf('consumer_key') or '').strip(), (self.conf('consumer_secret') or '').strip()

    def userKeys(self):
        return (self.conf('access_token_key') or '').strip(), (self.conf('access_token_secret') or '').strip()

    def missingKeys(self):
        names = ('API key', 'API key secret', 'Access token', 'Access token secret')
        return [name for name, value in zip(names, self.appKeys() + self.userKeys()) if not value]

    # Requests

    def call(self, method, path, body = None):
        """ One signed v2 call. Returns the parsed JSON, or raises XError with X's own message """
        url = self.api + path
        consumer_key, consumer_secret = self.appKeys()
        token, token_secret = self.userKeys()
        headers = {'Authorization': oauthHeader(method, url, consumer_key, consumer_secret, token, token_secret)}
        if body is not None:
            headers['Content-Type'] = 'application/json'

        # Not self.urlopen: an X 4xx (bad keys, no credits) is an answer, and urlopen would
        # count it as the host failing and block api.x.com for 15 minutes.
        r = requests.request(method, url, headers = headers, data = json.dumps(body) if body is not None else None, timeout = self.timeout)
        try:
            data = r.json()
        except ValueError:
            data = {}
        if r.status_code >= 400:
            raise XError(r.status_code, data)
        return data

    def post(self, text):
        return self.call('POST', '/2/tweets', {'text': text})

    def directMessage(self, screen_name, text):
        user = self.call('GET', '/2/users/by/username/%s' % quote(screen_name.lstrip('@'), safe = ''))
        user_id = (user.get('data') or {}).get('id')
        if not user_id:
            raise XError(404, {'detail': 'No X account named @%s' % screen_name.lstrip('@')})
        return self.call('POST', '/2/dm_conversations/with/%s/messages' % user_id, {'text': text})

    # Notifier

    def splitMessage(self, message, mention_tag = None):
        """ The post text, as one post if it fits in 280 characters, else two marked 1/2 and 2/2 """
        if len(message) <= self.max_length:
            return [message]

        suffix_one = (' %s 1/2' % mention_tag) if mention_tag else ' 1/2'
        suffix_two = (' %s 2/2' % mention_tag) if mention_tag else ' 2/2'
        if mention_tag and message.endswith(' ' + mention_tag):
            message = message[:-len(mention_tag) - 1]
        cut = self.max_length - len(suffix_one)
        return [message[:cut] + suffix_one, message[cut:][:self.max_length - len(suffix_two)] + suffix_two]

    def notify(self, message = '', data = None, listener = None):
        if not data: data = {}

        missing = self.missingKeys()
        if missing:
            log.error('X notifications are on, but these keys are empty: %s. Copy them from your app\'s "Keys and tokens" page on developer.x.com', (', '.join(missing),))
            return False

        direct_message = self.conf('direct_message')
        direct_message_users = self.conf('screen_name') or ''

        mention = self.conf('mention')
        mention_tag = None
        if mention:
            if direct_message:
                direct_message_users = '%s %s' % (direct_message_users, mention)
                direct_message_users = direct_message_users.replace('@', ' ')
                direct_message_users = direct_message_users.replace(',', ' ')
            else:
                mention_tag = '@%s' % mention.lstrip('@')
                message = '%s %s' % (message, mention_tag)

        text = '[%s] %s' % (self.default_title, message)
        try:
            if direct_message:
                users = direct_message_users.split()
                if not users:
                    log.error('X direct messages are on, but there is no screen name to send them to')
                    return False
                for user in users:
                    self.directMessage(user, text)
            else:
                for part in self.splitMessage(text, mention_tag):
                    self.post(part)
        except XError as e:
            log.error('X refused the %s: %s', ('direct message' if direct_message else 'post', e))
            return False
        except requests.RequestException as e:
            log.error('Could not reach X: %s', (e,))
            return False

        return True

    # Optional: sign in through X instead of pasting the access token.
    # Needs your app's API key + secret, and this callback URL added to the app on developer.x.com.

    def getAuthorizationUrl(self, host = None, **kwargs):
        consumer_key, consumer_secret = self.appKeys()
        if not consumer_key or not consumer_secret:
            return {'success': False, 'error': 'Fill in your X app\'s API key and API key secret first'}

        callback_url = cleanHost(host) + '%snotify.%s.credentials/' % (Env.get('api_base').lstrip('/'), self.getName().lower())
        header = oauthHeader('POST', self.urls['request'], consumer_key, consumer_secret, extra = {'oauth_callback': callback_url})
        try:
            r = requests.post(self.urls['request'], headers = {'Authorization': header}, timeout = self.timeout)
        except requests.RequestException as e:
            log.error('Could not reach X: %s', (e,))
            return {'success': False}

        if r.status_code != 200:
            log.error('X refused the sign-in request (HTTP %s). Is %s on your app\'s list of callback URLs?', (r.status_code, callback_url))
            return {'success': False}

        self.request_token = dict(parse_qsl(r.text))
        auth_url = self.urls['authorize'] + '?oauth_token=%s' % self.request_token['oauth_token']
        log.info('Redirecting to "%s"', (auth_url,))
        return {'success': True, 'url': auth_url}

    def getCredentials(self, oauth_verifier, **kwargs):
        if not self.request_token:
            return 'X sign-in expired: start it again from Settings'

        consumer_key, consumer_secret = self.appKeys()
        header = oauthHeader('POST', self.urls['access'], consumer_key, consumer_secret,
                             self.request_token['oauth_token'], self.request_token['oauth_token_secret'],
                             extra = {'oauth_verifier': oauth_verifier})
        try:
            r = requests.post(self.urls['access'], headers = {'Authorization': header}, timeout = self.timeout)
        except requests.RequestException as e:
            log.error('Could not reach X: %s', (e,))
            return 'X auth failed'

        if r.status_code != 200:
            log.error('The request for an access token did not succeed: %s', (r.status_code,))
            return 'X auth failed'

        access_token = dict(parse_qsl(r.text))
        self.conf('access_token_key', value = access_token['oauth_token'])
        self.conf('access_token_secret', value = access_token['oauth_token_secret'])
        self.conf('screen_name', value = access_token.get('screen_name', ''))
        self.request_token = None
        log.info('Signed in to X as @%s', (access_token.get('screen_name', '?'),))

        return 'redirect', Env.get('web_base') + 'settings/notifications/'


class XError(Exception):
    """ X answered with an error. Holds X's own explanation (never the keys) """

    def __init__(self, status, data):
        self.status = status
        detail = (data or {}).get('detail') or (data or {}).get('title')
        if not detail and (data or {}).get('errors'):
            detail = '; '.join(e.get('message') or e.get('detail') or '' for e in data['errors'])
        hint = {
            401: 'check the four keys, and that the access token was made after the app got "Read and write" permission',
            402: 'your X developer account is out of credits',
            403: 'the app is not allowed to do this; give it "Read and write" (and "Direct message" for DMs)',
            429: 'X\'s rate limit; it resets within 15 minutes',
        }.get(status)
        super(XError, self).__init__('HTTP %s%s%s' % (status, ': %s' % detail if detail else '', ' (%s)' % hint if hint else ''))

import json
import time
import traceback

from couchpotato import Env, fireEvent
from couchpotato.api import addApiView
from couchpotato.core.event import addEvent
from couchpotato.core.logger import CPLog
from couchpotato.core.media._base.providers.base import Provider
from couchpotato.core.media.movie.providers.automation.base import Automation


log = CPLog(__name__)


class TraktBase(Provider):

    # The project's own Trakt app (backlog §10, registered 2026-11-20 on developer.trakt.tv). Users sign in
    # with a code shown in the app, so they never register an app themselves. Trakt's new developer site
    # issues no client secret for such apps ("signs users in with PKCE"), so the id alone is enough and it is
    # public by design. A secret is sent only if one is ever set here (apps registered on the old site).
    client_id = 'W3CQ0MtQWR9JHkboG8MN1EeqvXB4aJrCCzJ4c3TW4mQ'
    client_secret = ''

    api_url = 'https://api.trakt.tv/'
    oob_redirect = 'urn:ietf:wg:oauth:2.0:oob'
    timeout = (3, 15)  # short connect timeout: a dead IPv6 route must not stall a sign-in poll

    refresh_margin = 12 * 3600  # renew the token once it has less than this left

    def configured(self):
        return bool(self.client_id)

    def credentials(self, **payload):
        payload['client_id'] = self.client_id
        if self.client_secret:
            payload['client_secret'] = self.client_secret
        return payload

    def apiHeaders(self, signed_in = True):
        headers = {
            'Content-Type': 'application/json',
            'trakt-api-version': '2',
            'trakt-api-key': self.client_id,
            'User-Agent': 'CouchTomato',
        }
        if signed_in:
            headers['Authorization'] = 'Bearer %s' % self.conf('automation_oauth_token')
        return headers

    def call(self, method_url, post_data = None):
        self.refreshToken()

        if post_data:
            post_data = json.dumps(post_data)

        data = self.getJsonData(self.api_url + method_url, data = post_data or {}, headers = self.apiHeaders())
        return data if data else []

    def oauth(self, path, payload):
        """ POST to Trakt's OAuth endpoints and return (status, json). Not through urlopen(): the device poll
        answers 400 on purpose until the user has entered the code, and urlopen() would count every one of
        those as a failure and block api.trakt.tv for 15 minutes after five. """
        response = Env.get('http_opener').post(self.api_url + path, data = json.dumps(payload),
                                               headers = self.apiHeaders(signed_in = False), timeout = self.timeout)
        try:
            body = response.json() if response.content else {}
        except ValueError:
            body = {}
        return response.status_code, body

    def saveTokens(self, data):
        created = int(data.get('created_at') or time.time())
        self.conf('automation_oauth_token', value = data.get('access_token'))
        self.conf('automation_oauth_refresh', value = data.get('refresh_token'))
        self.conf('automation_oauth_expires', value = created + int(data.get('expires_in') or 0))

    def refreshToken(self):
        """ Renew the token before it runs out. Safe to call often: it only talks to Trakt near expiry. """
        token = self.conf('automation_oauth_token')
        refresh_token = self.conf('automation_oauth_refresh')
        if not token or not self.configured():
            return False

        try:
            expires = int(self.conf('automation_oauth_expires') or 0)
        except ValueError:
            expires = 0

        if not expires:
            # Signed in through the old CouchPotato app, which Trakt no longer knows ("client not found")
            log.error('Trakt sign-in is from the old CouchPotato app and no longer works. Sign in again in Settings > Automation > Trakt')
            return False

        if expires - time.time() > self.refresh_margin:
            return True

        if not refresh_token:
            log.error('Trakt sign-in has expired. Sign in again in Settings > Automation > Trakt')
            return False

        try:
            status, data = self.oauth('oauth/token', self.credentials(
                refresh_token = refresh_token,
                redirect_uri = self.oob_redirect,
                grant_type = 'refresh_token',
            ))
        except Exception:
            log.warning('Could not reach Trakt to renew the sign-in, will retry: %s', traceback.format_exc(0))
            return False

        if status == 200 and data.get('access_token'):
            self.saveTokens(data)
            log.info('Renewed the Trakt sign-in')
            return True

        log.error('Trakt refused to renew the sign-in (HTTP %s). Sign in again in Settings > Automation > Trakt', status)
        return False


class Trakt(Automation, TraktBase):

    urls = {
        'watchlist': 'sync/watchlist/movies?extended=full',
    }

    # Trakt's answers to a device-token poll, other than 200 (signed in)
    poll_answers = {
        400: 'pending',     # the user hasn't entered the code yet
        404: 'invalid',     # unknown device code
        409: 'used',        # this code was already approved
        410: 'expired',     # the code ran out before it was entered
        418: 'denied',      # the user said no
        429: 'slow_down',   # polling too fast
    }

    def __init__(self):
        super(Trakt, self).__init__()

        self.device = None  # the sign-in in progress: device_code + when it expires; never sent to the browser

        addApiView('automation.trakt.device_code', self.startSignIn, docs = {
            'desc': 'Start a Trakt sign-in: returns the code to enter at the returned url',
        })
        addApiView('automation.trakt.device_poll', self.pollSignIn, docs = {
            'desc': 'Check the Trakt sign-in started by device_code: status is connected, pending, slow_down, expired, denied, invalid or used',
        })

        # Its own schedule id: under 'updater.check' (as it was) it replaced the updater's daily job
        fireEvent('schedule.interval', 'trakt.refresh_token', self.refreshToken, hours = 6)
        addEvent('app.load', self.refreshToken)

    def getIMDBids(self):
        movies = []
        for movie in self.getWatchlist():
            m = movie.get('movie')
            m['original_title'] = m['title']
            log.debug("Movie: %s", m)
            if self.isMinimalMovie(m):
                log.info("Trakt automation: %s satisfies requirements, added", m.get('title'))
                movies.append(m.get('ids').get('imdb'))
                continue

        return movies

    def getWatchlist(self):
        return self.call(self.urls['watchlist'])

    def startSignIn(self, **kwargs):
        if not self.configured():
            return {'success': False, 'error': 'This CouchTomato build has no Trakt app keys yet'}

        try:
            status, data = self.oauth('oauth/device/code', {'client_id': self.client_id})
        except Exception as e:
            log.warning('Could not reach Trakt to start a sign-in: %s', e)
            return {'success': False, 'error': 'Could not reach trakt.tv'}

        if status != 200 or not data.get('device_code'):
            log.error('Trakt refused to start a sign-in (HTTP %s): %s', (status, data))
            return {'success': False, 'error': 'trakt.tv refused the sign-in (HTTP %s)' % status}

        self.device = {
            'code': data['device_code'],
            'expires': time.time() + int(data.get('expires_in', 600)),
        }

        return {
            'success': True,
            'user_code': data.get('user_code'),
            'verification_url': data.get('verification_url', 'https://trakt.tv/activate'),
            'interval': int(data.get('interval', 5)),
            'expires_in': int(data.get('expires_in', 600)),
        }

    def pollSignIn(self, **kwargs):
        device = self.device
        if not device or device['expires'] < time.time():
            self.device = None
            return {'success': False, 'status': 'expired'}

        try:
            status, data = self.oauth('oauth/device/token', self.credentials(code = device['code']))
        except Exception as e:
            log.debug('Trakt sign-in poll failed, will retry: %s', e)
            return {'success': False, 'status': 'pending'}

        if status == 200 and data.get('access_token'):
            self.saveTokens(data)
            self.device = None
            log.info('Signed in to Trakt')
            return {'success': True, 'status': 'connected'}

        answer = self.poll_answers.get(status, 'error')
        if answer not in ('pending', 'slow_down'):
            self.device = None
            log.info('Trakt sign-in ended: %s (HTTP %s)', (answer, status))

        return {'success': False, 'status': answer}

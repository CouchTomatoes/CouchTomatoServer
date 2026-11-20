from couchpotato.api import addApiView
from couchpotato.core.event import addEvent, fireEvent, fireEventAsync
from couchpotato.core._base.downloader.main import DownloaderBase, ReleaseDownloadList
from couchpotato.core.logger import CPLog
from couchpotato.environment import Env
from pio import api as pio
import datetime
import time

log = CPLog(__name__)

autoload = 'Putiodownload'


class PutIO(DownloaderBase):

    protocol = ['torrent', 'torrent_magnet']
    downloading_list = []

    # The project's own put.io app (backlog §10). Users link their account with a code entered at put.io/link,
    # so nobody registers an app or needs an address put.io can call back. The id is public by design.
    app_id = ''

    oob_url = 'https://api.put.io/v2/oauth2/oob/code'
    link_url = 'https://put.io/link'
    timeout = (3, 15)
    code_lifetime = 600  # stop polling a code after this; put.io answers 404 once it has gone

    def __init__(self):
        addApiView('downloader.putio.getfrom', self.getFromPutio, docs = {
            'desc': 'Allows you to download file from prom Put.io',
        })
        addApiView('downloader.putio.device_code', self.startSignIn, docs = {
            'desc': 'Start linking a put.io account: returns the code to enter at put.io/link',
        })
        addApiView('downloader.putio.device_poll', self.pollSignIn, docs = {
            'desc': 'Check the put.io link started by device_code: status is connected, pending or expired',
        })
        self.device = None  # the link in progress: code + when to give up
        addEvent('putio.download', self.putioDownloader)

        return super(PutIO, self).__init__()

    # This is a recusive function to check for the folders
    def recursionFolder(self, client, folder = 0, tfolder = ''):
        files = client.File.list(folder)
        for f in files:
            if f.content_type == 'application/x-directory':
                if f.name == tfolder:
                   return f.id
                else:
                    result = self.recursionFolder(client, f.id, tfolder)
                    if result != 0:
                       return result
        return 0

    # This will check the root for the folder, and kick of recusively checking sub folder
    def convertFolder(self, client, folder):
        if folder == 0:
            return 0
        else:
            return self.recursionFolder(client, 0, folder)

    def download(self, data = None, media = None, filedata = None):
        if not media: media = {}
        if not data: data = {}

        log.info('Sending "%s" to put.io', data.get('name'))
        url = data.get('url')
        client = pio.Client(self.conf('oauth_token'))
        putioFolder = self.convertFolder(client, self.conf('folder'))
        log.debug('putioFolder ID is %s', putioFolder)
        # It might be possible to call getFromPutio from the renamer if we can then we don't need to do this.
        # Note callback_host is NOT our address, it's the internet host that putio can call too
        callbackurl = None
        if self.conf('download'):
            pre = 'http://'
            if self.conf('https'):
              pre = 'https://'
            callbackurl = pre + self.conf('callback_host') + '%sdownloader.putio.getfrom/' %Env.get('api_base'.strip('/'))
        log.debug('callbackurl is %s', callbackurl)
        resp = client.Transfer.add_url(url, callback_url = callbackurl, parent_id = putioFolder)
        log.debug('resp is %s', resp.id)
        return self.downloadReturnId(resp.id)

    def test(self):
        try:
            client = pio.Client(self.conf('oauth_token'))
            if client.File.list():
                return True
        except:
            log.info('Failed to get file listing, check OAUTH_TOKEN')
            return False

    def oob(self, path = ''):
        """ GET put.io's code-link endpoints. Not through urlopen(): an expired code answers 404, which
        urlopen() would count as a failing host. Returns (status, json). """
        response = Env.get('http_opener').get(self.oob_url + path, params = {'app_id': self.app_id} if not path else None,
                                              headers = {'User-Agent': 'CouchTomato'}, timeout = self.timeout)
        try:
            body = response.json() if response.content else {}
        except ValueError:
            body = {}
        return response.status_code, body

    def startSignIn(self, **kwargs):
        if not self.app_id:
            return {'success': False, 'error': 'This CouchTomato build has no put.io app id yet'}

        try:
            status, data = self.oob()
        except Exception as e:
            log.warning('Could not reach put.io to start linking: %s', e)
            return {'success': False, 'error': 'Could not reach put.io'}

        if status != 200 or not data.get('code'):
            log.error('put.io refused to start linking (HTTP %s): %s', (status, data))
            return {'success': False, 'error': 'put.io refused the link (HTTP %s)' % status}

        self.device = {'code': data['code'], 'expires': time.time() + self.code_lifetime}
        return {
            'success': True,
            'user_code': data['code'],
            'verification_url': self.link_url,
            'interval': 5,
            'expires_in': self.code_lifetime,
        }

    def pollSignIn(self, **kwargs):
        device = self.device
        if not device or device['expires'] < time.time():
            self.device = None
            return {'success': False, 'status': 'expired'}

        try:
            status, data = self.oob('/' + device['code'])
        except Exception as e:
            log.debug('put.io link poll failed, will retry: %s', e)
            return {'success': False, 'status': 'pending'}

        if status == 200 and data.get('oauth_token'):
            self.conf('oauth_token', value = data['oauth_token'])
            self.device = None
            log.info('Linked the put.io account')
            fireEvent('history.add', 'signin', detail = 'Linked the put.io account')
            return {'success': True, 'status': 'connected'}

        if status == 200:
            return {'success': False, 'status': 'pending'}

        self.device = None
        log.info('put.io link ended (HTTP %s)', status)
        return {'success': False, 'status': 'expired' if status == 404 else 'error'}

    def getAllDownloadStatus(self, ids):

        log.debug('Checking putio download status.')
        client = pio.Client(self.conf('oauth_token'))

        transfers = client.Transfer.list()

        log.debug(transfers);
        release_downloads = ReleaseDownloadList(self)
        for t in transfers:
            if t.id in ids:

                log.debug('downloading list is %s', self.downloading_list)
                if t.status == "COMPLETED" and self.conf('download') == False :
                    status = 'completed'

                # So check if we are trying to download something
                elif t.status == "COMPLETED" and self.conf('download') == True:
                      # Assume we are done
                      status = 'completed'
                      if not self.downloading_list:
                          now = datetime.datetime.utcnow()
                          date_time = datetime.datetime.strptime(t.finished_at,"%Y-%m-%dT%H:%M:%S")
                          # We need to make sure a race condition didn't happen
                          if (now - date_time) < datetime.timedelta(minutes=5):
                              # 5 minutes haven't passed so we wait
                              status = 'busy'
                      else:
                          # If we have the file_id in the downloading_list mark it as busy
                          if str(t.file_id) in self.downloading_list:
                              status = 'busy'
                else:
                    status = 'busy'
                release_downloads.append({
                    'id' : t.id,
                    'name': t.name,
                    'status': status,
                    'timeleft': t.estimated_time,
                })

        return release_downloads

    def putioDownloader(self, fid):

        log.info('Put.io Real downloader called with file_id: %s',fid)
        client = pio.Client(self.conf('oauth_token'))

        log.debug('About to get file List')
        putioFolder = self.convertFolder(client, self.conf('folder'))
        log.debug('PutioFolderID is %s', putioFolder)
        files = client.File.list(parent_id=putioFolder)
        downloaddir = self.conf('download_dir')

        for f in files:
            if str(f.id) == str(fid):
                client.File.download(f, dest = downloaddir, delete_after_download = self.conf('delete_file'))
                # Once the download is complete we need to remove it from the running list.
                self.downloading_list.remove(fid)

        return True

    def getFromPutio(self, **kwargs):

        try:
            file_id = str(kwargs.get('file_id'))
        except:
            return {
                'success' : False,
            }

        log.info('Put.io Download has been called file_id is %s', file_id)
        if file_id not in self.downloading_list:
            self.downloading_list.append(file_id)
            fireEventAsync('putio.download',fid = file_id)
            return {
               'success': True,
            }

        return {
            'success': False,
        }


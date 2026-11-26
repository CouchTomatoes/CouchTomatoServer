from hashlib import md5

from CodernityDB.hash_index import HashIndex
from CodernityDB.tree_index import TreeBasedIndex


class ReleaseIndex(TreeBasedIndex):
    _version = 2  # 2: keys are bytes (a str key crashed the tree search: "'<' not supported between str and bytes")

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = '32s'
        super(ReleaseIndex, self).__init__(*args, **kwargs)

    def make_key(self, key):
        return key.encode('utf-8') if isinstance(key, str) else key

    def make_key_value(self, data):
        if data.get('_t') == 'release' and data.get('media_id'):
            media_id = data['media_id']
            return (media_id.encode('utf-8') if isinstance(media_id, str) else media_id), None


class ReleaseStatusIndex(TreeBasedIndex):
    _version = 1

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = '32s'
        super(ReleaseStatusIndex, self).__init__(*args, **kwargs)

    def make_key(self, key):
        return md5(key.encode('utf-8')).hexdigest().encode('utf-8')

    def make_key_value(self, data):
        if data.get('_t') == 'release' and data.get('status'):
            return md5(data.get('status').encode('utf-8')).hexdigest().encode('utf-8'), {'media_id': data.get('media_id')}


class ReleaseIDIndex(HashIndex):
    _version = 1

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = '32s'
        super(ReleaseIDIndex, self).__init__(*args, **kwargs)

    def make_key(self, key):
        return md5(key.encode('utf-8')).hexdigest().encode('utf-8')

    def make_key_value(self, data):
        if data.get('_t') == 'release' and data.get('identifier'):
            return md5(data.get('identifier').encode('utf-8')).hexdigest().encode('utf-8'), {'media_id': data.get('media_id')}


class ReleaseDownloadIndex(HashIndex):
    _version = 2

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = '32s'
        super(ReleaseDownloadIndex, self).__init__(*args, **kwargs)

    def make_key(self, key):
        return md5(key.lower().encode('utf-8')).hexdigest().encode('utf-8')

    def make_key_value(self, data):
        if data.get('_t') == 'release' and data.get('download_info') and data['download_info']['id'] and data['download_info']['downloader']:
            return md5(('%s-%s' % (data['download_info']['downloader'], data['download_info']['id'])).lower().encode('utf-8')).hexdigest().encode('utf-8'), None

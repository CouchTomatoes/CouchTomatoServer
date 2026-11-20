from hashlib import md5

from CodernityDB.hash_index import HashIndex
from CodernityDB.tree_index import TreeBasedIndex


class HistoryIndex(TreeBasedIndex):
    """ History events by time """
    _version = 1

    custom_header = """from CodernityDB.tree_index import TreeBasedIndex"""

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = 'I'
        super(HistoryIndex, self).__init__(*args, **kwargs)

    def make_key(self, key):
        return key

    def make_key_value(self, data):
        if data.get('_t') == 'history':
            return data.get('time'), None


class HistoryEventIndex(HashIndex):
    """ History events by event id, so an import never adds the same event twice """
    _version = 1

    custom_header = """from CodernityDB.hash_index import HashIndex
from hashlib import md5"""

    def __init__(self, *args, **kwargs):
        kwargs['key_format'] = '32s'
        super(HistoryEventIndex, self).__init__(*args, **kwargs)

    def make_key(self, key):
        return md5(key.encode('utf-8')).hexdigest().encode('utf-8')

    def make_key_value(self, data):
        if data.get('_t') == 'history' and data.get('eid'):
            return md5(data['eid'].encode('utf-8')).hexdigest().encode('utf-8'), None

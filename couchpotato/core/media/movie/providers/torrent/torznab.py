from couchpotato.core.helpers.encoding import tryUrlencode
from couchpotato.core.helpers.variable import getIdentifier, getTitle
from couchpotato.core.logger import CPLog
from couchpotato.core.media._base.providers.torrent.torznab import Base
from couchpotato.core.media.movie.providers.base import MovieProvider

log = CPLog(__name__)

autoload = 'Torznab'


class Torznab(MovieProvider, Base):

    def buildQueries(self, media, host):
        """ IMDb search first (exact), then a title + year search for indexers without IMDb support """
        common = {'apikey': host['api_key'], 'cat': host['custom_category'] or '2000', 'extended': 1}

        queries = []
        imdb = getIdentifier(media)
        if imdb:
            q = dict(common, t = 'movie', imdbid = imdb)
            queries.append(tryUrlencode(q))

        title = getTitle(media)
        year = (media.get('info') or {}).get('year')
        if title:
            q = dict(common, t = 'search', q = '%s %s' % (title, year) if year else title)
            queries.append(tryUrlencode(q))

        return queries

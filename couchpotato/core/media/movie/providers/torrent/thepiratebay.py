from couchpotato.core.logger import CPLog
from couchpotato.core.event import fireEvent
from couchpotato.core.media._base.providers.torrent.thepiratebay import Base
from couchpotato.core.media.movie.providers.base import MovieProvider

log = CPLog(__name__)

autoload = 'ThePirateBay'


class ThePirateBay(MovieProvider, Base):

    # apibay categories: 201 Movies, 202 DVDR, 207 HD Movies, 209 3D, 210 CAM/TS, 211 UHD/4K Movies
    cat_ids = [
        ([209], ['3d']),
        ([211], ['2160p']),
        ([207], ['720p', '1080p', 'bd50']),
        ([201, 210], ['cam', 'ts', 'tc', 'r5', 'scr']),
        ([201], ['dvdrip']),
        ([201, 207], ['brrip']),
        ([202], ['dvdr'])
    ]

    def buildQuery(self, media):
        return fireEvent('library.query', media, single = True)

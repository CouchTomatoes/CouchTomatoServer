"""
couchpota.to (upstream's old site) is a parked, for-sale domain. Its page runs a for-sale
script that hands visitors on to ad campaigns, so anything the app *loads* from it (an
iframe, image or script) runs that in the user's browser on every view of the page.
Nothing in the web UI may load from it. Plain links (opened only on a click) are not
covered here.
Run from the repo root:  python3 -m unittest discover -s tests
"""
import os
import re
import unittest

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEAD = r'(?:[\w-]+\.)*couchpota\.to'
# 'src': 'https://couchpota.to/...'   src="https://couchpota.to/..."   url(https://couchpota.to/...)
LOADS = re.compile(r"""(?:\bsrc['"]?\s*[:=]\s*['"]|url\(\s*['"]?)(?:https?:)?//""" + DEAD, re.I)


def web_files():
    for base in ('couchpotato',):
        for dirpath, _, files in os.walk(os.path.join(root, base)):
            for name in files:
                if name.endswith(('.js', '.html', '.css', '.scss')):
                    yield os.path.join(dirpath, name)


class NoDeadDomainLoadsTest(unittest.TestCase):

    def test_pattern_catches_the_shapes_that_were_there(self):
        for bad in ("'src': 'https://couchpota.to/media/images/userscript.gif'",
                    '<iframe src="https://couchpota.to/donate.html" scrolling="no">',
                    'src:"https://couchpota.to/x.gif"',
                    'background: url(https://couchpota.to/bg.png)'):
            self.assertTrue(LOADS.search(bad), bad)
        self.assertFalse(LOADS.search("'href': 'https://couchpota.to/support/'"))

    def test_web_ui_loads_nothing_from_couchpota_to(self):
        hits = []
        for path in web_files():
            with open(path, encoding = 'utf-8', errors = 'replace') as f:
                for n, line in enumerate(f, 1):
                    if LOADS.search(line):
                        hits.append('%s:%d' % (os.path.relpath(path, root), n))
        self.assertEqual(hits, [], 'loads from the parked couchpota.to domain')

    def test_donate_link_points_at_the_github_repo(self):
        # The menu's Donate link used to open couchpota.to/support/ (the ad-serving parked page).
        for rel in ('couchpotato/static/scripts/couchpotato.js',
                    'couchpotato/static/scripts/combined.base.min.js'):
            with open(os.path.join(root, rel), encoding = 'utf-8') as f:
                src = f.read()
            self.assertNotIn('couchpota.to/support', src, rel)
            self.assertIn('github.com/CouchTomatoes/CouchTomatoServer', src, rel)


if __name__ == '__main__':
    unittest.main()

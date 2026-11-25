"""
Tests for couchpotato/core/plugins/screens.py: what the Movie details page is told at start.
A saved value the page doesn't know (hand-edited settings.conf, an old value) must fall back
to the default instead of reaching the page, which would otherwise show no view at all.
Run from the repo root:  python3 -m unittest discover -s tests
"""
import os
import sys
import unittest

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)
sys.path.insert(0, os.path.join(root, 'libs'))

from couchpotato.core.plugins import screens  # noqa: E402


def getter(saved):
    """Stands in for Env.setting(name, section = ..., default = ...)."""
    calls = []

    def get(name, section = 'core', default = ''):
        calls.append((section, name))
        return saved.get(name, default)

    get.calls = calls
    return get


class FrontendOptionsTest(unittest.TestCase):

    def test_defaults_when_nothing_saved(self):
        self.assertEqual(screens.frontendOptions(getter({})),
                         {'details_view': 'poster', 'details_backdrop': 'full'})

    def test_saved_values_are_passed_through(self):
        for view in screens.DETAILS_VIEWS:
            for backdrop in screens.DETAILS_BACKDROPS:
                got = screens.frontendOptions(getter({'details_view': view, 'details_backdrop': backdrop}))
                self.assertEqual(got, {'details_view': view, 'details_backdrop': backdrop})

    def test_unknown_values_fall_back(self):
        got = screens.frontendOptions(getter({'details_view': 'Hero ', 'details_backdrop': 'huge'}))
        self.assertEqual(got, {'details_view': 'poster', 'details_backdrop': 'full'})

    def test_reads_the_screens_section(self):
        get = getter({})
        screens.frontendOptions(get)
        self.assertEqual(sorted(get.calls), [('screens', 'details_backdrop'), ('screens', 'details_view')])

    def test_settings_dropdowns_match_what_the_page_accepts(self):
        options = {o['name']: o for o in screens.config[0]['groups'][0]['options']}
        self.assertEqual(tuple(v for _, v in options['details_view']['values']), screens.DETAILS_VIEWS)
        self.assertEqual(tuple(v for _, v in options['details_backdrop']['values']), screens.DETAILS_BACKDROPS)
        self.assertEqual(options['details_view']['default'], 'poster')
        self.assertEqual(options['details_backdrop']['default'], 'full')


if __name__ == '__main__':
    unittest.main()

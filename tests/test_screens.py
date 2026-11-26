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
                         {'home_view': 'classic', 'wanted_view': 'classic', 'manage_view': 'classic', 'activity_view': 'table', 'snatched_view': 'classic', 'details_view': 'poster', 'details_backdrop': 'full', 'show_new_tags': True})

    def test_saved_values_are_passed_through(self):
        for view in screens.DETAILS_VIEWS:
            for backdrop in screens.DETAILS_BACKDROPS:
                got = screens.frontendOptions(getter({'details_view': view, 'details_backdrop': backdrop}))
                self.assertEqual((got['details_view'], got['details_backdrop']), (view, backdrop))

    def test_unknown_values_fall_back(self):
        got = screens.frontendOptions(getter({'home_view': 'Sections', 'wanted_view': 'grid', 'manage_view': 'Posters', 'activity_view': 'Cards', 'snatched_view': 'Table', 'details_view': 'Hero ', 'details_backdrop': 'huge', 'show_new_tags': 'maybe'}))
        self.assertEqual(got, {'home_view': 'classic', 'wanted_view': 'classic', 'manage_view': 'classic', 'activity_view': 'table', 'snatched_view': 'classic', 'details_view': 'poster', 'details_backdrop': 'full', 'show_new_tags': True})

    def test_home_view_passed_through(self):
        for view in screens.HOME_VIEWS:
            self.assertEqual(screens.frontendOptions(getter({'home_view': view}))['home_view'], view)

    def test_wanted_and_manage_views_passed_through(self):
        for view in screens.LIST_VIEWS:
            got = screens.frontendOptions(getter({'wanted_view': view, 'manage_view': view}))
            self.assertEqual((got['wanted_view'], got['manage_view']), (view, view))

    def test_activity_view_passed_through(self):
        for view in screens.ACTIVITY_VIEWS:
            self.assertEqual(screens.frontendOptions(getter({'activity_view': view}))['activity_view'], view)

    def test_snatched_view_passed_through(self):
        for view in screens.SNATCHED_VIEWS:
            self.assertEqual(screens.frontendOptions(getter({'snatched_view': view}))['snatched_view'], view)

    def test_show_new_tags_reads_bools_and_settings_text(self):
        for saved, want in ((True, True), (False, False), ('1', True), ('0', False), ('False', False), ('True', True)):
            got = screens.frontendOptions(getter({'show_new_tags': saved}))
            self.assertIs(got['show_new_tags'], want, saved)

    def test_reads_the_screens_section(self):
        get = getter({})
        screens.frontendOptions(get)
        self.assertEqual(sorted(get.calls), [('screens', 'activity_view'), ('screens', 'details_backdrop'), ('screens', 'details_view'),
                                             ('screens', 'home_view'), ('screens', 'manage_view'),
                                             ('screens', 'show_new_tags'), ('screens', 'snatched_view'), ('screens', 'wanted_view')])

    def test_settings_dropdowns_match_what_the_page_accepts(self):
        options = {o['name']: o for g in screens.config[0]['groups'] for o in g['options']}
        self.assertEqual(tuple(v for _, v in options['details_view']['values']), screens.DETAILS_VIEWS)
        self.assertEqual(tuple(v for _, v in options['details_backdrop']['values']), screens.DETAILS_BACKDROPS)
        self.assertEqual(tuple(v for _, v in options['home_view']['values']), screens.HOME_VIEWS)
        self.assertEqual(options['home_view']['default'], 'classic')  # existing screens open in Classic (locked 11-20)
        for key in ('wanted_view', 'manage_view'):
            self.assertEqual(tuple(v for _, v in options[key]['values']), screens.LIST_VIEWS)
            self.assertEqual(options[key]['default'], 'classic')
        self.assertEqual(tuple(v for _, v in options['activity_view']['values']), screens.ACTIVITY_VIEWS)
        self.assertEqual(options['activity_view']['default'], 'table')  # new screens open in the new view (locked 11-20)
        self.assertEqual(tuple(v for _, v in options['snatched_view']['values']), screens.SNATCHED_VIEWS)
        self.assertEqual(options['snatched_view']['default'], 'classic')  # an existing list: Classic (locked 11-20)
        self.assertEqual(options['details_view']['default'], 'poster')
        self.assertEqual(options['details_backdrop']['default'], 'full')
        self.assertEqual((options['show_new_tags']['type'], options['show_new_tags']['default']), ('bool', True))
        self.assertTrue(all(g['tab'] == 'screens' for g in screens.config[0]['groups']))


if __name__ == '__main__':
    unittest.main()

"""
Tests for the FlareSolverr fallback in couchpotato/core/plugins/base.py: recognising a
Cloudflare challenge, and unwrapping the JSON FlareSolverr returns inside the browser's <pre>.
Run from the repo root:  python3 -m unittest discover -s tests
"""
import os
import sys
import unittest

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)
sys.path.insert(0, os.path.join(root, 'libs'))

from couchpotato.core.plugins.base import isCloudflareChallenge, unwrapBrowserJson


class FakeResponse(object):

    def __init__(self, status_code, headers = None, text = ''):
        self.status_code = status_code
        self.headers = headers or {}
        self.text = text


CHALLENGE_PAGE = '<!DOCTYPE html><html lang="en-US"><head><title>Just a moment...</title></head><body></body></html>'


class CloudflareChallengeTest(unittest.TestCase):

    def test_cf_mitigated_header(self):
        self.assertTrue(isCloudflareChallenge(FakeResponse(403, {'cf-mitigated': 'challenge'})))

    def test_just_a_moment_page_from_cloudflare(self):
        self.assertTrue(isCloudflareChallenge(FakeResponse(403, {'Server': 'cloudflare'}, CHALLENGE_PAGE)))
        self.assertTrue(isCloudflareChallenge(FakeResponse(503, {'Server': 'cloudflare'}, CHALLENGE_PAGE)))

    def test_plain_403_is_a_real_refusal(self):
        self.assertFalse(isCloudflareChallenge(FakeResponse(403, {'Server': 'nginx'}, 'Forbidden')))
        self.assertFalse(isCloudflareChallenge(FakeResponse(403, {'Server': 'cloudflare'}, 'Access denied by the site')))

    def test_other_statuses_are_left_alone(self):
        self.assertFalse(isCloudflareChallenge(FakeResponse(404, {'cf-mitigated': 'challenge'})))
        self.assertFalse(isCloudflareChallenge(FakeResponse(500, {'Server': 'cloudflare'}, CHALLENGE_PAGE)))


class UnwrapBrowserJsonTest(unittest.TestCase):

    def test_json_in_chrome_pre_is_unwrapped_and_unescaped(self):
        body = ('<html><head><meta name="color-scheme" content="light dark"><meta charset="utf-8"></head>'
                '<body><pre>[{"id":"1","name":"Fast &amp; Furious"}]</pre><div class="json-formatter-container"></div></body></html>')
        self.assertEqual(unwrapBrowserJson(body), '[{"id":"1","name":"Fast & Furious"}]')

    def test_html_pages_are_returned_as_is(self):
        page = '<html><head><title>Search</title></head><body><table class="download"></table></body></html>'
        self.assertEqual(unwrapBrowserJson(page), page)

    def test_pre_with_text_that_is_not_json_is_returned_as_is(self):
        page = '<html><head></head><body><pre>plain text</pre></body></html>'
        self.assertEqual(unwrapBrowserJson(page), page)


if __name__ == '__main__':
    unittest.main()

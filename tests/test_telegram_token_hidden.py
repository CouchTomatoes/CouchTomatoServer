"""The Telegram bot token must never be written to the log (it was, on every failed send)."""
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'libs'))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests

from couchpotato.core.notifications import telegrambot
from couchpotato.core.notifications.telegrambot import TelegramBot

TOKEN = '7000000001:AAFakeSecretPartThatMustNotBeLogged'


def make_bot():
    bot = TelegramBot.__new__(TelegramBot)
    bot.conf = lambda key, *a, **kw: {'bot_token': TOKEN, 'receiver_user_id': '42'}.get(key)
    return bot


def logged_text(error_mock):
    out = []
    for call in error_mock.call_args_list:
        args = call[0]
        msg = args[0]
        params = args[1] if len(args) > 1 else ()
        out.append(msg % params if params else msg)
    return '\n'.join(out)


class TelegramTokenHiddenTest(unittest.TestCase):

    def test_bad_response_logs_bot_id_not_token(self):
        resp = mock.Mock(status_code=502, text='{"ok":false,"error_code":502,"description":"Bad Gateway"}')
        with mock.patch.object(telegrambot.requests, 'post', return_value=resp), \
                mock.patch.object(telegrambot.log, 'error') as err:
            self.assertFalse(make_bot().notify('hello'))
        text = logged_text(err)
        self.assertIn('Bad Gateway', text)
        self.assertIn('7000000001', text)
        self.assertNotIn('AAFakeSecretPart', text)

    def test_connection_error_with_url_is_masked(self):
        exc = requests.ConnectionError(
            "HTTPSConnectionPool(host='api.telegram.org', port=443): Max retries exceeded with url: /bot%s/sendMessage" % TOKEN)
        with mock.patch.object(telegrambot.requests, 'post', side_effect=exc), \
                mock.patch.object(telegrambot.log, 'error') as err:
            self.assertFalse(make_bot().notify('hello'))
        text = logged_text(err)
        self.assertIn('Max retries exceeded', text)
        self.assertNotIn('AAFakeSecretPart', text)

    def test_success_logs_nothing(self):
        resp = mock.Mock(status_code=200, text='{"ok":true}')
        with mock.patch.object(telegrambot.requests, 'post', return_value=resp), \
                mock.patch.object(telegrambot.log, 'error') as err:
            self.assertTrue(make_bot().notify('hello'))
        err.assert_not_called()


if __name__ == '__main__':
    unittest.main()

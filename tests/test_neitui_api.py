import http.client
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest

from server.neitui_api import ReferralServer


ADD_PASSWORD = 'test-add-password'
DELETE_PASSWORD = 'test-delete-password'


class ReferralApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.server = ReferralServer(
            ('127.0.0.1', 0), str(Path(self.temp.name) / 'referrals.db'),
            ADD_PASSWORD, DELETE_PASSWORD
        )
        self.addCleanup(self.server.server_close)
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(self.server.shutdown)

    def request(self, method, path, body=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port)
        headers = {'Content-Type': 'application/json'}
        payload = json.dumps(body) if body is not None else None
        connection.request(method, path, body=payload, headers=headers)
        response = connection.getresponse()
        result = response.status, json.loads(response.read())
        connection.close()
        return result

    def test_add_requires_password_and_consent_then_appears(self):
        listing = {
            'information': '北京后端实习', 'contact': '联系人',
            'contactDetails': 'QQ：12345', 'contactConsent': True
        }
        status, result = self.request('POST', '/api/neitui', {**listing, 'password': 'wrong'})
        self.assertEqual((status, result['error']), (403, 'wrong_password'))
        status, result = self.request('POST', '/api/neitui', {**listing, 'contactConsent': False, 'password': ADD_PASSWORD})
        self.assertEqual((status, result['error']), (400, 'invalid_referral'))
        status, result = self.request('POST', '/api/neitui', {**listing, 'password': ADD_PASSWORD})
        self.assertEqual(status, 201)
        status, data = self.request('GET', '/api/neitui')
        self.assertEqual(status, 200)
        self.assertEqual(len(data['referrals']), 2)
        self.assertEqual(data['referrals'][0]['id'], result['id'])

    def test_delete_uses_separate_password_and_does_not_reseed(self):
        _, data = self.request('GET', '/api/neitui')
        item_id = data['referrals'][0]['id']
        status, result = self.request('POST', '/api/neitui/delete', {'id': item_id, 'password': ADD_PASSWORD})
        self.assertEqual((status, result['error']), (403, 'wrong_password'))
        status, result = self.request('POST', '/api/neitui/delete', {'id': item_id, 'password': DELETE_PASSWORD})
        self.assertEqual((status, result['ok']), (200, True))
        _, data = self.request('GET', '/api/neitui')
        self.assertEqual(data['referrals'], [])
        with sqlite3.connect(self.server.database) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM referrals').fetchone()[0], 0)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM deleted_referrals WHERE id = ?', (item_id,)).fetchone()[0], 1)
        from server.neitui_api import initialize_database
        initialize_database(self.server.database)
        _, data = self.request('GET', '/api/neitui')
        self.assertEqual(data['referrals'], [])

    def test_wrong_password_is_rate_limited(self):
        for _ in range(5):
            status, _ = self.request('POST', '/api/neitui', {'password': 'wrong'})
            self.assertEqual(status, 403)
        status, result = self.request('POST', '/api/neitui', {'password': ADD_PASSWORD})
        self.assertEqual((status, result['error']), (429, 'too_many_attempts'))


if __name__ == '__main__':
    unittest.main()

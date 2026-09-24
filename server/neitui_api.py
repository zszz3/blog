#!/usr/bin/env python3
"""Small same-origin API for password-confirmed referral submissions."""

import hmac
import json
import os
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


MAX_BODY = 16_384
MAX_ATTEMPTS = 5
ATTEMPT_WINDOW = 600
SEED_FILE = Path(__file__).resolve().parents[1] / 'src/data/neitui.json'


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def initialize_database(path, seed_file=SEED_FILE):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open_database(path) as db:
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('''CREATE TABLE IF NOT EXISTS referrals (
            id TEXT PRIMARY KEY,
            information TEXT NOT NULL,
            contact TEXT NOT NULL,
            contact_details TEXT NOT NULL,
            created_at TEXT NOT NULL
        )''')
        db.execute('''CREATE TABLE IF NOT EXISTS deleted_referrals (
            id TEXT PRIMARY KEY,
            deleted_at TEXT NOT NULL
        )''')
        for item in json.loads(Path(seed_file).read_text(encoding='utf-8')):
            if db.execute('SELECT 1 FROM deleted_referrals WHERE id = ?', (item['id'],)).fetchone():
                continue
            db.execute('''INSERT OR IGNORE INTO referrals
                (id, information, contact, contact_details, created_at)
                VALUES (?, ?, ?, ?, ?)''', (
                    item['id'], item['information'], item['contact'],
                    item['contactDetails'], now_iso()
                ))


@contextmanager
def open_database(path):
    db = sqlite3.connect(path, timeout=5)
    try:
        yield db
        db.commit()
    finally:
        db.close()


class AttemptLimiter:
    def __init__(self, limit=MAX_ATTEMPTS, window=ATTEMPT_WINDOW):
        self.attempts = {}
        self.lock = threading.Lock()
        self.limit = limit
        self.window = window

    def blocked(self, address):
        with self.lock:
            now = time.monotonic()
            times = [t for t in self.attempts.get(address, []) if now - t < self.window]
            self.attempts[address] = times
            return len(times) >= self.limit

    def failure(self, address):
        with self.lock:
            self.attempts.setdefault(address, []).append(time.monotonic())

    def success(self, address):
        with self.lock:
            self.attempts.pop(address, None)


class ReferralServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, database, add_password, delete_password):
        if len(add_password) < 6 or len(delete_password) < 6 or add_password == delete_password:
            raise ValueError('Two distinct passwords of at least 6 characters are required')
        initialize_database(database)
        self.database = database
        self.add_password = add_password
        self.delete_password = delete_password
        self.limiter = AttemptLimiter()
        self.global_limiter = AttemptLimiter(limit=50)
        self.submission_limiter = AttemptLimiter(limit=5)
        super().__init__(address, ReferralHandler)


class ReferralHandler(BaseHTTPRequestHandler):
    def json_response(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(body)

    def database(self):
        return open_database(self.server.database)

    def do_GET(self):
        if self.path != '/api/neitui':
            return self.json_response(404, {'error': 'not_found'})
        with self.database() as db:
            rows = db.execute('''SELECT id, information, contact, contact_details, created_at
                FROM referrals ORDER BY created_at DESC, rowid DESC''').fetchall()
        self.json_response(200, {'referrals': [
            {'id': row[0], 'information': row[1], 'contact': row[2],
             'contactDetails': row[3], 'createdAt': row[4]}
            for row in rows
        ]})

    def read_json(self):
        if self.headers.get('Content-Type', '').split(';', 1)[0].strip() != 'application/json':
            return None
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if size < 1 or size > MAX_BODY:
                return None
            value = json.loads(self.rfile.read(size))
            return value if isinstance(value, dict) else None
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
            return None

    def client_id(self):
        # Caddy overwrites this header and the API container has no published port.
        return self.headers.get('X-Real-IP', self.client_address[0])

    def authorized(self, supplied, expected):
        address = f'{self.path}:{self.client_id()}'
        action = self.path
        if self.server.limiter.blocked(address) or self.server.global_limiter.blocked(action):
            self.json_response(429, {'error': 'too_many_attempts'})
            return False
        if not isinstance(supplied, str) or not hmac.compare_digest(supplied, expected):
            self.server.limiter.failure(address)
            self.server.global_limiter.failure(action)
            self.json_response(403, {'error': 'wrong_password'})
            return False
        self.server.limiter.success(address)
        return True

    def do_POST(self):
        if self.path not in ('/api/neitui', '/api/neitui/delete'):
            return self.json_response(404, {'error': 'not_found'})
        data = self.read_json()
        if data is None:
            return self.json_response(400, {'error': 'invalid_request'})
        expected = self.server.add_password if self.path == '/api/neitui' else self.server.delete_password
        if not self.authorized(data.get('password'), expected):
            return

        if self.path == '/api/neitui':
            information = data.get('information')
            contact = data.get('contact')
            contact_details = data.get('contactDetails')
            if data.get('contactConsent') is not True or not all(
                isinstance(value, str) and value.strip() and len(value.strip()) <= maximum
                for value, maximum in ((information, 1000), (contact, 80), (contact_details, 200))
            ):
                return self.json_response(400, {'error': 'invalid_referral'})
            if self.server.submission_limiter.blocked(self.client_id()):
                return self.json_response(429, {'error': 'too_many_attempts'})
            item_id = str(uuid.uuid4())
            created_at = now_iso()
            with self.database() as db:
                db.execute('''INSERT INTO referrals
                    (id, information, contact, contact_details, created_at)
                    VALUES (?, ?, ?, ?, ?)''', (
                        item_id, information.strip(), contact.strip(),
                        contact_details.strip(), created_at
                    ))
            self.server.submission_limiter.failure(self.client_id())
            self.json_response(201, {'id': item_id})
            return

        item_id = data.get('id')
        if not isinstance(item_id, str) or len(item_id) > 100:
            return self.json_response(400, {'error': 'invalid_request'})
        with self.database() as db:
            changed = db.execute('DELETE FROM referrals WHERE id = ?', (item_id,)).rowcount
            if changed:
                db.execute('INSERT OR IGNORE INTO deleted_referrals (id, deleted_at) VALUES (?, ?)',
                           (item_id, now_iso()))
        if not changed:
            return self.json_response(404, {'error': 'not_found'})
        self.json_response(200, {'ok': True})


def main():
    database = os.environ.get('NEITUI_DB_PATH', '/data/neitui.sqlite3')
    add_password = os.environ.get('NEITUI_ADD_PASSWORD', '')
    delete_password = os.environ.get('NEITUI_DELETE_PASSWORD', '')
    server = ReferralServer(('0.0.0.0', 8080), database, add_password, delete_password)
    server.serve_forever()


if __name__ == '__main__':
    main()

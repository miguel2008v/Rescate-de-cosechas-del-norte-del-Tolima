"""Verifica la API WSGI sin librerías externas."""
import io
import json
import unittest
from app import app
from logic.algorithms import DEFAULT_PRODUCERS

def request(path, method='GET', data=None):
    body = json.dumps(data).encode('utf-8') if data is not None else b''
    env = {'PATH_INFO': path, 'REQUEST_METHOD': method,
           'CONTENT_LENGTH': str(len(body)), 'wsgi.input': io.BytesIO(body)}
    out = {}
    def start_response(status, headers):
        out['status'] = status
        out['headers'] = dict(headers)
    payload = b''.join(app(env, start_response))
    return out, payload

class WebTests(unittest.TestCase):
    def test_health(self):
        result, payload = request('/health')
        self.assertTrue(result['status'].startswith('200'))
        self.assertEqual(json.loads(payload), {'status': 'ok'})
    def test_ui(self):
        result, payload = request('/')
        self.assertTrue(result['status'].startswith('200'))
        self.assertIn(b'<!doctype html>', payload.lower())
    def test_assets(self):
        for path in ('/static/styles.css', '/static/app.js'):
            result, payload = request(path)
            self.assertTrue(result['status'].startswith('200'))
            self.assertGreater(len(payload), 100)
    def test_defaults(self):
        _, payload = request('/api/defaults')
        self.assertEqual(len(json.loads(payload)['producers']), 6)
    def test_solve(self):
        result, payload = request('/api/solve', 'POST',
                                  {'producers': DEFAULT_PRODUCERS,
                                   'capacities': [100,100]})
        self.assertTrue(result['status'].startswith('200'))
        data = json.loads(payload)
        self.assertTrue(data['feasible'])
        self.assertEqual(data['exact']['total_load'], 180)
    def test_benchmark(self):
        result, payload = request('/api/benchmark', 'POST')
        self.assertTrue(result['status'].startswith('200'))
        self.assertEqual(len(json.loads(payload)['rows']), 4)
    def test_invalid_json(self):
        result, payload = request('/api/solve', 'POST', {})
        self.assertTrue(result['status'].startswith('200'))
        # Sin producers/capacities se utiliza el escenario original.
        self.assertTrue(json.loads(payload)['feasible'])
    def test_denies_internal_files(self):
        for path in ('/app.py', '/logic/algorithms.py', '/.env', '/requirements.txt'):
            result, _ = request(path)
            self.assertTrue(result['status'].startswith('404'))

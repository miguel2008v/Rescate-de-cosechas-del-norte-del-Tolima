"""Rescate de Cosechas: servidor WSGI para Render.

La lógica de rutas vive en logic/algorithms.py. Esta capa HTTP sirve la
interfaz y expone la API JSON, sin framework ni credenciales privadas.
Localmente: python app.py  |  En Render: gunicorn app:app
"""

import json
from http import HTTPStatus
from pathlib import Path
from urllib.parse import unquote
from wsgiref.simple_server import make_server

from logic.algorithms import DEFAULT_PRODUCERS, DEPOT, solve

ROOT = Path(__file__).resolve().parent
MAX_REQUEST_BYTES = 100_000
STATIC_FILES = {
    '/': (ROOT / 'templates' / 'index.html', 'text/html; charset=utf-8'),
    '/static/app.js': (ROOT / 'static' / 'app.js', 'text/javascript; charset=utf-8'),
    '/static/styles.css': (ROOT / 'static' / 'styles.css', 'text/css; charset=utf-8'),
}


def run_benchmark():
    extras = [
        {'id': 'C7', 'name': 'Productor simulado 7', 'municipio': 'Simulado',
         'weight': 10, 'priority': 'Media', 'x': 7, 'y': 9},
        {'id': 'C8', 'name': 'Productor simulado 8', 'municipio': 'Simulado',
         'weight': 10, 'priority': 'Media', 'x': 9, 'y': 7},
    ]
    points = DEFAULT_PRODUCERS + extras
    rows = []
    for n in range(5, 9):
        result = solve(points[:n], [100, 100])
        if result['feasible']:
            st = result['stats']
            rows.append({
                'n': n,
                'greedy': result['greedy']['total_distance'],
                'backtracking': result['exact']['total_distance'],
                'ms': st['elapsed_ms'],
                'nodes': st['assignment_nodes'] + st['route_nodes'],
                'prunes': st['assignment_prunes_capacity'] + st['route_prunes_distance'],
            })
        else:
            rows.append({'n': n, 'error': result['message']})
    return {
        'rows': rows,
        'note': 'Para N=7 y N=8 se agregan productores académicos simulados de 10 kg.',
    }


def respond(start_response, status, content, content_type, headers=None):
    data = content if isinstance(content, bytes) else content.encode('utf-8')
    status_text = f'{status} {HTTPStatus(status).phrase}'
    out_headers = [
        ('Content-Type', content_type),
        ('Content-Length', str(len(data))),
        ('X-Content-Type-Options', 'nosniff'),
        ('X-Frame-Options', 'DENY'),
    ]
    if headers:
        out_headers.extend(headers)
    start_response(status_text, out_headers)
    return [data]


def json_response(start_response, data, status=200):
    content = json.dumps(data, ensure_ascii=False, allow_nan=False).encode('utf-8')
    return respond(start_response, status, content, 'application/json; charset=utf-8',
                   [('Cache-Control', 'no-store')])


def app(environ, start_response):
    """Punto de entrada WSGI para Gunicorn (`app:app`)."""
    route = unquote(environ.get('PATH_INFO') or '/')
    method = environ.get('REQUEST_METHOD', 'GET').upper()

    if method == 'GET':
        if route in ('/health', '/healthz'):
            return json_response(start_response, {'status': 'ok'})
        if route == '/api/defaults':
            return json_response(start_response, {
                'producers': DEFAULT_PRODUCERS,
                'capacities': [100, 100],
                'depot': DEPOT,
            })
        if route in STATIC_FILES:
            path, mime_type = STATIC_FILES[route]
            return respond(start_response, 200, path.read_bytes(), mime_type,
                           [('Cache-Control', 'public, max-age=300')])
        return json_response(start_response, {'error': 'Recurso no encontrado.'}, 404)

    if method != 'POST':
        return json_response(start_response, {'error': 'Método no permitido.'}, 405)

    if route not in ('/api/solve', '/api/benchmark'):
        return json_response(start_response, {'error': 'Recurso no encontrado.'}, 404)

    if route == '/api/benchmark':
        return json_response(start_response, run_benchmark())

    try:
        size = int(environ.get('CONTENT_LENGTH') or '0')
        if size <= 0 or size > MAX_REQUEST_BYTES:
            return json_response(start_response, {'error': 'Tamaño de solicitud inválido.'}, 400)
        payload = json.loads(environ['wsgi.input'].read(size))
        if not isinstance(payload, dict):
            raise ValueError('Envía un objeto JSON válido.')
        return json_response(start_response, solve(
            payload.get('producers'), payload.get('capacities')))
    except (ValueError, TypeError, KeyError, OverflowError) as exc:
        return json_response(start_response, {'error': str(exc)}, 400)


if __name__ == '__main__':
    # Desarrollo local solamente. Render utiliza Gunicorn como servidor HTTP.
    import os
    host = '127.0.0.1'
    port = int(os.environ.get('PORT', '5000'))
    with make_server(host, port, app) as server:
        print(f'Aplicación local disponible en http://{host}:{port}/')
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print('\nServidor detenido.')

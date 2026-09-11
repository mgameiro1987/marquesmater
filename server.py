import os
import json
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlsplit

PORT = int(os.environ.get("PORT", "10000"))
ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

try:
    from db import init_db, get_conn
except Exception:
    init_db = lambda: False
    get_conn = lambda: None

DB_READY = init_db()

class Handler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map,
        ".svg": "image/svg+xml", ".js": "application/javascript", ".css": "text/css"}

    def _json(self, status, payload):
        raw = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/api/health':
            self._json(200, {'ok': True, 'database': bool(DB_READY), 'version': 'V10'})
            return
        if path == '/api/db-status':
            self._json(200, {'database': bool(DB_READY)})
            return
        if path.endswith('.html') or path in ('', '/'):
            if path in ('', '/'):
                path = '/index.html'
            filename = os.path.join(ROOT, path.lstrip('/'))
            if os.path.isfile(filename):
                try:
                    with open(filename, 'rb') as f:
                        data = f.read()
                    marker = b'</head>'
                    injections = [
                        b'<link rel="stylesheet" href="/css/v8.5-mobilepc.css?v=85">',
                        b'<link rel="stylesheet" href="/css/v8.5-account-mobile.css?v=851">'
                    ]
                    for injection in injections:
                        if marker in data and injection not in data:
                            data = data.replace(marker, injection + marker, 1)
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html; charset=utf-8')
                    self.send_header('Content-Length', str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    return
                except OSError:
                    pass
        super().do_GET()

server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
print(f"MarquesMater V10 server running on port {PORT}; database={DB_READY}")
server.serve_forever()

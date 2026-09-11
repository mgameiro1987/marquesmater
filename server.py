import os
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlsplit

PORT = int(os.environ.get("PORT", "10000"))
ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

class Handler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map,
        ".svg": "image/svg+xml", ".js": "application/javascript", ".css": "text/css"}

    def do_GET(self):
        # V8.5: aplica o ajuste de layout a todas as páginas HTML.
        path = urlsplit(self.path).path
        if path.endswith('.html') or path in ('', '/'):
            if path in ('', '/'):
                path = '/index.html'
            filename = os.path.join(ROOT, path.lstrip('/'))
            if os.path.isfile(filename):
                try:
                    with open(filename, 'rb') as f:
                        data = f.read()
                    marker = b'</head>'
                    injection = b'<link rel="stylesheet" href="/css/v8.5-mobilepc.css?v=85">'
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
print(f"MarquesMater server running on port {PORT}")
server.serve_forever()

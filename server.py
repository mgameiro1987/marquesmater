import os
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

PORT = int(os.environ.get("PORT", "10000"))
ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

class Handler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map,
        ".svg": "image/svg+xml", ".js": "application/javascript", ".css": "text/css"}

server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
print(f"MarquesMater server running on port {PORT}")
server.serve_forever()

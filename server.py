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


def body_json(handler):
    try:
        length = int(handler.headers.get('Content-Length', '0'))
        raw = handler.rfile.read(length) if length else b'{}'
        return json.loads(raw.decode('utf-8') or '{}')
    except Exception:
        return {}


def customer_email(handler, data=None):
    email = handler.headers.get('X-Customer-Email', '')
    if not email and isinstance(data, dict):
        email = str(data.get('email', '') or '')
    return email.strip().lower()


def ensure_customer(conn, email, name='', phone=''):
    if not email:
        return None
    with conn.cursor() as cur:
        cur.execute("""INSERT INTO customers(email,name,phone) VALUES(%s,%s,%s)
                       ON CONFLICT(email) DO UPDATE SET
                       name=CASE WHEN EXCLUDED.name<>'' THEN EXCLUDED.name ELSE customers.name END,
                       phone=CASE WHEN EXCLUDED.phone<>'' THEN EXCLUDED.phone ELSE customers.phone END,
                       updated_at=NOW()
                       RETURNING id,email,name,phone""", (email, name, phone))
        return cur.fetchone()


class Handler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map,
        ".svg": "image/svg+xml", ".js": "application/javascript", ".css": "text/css"}

    def _json(self, status, payload):
        raw = json.dumps(payload, ensure_ascii=False, default=str).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/api/health':
            self._json(200, {'ok': True, 'database': bool(DB_READY), 'version': 'V10'})
            return
        if path == '/api/db-status':
            self._json(200, {'database': bool(DB_READY), 'version': 'V10'})
            return
        if path == '/api/customer':
            email = customer_email(self)
            if not DB_READY or not email:
                self._json(200, {'ok': False, 'database': bool(DB_READY)})
                return
            conn = get_conn()
            with conn:
                with conn.cursor() as cur:
                    cur.execute('SELECT id,email,name,phone,created_at,updated_at FROM customers WHERE email=%s', (email,))
                    row = cur.fetchone()
            self._json(200, {'ok': bool(row), 'customer': dict(zip(['id','email','name','phone','created_at','updated_at'], row)) if row else None})
            return
        if path == '/api/cart':
            email = customer_email(self)
            if not DB_READY or not email:
                self._json(200, {'ok': False, 'cart': []})
                return
            conn = get_conn()
            with conn:
                row = ensure_customer(conn, email)
                with conn.cursor() as cur:
                    cur.execute('SELECT data FROM customer_carts WHERE customer_id=%s', (row[0],))
                    found = cur.fetchone()
            self._json(200, {'ok': True, 'cart': found[0] if found else []})
            return
        if path == '/api/favorites':
            email = customer_email(self)
            if not DB_READY or not email:
                self._json(200, {'ok': False, 'favorites': []})
                return
            conn = get_conn()
            with conn:
                row = ensure_customer(conn, email)
                with conn.cursor() as cur:
                    cur.execute('SELECT sku FROM customer_favorites WHERE customer_id=%s ORDER BY created_at DESC', (row[0],))
                    favs = [r[0] for r in cur.fetchall()]
            self._json(200, {'ok': True, 'favorites': favs})
            return
        if path == '/api/orders':
            email = customer_email(self)
            if not DB_READY or not email:
                self._json(200, {'ok': False, 'orders': []})
                return
            conn = get_conn()
            with conn:
                row = ensure_customer(conn, email)
                with conn.cursor() as cur:
                    cur.execute('SELECT id,data,created_at FROM orders WHERE customer_id=%s ORDER BY created_at DESC', (row[0],))
                    orders = [{'id':r[0], 'data':r[1], 'created_at':r[2]} for r in cur.fetchall()]
            self._json(200, {'ok': True, 'orders': orders})
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
                    body_marker = b'</body>'
                    db_script = b'<script src="/js/v10-db-sync.js?v=10"></script>'
                    if body_marker in data and db_script not in data:
                        data = data.replace(body_marker, db_script + body_marker, 1)
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/html; charset=utf-8')
                    self.send_header('Content-Length', str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    return
                except OSError:
                    pass
        super().do_GET()

    def do_POST(self):
        path = urlsplit(self.path).path
        data = body_json(self)
        if path == '/api/customer':
            email = customer_email(self, data)
            if not DB_READY or not email:
                self._json(400, {'ok': False, 'error': 'Base de dados indisponível ou email em falta'})
                return
            conn = get_conn()
            with conn:
                row = ensure_customer(conn, email, str(data.get('name','') or ''), str(data.get('phone','') or ''))
            self._json(200, {'ok': True, 'customer': dict(zip(['id','email','name','phone'], row))})
            return
        if path == '/api/cart':
            email = customer_email(self, data)
            if not DB_READY or not email:
                self._json(400, {'ok': False, 'error': 'Cliente em falta'})
                return
            conn = get_conn()
            with conn:
                row = ensure_customer(conn, email)
                with conn.cursor() as cur:
                    cur.execute("""INSERT INTO customer_carts(customer_id,data,updated_at) VALUES(%s,%s,NOW())
                                   ON CONFLICT(customer_id) DO UPDATE SET data=EXCLUDED.data,updated_at=NOW()""", (row[0], json.dumps(data.get('cart', []))))
            self._json(200, {'ok': True})
            return
        if path == '/api/favorites':
            email = customer_email(self, data)
            if not DB_READY or not email:
                self._json(400, {'ok': False, 'error': 'Cliente em falta'})
                return
            conn = get_conn()
            with conn:
                row = ensure_customer(conn, email)
                with conn.cursor() as cur:
                    cur.execute('DELETE FROM customer_favorites WHERE customer_id=%s', (row[0],))
                    for sku in data.get('favorites', []) or []:
                        if sku:
                            cur.execute('INSERT INTO customer_favorites(customer_id,sku) VALUES(%s,%s) ON CONFLICT DO NOTHING', (row[0], str(sku)))
            self._json(200, {'ok': True})
            return
        if path == '/api/orders':
            email = customer_email(self, data)
            if not DB_READY or not email:
                self._json(400, {'ok': False, 'error': 'Cliente em falta'})
                return
            conn = get_conn()
            with conn:
                row = ensure_customer(conn, email, str(data.get('name','') or ''), str(data.get('phone','') or ''))
                with conn.cursor() as cur:
                    cur.execute('INSERT INTO orders(customer_id,data) VALUES(%s,%s) RETURNING id,created_at', (row[0], json.dumps(data.get('order', data))))
                    created = cur.fetchone()
            self._json(201, {'ok': True, 'id': created[0], 'created_at': created[1]})
            return
        self._json(404, {'ok': False, 'error': 'Endpoint inexistente'})


server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
print(f"MarquesMater V10 server running on port {PORT}; database={DB_READY}")
server.serve_forever()

import os, json
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlsplit

PORT = int(os.environ.get("PORT", "10000"))
ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

try:
    import psycopg
except Exception:
    psycopg = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS mm_product_stock (
  sku TEXT PRIMARY KEY,
  stock INTEGER NOT NULL DEFAULT 0,
  stock_min INTEGER NOT NULL DEFAULT 0,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS mm_stock_movements (
  id BIGSERIAL PRIMARY KEY,
  sku TEXT NOT NULL,
  movement_type TEXT NOT NULL,
  delta INTEGER NOT NULL,
  resulting_stock INTEGER NOT NULL,
  reason TEXT,
  notes TEXT,
  created_by TEXT NOT NULL DEFAULT 'MarquesMater',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS mm_stock_movements_sku_idx ON mm_stock_movements(sku, created_at DESC);
"""

def db():
    if psycopg is None or not os.environ.get("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL não configurado")
    return psycopg.connect(os.environ["DATABASE_URL"])

def init_db():
    with db() as conn:
        with conn.cursor() as cur:
            for stmt in SCHEMA.split(';'):
                if stmt.strip(): cur.execute(stmt)

def read_json(handler):
    n = int(handler.headers.get('Content-Length', '0') or 0)
    raw = handler.rfile.read(n) if n else b'{}'
    return json.loads(raw.decode('utf-8') or '{}')

class Handler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map,
        ".svg": "image/svg+xml", ".js": "application/javascript", ".css": "text/css"}

    def send_json(self, status, payload):
        data = json.dumps(payload, ensure_ascii=False, default=str).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_json(204, {})

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/api/stock':
            try:
                init_db()
                with db() as conn, conn.cursor() as cur:
                    cur.execute("SELECT sku, stock, stock_min, updated_at FROM mm_product_stock ORDER BY sku")
                    rows = cur.fetchall()
                self.send_json(200, {"ok": True, "items": [
                    {"sku": r[0], "stock": r[1], "stockMin": r[2], "updatedAt": r[3]} for r in rows]})
            except Exception as e:
                self.send_json(503, {"ok": False, "error": str(e)})
            return
        if path == '/api/stock/movements':
            try:
                init_db(); q = self.path.split('?',1)[1] if '?' in self.path else ''
                import urllib.parse
                params = urllib.parse.parse_qs(q); sku = (params.get('sku') or [''])[0]
                with db() as conn, conn.cursor() as cur:
                    if sku:
                        cur.execute("SELECT id, sku, movement_type, delta, resulting_stock, reason, notes, created_by, created_at FROM mm_stock_movements WHERE sku=%s ORDER BY created_at DESC LIMIT 100", (sku,))
                    else:
                        cur.execute("SELECT id, sku, movement_type, delta, resulting_stock, reason, notes, created_by, created_at FROM mm_stock_movements ORDER BY created_at DESC LIMIT 500")
                    rows = cur.fetchall()
                self.send_json(200, {"ok": True, "items": [dict(id=r[0], sku=r[1], type=r[2], delta=r[3], stock=r[4], reason=r[5] or '', notes=r[6] or '', user=r[7], createdAt=r[8]) for r in rows]})
            except Exception as e:
                self.send_json(503, {"ok": False, "error": str(e)})
            return
        if path.endswith('.html') or path in ('', '/'):
            if path in ('', '/'): path = '/index.html'
            filename = os.path.join(ROOT, path.lstrip('/'))
            if os.path.isfile(filename):
                try:
                    with open(filename, 'rb') as f: data = f.read()
                    marker = b'</head>'
                    injections = [b'<link rel="stylesheet" href="/css/v8.5-mobilepc.css?v=85">', b'<link rel="stylesheet" href="/css/v8.5-account-mobile.css?v=851">']
                    for injection in injections:
                        if marker in data and injection not in data: data = data.replace(marker, injection + marker, 1)
                    self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Cache-Control','no-store'); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data); return
                except OSError: pass
        super().do_GET()

    def do_POST(self):
        path = urlsplit(self.path).path
        if path not in ('/api/stock/ensure','/api/stock/adjust'):
            self.send_json(404, {"ok": False, "error": "Endpoint não encontrado"}); return
        try:
            init_db(); body = read_json(self)
            with db() as conn, conn.cursor() as cur:
                if path == '/api/stock/ensure':
                    items = body.get('items') or []
                    for p in items:
                        sku = str(p.get('sku') or '').strip()
                        if not sku: continue
                        # Only creates missing rows; never overwrites existing real stock.
                        stock = int(p.get('stock') or 0) if isinstance(p.get('stock'), (int,float)) else 0
                        cur.execute("INSERT INTO mm_product_stock(sku,stock,stock_min) VALUES(%s,%s,%s) ON CONFLICT(sku) DO NOTHING", (sku, stock, int(p.get('stockMin') or 0)))
                    conn.commit()
                    self.send_json(200, {"ok": True}); return
                sku = str(body.get('sku') or '').strip(); typ = str(body.get('type') or 'adjust').strip(); qty = int(body.get('quantity') or 0); minimum = int(body.get('stockMin') or 0)
                if not sku: raise ValueError('SKU obrigatório')
                if qty < 0: raise ValueError('Quantidade inválida')
                cur.execute("INSERT INTO mm_product_stock(sku,stock,stock_min) VALUES(%s,0,%s) ON CONFLICT(sku) DO NOTHING", (sku, minimum))
                cur.execute("SELECT stock, stock_min FROM mm_product_stock WHERE sku=%s FOR UPDATE", (sku,)); row = cur.fetchone(); old = int(row[0]); oldmin = int(row[1])
                if typ in ('in','entry','Entrada (+)','return','Devolução'): delta = qty
                elif typ in ('out','exit','Saída / venda'): delta = -qty
                elif typ in ('adjust','Ajuste para quantidade'): delta = qty - old
                else: raise ValueError('Tipo de movimento inválido')
                new = old + delta
                if new < 0: raise ValueError('O stock não pode ficar negativo')
                cur.execute("UPDATE mm_product_stock SET stock=%s, stock_min=%s, updated_at=NOW() WHERE sku=%s", (new, minimum if 'stockMin' in body else oldmin, sku))
                cur.execute("INSERT INTO mm_stock_movements(sku,movement_type,delta,resulting_stock,reason,notes,created_by) VALUES(%s,%s,%s,%s,%s,%s,%s)", (sku, typ, delta, new, str(body.get('reason') or ''), str(body.get('notes') or ''), str(body.get('user') or 'MarquesMater')))
                conn.commit()
            self.send_json(200, {"ok": True, "sku": sku, "stock": new, "stockMin": minimum if 'stockMin' in body else oldmin, "delta": delta})
        except Exception as e:
            self.send_json(400 if isinstance(e, ValueError) else 503, {"ok": False, "error": str(e)})

try:
    init_db()
    print('MarquesMater PostgreSQL stock API ready')
except Exception as e:
    print(f'PostgreSQL stock API not ready: {e}')

server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
print(f"MarquesMater server running on port {PORT}")
server.serve_forever()

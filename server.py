import os, json
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlsplit

PORT=int(os.environ.get('PORT','10000'))
ROOT=os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
try:
    import psycopg
except Exception:
    psycopg=None

SCHEMA="""CREATE TABLE IF NOT EXISTS mm_product_stock (sku TEXT PRIMARY KEY,stock INTEGER NOT NULL DEFAULT 0,stock_min INTEGER NOT NULL DEFAULT 0,updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW());CREATE TABLE IF NOT EXISTS mm_stock_movements (id BIGSERIAL PRIMARY KEY,sku TEXT NOT NULL,movement_type TEXT NOT NULL,delta INTEGER NOT NULL,resulting_stock INTEGER NOT NULL,reason TEXT,notes TEXT,created_by TEXT NOT NULL DEFAULT 'MarquesMater',created_at TIMESTAMPTZ NOT NULL DEFAULT NOW());CREATE INDEX IF NOT EXISTS mm_stock_movements_sku_idx ON mm_stock_movements(sku,created_at DESC);"""

def db():
    if psycopg is None or not os.environ.get('DATABASE_URL'):
        raise RuntimeError('DATABASE_URL não configurado')
    return psycopg.connect(os.environ['DATABASE_URL'])

def init_db():
    with db() as c:
        with c.cursor() as x:
            for statement in SCHEMA.split(';'):
                if statement.strip(): x.execute(statement)

def read_json(h):
    n=int(h.headers.get('Content-Length','0') or 0)
    raw=h.rfile.read(n) if n else b'{}'
    return json.loads(raw.decode('utf-8') or '{}')

class Handler(SimpleHTTPRequestHandler):
    extensions_map={**SimpleHTTPRequestHandler.extensions_map,'.svg':'image/svg+xml','.js':'application/javascript','.css':'text/css'}

    def send_json(self,status,payload):
        data=json.dumps(payload,ensure_ascii=False,default=str).encode()
        self.send_response(status)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Cache-Control','no-store')
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Access-Control-Allow-Headers','Content-Type')
        self.send_header('Access-Control-Allow-Methods','GET,POST,OPTIONS')
        self.send_header('Content-Length',str(len(data)))
        self.end_headers(); self.wfile.write(data)

    def do_OPTIONS(self): self.send_json(204,{})

    def do_GET(self):
        path=urlsplit(self.path).path
        if path=='/api/catalog/barcode':
            try:
                from v96_catalog_api import handle_get
                if handle_get(path,self.path.split('?',1)[1] if '?' in self.path else '',self.send_json): return
            except Exception as e:
                self.send_json(503,{'ok':False,'error':str(e)}); return
        if path in ('/api/stock','/api/stock/movements'):
            try:
                from v96_stock_api import handle_get
                if handle_get(path,self.path.split('?',1)[1] if '?' in self.path else '',self.send_json): return
            except Exception as e:
                self.send_json(503,{'ok':False,'error':str(e)}); return
        if path=='/api/orders' or path.startswith('/api/orders/'):
            try:
                from v96_api import handle_get
                if handle_get(path,self.path.split('?',1)[1] if '?' in self.path else '',self.send_json): return
            except Exception as e:
                self.send_json(503,{'ok':False,'error':str(e)}); return
        if path.endswith('.html') or path in ('','/'):
            if path in ('','/'): path='/index.html'
            fn=os.path.join(ROOT,path.lstrip('/'))
            if os.path.isfile(fn):
                try:
                    with open(fn,'rb') as f: data=f.read()
                    marker=b'</head>'
                    ins=[b'<link rel="stylesheet" href="/css/v8.5-mobilepc.css?v=85">',b'<link rel="stylesheet" href="/css/v8.5-account-mobile.css?v=851">']
                    if path!='/admin.html': ins.append(b'<script src="/js/v9.3.25-stock-public.js?v=93251"></script>')
                    for item in ins:
                        if marker in data and item not in data: data=data.replace(marker,item+marker,1)
                    self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Cache-Control','no-store'); self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data); return
                except OSError: pass
        super().do_GET()

    def do_POST(self):
        path=urlsplit(self.path).path
        if path=='/api/catalog/barcode':
            try:
                from v96_catalog_api import handle_post
                if handle_post(path,read_json(self),self.send_json): return
            except Exception as e:
                self.send_json(503,{'ok':False,'error':str(e)}); return
        if path in ('/api/stock/adjust',):
            try:
                from v96_stock_api import handle_post
                if handle_post(path,read_json(self),self.send_json): return
            except Exception as e:
                self.send_json(503,{'ok':False,'error':str(e)}); return
        if path=='/api/orders' or (path.startswith('/api/orders/') and path.endswith('/status')):
            try:
                from v96_api import handle_post
                if handle_post(path,read_json(self),self.send_json): return
            except Exception as e:
                self.send_json(503,{'ok':False,'error':str(e)}); return
        if path=='/api/stock/ensure':
            try:
                init_db(); body=read_json(self)
                with db() as c,x:
                    for p in body.get('items') or []:
                        sku=str(p.get('sku') or '').strip()
                        if sku: x.execute('INSERT INTO mm_product_stock(sku,stock,stock_min) VALUES(%s,%s,%s) ON CONFLICT(sku) DO NOTHING',(sku,int(p.get('stock') or 0),int(p.get('stockMin') or 0)))
                    c.commit()
                self.send_json(200,{'ok':True}); return
            except Exception as e:
                self.send_json(503,{'ok':False,'error':str(e)}); return
        self.send_json(404,{'ok':False,'error':'Endpoint não encontrado'})

try:
    init_db(); print('MarquesMater PostgreSQL stock API ready')
except Exception as e:
    print(f'PostgreSQL stock API not ready: {e}')

server=ThreadingHTTPServer(('0.0.0.0',PORT),Handler)
print(f'MarquesMater server running on port {PORT}')
server.serve_forever()

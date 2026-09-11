import os
import json
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlsplit, parse_qs

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


def catalog_product(data):
    return {
        'sku': str(data.get('sku','')).strip(), 'brand': str(data.get('brand','') or ''),
        'name': str(data.get('name','') or ''), 'category': str(data.get('category','') or ''),
        'subcategory': str(data.get('subcategory','') or ''), 'type': str(data.get('type','') or ''),
        'price': float(data.get('price') or 0),
        'oldPrice': float(data['oldPrice']) if data.get('oldPrice') not in (None,'') else None,
        'stock': str(data.get('stock','Em stock') or 'Em stock'), 'image': str(data.get('image','') or ''),
        'badge': str(data.get('badge','') or ''), 'description': str(data.get('description','') or ''),
        'options': data.get('options') or {}, 'specs': data.get('specs') or [], 'active': bool(data.get('active', True))
    }


def catalog_rows(conn, include_inactive=False):
    with conn.cursor() as cur:
        cur.execute("""SELECT sku,brand,name,category,subcategory,type,price,old_price,stock,image,badge,description,options,specs,active,updated_at
                       FROM catalog_products WHERE (%s OR active=TRUE) ORDER BY id""", (include_inactive,))
        rows = cur.fetchall()
    keys=['sku','brand','name','category','subcategory','type','price','oldPrice','stock','image','badge','description','options','specs','active','updated_at']
    out=[]
    for r in rows:
        p=dict(zip(keys,r)); p['price']=float(p['price']) if p['price'] is not None else 0; p['oldPrice']=float(p['oldPrice']) if p['oldPrice'] is not None else None
        if p['updated_at'] is not None:p['updated_at']=str(p['updated_at'])
        out.append(p)
    return out


class Handler(SimpleHTTPRequestHandler):
    extensions_map={**SimpleHTTPRequestHandler.extensions_map,".svg":"image/svg+xml",".js":"application/javascript",".css":"text/css"}

    def _json(self,status,payload):
        raw=json.dumps(payload,ensure_ascii=False,default=str).encode('utf-8');self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)

    def do_GET(self):
        path=urlsplit(self.path).path
        if path=='/api/health':
            database=False
            try:
                conn=get_conn()
                if conn:
                    with conn:
                        with conn.cursor() as cur:cur.execute('SELECT 1');cur.fetchone()
                    database=True
            except Exception as e:print(f'DB health error: {e}')
            self._json(200,{'ok':True,'database':database,'version':'V10.1'});return
        if path=='/api/db-status':self._json(200,{'database':bool(DB_READY),'version':'V10.1'});return
        if path=='/api/catalog':
            if not DB_READY:self._json(503,{'ok':False,'catalog':[],'error':'Base de dados indisponível'});return
            try:
                conn=get_conn()
                with conn:items=catalog_rows(conn)
                self._json(200,{'ok':True,'catalog':items,'count':len(items),'source':'postgresql'})
            except Exception as e:print(f'Catalog GET error: {e}');self._json(500,{'ok':False,'catalog':[],'error':'Erro ao ler catálogo'})
            return
        if path=='/api/customer':
            email=customer_email(self)
            if not DB_READY or not email:self._json(200,{'ok':False,'database':bool(DB_READY)});return
            conn=get_conn()
            with conn:
                with conn.cursor() as cur:cur.execute('SELECT id,email,name,phone,created_at,updated_at FROM customers WHERE email=%s',(email,));row=cur.fetchone()
            self._json(200,{'ok':bool(row),'customer':dict(zip(['id','email','name','phone','created_at','updated_at'],row)) if row else None});return
        if path=='/api/address':
            email=customer_email(self)
            if not DB_READY or not email:self._json(200,{'ok':False,'addresses':[]});return
            conn=get_conn()
            with conn:
                row=ensure_customer(conn,email)
                with conn.cursor() as cur:cur.execute('SELECT id,label,data,created_at FROM customer_addresses WHERE customer_id=%s ORDER BY id DESC',(row[0],));addresses=[{'id':r[0],'label':r[1],'data':r[2],'created_at':r[3]} for r in cur.fetchall()]
            self._json(200,{'ok':True,'addresses':addresses});return
        if path=='/api/cart':
            email=customer_email(self)
            if not DB_READY or not email:self._json(200,{'ok':False,'cart':[]});return
            conn=get_conn()
            with conn:
                row=ensure_customer(conn,email)
                with conn.cursor() as cur:cur.execute('SELECT data FROM customer_carts WHERE customer_id=%s',(row[0],));found=cur.fetchone()
            self._json(200,{'ok':True,'cart':found[0] if found else []});return
        if path=='/api/favorites':
            email=customer_email(self)
            if not DB_READY or not email:self._json(200,{'ok':False,'favorites':[]});return
            conn=get_conn()
            with conn:
                row=ensure_customer(conn,email)
                with conn.cursor() as cur:cur.execute('SELECT sku FROM customer_favorites WHERE customer_id=%s ORDER BY created_at DESC',(row[0],));favs=[r[0] for r in cur.fetchall()]
            self._json(200,{'ok':True,'favorites':favs});return
        if path=='/api/orders':
            email=customer_email(self)
            if not DB_READY or not email:self._json(200,{'ok':False,'orders':[]});return
            conn=get_conn()
            with conn:
                row=ensure_customer(conn,email)
                with conn.cursor() as cur:cur.execute('SELECT id,data,created_at FROM orders WHERE customer_id=%s ORDER BY created_at DESC',(row[0],));orders=[{'id':r[0],'data':r[1],'created_at':r[2]} for r in cur.fetchall()]
            self._json(200,{'ok':True,'orders':orders});return
        if path.endswith('.html') or path in ('','/'):
            if path in ('','/'):path='/index.html'
            filename=os.path.join(ROOT,path.lstrip('/'))
            if os.path.isfile(filename):
                try:
                    with open(filename,'rb') as f:data=f.read()
                    marker=b'</head>'
                    injections=[b'<link rel="stylesheet" href="/css/v8.5-mobilepc.css?v=85">',b'<link rel="stylesheet" href="/css/v8.5-account-mobile.css?v=851">']
                    for injection in injections:
                        if marker in data and injection not in data:data=data.replace(marker,injection+marker,1)
                    body_marker=b'</body>'
                    scripts=[b'<script src="/js/v10-db-sync.js?v=101"></script>',b'<script src="/js/v10-account-orders.js?v=101"></script>']
                    for script in scripts:
                        if body_marker in data and script not in data:data=data.replace(body_marker,script+body_marker,1)
                    self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data);return
                except OSError:pass
        super().do_GET()

    def do_POST(self):
        path=urlsplit(self.path).path;data=body_json(self)
        if path=='/api/catalog':
            if not DB_READY:self._json(503,{'ok':False,'error':'Base de dados indisponível'});return
            p=catalog_product(data)
            if not p['sku'] or not p['name']:self._json(400,{'ok':False,'error':'SKU e nome são obrigatórios'});return
            conn=get_conn()
            try:
                with conn:
                    with conn.cursor() as cur:
                        cur.execute("""INSERT INTO catalog_products (sku,brand,name,category,subcategory,type,price,old_price,stock,image,badge,description,options,specs,active,updated_at)
                        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s,NOW())
                        ON CONFLICT(sku) DO UPDATE SET brand=EXCLUDED.brand,name=EXCLUDED.name,category=EXCLUDED.category,subcategory=EXCLUDED.subcategory,type=EXCLUDED.type,price=EXCLUDED.price,old_price=EXCLUDED.old_price,stock=EXCLUDED.stock,image=EXCLUDED.image,badge=EXCLUDED.badge,description=EXCLUDED.description,options=EXCLUDED.options,specs=EXCLUDED.specs,active=EXCLUDED.active,updated_at=NOW() RETURNING sku""",(p['sku'],p['brand'],p['name'],p['category'],p['subcategory'],p['type'],p['price'],p['oldPrice'],p['stock'],p['image'],p['badge'],p['description'],json.dumps(p['options']),json.dumps(p['specs']),p['active']))
                        sku=cur.fetchone()[0]
                self._json(200,{'ok':True,'sku':sku,'source':'postgresql'})
            except Exception as e:print(f'Catalog POST error: {e}');self._json(500,{'ok':False,'error':'Erro ao guardar produto'})
            finally:conn.close()
            return
        if path=='/api/customer':
            email=customer_email(self,data)
            if not DB_READY or not email:self._json(400,{'ok':False,'error':'Base de dados indisponível ou email em falta'});return
            conn=get_conn()
            with conn:row=ensure_customer(conn,email,str(data.get('name','') or ''),str(data.get('phone','') or ''))
            self._json(200,{'ok':True,'customer':dict(zip(['id','email','name','phone'],row))});return
        if path=='/api/address':
            email=customer_email(self,data)
            if not DB_READY or not email:self._json(400,{'ok':False,'error':'Cliente em falta'});return
            conn=get_conn()
            with conn:
                row=ensure_customer(conn,email);address=data.get('address') or data.get('data') or {};label=str(data.get('label','Principal') or 'Principal')
                with conn.cursor() as cur:cur.execute('INSERT INTO customer_addresses(customer_id,label,data) VALUES(%s,%s,%s::jsonb) RETURNING id',(row[0],label,json.dumps(address)));aid=cur.fetchone()[0]
            self._json(201,{'ok':True,'id':aid});return
        if path=='/api/cart':
            email=customer_email(self,data)
            if not DB_READY or not email:self._json(400,{'ok':False,'error':'Cliente em falta'});return
            conn=get_conn()
            with conn:
                row=ensure_customer(conn,email)
                with conn.cursor() as cur:cur.execute("""INSERT INTO customer_carts(customer_id,data,updated_at) VALUES(%s,%s::jsonb,NOW()) ON CONFLICT(customer_id) DO UPDATE SET data=EXCLUDED.data,updated_at=NOW()""",(row[0],json.dumps(data.get('cart',[]))))
            self._json(200,{'ok':True});return
        if path=='/api/favorites':
            email=customer_email(self,data)
            if not DB_READY or not email:self._json(400,{'ok':False,'error':'Cliente em falta'});return
            conn=get_conn()
            with conn:
                row=ensure_customer(conn,email)
                with conn.cursor() as cur:
                    cur.execute('DELETE FROM customer_favorites WHERE customer_id=%s',(row[0],))
                    for sku in data.get('favorites',[]) or []:
                        if sku:cur.execute('INSERT INTO customer_favorites(customer_id,sku) VALUES(%s,%s) ON CONFLICT DO NOTHING',(row[0],str(sku)))
            self._json(200,{'ok':True});return
        if path=='/api/orders':
            email=customer_email(self,data)
            if not DB_READY or not email:self._json(400,{'ok':False,'error':'Cliente em falta'});return
            conn=get_conn()
            with conn:
                row=ensure_customer(conn,email,str(data.get('name','') or ''),str(data.get('phone','') or ''))
                with conn.cursor() as cur:cur.execute('INSERT INTO orders(customer_id,data) VALUES(%s,%s::jsonb) RETURNING id,created_at',(row[0],json.dumps(data.get('order',data))));created=cur.fetchone()
            self._json(201,{'ok':True,'id':created[0],'created_at':created[1]});return
        self._json(404,{'ok':False,'error':'Endpoint inexistente'})

    def do_DELETE(self):
        path=urlsplit(self.path).path
        if path!='/api/catalog':self._json(404,{'ok':False,'error':'Endpoint inexistente'});return
        if not DB_READY:self._json(503,{'ok':False,'error':'Base de dados indisponível'});return
        qs=parse_qs(urlsplit(self.path).query);sku=(qs.get('sku') or [''])[0].strip()
        if not sku:self._json(400,{'ok':False,'error':'SKU em falta'});return
        conn=get_conn()
        with conn:
            with conn.cursor() as cur:cur.execute('UPDATE catalog_products SET active=FALSE,updated_at=NOW() WHERE sku=%s RETURNING sku',(sku,));row=cur.fetchone()
        self._json(200,{'ok':bool(row),'sku':sku})

server=ThreadingHTTPServer(("0.0.0.0",PORT),Handler)
print(f"MarquesMater V10.1 server running on port {PORT}; database={DB_READY}")
server.serve_forever()

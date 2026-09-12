import os
import json
import re
import unicodedata
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlsplit, parse_qs

PORT = int(os.environ.get("PORT", "10000"))
ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)
try:
    from db import init_db, get_conn, slugify
except Exception:
    init_db = lambda: False
    get_conn = lambda: None
    def slugify(v):
        s=unicodedata.normalize('NFKD',str(v or '')).encode('ascii','ignore').decode('ascii').lower()
        return re.sub(r'[^a-z0-9]+','-',s).strip('-') or 'item'
DB_READY = init_db()


def body_json(handler):
    try:
        length=int(handler.headers.get('Content-Length','0')); raw=handler.rfile.read(length) if length else b'{}'
        return json.loads(raw.decode('utf-8') or '{}')
    except Exception:
        return {}


def customer_email(handler,data=None):
    email=handler.headers.get('X-Customer-Email','')
    if not email and isinstance(data,dict): email=str(data.get('email','') or '')
    return email.strip().lower()


def ensure_customer(conn,email,name='',phone=''):
    if not email:return None
    with conn.cursor() as cur:
        cur.execute("""INSERT INTO customers(email,name,phone) VALUES(%s,%s,%s)
        ON CONFLICT(email) DO UPDATE SET name=CASE WHEN EXCLUDED.name<>'' THEN EXCLUDED.name ELSE customers.name END,
        phone=CASE WHEN EXCLUDED.phone<>'' THEN EXCLUDED.phone ELSE customers.phone END,updated_at=NOW()
        RETURNING id,email,name,phone""",(email,name,phone)); return cur.fetchone()


def catalog_product(data):
    return {'sku':str(data.get('sku','')).strip(),'brand':str(data.get('brand','') or ''),'name':str(data.get('name','') or ''),
      'category':str(data.get('category','') or ''),'subcategory':str(data.get('subcategory','') or ''),'type':str(data.get('type','') or ''),
      'price':float(data.get('price') or 0),'oldPrice':float(data['oldPrice']) if data.get('oldPrice') not in (None,'') else None,
      'stock':str(data.get('stock','Em stock') or 'Em stock'),'image':str(data.get('image','') or ''),'badge':str(data.get('badge','') or ''),
      'description':str(data.get('description','') or ''),'options':data.get('options') or {},'specs':data.get('specs') or [],
      'active':bool(data.get('active',True)),'category_id':data.get('category_id'),'subcategory_id':data.get('subcategory_id'),
      'family_id':data.get('family_id'),'brand_id':data.get('brand_id'),'attributes':data.get('attributes') or {}}


def catalog_rows(conn,include_inactive=False):
    with conn.cursor() as cur:
        cur.execute("""SELECT sku,brand,name,category,subcategory,type,price,old_price,stock,image,badge,description,options,specs,active,updated_at,
        category_id,subcategory_id,family_id,brand_id,attributes FROM catalog_products WHERE (%s OR active=TRUE) ORDER BY id""",(include_inactive,)); rows=cur.fetchall()
    keys=['sku','brand','name','category','subcategory','type','price','oldPrice','stock','image','badge','description','options','specs','active','updated_at','category_id','subcategory_id','family_id','brand_id','attributes']
    out=[]
    for r in rows:
        p=dict(zip(keys,r)); p['price']=float(p['price'] or 0); p['oldPrice']=float(p['oldPrice']) if p['oldPrice'] is not None else None
        if p['updated_at'] is not None:p['updated_at']=str(p['updated_at'])
        out.append(p)
    return out


def structure_rows(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT id,name,slug,parent_id,kind,active,sort_order FROM catalog_categories ORDER BY kind,sort_order,name"); cats=[dict(zip(['id','name','slug','parent_id','kind','active','sort_order'],r)) for r in cur.fetchall()]
        cur.execute("SELECT id,name,slug,active FROM catalog_brands ORDER BY name"); brands=[dict(zip(['id','name','slug','active'],r)) for r in cur.fetchall()]
        cur.execute("SELECT id,name,slug,type,active FROM catalog_attributes ORDER BY name"); attrs=[dict(zip(['id','name','slug','type','active'],r)) for r in cur.fetchall()]
        cur.execute("SELECT id,attribute_id,value,slug,active,sort_order FROM catalog_attribute_values ORDER BY attribute_id,sort_order,value"); vals=[dict(zip(['id','attribute_id','value','slug','active','sort_order'],r)) for r in cur.fetchall()]
    for c in cats:c['id']=int(c['id']);c['parent_id']=int(c['parent_id']) if c['parent_id'] is not None else None
    for b in brands:b['id']=int(b['id'])
    for a in attrs:a['id']=int(a['id'])
    for v in vals:v['id']=int(v['id']);v['attribute_id']=int(v['attribute_id'])
    return {'categories':cats,'brands':brands,'attributes':attrs,'attributeValues':vals}


def upsert_structure(conn,data,kind):
    name=str(data.get('name','') or '').strip()
    if not name: raise ValueError('Nome obrigatório')
    slug=str(data.get('slug','') or '').strip() or slugify(name)
    active=bool(data.get('active',True))
    with conn.cursor() as cur:
        if kind=='category':
            parent=data.get('parent_id'); parent=int(parent) if parent not in (None,'') else None
            item_id=data.get('id')
            if item_id:
                cur.execute("UPDATE catalog_categories SET name=%s,slug=%s,parent_id=%s,kind='category',active=%s,updated_at=NOW() WHERE id=%s RETURNING id",(name,slug,parent,active,int(item_id)))
            else: cur.execute("INSERT INTO catalog_categories(name,slug,parent_id,kind,active) VALUES(%s,%s,%s,'category',%s) RETURNING id",(name,slug,parent,active))
        elif kind in ('subcategory','family'):
            parent=data.get('parent_id'); parent=int(parent) if parent not in (None,'') else None
            item_id=data.get('id')
            if item_id: cur.execute("UPDATE catalog_categories SET name=%s,slug=%s,parent_id=%s,kind=%s,active=%s,updated_at=NOW() WHERE id=%s RETURNING id",(name,slug,parent,kind,active,int(item_id)))
            else: cur.execute("INSERT INTO catalog_categories(name,slug,parent_id,kind,active) VALUES(%s,%s,%s,%s,%s) RETURNING id",(name,slug,parent,kind,active))
        elif kind=='brand':
            item_id=data.get('id')
            if item_id: cur.execute("UPDATE catalog_brands SET name=%s,slug=%s,active=%s,updated_at=NOW() WHERE id=%s RETURNING id",(name,slug,active,int(item_id)))
            else: cur.execute("INSERT INTO catalog_brands(name,slug,active) VALUES(%s,%s,%s) RETURNING id",(name,slug,active))
        else:
            item_id=data.get('id'); typ=str(data.get('type','select') or 'select')
            if item_id: cur.execute("UPDATE catalog_attributes SET name=%s,slug=%s,type=%s,active=%s,updated_at=NOW() WHERE id=%s RETURNING id",(name,slug,typ,active,int(item_id)))
            else: cur.execute("INSERT INTO catalog_attributes(name,slug,type,active) VALUES(%s,%s,%s,%s) RETURNING id",(name,slug,typ,active))
        row=cur.fetchone()
    return row[0]


class Handler(SimpleHTTPRequestHandler):
    extensions_map={**SimpleHTTPRequestHandler.extensions_map,'.svg':'image/svg+xml','.js':'application/javascript','.css':'text/css'}
    def _json(self,status,payload):
        raw=json.dumps(payload,ensure_ascii=False,default=str).encode('utf-8');self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)

    def do_GET(self):
        path=urlsplit(self.path).path; qs=parse_qs(urlsplit(self.path).query)
        if path=='/api/health':
            database=False
            try:
                conn=get_conn()
                if conn:
                    with conn:
                        with conn.cursor() as cur:cur.execute('SELECT 1');cur.fetchone()
                    database=True
            except Exception as e:print(f'DB health error: {e}')
            self._json(200,{'ok':True,'database':database,'version':'V10.6'});return
        if path=='/api/db-status':self._json(200,{'database':bool(DB_READY),'version':'V10.6'});return
        if path=='/api/catalog':
            if not DB_READY:self._json(503,{'ok':False,'catalog':[],'error':'Base de dados indisponível'});return
            try:
                conn=get_conn(); include_inactive=(qs.get('include_inactive',['0'])[0]=='1')
                with conn:items=catalog_rows(conn,include_inactive)
                self._json(200,{'ok':True,'catalog':items,'count':len(items),'source':'postgresql'})
            except Exception as e:print(f'Catalog GET error: {e}');self._json(500,{'ok':False,'catalog':[],'error':'Erro ao ler catálogo'})
            return
        if path=='/api/catalog-structure':
            if not DB_READY:self._json(503,{'ok':False,'error':'Base de dados indisponível'});return
            conn=get_conn()
            try:
                with conn: self._json(200,{'ok':True,**structure_rows(conn)})
            finally: conn.close()
            return
        if path in ('/api/customer','/api/address','/api/cart','/api/favorites','/api/orders'):
            email=customer_email(self)
            if not DB_READY or not email:
                key='customer' if path=='/api/customer' else path.split('/')[-1]
                self._json(200,{'ok':False, 'customer':None,'addresses':[],'cart':[],'favorites':[],'orders':[]}.get(key,{}));return
            conn=get_conn()
            with conn:
                row=ensure_customer(conn,email)
                with conn.cursor() as cur:
                    if path=='/api/customer':cur.execute('SELECT id,email,name,phone,created_at,updated_at FROM customers WHERE email=%s',(email,)); r=cur.fetchone(); self._json(200,{'ok':bool(r),'customer':dict(zip(['id','email','name','phone','created_at','updated_at'],r)) if r else None});return
                    if path=='/api/address':cur.execute('SELECT id,label,data,created_at FROM customer_addresses WHERE customer_id=%s ORDER BY id DESC',(row[0],));self._json(200,{'ok':True,'addresses':[{'id':r[0],'label':r[1],'data':r[2],'created_at':r[3]} for r in cur.fetchall()]});return
                    if path=='/api/cart':cur.execute('SELECT data FROM customer_carts WHERE customer_id=%s',(row[0],));r=cur.fetchone();self._json(200,{'ok':True,'cart':r[0] if r else []});return
                    if path=='/api/favorites':cur.execute('SELECT sku FROM customer_favorites WHERE customer_id=%s ORDER BY created_at DESC',(row[0],));self._json(200,{'ok':True,'favorites':[r[0] for r in cur.fetchall()]});return
                    cur.execute('SELECT id,data,created_at FROM orders WHERE customer_id=%s ORDER BY created_at DESC',(row[0],));self._json(200,{'ok':True,'orders':[{'id':r[0],'data':r[1],'created_at':r[2]} for r in cur.fetchall()]});return
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
                    body_marker=b'</body>'; scripts=[b'<script src="/js/v10-db-sync.js?v=101"></script>',b'<script src="/js/v10-account-orders.js?v=101"></script>']
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
                        # If the UI sends names only, resolve their central IDs automatically.
                        if not p['category_id'] and p['category']:
                            cur.execute("SELECT id FROM catalog_categories WHERE kind='category' AND lower(name)=lower(%s) LIMIT 1",(p['category'],));r=cur.fetchone();p['category_id']=r[0] if r else None
                        if not p['subcategory_id'] and p['subcategory']:
                            cur.execute("SELECT id FROM catalog_categories WHERE kind='subcategory' AND lower(name)=lower(%s) LIMIT 1",(p['subcategory'],));r=cur.fetchone();p['subcategory_id']=r[0] if r else None
                        if not p['family_id'] and p['type']:
                            cur.execute("SELECT id FROM catalog_categories WHERE kind='family' AND lower(name)=lower(%s) LIMIT 1",(p['type'],));r=cur.fetchone();p['family_id']=r[0] if r else None
                        if not p['brand_id'] and p['brand']:
                            cur.execute("SELECT id FROM catalog_brands WHERE lower(name)=lower(%s) LIMIT 1",(p['brand'],));r=cur.fetchone();p['brand_id']=r[0] if r else None
                        cur.execute("""INSERT INTO catalog_products(sku,brand,name,category,subcategory,type,price,old_price,stock,image,badge,description,options,specs,active,category_id,subcategory_id,family_id,brand_id,attributes,updated_at)
                        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s,%s,%s,%s,%s::jsonb,NOW())
                        ON CONFLICT(sku) DO UPDATE SET brand=EXCLUDED.brand,name=EXCLUDED.name,category=EXCLUDED.category,subcategory=EXCLUDED.subcategory,type=EXCLUDED.type,price=EXCLUDED.price,old_price=EXCLUDED.old_price,stock=EXCLUDED.stock,image=EXCLUDED.image,badge=EXCLUDED.badge,description=EXCLUDED.description,options=EXCLUDED.options,specs=EXCLUDED.specs,active=EXCLUDED.active,category_id=EXCLUDED.category_id,subcategory_id=EXCLUDED.subcategory_id,family_id=EXCLUDED.family_id,brand_id=EXCLUDED.brand_id,attributes=EXCLUDED.attributes,updated_at=NOW() RETURNING sku""",
                        (p['sku'],p['brand'],p['name'],p['category'],p['subcategory'],p['type'],p['price'],p['oldPrice'],p['stock'],p['image'],p['badge'],p['description'],json.dumps(p['options']),json.dumps(p['specs']),p['active'],p['category_id'],p['subcategory_id'],p['family_id'],p['brand_id'],json.dumps(p['attributes'])))
                        sku=cur.fetchone()[0]
                self._json(200,{'ok':True,'sku':sku,'source':'postgresql'})
            except Exception as e:print(f'Catalog POST error: {e}');self._json(500,{'ok':False,'error':'Erro ao guardar produto'})
            finally:conn.close()
            return
        if path in ('/api/categories','/api/brands','/api/attributes'):
            if not DB_READY:self._json(503,{'ok':False,'error':'Base de dados indisponível'});return
            kind={'/api/categories':'category','/api/brands':'brand','/api/attributes':'attribute'}[path];conn=get_conn()
            try:
                with conn:
                    item_id=upsert_structure(conn,data,kind)
                self._json(200,{'ok':True,'id':item_id})
            except Exception as e:self._json(400,{'ok':False,'error':'Não foi possível guardar: '+str(e)})
            finally:conn.close()
            return
        if path=='/api/attribute-values':
            conn=get_conn()
            try:
                aid=int(data.get('attribute_id')); value=str(data.get('value','') or '').strip()
                if not value:raise ValueError('Valor obrigatório')
                with conn:
                    with conn.cursor() as cur:cur.execute("INSERT INTO catalog_attribute_values(attribute_id,value,slug) VALUES(%s,%s,%s) ON CONFLICT(attribute_id,slug) DO UPDATE SET value=EXCLUDED.value,active=TRUE RETURNING id",(aid,value,slugify(value)));vid=cur.fetchone()[0]
                self._json(200,{'ok':True,'id':vid})
            except Exception as e:self._json(400,{'ok':False,'error':str(e)})
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
                with conn.cursor() as cur:cur.execute("INSERT INTO customer_carts(customer_id,data,updated_at) VALUES(%s,%s::jsonb,NOW()) ON CONFLICT(customer_id) DO UPDATE SET data=EXCLUDED.data,updated_at=NOW()",(row[0],json.dumps(data.get('cart',[]))))
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
        path=urlsplit(self.path).path; qs=parse_qs(urlsplit(self.path).query)
        if path in ('/api/catalog','/api/categories','/api/brands','/api/attributes','/api/attribute-values'):
            if not DB_READY:self._json(503,{'ok':False,'error':'Base de dados indisponível'});return
            conn=get_conn()
            try:
                with conn:
                    with conn.cursor() as cur:
                        if path=='/api/catalog':
                            sku=(qs.get('sku') or [''])[0].strip()
                            if not sku:raise ValueError('SKU em falta')
                            cur.execute('UPDATE catalog_products SET active=FALSE,updated_at=NOW() WHERE sku=%s RETURNING sku',(sku,));row=cur.fetchone();self._json(200,{'ok':bool(row),'sku':sku});return
                        item_id=(qs.get('id') or [''])[0]
                        if not item_id:raise ValueError('ID em falta')
                        table={'/api/categories':'catalog_categories','/api/brands':'catalog_brands','/api/attributes':'catalog_attributes','/api/attribute-values':'catalog_attribute_values'}[path]
                        cur.execute(f'UPDATE {table} SET active=FALSE WHERE id=%s RETURNING id',(int(item_id),));row=cur.fetchone();self._json(200,{'ok':bool(row),'id':int(item_id)});return
            except Exception as e:self._json(400,{'ok':False,'error':str(e)})
            finally:conn.close()
            return
        self._json(404,{'ok':False,'error':'Endpoint inexistente'})

# MarquesMater — API admin de encomendas instalada diretamente no Handler.
try:
    from orders_admin_api import install as _mm_install_orders_direct
    _mm_install_orders_direct(Handler)
except Exception as _mm_orders_error:
    print('MarquesMater orders direct install error:', _mm_orders_error)

server=ThreadingHTTPServer(("0.0.0.0",PORT),Handler)
print(f"MarquesMater V10.6 server running on port {PORT}; database={DB_READY}")
server.serve_forever()

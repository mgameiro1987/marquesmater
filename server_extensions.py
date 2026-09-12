import os, json
from urllib.parse import urlsplit


def _read_json(handler):
    try:
        n = int(handler.headers.get('Content-Length', '0') or 0)
        raw = handler.rfile.read(n) if n else b'{}'
        return json.loads(raw.decode('utf-8') or '{}')
    except Exception:
        return {}


def _merge(a, b):
    out = dict(a or {})
    for k, v in (b or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict): out[k] = _merge(out[k], v)
        else: out[k] = v
    return out


def install(Handler, get_conn, DB_READY):
    """Adds persistent Backoffice APIs and injects the recovered UI."""
    original_get = Handler.do_GET
    original_post = Handler.do_POST

    def ensure_tables(conn):
        with conn.cursor() as cur:
            cur.execute("CREATE TABLE IF NOT EXISTS admin_settings (key TEXT PRIMARY KEY, data JSONB NOT NULL DEFAULT '{}'::jsonb, updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW())")
            cur.execute("CREATE TABLE IF NOT EXISTS admin_promotions (id BIGSERIAL PRIMARY KEY, data JSONB NOT NULL DEFAULT '{}'::jsonb, active BOOLEAN NOT NULL DEFAULT TRUE, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW())")

    def settings(conn):
        ensure_tables(conn)
        with conn.cursor() as cur:
            cur.execute('SELECT key,data FROM admin_settings')
            return {r[0]: r[1] for r in cur.fetchall()}

    def get_settings(conn):
        s = settings(conn)
        return s.get('settings', {}) if isinstance(s.get('settings', {}), dict) else {}

    def save_settings(conn, patch):
        current = get_settings(conn)
        merged = _merge(current, patch if isinstance(patch, dict) else {})
        with conn.cursor() as cur:
            cur.execute("INSERT INTO admin_settings(key,data) VALUES('settings',%s::jsonb) ON CONFLICT(key) DO UPDATE SET data=EXCLUDED.data,updated_at=NOW()", (json.dumps(merged, ensure_ascii=False),))
        return merged

    def promotion_list(conn):
        ensure_tables(conn)
        with conn.cursor() as cur:
            cur.execute('SELECT id,data,active,created_at,updated_at FROM admin_promotions ORDER BY id DESC')
            out=[]
            for r in cur.fetchall():
                d=r[1] if isinstance(r[1],dict) else {}
                out.append({'id':r[0], **d, 'active': bool(r[2]), 'created_at':str(r[3]), 'updated_at':str(r[4])})
            return out

    def admin_state():
        if not DB_READY: raise RuntimeError('Base de dados indisponível')
        conn=get_conn()
        try:
            with conn:
                from server import catalog_rows, structure_rows
                cats=structure_rows(conn)
                prods=catalog_rows(conn, True)
                fam=[]
                for c in cats.get('categories',[]):
                    if c.get('kind')=='family':
                        parent=next((x for x in cats['categories'] if x['id']==c.get('parent_id')),None)
                        sub=next((x for x in cats['categories'] if parent and x['id']==parent.get('parent_id')),None)
                        fam.append({'id':c['id'],'name':c['name'],'slug':c['slug'],'active':c['active'],'subs':[parent['name']] if parent else [],'category':sub['name'] if sub else ''})
                with conn.cursor() as cur:
                    cur.execute('SELECT COUNT(*) FROM orders'); orders_count=cur.fetchone()[0]
                    cur.execute('SELECT COUNT(*) FROM customers'); customers_count=cur.fetchone()[0]
                return {'ok':True,'products':prods,'families':fam,'categories':cats.get('categories',[]),'brands':[x['name'] for x in cats.get('brands',[])],'brandObjects':cats.get('brands',[]),'promotions':promotion_list(conn),'settings':get_settings(conn),'inventory':prods,'orders':orders_count,'customers':customers_count}
        finally: conn.close()

    def get_handler(self, *args, **kwargs):
        path=urlsplit(self.path).path
        if path=='/api/admin/state':
            try:self._json(200, admin_state())
            except Exception as e:self._json(500, {'ok':False,'error':str(e)})
            return
        if path=='/api/admin/settings':
            try:
                conn=get_conn()
                with conn:self._json(200, {'ok':True,'settings':get_settings(conn)})
                conn.close()
            except Exception as e:self._json(500, {'ok':False,'error':str(e)})
            return
        if path=='/api/admin/promotions':
            try:
                conn=get_conn()
                with conn:self._json(200, {'ok':True,'promotions':promotion_list(conn)})
                conn.close()
            except Exception as e:self._json(500, {'ok':False,'error':str(e)})
            return
        if path=='/api/admin/customers':
            try:
                conn=get_conn()
                with conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT c.id,c.name,c.email,c.phone,c.updated_at,COUNT(o.id) FROM customers c LEFT JOIN orders o ON o.customer_id=c.id GROUP BY c.id ORDER BY c.updated_at DESC")
                        rows=cur.fetchall()
                    self._json(200, {'ok':True,'customers':[{'id':r[0],'name':r[1],'email':r[2],'phone':r[3],'updated_at':str(r[4]),'orders_count':r[5]} for r in rows]})
                conn.close()
            except Exception as e:self._json(500, {'ok':False,'error':str(e)})
            return
        return original_get(*args, **kwargs)

    def post_handler(self, *args, **kwargs):
        path=urlsplit(self.path).path
        if path in ('/api/admin/settings','/api/admin/promotions'):
            data=_read_json(self)
            try:
                conn=get_conn()
                with conn:
                    if path=='/api/admin/settings':
                        patch=data.get('settings', data)
                        saved=save_settings(conn, patch)
                        result={'ok':True,'settings':saved}
                    else:
                        items=data.get('promotions')
                        if items is None: items=[data]
                        ensure_tables(conn)
                        with conn.cursor() as cur:
                            cur.execute('DELETE FROM admin_promotions')
                            for item in items:
                                active=bool(item.get('active',True)) if isinstance(item,dict) else True
                                cur.execute('INSERT INTO admin_promotions(data,active) VALUES(%s::jsonb,%s)',(json.dumps(item,ensure_ascii=False),active))
                        result={'ok':True,'promotions':promotion_list(conn)}
                self._json(200,result)
            except Exception as e:self._json(500, {'ok':False,'error':str(e)})
            return
        return original_post(*args, **kwargs)

    Handler.do_GET=get_handler
    Handler.do_POST=post_handler

    old_get=get_handler
    def get_with_ui(self, *args, **kwargs):
        path=urlsplit(self.path).path
        if path=='/admin.html':
            filename=os.path.join(os.path.dirname(os.path.abspath(__file__)),'admin.html')
            try:
                with open(filename,'rb') as f:data=f.read()
                tag=b'<script src="js/v10.40-backoffice-recovery.js?v=140"></script>'
                if tag not in data and b'</body>' in data:data=data.replace(b'</body>',tag+b'</body>',1)
                self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data);return
            except Exception: pass
        return old_get(self, *args, **kwargs)
    Handler.do_GET=get_with_ui

import os,json
from urllib.parse import urlsplit

def _read_json(h):
    try:
        n=int(h.headers.get('Content-Length','0') or 0); return json.loads(h.rfile.read(n).decode('utf-8') or '{}') if n else {}
    except Exception:return {}

def _merge(a,b):
    o=dict(a or {})
    for k,v in (b or {}).items(): o[k]=_merge(o.get(k),v) if isinstance(v,dict) and isinstance(o.get(k),dict) else v
    return o

def install(Handler,get_conn,DB_READY):
    original_get,original_post=Handler.do_GET,Handler.do_POST
    def ensure_tables(c):
        with c.cursor() as q:
            q.execute("CREATE TABLE IF NOT EXISTS admin_settings (key TEXT PRIMARY KEY,data JSONB NOT NULL DEFAULT '{}'::jsonb,updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW())")
            q.execute("CREATE TABLE IF NOT EXISTS admin_promotions (id BIGSERIAL PRIMARY KEY,data JSONB NOT NULL DEFAULT '{}'::jsonb,active BOOLEAN NOT NULL DEFAULT TRUE,created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW())")
    def get_settings(c):
        ensure_tables(c)
        with c.cursor() as q:q.execute("SELECT data FROM admin_settings WHERE key='settings'");r=q.fetchone()
        return r[0] if r and isinstance(r[0],dict) else {}
    def save_settings(c,p):
        s=_merge(get_settings(c),p if isinstance(p,dict) else {})
        with c.cursor() as q:q.execute("INSERT INTO admin_settings(key,data) VALUES('settings',%s::jsonb) ON CONFLICT(key) DO UPDATE SET data=EXCLUDED.data,updated_at=NOW()",(json.dumps(s,ensure_ascii=False),))
        return s
    def promotions(c):
        ensure_tables(c)
        with c.cursor() as q:q.execute('SELECT id,data,active,created_at,updated_at FROM admin_promotions ORDER BY id DESC');rows=q.fetchall()
        return [{'id':r[0],**(r[1] if isinstance(r[1],dict) else {}),'active':bool(r[2]),'created_at':str(r[3]),'updated_at':str(r[4])} for r in rows]
    def state():
        if not DB_READY:raise RuntimeError('Base de dados indisponível')
        c=get_conn()
        try:
            from server import catalog_rows,structure_rows
            with c:
                st=structure_rows(c);prods=catalog_rows(c,True)
                with c.cursor() as q:q.execute('SELECT COUNT(*) FROM orders');oc=q.fetchone()[0];q.execute('SELECT COUNT(*) FROM customers');cc=q.fetchone()[0]
                return {'ok':True,'products':prods,'inventory':prods,'categories':st.get('categories',[]),'brands':[x['name'] for x in st.get('brands',[])],'brandObjects':st.get('brands',[]),'promotions':promotions(c),'settings':get_settings(c),'orders':oc,'customers':cc,'families':[]}
        finally:c.close()
    def get_handler(*args,**kwargs):
        self=args[0];path=urlsplit(self.path).path
        try:
            if path=='/api/admin/state':self._json(200,state());return
            if path=='/api/admin/settings':
                c=get_conn()
                try:
                    with c:self._json(200,{'ok':True,'settings':get_settings(c)})
                finally:c.close()
                return
            if path=='/api/admin/promotions':
                c=get_conn()
                try:
                    with c:self._json(200,{'ok':True,'promotions':promotions(c)})
                finally:c.close()
                return
            if path=='/api/admin/customers':
                c=get_conn()
                try:
                    with c:
                        with c.cursor() as q:
                            q.execute("SELECT c.id,c.name,c.email,c.phone,c.updated_at,COUNT(o.id) FROM customers c LEFT JOIN orders o ON o.customer_id=c.id GROUP BY c.id ORDER BY c.updated_at DESC");rows=q.fetchall()
                        self._json(200,{'ok':True,'customers':[{'id':r[0],'name':r[1],'email':r[2],'phone':r[3],'updated_at':str(r[4]),'orders_count':r[5]} for r in rows]})
                finally:c.close()
                return
        except Exception as e:
            try:self._json(500,{'ok':False,'error':str(e)})
            except Exception:pass
            return
        return original_get(self)
    def post_handler(*args,**kwargs):
        self=args[0];path=urlsplit(self.path).path
        if path=='/api/admin/catalog-structure/delete':
            data=_read_json(self)
            try:
                if not DB_READY:raise RuntimeError('Base de dados indisponível')
                item_id=int(data.get('id') or 0)
                if item_id<=0:raise ValueError('ID inválido')
                c=get_conn()
                try:
                    with c:
                        with c.cursor() as q:
                            q.execute("SELECT kind,name FROM catalog_categories WHERE id=%s",(item_id,));item=q.fetchone()
                            if not item:raise ValueError('Elemento não encontrado')
                            q.execute("SELECT COUNT(*) FROM catalog_categories WHERE parent_id=%s",(item_id,));children=q.fetchone()[0]
                            q.execute("SELECT COUNT(*) FROM catalog_products WHERE category_id=%s OR subcategory_id=%s OR family_id=%s",(item_id,item_id,item_id));products=q.fetchone()[0]
                            if children or products:raise ValueError('Não é possível eliminar: este elemento ainda tem elementos dependentes ou produtos associados. Desative-o em vez de o apagar.')
                            q.execute("DELETE FROM catalog_categories WHERE id=%s RETURNING id",(item_id,));row=q.fetchone()
                    self._json(200,{'ok':bool(row),'id':item_id})
                finally:c.close()
            except Exception as e:self._json(400,{'ok':False,'error':str(e)})
            return
        if path in ('/api/admin/settings','/api/admin/promotions'):
            data=_read_json(self)
            try:
                c=get_conn()
                with c:
                    if path=='/api/admin/settings':result={'ok':True,'settings':save_settings(c,data.get('settings',data))}
                    else:
                        items=data.get('promotions');items=items if isinstance(items,list) else [data]
                        ensure_tables(c)
                        with c.cursor() as q:
                            q.execute('DELETE FROM admin_promotions')
                            for x in items:q.execute('INSERT INTO admin_promotions(data,active) VALUES(%s::jsonb,%s)',(json.dumps(x,ensure_ascii=False),bool(x.get('active',True)) if isinstance(x,dict) else True))
                        result={'ok':True,'promotions':promotions(c)}
                self._json(200,result)
            except Exception as e:self._json(500,{'ok':False,'error':str(e)})
            return
        return original_post(self)
    Handler.do_GET=get_handler;Handler.do_POST=post_handler
    old_get=get_handler
    def get_with_ui(*args,**kwargs):
        self=args[0]
        if urlsplit(self.path).path=='/admin.html':
            try:
                root=os.path.dirname(os.path.abspath(__file__))
                with open(os.path.join(root,'admin.html'),'rb') as f:data=f.read()
                for old in (b'<script src="js/v10.40-backoffice-recovery.js?v=140"></script>',b'<script src="js/backoffice-current.js?v=143"></script>',b'<script src="js/v10.44-mobile-menu.js?v=144"></script>',b'<script src="js/backoffice-current.js?v=144"></script>',b'<script src="js/backoffice-current.js?v=145"></script>',b'<script src="js/backoffice-current-editor.js?v=145"></script>',b'<script src="js/v10.46-mobile-menu.js?v=146"></script>'):data=data.replace(old,b'')
                data=data.replace(b'Backoffice V10.29',b'Backoffice V10.51').replace(b'MarquesMater V10.29',b'MarquesMater V10.51')
                css_path=os.path.join(root,'css','v9-admin.css')
                try:
                    with open(css_path,'rb') as f:core_css=f.read()
                    style=b'<style id="mm47-core-css">'+core_css+b'</style>'
                    if b'</head>' in data:data=data.replace(b'</head>',style+b'</head>',1)
                except Exception as e:print('MarquesMater core CSS inline error:',e)
                navfix=b'<script id="mm50-navfix">(()=>{\'use strict\';let routing=false;const route=k=>{if(routing)return;routing=true;try{const go=window.MM104?.go;if(go)go(k);else document.querySelector(`.navitem[data-section="${CSS.escape(k)}"]`)?.click()}catch(e){console.error("MarquesMater navigation error:",e)}setTimeout(()=>{document.getElementById("sidebar")?.classList.remove("open");document.getElementById("mm46shade")?.classList.remove("open");document.body.classList.remove("mm46-lock");routing=false},80)};const handler=e=>{const b=e.target?.closest?.(".navitem");if(!b||routing)return;e.preventDefault();e.stopImmediatePropagation();route(b.dataset.section)};document.addEventListener("click",handler,true);document.addEventListener("pointerup",handler,true);document.addEventListener("touchend",handler,true)})();</script>'
                if b'</head>' in data:data=data.replace(b'</head>',navfix+b'</head>',1)
                tag=b'<script src="js/backoffice-current.js?v=150"></script><script src="js/backoffice-current-editor.js?v=150"></script><script src="js/v10.46-mobile-menu.js?v=150"></script><script src="js/v10.50-mobile-navigation.js?v=150"></script><script src="js/v10.51-catalog-actions.js?v=151"></script><script>window.MMCurrent&&window.MM104&&(function(){var g=window.MM104.go;window.MM104.go=function(k){if(k==="products"){return window.MMCurrent.products()}return g.apply(this,arguments)}})();</script>'
                if b'</body>' in data:data=data.replace(b'</body>',tag+b'</body>',1)
                self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data);return
            except Exception as e:print('MarquesMater admin injection error:',e)
        return old_get(self)
    Handler.do_GET=get_with_ui

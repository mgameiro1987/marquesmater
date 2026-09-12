import json, os, time, threading
from urllib.parse import urlsplit
try:
    import psycopg
except Exception:
    psycopg = None

def conn():
    return psycopg.connect(os.environ['DATABASE_URL']) if psycopg and os.environ.get('DATABASE_URL') else None

def out(h, status, payload):
    raw=json.dumps(payload, ensure_ascii=False, default=str).encode('utf-8')
    h.send_response(status); h.send_header('Content-Type','application/json; charset=utf-8'); h.send_header('Cache-Control','no-store'); h.send_header('Content-Length',str(len(raw))); h.end_headers(); h.wfile.write(raw)

def body(h):
    try:
        n=int(h.headers.get('Content-Length','0')); return json.loads(h.rfile.read(n).decode('utf-8') or '{}')
    except Exception: return {}

def normal_order(row):
    oid, data, created = row
    if not isinstance(data, dict): data={}
    status=str(data.get('status') or data.get('state') or 'Recebida')
    customer=data.get('customer') if isinstance(data.get('customer'),dict) else {}
    total=data.get('total', data.get('totalPrice', data.get('amount', 0)))
    items=data.get('items', data.get('cart', []))
    return {'id':int(oid),'data':data,'status':status,'customer':customer,'total':total,'items':items,'created_at':created}

def install(H):
    if getattr(H,'_mm_orders_admin_installed',False): return
    H._mm_orders_admin_installed=True
    old_get, old_post = H.do_GET, H.do_POST
    def get(self):
        path=urlsplit(self.path).path
        if path!='/api/admin/orders': return old_get(self)
        c=conn()
        if not c:return out(self,503,{'ok':False,'error':'Base de dados indisponível'})
        try:
            with c:
                with c.cursor() as q:
                    q.execute('SELECT id,data,created_at FROM orders ORDER BY created_at DESC')
                    orders=[normal_order(r) for r in q.fetchall()]
            return out(self,200,{'ok':True,'orders':orders,'count':len(orders)})
        except Exception:
            return out(self,500,{'ok':False,'error':'Erro ao ler encomendas'})
        finally:c.close()
    def post(self):
        path=urlsplit(self.path).path; data=body(self)
        if path!='/api/admin/orders/status': return old_post(self)
        c=conn()
        if not c:return out(self,503,{'ok':False,'error':'Base de dados indisponível'})
        allowed=('Recebida','Em preparação','Enviada','Concluída','Cancelada')
        try:
            oid=int(data.get('id')); status=str(data.get('status') or '')
            if status not in allowed:return out(self,400,{'ok':False,'error':'Estado inválido'})
            with c:
                with c.cursor() as q:
                    q.execute('SELECT data FROM orders WHERE id=%s FOR UPDATE',(oid,)); r=q.fetchone()
                    if not r:return out(self,404,{'ok':False,'error':'Encomenda não encontrada'})
                    obj=r[0] if isinstance(r[0],dict) else {}
                    obj['status']=status
                    q.execute('UPDATE orders SET data=%s WHERE id=%s',(json.dumps(obj,ensure_ascii=False),oid))
            return out(self,200,{'ok':True,'id':oid,'status':status})
        except Exception:
            c.rollback(); return out(self,500,{'ok':False,'error':'Erro ao atualizar encomenda'})
        finally:c.close()
    H.do_GET=get; H.do_POST=post

def install_later():
    def loop():
        for _ in range(200):
            H=getattr(__import__('__main__'),'Handler',None)
            if H:
                install(H); return
            time.sleep(.05)
    threading.Thread(target=loop,daemon=True).start()

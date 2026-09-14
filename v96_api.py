import os, json
import psycopg

def _db():
    url=os.environ.get('DATABASE_URL')
    if not url: raise RuntimeError('DATABASE_URL não configurado no Render')
    return psycopg.connect(url)

def _ensure_history():
    with _db() as conn, conn.cursor() as cur:
        cur.execute("CREATE TABLE IF NOT EXISTS mm_order_status_history (id BIGSERIAL PRIMARY KEY, order_id BIGINT NOT NULL, old_status TEXT, new_status TEXT NOT NULL, created_by TEXT NOT NULL DEFAULT 'MarquesMater', created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())")
        cur.execute("CREATE INDEX IF NOT EXISTS mm_order_status_history_order_idx ON mm_order_status_history(order_id,created_at DESC)")
        conn.commit()

def handle_get(path,query,send_json):
    if not(path=='/api/orders' or path.startswith('/api/orders/') or path=='/api/stock'): return False
    try:
        _ensure_history()
        with _db() as conn, conn.cursor() as cur:
            if path=='/api/orders':
                cur.execute("SELECT o.id,o.created_at,o.data,c.name,c.email,COALESCE((SELECT COUNT(*) FROM jsonb_array_elements(CASE WHEN jsonb_typeof(o.data->'items')='array' THEN o.data->'items' ELSE '[]'::jsonb END)),0) FROM orders o LEFT JOIN customers c ON c.id=o.customer_id ORDER BY o.created_at DESC,o.id DESC LIMIT 500")
                out=[]
                for r in cur.fetchall():
                    d=r[2] or {}; cust=d.get('customer') or {}
                    out.append({'id':r[0],'created_at':r[1],'order_number':d.get('number') or f'MM-{r[0]}','status':d.get('status') or 'Pendente','total':d.get('total') or 0,'customer_name':r[3] or cust.get('name',''),'customer_email':r[4] or cust.get('email',''),'item_count':r[5] or 0})
                send_json(200,{'ok':True,'items':out}); return True
            if path.startswith('/api/orders/'):
                raw=path.rsplit('/',1)[-1]
                if not raw.isdigit(): send_json(404,{'ok':False,'error':'Encomenda não encontrada'}); return True
                oid=int(raw)
                cur.execute("SELECT o.id,o.customer_id,o.data,o.created_at,c.name,c.email,c.phone FROM orders o LEFT JOIN customers c ON c.id=o.customer_id WHERE o.id=%s",(oid,)); r=cur.fetchone()
                if not r: send_json(404,{'ok':False,'error':'Encomenda não encontrada'}); return True
                d=r[2] or {}; cust=d.get('customer') or {}
                cur.execute("SELECT old_status,new_status,created_by,created_at FROM mm_order_status_history WHERE order_id=%s ORDER BY created_at DESC LIMIT 50",(oid,))
                hist=[{'oldStatus':a,'newStatus':b,'user':c,'createdAt':e} for a,b,c,e in cur.fetchall()]
                items=[{'sku':x.get('sku',''),'quantity':x.get('qty',x.get('quantity',0)),'productName':x.get('name',x.get('productName','')),'price':x.get('price',0)} for x in (d.get('items') or [])]
                send_json(200,{'ok':True,'order':{'id':r[0],'customer_id':r[1],'order_number':d.get('number') or f'MM-{r[0]}','status':d.get('status') or 'Pendente','total':d.get('total') or 0,'created_at':r[3],'customer_name':r[4] or cust.get('name',''),'customer_email':r[5] or cust.get('email',''),'customer_phone':r[6] or cust.get('phone',''),'customer':cust,'items':items,'history':hist}}); return True
            if path=='/api/stock':
                cur.execute("SELECT s.sku,s.stock,s.stock_min,COALESCE((SELECT SUM(COALESCE((x->>'qty')::int,0)) FROM orders o CROSS JOIN LATERAL jsonb_array_elements(CASE WHEN jsonb_typeof(o.data->'items')='array' THEN o.data->'items' ELSE '[]'::jsonb END) x WHERE x->>'sku'=s.sku AND LOWER(COALESCE(o.data->>'status','')) IN ('pendente','pending','em processamento','processing')),0),s.updated_at FROM mm_product_stock s ORDER BY s.sku")
                out=[{'sku':r[0],'stock':int(r[1] or 0),'reserved':int(r[3] or 0),'available':max(0,int(r[1] or 0)-int(r[3] or 0)),'stockMin':int(r[2] or 0),'updatedAt':r[4]} for r in cur.fetchall()]
                send_json(200,{'ok':True,'items':out}); return True
    except Exception as e: send_json(503,{'ok':False,'error':f'API V9.6: {e}'}); return True

def handle_post(path,body,send_json):
    if not(path.startswith('/api/orders/') and path.endswith('/status')): return False
    try:
        _ensure_history(); raw=path.split('/')[-2]
        if not raw.isdigit(): send_json(404,{'ok':False,'error':'Encomenda não encontrada'}); return True
        new=str(body.get('status') or '').strip(); user=str(body.get('user') or 'MarquesMater')
        allowed={'Recebida','Pendente','Em processamento','Em preparação','Pago','Enviada','Concluída','Cancelada'}
        if new not in allowed: send_json(400,{'ok':False,'error':'Estado inválido'}); return True
        oid=int(raw)
        with _db() as conn, conn.cursor() as cur:
            cur.execute('SELECT data FROM orders WHERE id=%s FOR UPDATE',(oid,)); row=cur.fetchone()
            if not row: send_json(404,{'ok':False,'error':'Encomenda não encontrada'}); return True
            data=row[0] or {}; old=data.get('status') or 'Pendente'; data['status']=new
            cur.execute('UPDATE orders SET data=%s WHERE id=%s',(json.dumps(data,ensure_ascii=False),oid))
            if old!=new: cur.execute('INSERT INTO mm_order_status_history(order_id,old_status,new_status,created_by) VALUES(%s,%s,%s,%s)',(oid,old,new,user))
            conn.commit()
        send_json(200,{'ok':True,'id':oid,'status':new}); return True
    except Exception as e: send_json(503,{'ok':False,'error':f'API V9.6: {e}'}); return True

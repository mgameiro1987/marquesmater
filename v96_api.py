import os, json
import psycopg

PRE_SHIPMENT={'Recebida','Pendente','Em processamento','Em preparação','Pago'}
SHIPMENT_STATUS='Enviada'
STATUS_ORDER=['Recebida','Pendente','Em processamento','Em preparação','Pago','Enviada','Concluída']

def _db():
    url=os.environ.get('DATABASE_URL')
    if not url: raise RuntimeError('DATABASE_URL não configurado no Render')
    return psycopg.connect(url)

def _ensure_history():
    with _db() as conn, conn.cursor() as cur:
        cur.execute("CREATE TABLE IF NOT EXISTS mm_order_status_history (id BIGSERIAL PRIMARY KEY, order_id BIGINT NOT NULL, old_status TEXT, new_status TEXT NOT NULL, created_by TEXT NOT NULL DEFAULT 'MarquesMater', created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())")
        cur.execute("CREATE INDEX IF NOT EXISTS mm_order_status_history_order_idx ON mm_order_status_history(order_id,created_at DESC)")
        cur.execute("CREATE TABLE IF NOT EXISTS mm_order_stock_movements (id BIGSERIAL PRIMARY KEY, order_id BIGINT NOT NULL, sku TEXT NOT NULL, quantity INTEGER NOT NULL, movement_type TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), UNIQUE(order_id,sku,movement_type))")
        cur.execute("CREATE INDEX IF NOT EXISTS mm_order_stock_movements_order_idx ON mm_order_stock_movements(order_id)")
        cur.execute("""CREATE OR REPLACE FUNCTION mm_reject_zero_order() RETURNS trigger AS $$
DECLARE total_text TEXT; total_value NUMERIC;
BEGIN
  total_text := NULLIF(BTRIM(NEW.data->>'total'),'');
  IF total_text IS NULL THEN RAISE EXCEPTION 'Uma encomenda tem de ter um total superior a 0 EUR'; END IF;
  BEGIN total_value := total_text::numeric; EXCEPTION WHEN others THEN RAISE EXCEPTION 'Total de encomenda inválido'; END;
  IF total_value <= 0 THEN RAISE EXCEPTION 'Uma encomenda não pode ter custo zero ou negativo'; END IF;
  RETURN NEW;
END; $$ LANGUAGE plpgsql""")
        cur.execute("DROP TRIGGER IF EXISTS mm_reject_zero_order_trigger ON orders")
        cur.execute("CREATE TRIGGER mm_reject_zero_order_trigger BEFORE INSERT OR UPDATE OF data ON orders FOR EACH ROW EXECUTE FUNCTION mm_reject_zero_order()")

def _order_items(data):
    result={}
    for item in (data.get('items') or []):
        sku=str(item.get('sku') or '').strip()
        qty=item.get('qty',item.get('quantity',0))
        try: qty=int(qty or 0)
        except Exception: qty=0
        if sku and qty>0: result[sku]=result.get(sku,0)+qty
    return result

def _validate_reservation(cur,order_id,data):
    items=_order_items(data)
    for sku,qty in items.items():
        cur.execute("SELECT stock FROM mm_product_stock WHERE sku=%s FOR UPDATE",(sku,))
        row=cur.fetchone()
        if not row: raise ValueError(f'SKU {sku} não tem stock configurado')
        physical=int(row[0] or 0)
        cur.execute("SELECT COALESCE(SUM(COALESCE((x->>'qty')::int,0)),0) FROM orders o CROSS JOIN LATERAL jsonb_array_elements(CASE WHEN jsonb_typeof(o.data->'items')='array' THEN o.data->'items' ELSE '[]'::jsonb END) x WHERE o.id<>%s AND x->>'sku'=%s AND LOWER(COALESCE(o.data->>'status','')) IN ('recebida','pendente','pending','em processamento','processing','em preparação','pago')",(order_id,sku))
        reserved=int(cur.fetchone()[0] or 0)
        available=physical-reserved
        if available<qty: raise ValueError(f'Stock insuficiente para reservar {sku}: disponível {max(0,available)}, necessário {qty}')

def _deduct_stock_for_shipment(cur,order_id,data):
    items=_order_items(data)
    for sku,qty in items.items():
        cur.execute("SELECT stock FROM mm_product_stock WHERE sku=%s FOR UPDATE",(sku,))
        row=cur.fetchone()
        if not row: raise ValueError(f'SKU {sku} não tem stock configurado')
        stock=int(row[0] or 0)
        if stock<qty: raise ValueError(f'Stock insuficiente para {sku}: disponível {stock}, necessário {qty}')
    for sku,qty in items.items():
        cur.execute("SELECT 1 FROM mm_order_stock_movements WHERE order_id=%s AND sku=%s AND movement_type='shipment'",(order_id,sku))
        if cur.fetchone(): continue
        cur.execute("UPDATE mm_product_stock SET stock=stock-%s,updated_at=NOW() WHERE sku=%s",(qty,sku))
        cur.execute("SELECT stock FROM mm_product_stock WHERE sku=%s",(sku,))
        resulting=int(cur.fetchone()[0])
        cur.execute("INSERT INTO mm_stock_movements(sku,movement_type,delta,resulting_stock,reason,notes,created_by) VALUES(%s,%s,%s,%s,%s,%s,%s)",(sku,'Saída / encomenda',-qty,resulting,'Encomenda enviada',f'Encomenda #{order_id}','MarquesMater'))
        cur.execute("INSERT INTO mm_order_stock_movements(order_id,sku,quantity,movement_type) VALUES(%s,%s,%s,'shipment') ON CONFLICT(order_id,sku,movement_type) DO NOTHING",(order_id,sku,qty))

def _safe_total(value):
    try: total=float(str(value).replace(',','.'))
    except Exception: raise ValueError('Total de encomenda inválido')
    if total<=0: raise ValueError('Uma encomenda não pode ter custo zero ou negativo.')
    return round(total,2)

def handle_get(path,query,send_json):
    if not(path=='/api/orders' or path.startswith('/api/orders/') or path=='/api/stock'): return False
    try:
        _ensure_history()
        with _db() as conn, conn.cursor() as cur:
            if path=='/api/orders':
                cur.execute("SELECT o.id,o.created_at,o.data,c.name,c.email,COALESCE((SELECT COUNT(*) FROM jsonb_array_elements(CASE WHEN jsonb_typeof(o.data->'items')='array' THEN o.data->'items' ELSE '[]'::jsonb END)),0) FROM orders o LEFT JOIN customers c ON c.id=o.customer_id WHERE COALESCE(NULLIF(o.data->>'total','')::numeric,0)>0 ORDER BY o.created_at DESC,o.id DESC LIMIT 500")
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
                d=r[2] or {}
                try: _safe_total(d.get('total'))
                except ValueError: send_json(404,{'ok':False,'error':'Encomenda inválida ou sem total'}); return True
                cust=d.get('customer') or {}
                cur.execute("SELECT old_status,new_status,created_by,created_at FROM mm_order_status_history WHERE order_id=%s ORDER BY created_at DESC LIMIT 50",(oid,))
                hist=[{'oldStatus':a,'newStatus':b,'user':c,'createdAt':e} for a,b,c,e in cur.fetchall()]
                items=[{'sku':x.get('sku',''),'quantity':x.get('qty',x.get('quantity',0)),'productName':x.get('name',x.get('productName','')),'price':x.get('price',0),'options':x.get('options') or {},'image':x.get('image',''),'brand':x.get('brand','')} for x in (d.get('items') or [])]
                send_json(200,{'ok':True,'order':{'id':r[0],'customer_id':r[1],'order_number':d.get('number') or f'MM-{r[0]}','status':d.get('status') or 'Pendente','total':d.get('total') or 0,'created_at':r[3],'customer_name':r[4] or cust.get('name',''),'customer_email':r[5] or cust.get('email',''),'customer_phone':r[6] or cust.get('phone',''),'customer':cust,'items':items,'history':hist,'delivery':d.get('delivery',''),'payment':d.get('payment','')} }); return True
            if path=='/api/stock':
                cur.execute("SELECT s.sku,s.stock,s.stock_min,COALESCE((SELECT SUM(COALESCE((x->>'qty')::int,0)) FROM orders o CROSS JOIN LATERAL jsonb_array_elements(CASE WHEN jsonb_typeof(o.data->'items')='array' THEN o.data->'items' ELSE '[]'::jsonb END) x WHERE x->>'sku'=s.sku AND LOWER(COALESCE(o.data->>'status','')) IN ('recebida','pendente','pending','em processamento','processing','em preparação','pago')),0),s.updated_at FROM mm_product_stock s ORDER BY s.sku")
                out=[{'sku':r[0],'stock':int(r[1] or 0),'reserved':int(r[3] or 0),'available':max(0,int(r[1] or 0)-int(r[3] or 0)),'stockMin':int(r[2] or 0),'updatedAt':r[4]} for r in cur.fetchall()]
                send_json(200,{'ok':True,'items':out}); return True
    except Exception as e: send_json(503,{'ok':False,'error':f'API V9.6: {e}'}); return True

def handle_post(path,body,send_json):
    if path=='/api/orders':
        try:
            _ensure_history()
            items=body.get('items') or []
            if not isinstance(items,list) or not items: raise ValueError('A encomenda tem de conter pelo menos um artigo.')
            total=_safe_total(body.get('total'))
            clean=[]
            for item in items:
                sku=str(item.get('sku') or '').strip(); name=str(item.get('name') or item.get('productName') or '').strip()
                try: qty=int(item.get('qty',item.get('quantity',0)) or 0); price=float(str(item.get('price',0)).replace(',','.'))
                except Exception: raise ValueError('Linha de artigo inválida')
                if not sku or not name or qty<=0 or price<0: raise ValueError('Linha de artigo inválida')
                clean.append({'sku':sku,'name':name,'qty':qty,'price':round(price,2),'options':item.get('options') or {},'image':item.get('image',''),'brand':item.get('brand','')})
            email=str((body.get('customer') or {}).get('email') or '').strip().lower()
            name=str((body.get('customer') or {}).get('name') or '').strip()
            if not email or not name: raise ValueError('Nome e email do cliente são obrigatórios')
            customer=body.get('customer') or {}
            with _db() as conn, conn.cursor() as cur:
                cur.execute("SELECT id FROM customers WHERE LOWER(email)=LOWER(%s) ORDER BY id LIMIT 1",(email,)); row=cur.fetchone()
                if row:
                    cid=int(row[0]); cur.execute("UPDATE customers SET name=%s,phone=%s,updated_at=NOW() WHERE id=%s",(name,str(customer.get('phone') or ''),cid))
                else:
                    cur.execute("INSERT INTO customers(email,name,phone) VALUES(%s,%s,%s) RETURNING id",(email,name,str(customer.get('phone') or ''))); cid=int(cur.fetchone()[0])
                data={'number':'','date':None,'total':total,'status':'Recebida','items':clean,'customer':customer,'delivery':str(body.get('delivery') or ''),'payment':str(body.get('payment') or '')}
                cur.execute("INSERT INTO orders(customer_id,data) VALUES(%s,%s::jsonb) RETURNING id,created_at",(cid,json.dumps(data,ensure_ascii=False)))
                oid,created=cur.fetchone(); number=f'MM-{oid}'
                data['number']=number; data['date']=created.isoformat()
                cur.execute("UPDATE orders SET data=%s::jsonb WHERE id=%s",(json.dumps(data,ensure_ascii=False),oid))
                cur.execute("INSERT INTO mm_order_status_history(order_id,old_status,new_status,created_by) VALUES(%s,%s,%s,%s)",(oid,None,'Recebida','Loja online'))
                conn.commit()
            send_json(201,{'ok':True,'order':{'id':oid,'order_number':number,'status':'Recebida','total':total,'created_at':created,'items':clean}}); return True
        except ValueError as e:
            try: conn.rollback()
            except Exception: pass
            send_json(400,{'ok':False,'error':str(e)}); return True
        except Exception as e:
            try: conn.rollback()
            except Exception: pass
            send_json(503,{'ok':False,'error':f'API V9.6: {e}'}); return True
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
            data=row[0] or {}; _safe_total(data.get('total'))
            old=data.get('status') or 'Pendente'
            if old==new:
                send_json(200,{'ok':True,'id':oid,'status':new,'stockUpdated':False}); return True
            if old in {'Enviada','Concluída'} and new in PRE_SHIPMENT:
                raise ValueError('Não é permitido voltar uma encomenda já enviada/concluída para um estado anterior sem um processo de devolução.')
            if old=='Concluída' and new!='Cancelada': raise ValueError('Uma encomenda concluída não pode voltar atrás.')
            if new in PRE_SHIPMENT: _validate_reservation(cur,oid,data)
            if new==SHIPMENT_STATUS: _deduct_stock_for_shipment(cur,oid,data)
            data['status']=new
            cur.execute('UPDATE orders SET data=%s WHERE id=%s',(json.dumps(data,ensure_ascii=False),oid))
            cur.execute('INSERT INTO mm_order_status_history(order_id,old_status,new_status,created_by) VALUES(%s,%s,%s,%s)',(oid,old,new,user))
            conn.commit()
        send_json(200,{'ok':True,'id':oid,'status':new,'stockUpdated':new==SHIPMENT_STATUS}); return True
    except ValueError as e:
        try: conn.rollback()
        except Exception: pass
        send_json(409,{'ok':False,'error':str(e)}); return True
    except Exception as e: send_json(503,{'ok':False,'error':f'API V9.6: {e}'}); return True

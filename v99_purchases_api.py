import os, json
import psycopg

def db():
    url=os.environ.get('DATABASE_URL')
    if not url: raise RuntimeError('DATABASE_URL não configurado no Render')
    return psycopg.connect(url)

def ensure(cur):
    cur.execute("CREATE TABLE IF NOT EXISTS mm_purchases (id BIGSERIAL PRIMARY KEY,supplier_id BIGINT NOT NULL REFERENCES mm_suppliers(id),number TEXT NOT NULL UNIQUE,status TEXT NOT NULL DEFAULT 'Rascunho',order_date DATE NOT NULL DEFAULT CURRENT_DATE,expected_date DATE,received_at TIMESTAMPTZ,notes TEXT NOT NULL DEFAULT '',subtotal NUMERIC(12,2) NOT NULL DEFAULT 0,transport NUMERIC(12,2) NOT NULL DEFAULT 0,total NUMERIC(12,2) NOT NULL DEFAULT 0,items JSONB NOT NULL DEFAULT '[]'::jsonb,created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW())")
    cur.execute("CREATE TABLE IF NOT EXISTS mm_purchase_stock_receipts (id BIGSERIAL PRIMARY KEY,purchase_id BIGINT NOT NULL REFERENCES mm_purchases(id) ON DELETE CASCADE,sku TEXT NOT NULL,quantity INTEGER NOT NULL,created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),UNIQUE(purchase_id,sku))")

def money(v):
    try:return round(float(v or 0),2)
    except:return 0.0

def normalize_items(items):
    out=[]
    for x in items or []:
        sku=str(x.get('sku') or '').strip(); name=str(x.get('name') or '').strip(); qty=int(x.get('quantity') or 0); cost=money(x.get('cost'))
        if sku and qty>0: out.append({'sku':sku,'name':name,'quantity':qty,'cost':cost,'total':round(qty*cost,2)})
    return out

def handle_get(path,query,send_json):
    if path!='/api/purchases': return False
    try:
        from urllib.parse import parse_qs
        q=parse_qs(query or ''); status=(q.get('status') or [''])[0].strip(); supplier=(q.get('supplier_id') or [''])[0].strip()
        with db() as conn,conn.cursor() as cur:
            ensure(cur);conn.commit()
            cur.execute("SELECT p.id,p.number,p.supplier_id,p.status,p.order_date,p.expected_date,p.received_at,p.notes,p.subtotal,p.transport,p.total,p.items,s.id,s.name FROM mm_purchases p JOIN mm_suppliers s ON s.id=p.supplier_id ORDER BY p.order_date DESC,p.id DESC")
            items=[]
            for r in cur.fetchall(): items.append({'id':r[0],'number':r[1],'supplier_id':r[2],'status':r[3],'order_date':r[4],'expected_date':r[5],'received_at':r[6],'notes':r[7],'subtotal':float(r[8] or 0),'transport':float(r[9] or 0),'total':float(r[10] or 0),'items':r[11] or [],'supplier':{'id':r[12],'name':r[13]}})
            if status: items=[x for x in items if x['status']==status]
            if supplier:
                try: sid=int(supplier); items=[x for x in items if x['supplier_id']==sid]
                except: pass
            send_json(200,{'ok':True,'items':items,'count':len(items)});return True
    except Exception as e: send_json(503,{'ok':False,'error':f'Compras V9.9: {e}'});return True

def handle_post(path,body,send_json):
    if path!='/api/purchases': return False
    try:
        sid=int(body.get('supplier_id') or 0);items=normalize_items(body.get('items'));transport=money(body.get('transport'));subtotal=round(sum(x['total'] for x in items),2);total=round(subtotal+transport,2);status=str(body.get('status') or 'Rascunho').strip()
        if not sid: raise ValueError('Fornecedor é obrigatório')
        if not items: raise ValueError('Adiciona pelo menos um artigo à compra')
        if status not in {'Rascunho','Encomendada'}: raise ValueError('Estado inicial inválido')
        with db() as conn,conn.cursor() as cur:
            ensure(cur);cur.execute("SELECT id FROM mm_suppliers WHERE id=%s",(sid,))
            if not cur.fetchone(): raise ValueError('Fornecedor não encontrado')
            cur.execute("SELECT COALESCE(MAX(id),0)+1 FROM mm_purchases");seq=cur.fetchone()[0];number=f'CP-{int(seq):05d}'
            cur.execute("INSERT INTO mm_purchases(supplier_id,number,status,order_date,expected_date,notes,subtotal,transport,total,items) VALUES(%s,%s,%s,COALESCE(NULLIF(%s,'')::date,CURRENT_DATE),NULLIF(%s,'')::date,%s,%s,%s,%s,%s::jsonb) RETURNING id",(sid,number,status,str(body.get('order_date') or ''),str(body.get('expected_date') or ''),str(body.get('notes') or ''),subtotal,transport,total,json.dumps(items,ensure_ascii=False)))
            rid=cur.fetchone()[0];conn.commit();send_json(201,{'ok':True,'id':rid,'number':number});return True
    except ValueError as e: send_json(400,{'ok':False,'error':str(e)});return True
    except Exception as e: send_json(503,{'ok':False,'error':f'Compras V9.9: {e}'});return True

def handle_patch(path,body,send_json):
    if path!='/api/purchases': return False
    try: pid=int(body.get('id') or 0)
    except: pid=0
    if not pid: send_json(400,{'ok':False,'error':'ID da compra inválido'});return True
    try:
        with db() as conn,conn.cursor() as cur:
            ensure(cur);cur.execute("SELECT supplier_id,status,order_date,expected_date,notes,transport,items FROM mm_purchases WHERE id=%s FOR UPDATE",(pid,));row=cur.fetchone()
            if not row: send_json(404,{'ok':False,'error':'Compra não encontrada'});return True
            supplier_id,old_status,old_order,old_expected,old_notes,old_transport,old_items=row
            requested_status=str(body.get('status') or old_status).strip()
            allowed={'Rascunho','Encomendada','Recebida','Cancelada'}
            if requested_status not in allowed: send_json(400,{'ok':False,'error':'Estado inválido'});return True
            if old_status=='Recebida' and requested_status!='Recebida': send_json(409,{'ok':False,'error':'Uma compra já recebida não pode voltar atrás.'});return True
            if old_status=='Cancelada' and requested_status!='Cancelada': send_json(409,{'ok':False,'error':'Uma compra cancelada não pode voltar atrás.'});return True
            # Edits are allowed only before reception/cancellation.
            if old_status in {'Rascunho','Encomendada'} and any(k in body for k in ('supplier_id','order_date','expected_date','notes','transport','items')):
                sid=int(body.get('supplier_id') or supplier_id);items=normalize_items(body.get('items',old_items));transport=money(body.get('transport',old_transport));subtotal=round(sum(x['total'] for x in items),2);total=round(subtotal+transport,2)
                if not items: send_json(400,{'ok':False,'error':'A compra tem de ter pelo menos um artigo.'});return True
                cur.execute("SELECT id FROM mm_suppliers WHERE id=%s",(sid,))
                if not cur.fetchone(): send_json(404,{'ok':False,'error':'Fornecedor não encontrado'});return True
                cur.execute("UPDATE mm_purchases SET supplier_id=%s,order_date=COALESCE(NULLIF(%s,'')::date,CURRENT_DATE),expected_date=NULLIF(%s,'')::date,notes=%s,transport=%s,subtotal=%s,total=%s,items=%s::jsonb,status=%s,updated_at=NOW() WHERE id=%s",(sid,str(body.get('order_date') or old_order or ''),str(body.get('expected_date') or old_expected or ''),str(body.get('notes',old_notes) or ''),transport,subtotal,total,json.dumps(items,ensure_ascii=False),requested_status,pid))
                old_status=requested_status;old_items=items
            elif requested_status in {'Rascunho','Encomendada'}:
                cur.execute("UPDATE mm_purchases SET status=%s,updated_at=NOW() WHERE id=%s",(requested_status,pid))
            if requested_status=='Recebida' and old_status!='Recebida':
                for x in old_items or []:
                    sku=str(x.get('sku') or '').strip();qty=int(x.get('quantity') or 0)
                    if not sku or qty<=0: continue
                    cur.execute("SELECT 1 FROM mm_purchase_stock_receipts WHERE purchase_id=%s AND sku=%s",(pid,sku))
                    if cur.fetchone(): continue
                    cur.execute("INSERT INTO mm_product_stock(sku,stock,stock_min) VALUES(%s,0,0) ON CONFLICT(sku) DO NOTHING",(sku,))
                    cur.execute("SELECT stock FROM mm_product_stock WHERE sku=%s FOR UPDATE",(sku,));stock=int(cur.fetchone()[0] or 0);new=stock+qty
                    cur.execute("UPDATE mm_product_stock SET stock=%s,updated_at=NOW() WHERE sku=%s",(new,sku))
                    cur.execute("INSERT INTO mm_stock_movements(sku,movement_type,delta,resulting_stock,reason,notes,created_by) VALUES(%s,'Compra recebida',%s,%s,%s,%s,'MarquesMater')",(sku,qty,new,f'Entrada de compra CP-{pid}',str(body.get('notes') or old_notes or '')))
                    cur.execute("INSERT INTO mm_purchase_stock_receipts(purchase_id,sku,quantity) VALUES(%s,%s,%s) ON CONFLICT(purchase_id,sku) DO NOTHING",(pid,sku,qty))
                cur.execute("UPDATE mm_purchases SET status='Recebida',received_at=NOW(),updated_at=NOW() WHERE id=%s",(pid,));requested_status='Recebida'
            elif requested_status=='Cancelada':
                cur.execute("UPDATE mm_purchases SET status='Cancelada',updated_at=NOW() WHERE id=%s",(pid,))
            conn.commit();send_json(200,{'ok':True,'id':pid,'status':requested_status});return True
    except (ValueError,TypeError) as e: send_json(400,{'ok':False,'error':str(e)});return True
    except Exception as e: send_json(503,{'ok':False,'error':f'Compras V9.9: {e}'});return True

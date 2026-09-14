import os, json
import psycopg

def _db():
    url=os.environ.get('DATABASE_URL')
    if not url: raise RuntimeError('DATABASE_URL não configurado no Render')
    return psycopg.connect(url)

def _ensure():
    with _db() as conn, conn.cursor() as cur:
        cur.execute("CREATE TABLE IF NOT EXISTS mm_product_stock (sku TEXT PRIMARY KEY, stock INTEGER NOT NULL DEFAULT 0, stock_min INTEGER NOT NULL DEFAULT 0, updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW())")
        cur.execute("CREATE TABLE IF NOT EXISTS mm_stock_movements (id BIGSERIAL PRIMARY KEY, sku TEXT NOT NULL, movement_type TEXT NOT NULL, delta INTEGER NOT NULL, resulting_stock INTEGER NOT NULL, reason TEXT, notes TEXT, created_by TEXT NOT NULL DEFAULT 'MarquesMater', created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())")
        cur.execute("CREATE INDEX IF NOT EXISTS mm_stock_movements_sku_idx ON mm_stock_movements(sku,created_at DESC)")
        cur.execute("ALTER TABLE catalog_products ADD COLUMN IF NOT EXISTS barcode TEXT")
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS catalog_products_barcode_uq ON catalog_products(barcode) WHERE barcode IS NOT NULL AND BTRIM(barcode)<>''")

def _reserved(cur,sku):
    cur.execute("SELECT COALESCE(SUM(COALESCE((x->>'qty')::int,COALESCE((x->>'quantity')::int,0))),0) FROM orders o CROSS JOIN LATERAL jsonb_array_elements(CASE WHEN jsonb_typeof(o.data->'items')='array' THEN o.data->'items' ELSE '[]'::jsonb END) x WHERE x->>'sku'=%s AND LOWER(COALESCE(o.data->>'status','')) IN ('recebida','pendente','pending','em processamento','processing','em preparação','pago')",(sku,))
    return int(cur.fetchone()[0] or 0)

def handle_get(path,query,send_json):
    if path not in ('/api/stock','/api/stock/movements'): return False
    try:
        _ensure()
        with _db() as conn, conn.cursor() as cur:
            if path=='/api/stock':
                cur.execute("SELECT s.sku,s.stock,s.stock_min,s.updated_at,COALESCE(cp.barcode,'') FROM mm_product_stock s LEFT JOIN catalog_products cp ON cp.sku=s.sku ORDER BY s.sku")
                out=[]
                for sku,physical,minimum,updated,barcode in cur.fetchall():
                    physical=int(physical or 0); reserved=_reserved(cur,sku); available=max(0,physical-reserved)
                    out.append({'sku':sku,'stock':physical,'reserved':reserved,'available':available,'stockMin':int(minimum or 0),'barcode':barcode or '','updatedAt':updated})
                send_json(200,{'ok':True,'items':out}); return True
            import urllib.parse
            q=urllib.parse.parse_qs(query or ''); sku=(q.get('sku') or [''])[0].strip()
            if sku: cur.execute("SELECT id,sku,movement_type,delta,resulting_stock,reason,notes,created_by,created_at FROM mm_stock_movements WHERE sku=%s ORDER BY created_at DESC LIMIT 500",(sku,))
            else: cur.execute("SELECT id,sku,movement_type,delta,resulting_stock,reason,notes,created_by,created_at FROM mm_stock_movements ORDER BY created_at DESC LIMIT 500")
            send_json(200,{'ok':True,'items':[{'id':r[0],'sku':r[1],'type':r[2],'delta':r[3],'stock':r[4],'reason':r[5] or '','notes':r[6] or '','user':r[7],'createdAt':r[8]} for r in cur.fetchall()]}); return True
    except Exception as e:
        send_json(503,{'ok':False,'error':f'Stock V9.6: {e}'}); return True

def handle_post(path,body,send_json):
    if path!='/api/stock/adjust': return False
    try:
        _ensure(); sku=str(body.get('sku') or '').strip(); typ=str(body.get('type') or 'adjust').strip(); qty=int(body.get('quantity') or 0); minimum=int(body.get('stockMin') or 0)
        if not sku: raise ValueError('SKU obrigatório')
        if qty<0 or minimum<0: raise ValueError('Quantidade inválida')
        with _db() as conn, conn.cursor() as cur:
            cur.execute("INSERT INTO mm_product_stock(sku,stock,stock_min) VALUES(%s,0,%s) ON CONFLICT(sku) DO NOTHING",(sku,minimum))
            cur.execute("SELECT stock,stock_min FROM mm_product_stock WHERE sku=%s FOR UPDATE",(sku,)); old,oldmin=map(int,cur.fetchone()); reserved=_reserved(cur,sku)
            if typ in ('in','entry'): delta=qty
            elif typ in ('return','Devolução'): delta=qty
            elif typ in ('out','exit'): delta=-qty
            elif typ in ('adjust','Ajuste para quantidade'): delta=qty-old
            else: raise ValueError('Tipo de movimento inválido')
            new=old+delta
            if new<reserved: raise ValueError(f'O stock físico não pode ficar abaixo do stock reservado ({reserved}).')
            if new<0: raise ValueError('O stock não pode ficar negativo')
            newmin=minimum if 'stockMin' in body else oldmin
            cur.execute("UPDATE mm_product_stock SET stock=%s,stock_min=%s,updated_at=NOW() WHERE sku=%s",(new,newmin,sku))
            cur.execute("INSERT INTO mm_stock_movements(sku,movement_type,delta,resulting_stock,reason,notes,created_by) VALUES(%s,%s,%s,%s,%s,%s,%s)",(sku,typ,delta,new,str(body.get('reason') or ''),str(body.get('notes') or ''),str(body.get('user') or 'MarquesMater')))
            conn.commit()
        send_json(200,{'ok':True,'sku':sku,'stock':new,'reserved':reserved,'available':max(0,new-reserved),'delta':delta}); return True
    except ValueError as e:
        send_json(409,{'ok':False,'error':str(e)}); return True
    except Exception as e:
        send_json(503,{'ok':False,'error':f'Stock V9.6: {e}'}); return True

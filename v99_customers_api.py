import os, json, re
import psycopg


def _db():
    url=os.environ.get('DATABASE_URL')
    if not url: raise RuntimeError('DATABASE_URL não configurado no Render')
    return psycopg.connect(url)


def _money(v):
    try: return float(v or 0)
    except Exception: return 0


def _customer_row(cur, row):
    cols=[d.name for d in cur.description]
    d=dict(zip(cols,row))
    return d


def _orders_for(cur, cid, email):
    cur.execute("""SELECT id,created_at,data FROM orders
                   WHERE customer_id=%s OR LOWER(COALESCE(data->'customer'->>'email',''))=LOWER(%s)
                   ORDER BY created_at DESC,id DESC""",(cid,email or ''))
    out=[]
    for oid,created,data in cur.fetchall():
        data=data or {}
        total=_money(data.get('total'))
        if total<=0: continue
        out.append({'id':oid,'created_at':created,'number':data.get('number') or f'MM-{oid}','status':data.get('status') or 'Pendente','total':total,'delivery':data.get('delivery',''),'payment':data.get('payment',''),'items':data.get('items') or [],'address':data.get('address') or {}})
    return out


def handle_get(path, query, send_json):
    try:
        from urllib.parse import parse_qs
        q=parse_qs(query or '')
        with _db() as conn, conn.cursor() as cur:
            cur.execute('SELECT * FROM customers ORDER BY id DESC')
            rows=[_customer_row(cur,r) for r in cur.fetchall()]
            items=[]
            for d in rows:
                cid=d.get('id'); email=str(d.get('email') or '').strip()
                orders=_orders_for(cur,cid,email)
                items.append({'id':cid,'name':d.get('name') or '','email':email,'phone':d.get('phone') or '','created_at':d.get('created_at'),'updated_at':d.get('updated_at'),'orders_count':len(orders),'total_spent':round(sum(x['total'] for x in orders),2),'last_order':orders[0]['created_at'] if orders else None})
            search=str((q.get('search') or [''])[0]).strip().lower()
            if search: items=[x for x in items if search in ' '.join(str(x.get(k) or '') for k in ('name','email','phone')).lower()]
            detail=(q.get('id') or [''])[0]
            if detail:
                try: did=int(detail)
                except: did=-1
                found=next((x for x in rows if x.get('id')==did),None)
                if not found: send_json(404,{'ok':False,'error':'Cliente não encontrado'}); return True
                email=str(found.get('email') or '').strip(); orders=_orders_for(cur,found.get('id'),email)
                send_json(200,{'ok':True,'item':{'id':found.get('id'),'name':found.get('name') or '','email':email,'phone':found.get('phone') or '','created_at':found.get('created_at'),'updated_at':found.get('updated_at'),'orders_count':len(orders),'total_spent':round(sum(x['total'] for x in orders),2),'orders':orders}}); return True
            send_json(200,{'ok':True,'items':items,'count':len(items)}); return True
    except Exception as e:
        send_json(503,{'ok':False,'error':f'API V9.9: {e}'}); return True


def handle_post(path, body, send_json):
    if path!='/api/customers': return False
    name=str(body.get('name') or '').strip(); email=str(body.get('email') or '').strip().lower(); phone=str(body.get('phone') or '').strip()
    if not name or not email or not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$',email):
        send_json(400,{'ok':False,'error':'Nome e email válidos são obrigatórios'}); return True
    try:
        with _db() as conn, conn.cursor() as cur:
            cur.execute('SELECT id FROM customers WHERE LOWER(email)=LOWER(%s) LIMIT 1',(email,)); old=cur.fetchone()
            if old:
                send_json(409,{'ok':False,'error':'Já existe um cliente com este email','id':old[0]}); return True
            cur.execute('INSERT INTO customers (name,email,phone) VALUES (%s,%s,%s) RETURNING id,name,email,phone', (name,email,phone))
            r=cur.fetchone(); conn.commit(); send_json(201,{'ok':True,'item':{'id':r[0],'name':r[1],'email':r[2],'phone':r[3] or '','orders_count':0,'total_spent':0,'last_order':None}}); return True
    except Exception as e:
        send_json(503,{'ok':False,'error':f'API V9.9: {e}'}); return True

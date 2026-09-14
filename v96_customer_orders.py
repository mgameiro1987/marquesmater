import os, json
import psycopg

def _db():
    url=os.environ.get('DATABASE_URL')
    if not url: raise RuntimeError('DATABASE_URL não configurado no Render')
    return psycopg.connect(url)

def handle_get(email, send_json):
    email=str(email or '').strip().lower()
    if not email:
        send_json(400,{'ok':False,'error':'Email do cliente em falta'}); return True
    try:
        with _db() as conn, conn.cursor() as cur:
            cur.execute("""SELECT o.id,o.created_at,o.data,c.name,c.email,c.phone
                         FROM orders o
                         LEFT JOIN customers c ON c.id=o.customer_id
                         WHERE COALESCE(NULLIF(o.data->>'total','')::numeric,0)>0
                           AND (LOWER(COALESCE(c.email,''))=LOWER(%s)
                                OR LOWER(COALESCE(o.data->'customer'->>'email',''))=LOWER(%s))
                         ORDER BY o.created_at DESC,o.id DESC""",(email,email))
            out=[]
            for r in cur.fetchall():
                d=r[2] or {}; cust=d.get('customer') or {}
                out.append({'id':r[0],'created_at':r[1],'order_number':d.get('number') or f'MM-{r[0]}','status':d.get('status') or 'Pendente','total':d.get('total') or 0,'customer':cust,'customer_name':r[3] or cust.get('name',''),'customer_email':r[4] or cust.get('email',''),'customer_phone':r[5] or cust.get('phone',''),'delivery':d.get('delivery',''),'payment':d.get('payment',''),'items':d.get('items') or []})
            send_json(200,{'ok':True,'items':out,'count':len(out)}); return True
    except Exception as e:
        send_json(503,{'ok':False,'error':f'API V9.6: {e}'}); return True

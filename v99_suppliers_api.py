import os, re
import psycopg

def db():
    url=os.environ.get('DATABASE_URL')
    if not url: raise RuntimeError('DATABASE_URL não configurado no Render')
    return psycopg.connect(url)

def clean(v): return str(v or '').strip()

def ensure(cur):
    cur.execute("CREATE TABLE IF NOT EXISTS mm_suppliers (id BIGSERIAL PRIMARY KEY,name TEXT NOT NULL,email TEXT NOT NULL DEFAULT '',phone TEXT NOT NULL DEFAULT '',vat TEXT NOT NULL DEFAULT '',address TEXT NOT NULL DEFAULT '',payment_terms TEXT NOT NULL DEFAULT '',notes TEXT NOT NULL DEFAULT '',active BOOLEAN NOT NULL DEFAULT TRUE,created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW())")
    cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS mm_suppliers_vat_uq ON mm_suppliers(LOWER(vat)) WHERE BTRIM(vat)<>''")

def handle_get(path,query,send_json):
    if path!='/api/suppliers': return False
    try:
        from urllib.parse import parse_qs
        q=parse_qs(query or ''); search=clean((q.get('search') or [''])[0]).lower()
        with db() as conn,conn.cursor() as cur:
            ensure(cur); conn.commit()
            cur.execute("SELECT id,name,email,phone,vat,address,payment_terms,notes,active,created_at,updated_at FROM mm_suppliers ORDER BY name")
            items=[{'id':r[0],'name':r[1],'email':r[2],'phone':r[3],'vat':r[4],'address':r[5],'payment_terms':r[6],'notes':r[7],'active':r[8],'created_at':r[9],'updated_at':r[10]} for r in cur.fetchall()]
            if search: items=[x for x in items if search in ' '.join(str(x.get(k) or '') for k in ('name','email','phone','vat')).lower()]
            send_json(200,{'ok':True,'items':items,'count':len(items)}); return True
    except Exception as e: send_json(503,{'ok':False,'error':f'Fornecedores V9.9: {e}'}); return True

def handle_post(path,body,send_json):
    if path!='/api/suppliers': return False
    name=clean(body.get('name')); email=clean(body.get('email')).lower(); phone=clean(body.get('phone')); vat=clean(body.get('vat')); address=clean(body.get('address')); terms=clean(body.get('payment_terms')); notes=clean(body.get('notes')); active=bool(body.get('active',True))
    if not name: send_json(400,{'ok':False,'error':'Nome do fornecedor é obrigatório'}); return True
    if email and not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$',email): send_json(400,{'ok':False,'error':'Email inválido'}); return True
    try:
        with db() as conn,conn.cursor() as cur:
            ensure(cur)
            cur.execute("INSERT INTO mm_suppliers(name,email,phone,vat,address,payment_terms,notes,active) VALUES(%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id",(name,email,phone,vat,address,terms,notes,active))
            rid=cur.fetchone()[0];conn.commit();send_json(201,{'ok':True,'id':rid});return True
    except psycopg.errors.UniqueViolation: send_json(409,{'ok':False,'error':'Já existe um fornecedor com este NIF.'});return True
    except Exception as e: send_json(503,{'ok':False,'error':f'Fornecedores V9.9: {e}'});return True

def handle_patch(path,body,send_json):
    if path!='/api/suppliers': return False
    try: rid=int(body.get('id') or 0)
    except: rid=0
    if not rid: send_json(400,{'ok':False,'error':'Fornecedor inválido'});return True
    name=clean(body.get('name'));email=clean(body.get('email')).lower();phone=clean(body.get('phone'));vat=clean(body.get('vat'));address=clean(body.get('address'));terms=clean(body.get('payment_terms'));notes=clean(body.get('notes'));active=bool(body.get('active',True))
    if not name: send_json(400,{'ok':False,'error':'Nome do fornecedor é obrigatório'});return True
    try:
        with db() as conn,conn.cursor() as cur:
            ensure(cur);cur.execute("UPDATE mm_suppliers SET name=%s,email=%s,phone=%s,vat=%s,address=%s,payment_terms=%s,notes=%s,active=%s,updated_at=NOW() WHERE id=%s",(name,email,phone,vat,address,terms,notes,active,rid))
            if cur.rowcount!=1: send_json(404,{'ok':False,'error':'Fornecedor não encontrado'});return True
            conn.commit();send_json(200,{'ok':True});return True
    except psycopg.errors.UniqueViolation: send_json(409,{'ok':False,'error':'Já existe um fornecedor com este NIF.'});return True
    except Exception as e: send_json(503,{'ok':False,'error':f'Fornecedores V9.9: {e}'});return True

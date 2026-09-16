import json
import psycopg

def _db():
    import os
    url=os.environ.get('DATABASE_URL')
    if not url: raise RuntimeError('DATABASE_URL não configurado no Render')
    return psycopg.connect(url)
SCHEMA='''CREATE TABLE IF NOT EXISTS mm_marketing_coupons (id BIGSERIAL PRIMARY KEY, code TEXT UNIQUE NOT NULL, name TEXT NOT NULL, discount_type TEXT NOT NULL, discount_value NUMERIC(12,2) NOT NULL, min_order NUMERIC(12,2) NOT NULL DEFAULT 0, max_uses INTEGER, used_count INTEGER NOT NULL DEFAULT 0, starts_at TIMESTAMPTZ, ends_at TIMESTAMPTZ, active BOOLEAN NOT NULL DEFAULT TRUE, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()); CREATE TABLE IF NOT EXISTS mm_marketing_promotions (id BIGSERIAL PRIMARY KEY, name TEXT NOT NULL, discount_type TEXT NOT NULL, discount_value NUMERIC(12,2) NOT NULL, scope TEXT NOT NULL DEFAULT 'all', scope_value TEXT, starts_at TIMESTAMPTZ, ends_at TIMESTAMPTZ, active BOOLEAN NOT NULL DEFAULT TRUE, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW());'''
def ensure():
    with _db() as c:
        with c.cursor() as x:
            for s in SCHEMA.split(';'):
                if s.strip(): x.execute(s)
        c.commit()
def get(query,send_json):
    ensure()
    with _db() as c, c.cursor() as x:
        x.execute("SELECT id,code,name,discount_type,discount_value,min_order,max_uses,used_count,starts_at,ends_at,active FROM mm_marketing_coupons ORDER BY id DESC")
        coupons=[{'id':r[0],'code':r[1],'name':r[2],'discountType':r[3],'discountValue':float(r[4]),'minOrder':float(r[5]),'maxUses':r[6],'usedCount':r[7],'startsAt':r[8],'endsAt':r[9],'active':r[10]} for r in x.fetchall()]
        x.execute("SELECT id,name,discount_type,discount_value,scope,scope_value,starts_at,ends_at,active FROM mm_marketing_promotions ORDER BY id DESC")
        promotions=[{'id':r[0],'name':r[1],'discountType':r[2],'discountValue':float(r[3]),'scope':r[4],'scopeValue':r[5],'startsAt':r[6],'endsAt':r[7],'active':r[8]} for r in x.fetchall()]
    send_json(200,{'ok':True,'coupons':coupons,'promotions':promotions}); return True
def post(body,send_json):
    ensure(); kind=str(body.get('kind') or 'coupon')
    with _db() as c, c.cursor() as x:
        if kind=='coupon':
            code=str(body.get('code') or '').strip().upper(); name=str(body.get('name') or code).strip(); typ=str(body.get('discountType') or 'percent')
            if not code or typ not in ('percent','fixed'): raise ValueError('Dados do cupão inválidos')
            value=float(body.get('discountValue') or 0); minimum=max(0,float(body.get('minOrder') or 0)); maxuses=body.get('maxUses'); maxuses=int(maxuses) if maxuses not in (None,'') else None
            if value<=0 or (typ=='percent' and value>100) or (maxuses is not None and maxuses<1): raise ValueError('Desconto ou limite inválido')
            x.execute("INSERT INTO mm_marketing_coupons(code,name,discount_type,discount_value,min_order,max_uses,starts_at,ends_at,active) VALUES(%s,%s,%s,%s,%s,%s,NULLIF(%s,'')::timestamptz,NULLIF(%s,'')::timestamptz,%s)",(code,name,typ,value,minimum,maxuses,str(body.get('startsAt') or ''),str(body.get('endsAt') or ''),bool(body.get('active',True))))
        else:
            name=str(body.get('name') or '').strip(); typ=str(body.get('discountType') or 'percent'); value=float(body.get('discountValue') or 0)
            if not name or typ not in ('percent','fixed') or value<=0 or (typ=='percent' and value>100): raise ValueError('Dados da promoção inválidos')
            x.execute("INSERT INTO mm_marketing_promotions(name,discount_type,discount_value,scope,scope_value,starts_at,ends_at,active) VALUES(%s,%s,%s,%s,%s,NULLIF(%s,'')::timestamptz,NULLIF(%s,'')::timestamptz,%s)",(name,typ,value,str(body.get('scope') or 'all'),str(body.get('scopeValue') or ''),str(body.get('startsAt') or ''),str(body.get('endsAt') or ''),bool(body.get('active',True))))
        c.commit()
    send_json(201,{'ok':True}); return True
def patch(body,send_json):
    ensure(); kind=str(body.get('kind') or 'coupon'); ident=int(body.get('id') or 0); active=bool(body.get('active')); table='mm_marketing_coupons' if kind=='coupon' else 'mm_marketing_promotions'
    with _db() as c, c.cursor() as x:
        x.execute(f'UPDATE {table} SET active=%s WHERE id=%s',(active,ident)); c.commit()
    send_json(200,{'ok':True}); return True

import os
import base64
import re
import psycopg
from datetime import datetime, timezone
from urllib.parse import parse_qs

def _db():
    url=os.environ.get('DATABASE_URL')
    if not url: raise RuntimeError('DATABASE_URL não configurado no Render')
    return psycopg.connect(url)
SCHEMA='''CREATE TABLE IF NOT EXISTS mm_marketing_coupons (id BIGSERIAL PRIMARY KEY, code TEXT UNIQUE NOT NULL, name TEXT NOT NULL, discount_type TEXT NOT NULL, discount_value NUMERIC(12,2) NOT NULL, min_order NUMERIC(12,2) NOT NULL DEFAULT 0, max_uses INTEGER, used_count INTEGER NOT NULL DEFAULT 0, starts_at TIMESTAMPTZ, ends_at TIMESTAMPTZ, active BOOLEAN NOT NULL DEFAULT TRUE, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()); CREATE TABLE IF NOT EXISTS mm_marketing_promotions (id BIGSERIAL PRIMARY KEY, name TEXT NOT NULL, discount_type TEXT NOT NULL, discount_value NUMERIC(12,2) NOT NULL, scope TEXT NOT NULL DEFAULT 'all', scope_value TEXT, starts_at TIMESTAMPTZ, ends_at TIMESTAMPTZ, active BOOLEAN NOT NULL DEFAULT TRUE, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()); CREATE TABLE IF NOT EXISTS mm_heroes (id BIGSERIAL PRIMARY KEY, title TEXT NOT NULL, subtitle TEXT, description TEXT, button_text TEXT, button_url TEXT, image_desktop TEXT NOT NULL, image_mobile TEXT, position INTEGER NOT NULL DEFAULT 1, active BOOLEAN NOT NULL DEFAULT TRUE, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()); CREATE TABLE IF NOT EXISTS mm_hero_assets (id BIGSERIAL PRIMARY KEY, filename TEXT NOT NULL, mime_type TEXT NOT NULL, data BYTEA NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW());'''
def ensure():
    with _db() as c:
        with c.cursor() as x:
            for s in SCHEMA.split(';'):
                if s.strip(): x.execute(s)
        c.commit()
def _now(): return datetime.now(timezone.utc)
def _active_window(starts_at,ends_at,now=None):
    now=now or _now(); return not (starts_at and starts_at>now) and not (ends_at and ends_at<now)
def _discount(amount,typ,value):
    amount=max(0.0,float(amount or 0)); value=float(value or 0); return min(amount,round(amount*value/100,2)) if typ=='percent' else min(amount,round(value,2))
def _promotion_matches(promo,item):
    scope=str(promo[4] or 'all').lower(); value=str(promo[5] or '').strip().lower()
    if scope=='all': return True
    if scope=='product': return value and value==str(item.get('sku') or '').strip().lower()
    if scope=='brand': return value and value==str(item.get('brand') or '').strip().lower()
    if scope=='category': return value in [str(item.get(k) or '').strip().lower() for k in ('category','categoryName','category_name')]
    return False
def calculate(cur,code,subtotal,items):
    subtotal=round(max(0.0,float(subtotal or 0)),2); coupon=None; coupon_discount=promotion_discount=0.0; applied_promotions=[]; code=str(code or '').strip().upper(); now=_now()
    if code:
        cur.execute("SELECT id,code,name,discount_type,discount_value,min_order,max_uses,used_count,starts_at,ends_at,active FROM mm_marketing_coupons WHERE UPPER(code)=UPPER(%s) LIMIT 1 FOR UPDATE",(code,)); coupon=cur.fetchone()
        if not coupon: raise ValueError('Cupão inválido ou inexistente.')
        if not bool(coupon[10]): raise ValueError('Este cupão está desativado.')
        if not _active_window(coupon[8],coupon[9],now): raise ValueError('Este cupão não está disponível neste momento.')
        if coupon[6] is not None and int(coupon[7] or 0)>=int(coupon[6]): raise ValueError('Este cupão já atingiu o limite de utilizações.')
        if subtotal<float(coupon[5] or 0): raise ValueError(f'Este cupão exige um mínimo de {float(coupon[5]):.2f} €.')
        coupon_discount=_discount(subtotal,coupon[3],coupon[4])
    cur.execute("SELECT id,name,discount_type,discount_value,scope,scope_value,starts_at,ends_at,active FROM mm_marketing_promotions WHERE active=TRUE ORDER BY id DESC")
    for p in cur.fetchall():
        if not _active_window(p[6],p[7],now): continue
        eligible=[i for i in (items or []) if _promotion_matches(p,i)]
        if not eligible: continue
        base=sum(float(i.get('price') or 0)*max(1,int(i.get('qty',i.get('quantity',1)) or 1)) for i in eligible); d=_discount(base,p[2],p[3])
        if d>0: promotion_discount=round(promotion_discount+d,2); applied_promotions.append({'id':p[0],'name':p[1],'discount':d})
    promotion_discount=min(subtotal,promotion_discount); coupon_base=max(0.0,subtotal-promotion_discount); coupon_discount=min(coupon_discount,coupon_base) if coupon else 0; total_discount=min(subtotal,round(promotion_discount+coupon_discount,2))
    return {'coupon':code or None,'couponDiscount':round(coupon_discount,2),'promotionDiscount':round(promotion_discount,2),'discount':round(total_discount,2),'subtotal':subtotal,'totalAfterDiscount':round(max(0.0,subtotal-total_discount),2),'promotions':applied_promotions}
def consume_coupon(cur,code):
    if code: cur.execute("UPDATE mm_marketing_coupons SET used_count=used_count+1 WHERE UPPER(code)=UPPER(%s)",(str(code).strip().upper(),))
def _hero(row):
    return {'id':row[0],'title':row[1],'subtitle':row[2] or '','description':row[3] or '','buttonText':row[4] or '','buttonUrl':row[5] or '','imageDesktop':row[6],'imageMobile':row[7] or row[6],'position':int(row[8] or 1),'active':bool(row[9])}
def _heroes_get(send_json):
    with _db() as c,c.cursor() as x:
        x.execute('SELECT id,title,subtitle,description,button_text,button_url,image_desktop,image_mobile,position,active FROM mm_heroes ORDER BY position ASC,id ASC')
        allh=[_hero(r) for r in x.fetchall()]
    send_json(200,{'ok':True,'heroes':allh}); return True
def _extract_multipart(handler):
    length=int(handler.headers.get('Content-Length','0') or 0)
    if length<=0 or length>8*1024*1024: raise ValueError('Imagem inválida ou superior a 8 MB.')
    raw=handler.rfile.read(length)
    ctype=handler.headers.get('Content-Type','')
    m=re.search(r'boundary=(?:"([^"]+)"|([^;]+))',ctype)
    if not m: raise ValueError('Upload inválido: boundary em falta')
    boundary=(m.group(1) or m.group(2)).encode()
    for part in raw.split(b'--'+boundary):
        if b'filename=' not in part: continue
        head,sep,body=part.partition(b'\r\n\r\n')
        if not sep: continue
        hm=re.search(br'filename="([^"]*)"',head)
        filename=(hm.group(1).decode('utf-8','replace') if hm else 'hero.jpg')
        return filename,body.rstrip(b'\r\n-')
    raise ValueError('Nenhuma imagem encontrada.')

def _hero_image_dimensions(data,mime):
    # Leitura leve das dimensões sem depender de Pillow.
    if mime=='image/png' and len(data)>=24 and data[:8]==b'\\x89PNG\\r\\n\\x1a\\n':
        import struct
        return struct.unpack('>II',data[16:24])
    if mime in ('image/jpeg',):
        i=2
        while i+9<=len(data):
            if data[i]!=0xFF: i+=1; continue
            while i<len(data) and data[i]==0xFF: i+=1
            if i>=len(data): break
            marker=data[i]; i+=1
            if marker in (0xD8,0xD9): continue
            if i+2>len(data): break
            ln=int.from_bytes(data[i:i+2],'big')
            if ln<2 or i+ln>len(data): break
            if marker in list(range(0xC0,0xC4))+list(range(0xC5,0xC8))+list(range(0xC9,0xCC))+list(range(0xCD,0xD0)):
                if i+7<=len(data): return int.from_bytes(data[i+5:i+7],'big'),int.from_bytes(data[i+3:i+5],'big')
            i+=ln
    if mime=='image/webp' and data[:4]==b'RIFF' and data[8:12]==b'WEBP':
        if data[12:16]==b'VP8X' and len(data)>=30:
            w=1+int.from_bytes(data[24:27],'little'); h=1+int.from_bytes(data[27:30],'little'); return w,h
        if data[12:16]==b'VP8L' and len(data)>=25:
            b=data[21:25]; w=1+((b[1]&0x3f)<<8|b[0]); h=1+((b[3]&0xf)<<10|b[2]<<2|((b[1]&0xc0)>>6)); return w,h
    return None,None

def hero_upload(handler,send_json):
    filename,data=_extract_multipart(handler)
    ext=os.path.splitext(filename.lower())[1]
    mime={'.jpg':'image/jpeg','.jpeg':'image/jpeg','.png':'image/png','.webp':'image/webp'}.get(ext)
    if not mime: raise ValueError('Formato de imagem não suportado. Use JPG, PNG ou WebP.')
    if not data: raise ValueError('A imagem está vazia.')
    w,h=_hero_image_dimensions(data,mime)
    slot=(parse_qs(getattr(handler,'path','').split('?',1)[1] if '?' in getattr(handler,'path','') else '').get('slot') or [''])[0].lower()
    # O frontend envia o slot no multipart; quando ausente, aplicar a regra Desktop.
    if slot not in ('desktop','mobile'): slot='desktop'
    if slot=='desktop':
        min_w,min_h,target_ratio=1600,467,1920/560
        label='Desktop'
    else:
        min_w,min_h,target_ratio=900,508,1080/610
        label='Mobile'
    if not w or not h:
        raise ValueError('Não foi possível ler as dimensões da imagem. Escolhe um JPG, PNG ou WebP válido.')
    ratio=w/h
    if w<min_w or h<min_h:
        raise ValueError(f'Imagem {label} demasiado pequena: {w}×{h}px. Usa pelo menos {min_w}×{min_h}px (recomendado: '+('1920×560' if slot=='desktop' else '1080×610')+').')
    if abs(ratio-target_ratio)>0.12:
        raise ValueError(f'Proporção da imagem {label} incorreta: {w}×{h}px. Recomendado: '+('1920×560 px (24:7).' if slot=='desktop' else '1080×610 px (aprox. 16:9).'))
    with _db() as c,c.cursor() as x:
        x.execute('INSERT INTO mm_hero_assets(filename,mime_type,data) VALUES(%s,%s,%s) RETURNING id',(filename,mime,psycopg.Binary(data)))
        ident=x.fetchone()[0]; c.commit()
    send_json(200,{'ok':True,'imageUrl':f'/api/marketing/hero-image?id={ident}','filename':filename,'bytes':len(data),'width':w,'height':h,'slot':slot})
    return True

def hero_image(query,send_binary):
    q=parse_qs(query or '')
    try: ident=int((q.get('id') or ['0'])[0])
    except Exception: ident=0
    if ident<=0: return False
    with _db() as c,c.cursor() as x:
        x.execute('SELECT mime_type,data FROM mm_hero_assets WHERE id=%s LIMIT 1',(ident,))
        row=x.fetchone()
    if not row: return False
    mime,data=row
    send_binary(200,mime,bytes(data),max_age=31536000)
    return True

def _hero_write(body,send_json):
    action=str(body.get('action') or 'create'); title=str(body.get('title') or '').strip(); image=str(body.get('imageDesktop') or '').strip()
    if not title or not image: raise ValueError('Título e imagem Desktop são obrigatórios.')
    subtitle=str(body.get('subtitle') or '').strip(); description=str(body.get('description') or '').strip(); bt=str(body.get('buttonText') or '').strip(); bu=str(body.get('buttonUrl') or '').strip(); mobile=str(body.get('imageMobile') or image).strip(); pos=max(1,int(body.get('position') or 1)); active=bool(body.get('active',True)); ident=int(body.get('id') or 0)
    with _db() as c,c.cursor() as x:
        if action=='update' and ident:
            x.execute('UPDATE mm_heroes SET title=%s,subtitle=%s,description=%s,button_text=%s,button_url=%s,image_desktop=%s,image_mobile=%s,position=%s,active=%s,updated_at=NOW() WHERE id=%s',(title,subtitle,description,bt,bu,image,mobile,pos,active,ident))
            if x.rowcount==0: raise ValueError('Hero não encontrado.')
        else:
            x.execute('INSERT INTO mm_heroes(title,subtitle,description,button_text,button_url,image_desktop,image_mobile,position,active) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)',(title,subtitle,description,bt,bu,image,mobile,pos,active))
        c.commit()
    send_json(200,{'ok':True}); return True
def _hero_delete(body,send_json):
    ident=int(body.get('id') or 0)
    with _db() as c,c.cursor() as x: x.execute('DELETE FROM mm_heroes WHERE id=%s',(ident,)); c.commit()
    send_json(200,{'ok':True}); return True
def get(query,send_json):
    ensure()
    if 'resource=heroes' in query or parse_qs(query).get('resource')==['heroes']: return _heroes_get(send_json)
    with _db() as c,c.cursor() as x:
        x.execute("SELECT id,code,name,discount_type,discount_value,min_order,max_uses,used_count,starts_at,ends_at,active FROM mm_marketing_coupons ORDER BY id DESC")
        coupons=[{'id':r[0],'code':r[1],'name':r[2],'discountType':r[3],'discountValue':float(r[4]),'minOrder':float(r[5]),'maxUses':r[6],'usedCount':r[7],'startsAt':r[8],'endsAt':r[9],'active':r[10]} for r in x.fetchall()]
        x.execute("SELECT id,name,discount_type,discount_value,scope,scope_value,starts_at,ends_at,active FROM mm_marketing_promotions ORDER BY id DESC")
        promotions=[{'id':r[0],'name':r[1],'discountType':r[2],'discountValue':float(r[3]),'scope':r[4],'scopeValue':r[5],'startsAt':r[6],'endsAt':r[7],'active':r[8]} for r in x.fetchall()]
    send_json(200,{'ok':True,'coupons':coupons,'promotions':promotions}); return True
def validate(body,send_json):
    ensure(); items=body.get('items') or []
    try: subtotal=round(float(body.get('subtotal') or 0),2)
    except Exception: raise ValueError('Subtotal inválido.')
    if subtotal<=0: raise ValueError('O subtotal tem de ser superior a 0 €.')
    with _db() as c,c.cursor() as x: result=calculate(x,body.get('code'),subtotal,items)
    send_json(200,{'ok':True,'result':result}); return True
def post(body,send_json):
    ensure(); kind=str(body.get('kind') or 'coupon')
    if kind=='hero': return _hero_write(body,send_json)
    with _db() as c,c.cursor() as x:
        if kind=='coupon':
            code=str(body.get('code') or '').strip().upper(); name=str(body.get('name') or code).strip(); typ=str(body.get('discountType') or 'percent'); value=float(body.get('discountValue') or 0); minimum=max(0,float(body.get('minOrder') or 0)); maxuses=body.get('maxUses'); maxuses=int(maxuses) if maxuses not in (None,'') else None
            if not code or typ not in ('percent','fixed') or value<=0 or (typ=='percent' and value>100) or (maxuses is not None and maxuses<1): raise ValueError('Dados do cupão inválidos')
            if typ=='percent' and value==100:
                key=str(body.get('authorizationKey') or ''); secret=os.environ.get('MM_100_COUPON_PASSWORD','')
                if not secret or key!=secret: raise ValueError('Cupão de 100% requer a palavra-passe especial de autorização.')
            x.execute("INSERT INTO mm_marketing_coupons(code,name,discount_type,discount_value,min_order,max_uses,starts_at,ends_at,active) VALUES(%s,%s,%s,%s,%s,%s,NULLIF(%s,'')::timestamptz,NULLIF(%s,'')::timestamptz,%s)",(code,name,typ,value,minimum,maxuses,str(body.get('startsAt') or ''),str(body.get('endsAt') or ''),bool(body.get('active',True))))
        else:
            name=str(body.get('name') or '').strip(); typ=str(body.get('discountType') or 'percent'); value=float(body.get('discountValue') or 0)
            if not name or typ not in ('percent','fixed') or value<=0 or (typ=='percent' and value>100): raise ValueError('Dados da promoção inválidos')
            scope=str(body.get('scope') or 'all')
            if scope not in ('all','category','brand','product'): raise ValueError('Âmbito de promoção inválido')
            x.execute("INSERT INTO mm_marketing_promotions(name,discount_type,discount_value,scope,scope_value,starts_at,ends_at,active) VALUES(%s,%s,%s,%s,%s,NULLIF(%s,'')::timestamptz,NULLIF(%s,'')::timestamptz,%s)",(name,typ,value,scope,str(body.get('scopeValue') or ''),str(body.get('startsAt') or ''),str(body.get('endsAt') or ''),bool(body.get('active',True))))
        c.commit()
    send_json(201,{'ok':True}); return True
def patch(body,send_json):
    ensure(); kind=str(body.get('kind') or 'coupon'); ident=int(body.get('id') or 0); active=bool(body.get('active')); table='mm_marketing_coupons' if kind=='coupon' else 'mm_marketing_promotions'
    if kind=='hero':
        with _db() as c,c.cursor() as x:
            x.execute('UPDATE mm_heroes SET active=%s,updated_at=NOW() WHERE id=%s',(active,ident)); c.commit()
        send_json(200,{'ok':True}); return True
    with _db() as c,c.cursor() as x: x.execute(f'UPDATE {table} SET active=%s WHERE id=%s',(active,ident)); c.commit()
    send_json(200,{'ok':True}); return True

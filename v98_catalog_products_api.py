import os, json
import psycopg
from urllib.parse import parse_qs

def db():
    url=os.environ.get('DATABASE_URL')
    if not url: raise RuntimeError('DATABASE_URL não configurado no Render')
    return psycopg.connect(url)

def _clean(v): return str(v or '').strip()
def _num(v, default=0):
    try:return float(v)
    except Exception:return default
def _int_or_none(v):
    if v in (None,'','null'): return None
    try:return int(v)
    except Exception:return None
def _json(v, default=None):
    if v is None:return default
    if isinstance(v,(dict,list)):return v
    try:return json.loads(v)
    except Exception:return default

def _reserved(cur,sku):
    cur.execute("SELECT COALESCE(SUM(COALESCE((x->>'qty')::int,COALESCE((x->>'quantity')::int,0))),0) FROM orders o CROSS JOIN LATERAL jsonb_array_elements(CASE WHEN jsonb_typeof(o.data->'items')='array' THEN o.data->'items' ELSE '[]'::jsonb END) x WHERE x->>'sku'=%s AND LOWER(COALESCE(o.data->>'status','')) IN ('recebida','pendente','pending','em processamento','processing','em preparação','pago')",(sku,))
    return int(cur.fetchone()[0] or 0)

def _specs(v):
    if isinstance(v,list): return v
    if isinstance(v,dict): return [f'{k}: {x}' for k,x in v.items()]
    if v is None:return []
    return [str(v)]

def _row(row):
    attrs=row[22] or {}
    return {'id':row[0],'sku':row[1],'brand':row[2] or '','name':row[3] or '','category':row[4] or '','subcategory':row[5] or '','type':row[6] or '','price':float(row[7] or 0),'oldPrice':float(row[8] or 0),'stockText':row[9] or '','image':row[10] or '','badge':row[11] or '','description':row[12] or '','options':row[13] or {},'specs':_specs(row[14]),'active':bool(row[15]),'createdAt':row[16],'updatedAt':row[17],'categoryId':row[18],'subcategoryId':row[19],'familyId':row[20],'brandId':row[21],'attributes':attrs,'barcode':row[23] or '','family':attrs.get('family',''),'cost':float(attrs.get('cost') or 0),'vatRate':float(attrs.get('vatRate') or 23)}

SELECT="""SELECT p.id,p.sku,p.brand,p.name,p.category,p.subcategory,p.type,p.price,p.old_price,p.stock,p.image,p.badge,p.description,p.options,p.specs,p.active,p.created_at,p.updated_at,p.category_id,p.subcategory_id,p.family_id,p.brand_id,p.attributes,p.barcode,COALESCE(s.stock,0),COALESCE(s.stock_min,0),s.updated_at FROM catalog_products p LEFT JOIN mm_product_stock s ON s.sku=p.sku"""

def _resolve_taxonomy(cur,body):
    category=_clean(body.get('category'));subcategory=_clean(body.get('subcategory'));family=_clean(body.get('family'))
    category_id=_int_or_none(body.get('categoryId'));subcategory_id=_int_or_none(body.get('subcategoryId'));family_id=_int_or_none(body.get('familyId'))
    brand_id=_int_or_none(body.get('brandId'));brand=_clean(body.get('brand'))
    if category_id:
        cur.execute("SELECT id FROM catalog_categories WHERE id=%s AND kind='category' AND active=true",(category_id,))
        if not cur.fetchone(): category_id=None
    if not category_id and category:
        cur.execute("SELECT id FROM catalog_categories WHERE lower(name)=lower(%s) AND kind='category' AND active=true ORDER BY id LIMIT 1",(category,))
        x=cur.fetchone(); category_id=x[0] if x else None
    if subcategory_id:
        cur.execute("SELECT id FROM catalog_categories WHERE id=%s AND kind='subcategory' AND active=true",(subcategory_id,))
        if not cur.fetchone(): subcategory_id=None
    if not subcategory_id and subcategory:
        cur.execute("SELECT id FROM catalog_categories WHERE lower(name)=lower(%s) AND kind='subcategory' AND active=true ORDER BY id LIMIT 1",(subcategory,))
        x=cur.fetchone(); subcategory_id=x[0] if x else None
    if family_id:
        cur.execute("SELECT id FROM catalog_categories WHERE id=%s AND kind='family' AND active=true",(family_id,))
        if not cur.fetchone(): family_id=None
    if not family_id and family:
        cur.execute("SELECT id FROM catalog_categories WHERE lower(name)=lower(%s) AND kind='family' AND active=true ORDER BY id LIMIT 1",(family,))
        x=cur.fetchone(); family_id=x[0] if x else None
    if brand_id:
        cur.execute("SELECT id FROM catalog_brands WHERE id=%s",(brand_id,))
        if not cur.fetchone(): brand_id=None
    if not brand_id and brand:
        cur.execute("SELECT id FROM catalog_brands WHERE lower(name)=lower(%s) ORDER BY id LIMIT 1",(brand,))
        x=cur.fetchone(); brand_id=x[0] if x else None
    return category_id,subcategory_id,family_id,brand_id

def handle_image(query,send_binary):
    qs=parse_qs(query or '')
    sku=_clean((qs.get('sku') or [''])[0])
    if not sku:return False
    try:
        with db() as conn,conn.cursor() as cur:
            cur.execute("SELECT image FROM catalog_products WHERE sku=%s LIMIT 1",(sku,))
            row=cur.fetchone()
        image=_clean(row[0] if row else '')
        if not image.lower().startswith('data:image/') or ';base64,' not in image.lower():return False
        header,data=image.split(',',1)
        mime=header[5:].split(';',1)[0].lower()
        import base64
        raw=base64.b64decode(data,validate=False)
        send_binary(200,mime,raw,max_age=31536000)
        return True
    except Exception:
        return False

def handle_get(path,query,send_json):
    if path!='/api/catalog/products':return False
    try:
        qs=parse_qs(query or '');sku=_clean((qs.get('sku') or [''])[0])
        with db() as conn,conn.cursor() as cur:
            if sku:
                cur.execute(SELECT+' WHERE p.sku=%s LIMIT 1',(sku,));row=cur.fetchone()
                if not row:send_json(404,{'ok':False,'error':'Produto não encontrado'});return True
                item=_row(row);physical=int(row[24] or 0);item.update({'stock':physical,'stockMin':int(row[25] or 0),'reserved':_reserved(cur,sku),'stockUpdatedAt':row[26]});item['available']=max(0,physical-item['reserved']);send_json(200,{'ok':True,'item':item});return True
            cur.execute(SELECT+' ORDER BY p.name ASC,p.id ASC');items=[]
            for row in cur.fetchall():
                item=_row(row);physical=int(row[24] or 0);item.update({'stock':physical,'stockMin':int(row[25] or 0),'reserved':_reserved(cur,row[1]),'stockUpdatedAt':row[26]});item['available']=max(0,physical-item['reserved']);items.append(item)
        send_json(200,{'ok':True,'items':items,'count':len(items)});return True
    except Exception as e:send_json(503,{'ok':False,'error':f'API produtos: {e}'});return True

def handle_post(path,body,send_json):
    if path!='/api/catalog/products':return False
    try:
        sku=_clean(body.get('sku'));name=_clean(body.get('name'))
        if not sku:raise ValueError('SKU obrigatório')
        if not name:raise ValueError('Nome do produto obrigatório')
        price=_num(body.get('price'));old_price=_num(body.get('oldPrice'));active=bool(body.get('active',True))
        options=_json(body.get('options'),[]);specs=_json(body.get('specs'),{});attributes=_json(body.get('attributes'),{})
        if not isinstance(attributes,dict):attributes={}
        if 'family' in body:attributes['family']=_clean(body.get('family'))
        if 'cost' in body:attributes['cost']=_num(body.get('cost'))
        if 'vatRate' in body:attributes['vatRate']=_num(body.get('vatRate'),23)
        barcode=_clean(body.get('barcode')) or None
        stock_min=max(0,int(_num(body.get('stockMin'),0)))
        with db() as conn,conn.cursor() as cur:
            category_id,subcategory_id,family_id,brand_id=_resolve_taxonomy(cur,body)
            image_value=_clean(body.get('image'))
            pid=_int_or_none(body.get('id'))
            if pid and not image_value:
                cur.execute("SELECT image FROM catalog_products WHERE id=%s LIMIT 1",(pid,))
                current=cur.fetchone()
                if current and current[0]: image_value=current[0]
            fields=(sku,_clean(body.get('brand')),name,_clean(body.get('category')),_clean(body.get('subcategory')),_clean(body.get('type')),price,old_price,image_value,_clean(body.get('badge')),_clean(body.get('description')),json.dumps(options,ensure_ascii=False),json.dumps(specs,ensure_ascii=False),active,category_id,subcategory_id,family_id,brand_id,json.dumps(attributes,ensure_ascii=False),barcode)
            if pid:
                cur.execute("UPDATE catalog_products SET sku=%s,brand=%s,name=%s,category=%s,subcategory=%s,type=%s,price=%s,old_price=%s,stock=stock,image=%s,badge=%s,description=%s,options=%s::jsonb,specs=%s::jsonb,active=%s,category_id=%s,subcategory_id=%s,family_id=%s,brand_id=%s,attributes=%s::jsonb,barcode=%s,updated_at=NOW() WHERE id=%s RETURNING id",fields+(pid,))
            else:
                cur.execute("INSERT INTO catalog_products (sku,brand,name,category,subcategory,type,price,old_price,stock,image,badge,description,options,specs,active,category_id,subcategory_id,family_id,brand_id,attributes,barcode,created_at,updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,0,%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s,%s,%s,%s,%s::jsonb,%s,NOW(),NOW()) ON CONFLICT (sku) DO UPDATE SET brand=EXCLUDED.brand,name=EXCLUDED.name,category=EXCLUDED.category,subcategory=EXCLUDED.subcategory,type=EXCLUDED.type,price=EXCLUDED.price,old_price=EXCLUDED.old_price,stock=catalog_products.stock,image=EXCLUDED.image,badge=EXCLUDED.badge,description=EXCLUDED.description,options=EXCLUDED.options,specs=EXCLUDED.specs,active=EXCLUDED.active,category_id=EXCLUDED.category_id,subcategory_id=EXCLUDED.subcategory_id,family_id=EXCLUDED.family_id,brand_id=EXCLUDED.brand_id,attributes=EXCLUDED.attributes,barcode=EXCLUDED.barcode,updated_at=NOW() RETURNING id",fields)
            row=cur.fetchone()
            if not row:raise RuntimeError('Não foi possível guardar o produto')
            pid=row[0]
            cur.execute('INSERT INTO mm_product_stock(sku,stock,stock_min) VALUES(%s,0,%s) ON CONFLICT(sku) DO UPDATE SET stock_min=%s,updated_at=NOW()',(sku,stock_min,stock_min))
            conn.commit()
        send_json(200,{'ok':True,'id':pid,'sku':sku});return True
    except ValueError as e:send_json(400,{'ok':False,'error':str(e)});return True
    except Exception as e:send_json(409 if 'duplicate' in str(e).lower() else 503,{'ok':False,'error':f'Não foi possível guardar o produto: {e}'});return True

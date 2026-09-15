import os, json
import psycopg
from urllib.parse import parse_qs

def db():
    url=os.environ.get('DATABASE_URL')
    if not url: raise RuntimeError('DATABASE_URL não configurado no Render')
    return psycopg.connect(url)

def _clean(v): return str(v or '').strip()
def _num(v, default=0):
    try: return float(v)
    except Exception: return default
def _int_or_none(v):
    if v in (None,'','null'): return None
    try: return int(v)
    except Exception: return None
def _json(v, default=None):
    if v is None: return default
    if isinstance(v,(dict,list)): return v
    try: return json.loads(v)
    except Exception: return default

def _reserved(cur,sku):
    cur.execute("SELECT COALESCE(SUM(COALESCE((x->>'qty')::int,COALESCE((x->>'quantity')::int,0))),0) FROM orders o CROSS JOIN LATERAL jsonb_array_elements(CASE WHEN jsonb_typeof(o.data->'items')='array' THEN o.data->'items' ELSE '[]'::jsonb END) x WHERE x->>'sku'=%s AND LOWER(COALESCE(o.data->>'status','')) IN ('recebida','pendente','pending','em processamento','processing','em preparação','pago')",(sku,))
    return int(cur.fetchone()[0] or 0)

def _row(row):
    attrs=row[22] or {}
    return {'id':row[0],'sku':row[1],'brand':row[2] or '','name':row[3] or '','category':row[4] or '','subcategory':row[5] or '','type':row[6] or '','price':float(row[7] or 0),'oldPrice':float(row[8] or 0),'stockText':row[9] or '','image':row[10] or '','badge':row[11] or '','description':row[12] or '','options':row[13] or [],'specs':row[14] or {},'active':bool(row[15]),'createdAt':row[16],'updatedAt':row[17],'categoryId':row[18],'subcategoryId':row[19],'familyId':row[20],'brandId':row[21],'attributes':attrs,'barcode':row[23] or '','family':attrs.get('family',''),'cost':float(attrs.get('cost') or 0),'vatRate':float(attrs.get('vatRate') or 23)}

SELECT="""SELECT p.id,p.sku,p.brand,p.name,p.category,p.subcategory,p.type,p.price,p.old_price,p.stock,p.image,p.badge,p.description,p.options,p.specs,p.active,p.created_at,p.updated_at,p.category_id,p.subcategory_id,p.family_id,p.brand_id,p.attributes,p.barcode,COALESCE(s.stock,0),COALESCE(s.stock_min,0),s.updated_at FROM catalog_products p LEFT JOIN mm_product_stock s ON s.sku=p.sku"""

def handle_get(path,query,send_json):
    if path!='/api/catalog/products': return False
    try:
        qs=parse_qs(query or '');sku=_clean((qs.get('sku') or [''])[0])
        with db() as conn,conn.cursor() as cur:
            if sku:
                cur.execute(SELECT+' WHERE p.sku=%s LIMIT 1',(sku,));row=cur.fetchone()
                if not row: send_json(404,{'ok':False,'error':'Produto não encontrado'});return True
                item=_row(row);physical=int(row[24] or 0);item.update({'stock':physical,'stockMin':int(row[25] or 0),'reserved':_reserved(cur,sku),'stockUpdatedAt':row[26]});item['available']=max(0,physical-item['reserved']);send_json(200,{'ok':True,'item':item});return True
            cur.execute(SELECT+' ORDER BY p.name ASC,p.id ASC');items=[]
            for row in cur.fetchall():
                item=_row(row);physical=int(row[24] or 0);item.update({'stock':physical,'stockMin':int(row[25] or 0),'reserved':_reserved(cur,row[1]),'stockUpdatedAt':row[26]});item['available']=max(0,physical-item['reserved']);items.append(item)
        send_json(200,{'ok':True,'items':items,'count':len(items)});return True
    except Exception as e: send_json(503,{'ok':False,'error':f'API produtos: {e}'});return True

def handle_post(path,body,send_json):
    if path!='/api/catalog/products': return False
    try:
        sku=_clean(body.get('sku'));name=_clean(body.get('name'))
        if not sku: raise ValueError('SKU obrigatório')
        if not name: raise ValueError('Nome do produto obrigatório')
        price=_num(body.get('price'));old_price=_num(body.get('oldPrice'));active=bool(body.get('active',True));stock_text=_clean(body.get('stockText'))
        options=_json(body.get('options'),[]);specs=_json(body.get('specs'),{});attributes=_json(body.get('attributes'),{})
        if not isinstance(attributes,dict): attributes={}
        if 'family' in body: attributes['family']=_clean(body.get('family'))
        if 'cost' in body: attributes['cost']=_num(body.get('cost'))
        if 'vatRate' in body: attributes['vatRate']=_num(body.get('vatRate'),23)
        barcode=_clean(body.get('barcode')) or None
        fields=(sku,_clean(body.get('brand')),name,_clean(body.get('category')),_clean(body.get('subcategory')),_clean(body.get('type')),price,old_price,stock_text,_clean(body.get('image')),_clean(body.get('badge')),_clean(body.get('description')),json.dumps(options,ensure_ascii=False),json.dumps(specs,ensure_ascii=False),active,_int_or_none(body.get('categoryId')),_int_or_none(body.get('subcategoryId')),_int_or_none(body.get('familyId')),_int_or_none(body.get('brandId')),json.dumps(attributes,ensure_ascii=False),barcode)
        with db() as conn,conn.cursor() as cur:
            pid=_int_or_none(body.get('id'))
            if pid:
                cur.execute("UPDATE catalog_products SET sku=%s,brand=%s,name=%s,category=%s,subcategory=%s,type=%s,price=%s,old_price=%s,stock=%s,image=%s,badge=%s,description=%s,options=%s::jsonb,specs=%s::jsonb,active=%s,category_id=%s,subcategory_id=%s,family_id=%s,brand_id=%s,attributes=%s::jsonb,barcode=%s,updated_at=NOW() WHERE id=%s RETURNING id",fields+(pid,))
            else:
                cur.execute("INSERT INTO catalog_products (sku,brand,name,category,subcategory,type,price,old_price,stock,image,badge,description,options,specs,active,category_id,subcategory_id,family_id,brand_id,attributes,barcode,created_at,updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s,%s,%s,%s,%s::jsonb,%s,NOW(),NOW()) ON CONFLICT (sku) DO UPDATE SET brand=EXCLUDED.brand,name=EXCLUDED.name,category=EXCLUDED.category,subcategory=EXCLUDED.subcategory,type=EXCLUDED.type,price=EXCLUDED.price,old_price=EXCLUDED.old_price,stock=EXCLUDED.stock,image=EXCLUDED.image,badge=EXCLUDED.badge,description=EXCLUDED.description,options=EXCLUDED.options,specs=EXCLUDED.specs,active=EXCLUDED.active,category_id=EXCLUDED.category_id,subcategory_id=EXCLUDED.subcategory_id,family_id=EXCLUDED.family_id,brand_id=EXCLUDED.brand_id,attributes=EXCLUDED.attributes,barcode=EXCLUDED.barcode,updated_at=NOW() RETURNING id",fields)
            row=cur.fetchone()
            if not row: raise RuntimeError('Não foi possível guardar o produto')
            pid=row[0]
            cur.execute('SELECT 1 FROM mm_product_stock WHERE sku=%s',(sku,))
            if cur.fetchone() is None: cur.execute('INSERT INTO mm_product_stock(sku,stock,stock_min) VALUES(%s,%s,%s)',(sku,max(0,int(_num(body.get('stock'),0))),max(0,int(_num(body.get('stockMin'),0)))))
            else: cur.execute('UPDATE mm_product_stock SET stock_min=%s,updated_at=NOW() WHERE sku=%s',(max(0,int(_num(body.get('stockMin'),0))),sku))
            conn.commit()
        send_json(200,{'ok':True,'id':pid,'sku':sku});return True
    except ValueError as e: send_json(400,{'ok':False,'error':str(e)});return True
    except Exception as e: send_json(409 if 'duplicate' in str(e).lower() else 503,{'ok':False,'error':f'Não foi possível guardar o produto: {e}'});return True

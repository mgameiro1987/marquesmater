import os
import psycopg

DB=os.environ.get('DATABASE_URL')

def db():
    if not DB: raise RuntimeError('DATABASE_URL não configurado no Render')
    return psycopg.connect(DB)

def clean(v): return str(v or '').strip()
def iid(v):
    try: return int(v) if v not in (None,'','null') else None
    except Exception: return None

SCHEMA='''CREATE TABLE IF NOT EXISTS mm_product_classifications (
 id BIGSERIAL PRIMARY KEY,
 product_id BIGINT NOT NULL REFERENCES catalog_products(id) ON DELETE CASCADE,
 classification_type TEXT NOT NULL CHECK (classification_type IN ('commercial','rida')),
 category_id BIGINT REFERENCES catalog_categories(id) ON DELETE SET NULL,
 subcategory_id BIGINT REFERENCES catalog_categories(id) ON DELETE SET NULL,
 family_id BIGINT REFERENCES catalog_categories(id) ON DELETE SET NULL,
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 UNIQUE(product_id,classification_type)
);'''

def ensure(cur):
    cur.execute(SCHEMA)

def valid_node(cur,rid,kind):
    if not rid: return None
    cur.execute('SELECT id,name FROM catalog_categories WHERE id=%s AND kind=%s AND active=true',(rid,kind))
    return cur.fetchone()

def save_one(cur,product_id,typ,data):
    cid=iid(data.get('categoryId')); sid=iid(data.get('subcategoryId')); fid=iid(data.get('familyId'))
    if cid and not valid_node(cur,cid,'category'): cid=None
    if sid and not valid_node(cur,sid,'subcategory'): sid=None
    if fid and not valid_node(cur,fid,'family'): fid=None
    cur.execute('''INSERT INTO mm_product_classifications(product_id,classification_type,category_id,subcategory_id,family_id)
                   VALUES(%s,%s,%s,%s,%s)
                   ON CONFLICT(product_id,classification_type) DO UPDATE SET category_id=EXCLUDED.category_id,subcategory_id=EXCLUDED.subcategory_id,family_id=EXCLUDED.family_id,updated_at=NOW()''',(product_id,typ,cid,sid,fid))

def get_for_product(cur,pid):
    cur.execute('''SELECT id,classification_type,category_id,subcategory_id,family_id FROM mm_product_classifications WHERE product_id=%s ORDER BY classification_type''',(pid,))
    return [{'id':r[0],'type':r[1],'categoryId':r[2],'subcategoryId':r[3],'familyId':r[4]} for r in cur.fetchall()]

def get_options(cur):
    cur.execute("SELECT id,name,kind,parent_id FROM catalog_categories WHERE active=true ORDER BY kind,name")
    return [{'id':r[0],'name':r[1],'kind':r[2],'parentId':r[3]} for r in cur.fetchall()]

def handle_get(path,query,send_json):
    if path!='/api/catalog/classification': return False
    from urllib.parse import parse_qs
    qs=parse_qs(query or '')
    try:
        with db() as conn,conn.cursor() as cur:
            ensure(cur);conn.commit()
            if (qs.get('options') or [''])[0]=='1':
                send_json(200,{'ok':True,'options':get_options(cur)});return True
            if (qs.get('all') or [''])[0]=='1':
                cur.execute('''SELECT pc.product_id,pc.classification_type,pc.category_id,pc.subcategory_id,pc.family_id,
                                      cc.name AS category_name,cs.name AS subcategory_name,cf.name AS family_name
                               FROM mm_product_classifications pc
                               LEFT JOIN catalog_categories cc ON cc.id=pc.category_id
                               LEFT JOIN catalog_categories cs ON cs.id=pc.subcategory_id
                               LEFT JOIN catalog_categories cf ON cf.id=pc.family_id
                               ORDER BY pc.product_id,pc.classification_type''')
                grouped={}
                for r in cur.fetchall():
                    grouped.setdefault(str(r[0]),{})[r[1]]={'categoryId':r[2],'subcategoryId':r[3],'familyId':r[4],'category':r[5] or '','subcategory':r[6] or '','family':r[7] or ''}
                send_json(200,{'ok':True,'items':grouped});return True
            pid=iid((qs.get('productId') or [''])[0])
            if not pid:
                send_json(400,{'ok':False,'error':'productId obrigatório'});return True
            send_json(200,{'ok':True,'classifications':get_for_product(cur,pid)});return True
    except Exception as e:
        send_json(503,{'ok':False,'error':f'Classificação: {e}'});return True

def handle_post(path,body,send_json):
    if path!='/api/catalog/classification': return False
    try:
        pid=iid(body.get('productId'))
        if not pid: raise ValueError('productId obrigatório')
        with db() as conn,conn.cursor() as cur:
            ensure(cur)
            cur.execute('SELECT id FROM catalog_products WHERE id=%s',(pid,))
            if not cur.fetchone(): raise ValueError('Produto não encontrado')
            data=body.get('classifications') or {}
            for typ in ('commercial','rida'):
                if isinstance(data.get(typ),dict): save_one(cur,pid,typ,data[typ])
            conn.commit()
            send_json(200,{'ok':True,'classifications':get_for_product(cur,pid)});return True
    except ValueError as e: send_json(400,{'ok':False,'error':str(e)});return True
    except Exception as e: send_json(503,{'ok':False,'error':f'Não foi possível guardar a classificação: {e}'});return True

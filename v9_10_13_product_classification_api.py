import os
import psycopg

DB=os.environ.get('DATABASE_URL')

def db():
    if not DB: raise RuntimeError('DATABASE_URL não configurado no Render')
    return psycopg.connect(DB)

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

def ensure(cur): cur.execute(SCHEMA)

def normalize_rida_commercial(cur):
    # Organização comercial RIDA.
    cur.execute("SELECT id FROM catalog_categories WHERE kind='category' AND lower(name)=lower('Ferramentas') AND active=true LIMIT 1")
    tools=cur.fetchone()
    cur.execute("SELECT id FROM catalog_categories WHERE kind='category' AND lower(name)=lower('Jardim & Agricultura') AND active=true LIMIT 1")
    garden=cur.fetchone()
    if not tools or not garden:
        return
    tools_id=tools[0]; garden_id=garden[0]

    def get_or_create_subcategory(parent_id,name):
        cur.execute("SELECT id FROM catalog_categories WHERE kind='subcategory' AND parent_id=%s AND lower(name)=lower(%s) AND active=true LIMIT 1",(parent_id,name))
        row=cur.fetchone()
        if row: return row[0]
        cur.execute("""INSERT INTO catalog_categories(name,kind,parent_id,active)
                       VALUES(%s,'subcategory',%s,true) RETURNING id""",(name,parent_id))
        return cur.fetchone()[0]

    # Ferramentas: estrutura comercial definitiva.
    tool_subs={}
    for name in ('Berbequins e Aparafusadoras','Rebarbadoras','Martelos Perfuradores','Serras','Lixadoras','Ferramentas Especiais','Baterias e Carregadores','Acessórios'):
        tool_subs[name]=get_or_create_subcategory(tools_id,name)

    # Jardim: estrutura já alinhada.
    garden_subs={}
    for name in ('Motosserras','Podas e Corte','Roçadoras e Aparadores','Sopradores'):
        garden_subs[name]=get_or_create_subcategory(garden_id,name)

    garden_skus={
        'RGT11280','RGT11280-C12','RHT09025','RHT09025-C12',
        'RCS03V016','RCS03V016-C24','RCS06006','RCS06006-C12',
        'RBL06650','RBL06650-C22','RBP01040','RBP01040-C12',
        'JARD-SERRA-001','REP16245'
    }
    batteries={'RB2020','RB2040','RFC24','RDC30'}
    accessories={'BMCB75','000000','Mala BMC'}

    def tool_sub(sku):
        if sku in batteries: return tool_subs['Baterias e Carregadores']
        if sku in accessories: return tool_subs['Acessórios']
        if sku.startswith('RHD'): return tool_subs['Berbequins e Aparafusadoras']
        if sku.startswith('RCG'): return tool_subs['Rebarbadoras']
        if sku.startswith('RCH'): return tool_subs['Martelos Perfuradores']
        if sku.startswith(('RCC','RCJ','RCR')): return tool_subs['Serras']
        if sku.startswith('RCO'): return tool_subs['Lixadoras']
        return tool_subs['Ferramentas Especiais']

    cur.execute("SELECT id,sku,name FROM catalog_products WHERE upper(brand)='RIDA' AND active IS DISTINCT FROM FALSE")
    for pid,sku,name in cur.fetchall():
        sku=str(sku or '')
        lname=str(name or '').lower()
        if sku in garden_skus:
            if sku.startswith('RCS'): sid=garden_subs['Motosserras']
            elif sku in ('RBP01040','RBP01040-C12','JARD-SERRA-001','REP16245'): sid=garden_subs['Podas e Corte']
            elif sku.startswith(('RGT','RHT')): sid=garden_subs['Roçadoras e Aparadores']
            elif sku.startswith('RBL'): sid=garden_subs['Sopradores']
            else: sid=garden_subs['Podas e Corte']
            save_one(cur,pid,'commercial',{'categoryId':garden_id,'subcategoryId':sid,'familyId':None})
        else:
            sid=tool_sub(sku)
            save_one(cur,pid,'commercial',{'categoryId':tools_id,'subcategoryId':sid,'familyId':None})

def normalize_rida_construction_items(cur):
    # Correção pontual e idempotente: luz de trabalho e coluna RIDA pertencem à estrutura de Construção.
    cur.execute("""SELECT id FROM catalog_products WHERE sku IN ('RCL1250H','RCL1250H-C12','RJR12000')""")
    for (pid,) in cur.fetchall():
        save_one(cur,pid,'rida',{'categoryId':11,'subcategoryId':16602,'familyId':16603})

    # Jardim: serra de poda e respetiva vara extensível.
    cur.execute("""SELECT id FROM catalog_products WHERE sku IN ('JARD-SERRA-001','REP16245')""")
    for (pid,) in cur.fetchall():
        save_one(cur,pid,'rida',{'categoryId':11,'subcategoryId':16602,'familyId':16604})

def valid_node(cur,rid,kind):
    if not rid: return None
    cur.execute('SELECT id FROM catalog_categories WHERE id=%s AND kind=%s AND active=true',(rid,kind))
    return cur.fetchone()

def save_one(cur,pid,typ,data):
    cid=iid(data.get('categoryId'));sid=iid(data.get('subcategoryId'));fid=iid(data.get('familyId'))
    if cid and not valid_node(cur,cid,'category'): cid=None
    if sid and not valid_node(cur,sid,'subcategory'): sid=None
    if fid and not valid_node(cur,fid,'family'): fid=None
    cur.execute('''INSERT INTO mm_product_classifications(product_id,classification_type,category_id,subcategory_id,family_id)
    VALUES(%s,%s,%s,%s,%s)
    ON CONFLICT(product_id,classification_type) DO UPDATE SET category_id=EXCLUDED.category_id,subcategory_id=EXCLUDED.subcategory_id,family_id=EXCLUDED.family_id,updated_at=NOW()''',(pid,typ,cid,sid,fid))

def get_for_product(cur,pid):
    cur.execute('SELECT id,classification_type,category_id,subcategory_id,family_id FROM mm_product_classifications WHERE product_id=%s ORDER BY classification_type',(pid,))
    return [{'id':r[0],'type':r[1],'categoryId':r[2],'subcategoryId':r[3],'familyId':r[4]} for r in cur.fetchall()]

def get_options(cur):
    cur.execute('SELECT id,name,kind,parent_id FROM catalog_categories WHERE active=true ORDER BY kind,name')
    return [{'id':r[0],'name':r[1],'kind':r[2],'parentId':r[3]} for r in cur.fetchall()]

def handle_get(path,query,send_json):
    if path!='/api/catalog/classification': return False
    from urllib.parse import parse_qs
    qs=parse_qs(query or '')
    try:
        with db() as conn,conn.cursor() as cur:
            ensure(cur)
            # A normalização comercial é protegida: se a BD não tiver alguma estrutura esperada,
            # a API de classificações continua a devolver os dados existentes em vez de bloquear o catálogo.
            try:
                cur.execute('SAVEPOINT rida_normalize')
                normalize_rida_commercial(cur);normalize_rida_construction_items(cur)
                cur.execute('RELEASE SAVEPOINT rida_normalize')
            except Exception:
                cur.execute('ROLLBACK TO SAVEPOINT rida_normalize')
                cur.execute('RELEASE SAVEPOINT rida_normalize')
            conn.commit()
            if (qs.get('options') or [''])[0]=='1':
                send_json(200,{'ok':True,'options':get_options(cur)});return True
            if (qs.get('all') or [''])[0]=='1':
                cur.execute('''SELECT pc.product_id,pc.classification_type,pc.category_id,pc.subcategory_id,pc.family_id,
                                      c.name,sc.name,f.name
                               FROM mm_product_classifications pc
                               LEFT JOIN catalog_categories c ON c.id=pc.category_id
                               LEFT JOIN catalog_categories sc ON sc.id=pc.subcategory_id
                               LEFT JOIN catalog_categories f ON f.id=pc.family_id
                               ORDER BY pc.product_id,pc.classification_type''')
                items={}
                for r in cur.fetchall():
                    pid,typ,cid,sid,fid,cn,sn,fn=r
                    items.setdefault(str(pid),{})[typ]={
                        'categoryId':cid,'subcategoryId':sid,'familyId':fid,
                        'category':cn,'subcategory':sn,'family':fn
                    }
                send_json(200,{'ok':True,'items':items});return True
            pid=iid((qs.get('productId') or [''])[0])
            if not pid:
                send_json(400,{'ok':False,'error':'productId obrigatório'});return True
            rows=get_for_product(cur,pid)
            enriched=[]
            for row in rows:
                cur.execute('''SELECT c.name,sc.name,f.name
                               FROM (SELECT %s::bigint AS category_id,%s::bigint AS subcategory_id,%s::bigint AS family_id) z
                               LEFT JOIN catalog_categories c ON c.id=z.category_id
                               LEFT JOIN catalog_categories sc ON sc.id=z.subcategory_id
                               LEFT JOIN catalog_categories f ON f.id=z.family_id''',
                            (row['categoryId'],row['subcategoryId'],row['familyId']))
                names=cur.fetchone() or (None,None,None)
                row.update({'category':names[0],'subcategory':names[1],'family':names[2]})
                enriched.append(row)
            send_json(200,{'ok':True,'classifications':enriched});return True
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
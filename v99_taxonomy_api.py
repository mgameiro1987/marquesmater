import os
import psycopg

def db():
    url=os.environ.get('DATABASE_URL')
    if not url: raise RuntimeError('DATABASE_URL não configurado no Render')
    return psycopg.connect(url)

def clean(v): return str(v or '').strip()

def ensure(cur):
    # Limpeza autorizada dos produtos de demonstração/teste do catálogo.
    cur.execute("""
        DELETE FROM catalog_products
        WHERE sku IN ('DEMO-VAR-SILICONE','DEMO-VAR-RIDA-KIT','DEMO-VAR-CAIXA')
    """)
    cur.execute("CREATE TABLE IF NOT EXISTS mm_categories (id BIGSERIAL PRIMARY KEY,name TEXT NOT NULL UNIQUE,description TEXT NOT NULL DEFAULT '',icon TEXT NOT NULL DEFAULT '',active BOOLEAN NOT NULL DEFAULT TRUE,display_order INTEGER,created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW())")
    cur.execute("CREATE TABLE IF NOT EXISTS mm_subcategories (id BIGSERIAL PRIMARY KEY,category_id BIGINT NOT NULL REFERENCES mm_categories(id) ON DELETE CASCADE,name TEXT NOT NULL,active BOOLEAN NOT NULL DEFAULT TRUE,display_order INTEGER,created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),UNIQUE(category_id,name))")
    cur.execute("CREATE TABLE IF NOT EXISTS mm_families (id BIGSERIAL PRIMARY KEY,category_id BIGINT NOT NULL REFERENCES mm_categories(id) ON DELETE CASCADE,subcategory_id BIGINT REFERENCES mm_subcategories(id) ON DELETE SET NULL,name TEXT NOT NULL,active BOOLEAN NOT NULL DEFAULT TRUE,display_order INTEGER,created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),UNIQUE(category_id,name))")
    cur.execute("ALTER TABLE mm_categories ADD COLUMN IF NOT EXISTS display_order INTEGER")
    cur.execute("ALTER TABLE mm_subcategories ADD COLUMN IF NOT EXISTS display_order INTEGER")
    cur.execute("ALTER TABLE mm_families ADD COLUMN IF NOT EXISTS display_order INTEGER")
    cur.execute("UPDATE mm_categories SET display_order=x.rn FROM (SELECT id,ROW_NUMBER() OVER(ORDER BY name) rn FROM mm_categories) x WHERE mm_categories.id=x.id AND mm_categories.display_order IS NULL")
    cur.execute("UPDATE mm_subcategories SET display_order=x.rn FROM (SELECT id,ROW_NUMBER() OVER(PARTITION BY category_id ORDER BY name) rn FROM mm_subcategories) x WHERE mm_subcategories.id=x.id AND mm_subcategories.display_order IS NULL")
    cur.execute("UPDATE mm_families SET display_order=x.rn FROM (SELECT id,ROW_NUMBER() OVER(PARTITION BY category_id ORDER BY name) rn FROM mm_families) x WHERE mm_families.id=x.id AND mm_families.display_order IS NULL")
    cur.execute("UPDATE mm_subcategories SET active=FALSE WHERE category_id=(SELECT id FROM mm_categories WHERE name='RIDA') AND lower(name) IN ('berbequins e aparafusadoras','rebarbadoras','serras','baterias e carregadores')")
    cur.execute("INSERT INTO mm_subcategories(category_id,name,active,display_order) SELECT id,'Máquinas a bateria',TRUE,1 FROM mm_categories WHERE name='RIDA' ON CONFLICT(category_id,name) DO UPDATE SET active=TRUE,display_order=1")
    cur.execute("SELECT DISTINCT NULLIF(BTRIM(category),'') FROM catalog_products WHERE NULLIF(BTRIM(category),'') IS NOT NULL")
    for (name,) in cur.fetchall():
        cur.execute("INSERT INTO mm_categories(name,display_order) VALUES(%s,(SELECT COALESCE(MAX(display_order),0)+1 FROM mm_categories)) ON CONFLICT(name) DO NOTHING",(name,))
    cur.execute("SELECT id,name FROM mm_categories")
    cats={n:i for i,n in cur.fetchall()}
    cur.execute("SELECT DISTINCT NULLIF(BTRIM(category),''),NULLIF(BTRIM(subcategory),'') FROM catalog_products WHERE NULLIF(BTRIM(category),'') IS NOT NULL AND NULLIF(BTRIM(subcategory),'') IS NOT NULL")
    for c,s in cur.fetchall():
        cur.execute("INSERT INTO mm_subcategories(category_id,name,display_order) VALUES(%s,%s,(SELECT COALESCE(MAX(display_order),0)+1 FROM mm_subcategories WHERE category_id=%s)) ON CONFLICT(category_id,name) DO NOTHING",(cats[c],s,cats[c]))
    cur.execute("SELECT DISTINCT NULLIF(BTRIM(category),''),NULLIF(BTRIM(subcategory),''),NULLIF(BTRIM(COALESCE(attributes->>'family','')),'') FROM catalog_products WHERE NULLIF(BTRIM(category),'') IS NOT NULL AND NULLIF(BTRIM(COALESCE(attributes->>'family','')),'') IS NOT NULL")
    for c,s,f in cur.fetchall():
        sid=None
        if s:
            cur.execute("SELECT id FROM mm_subcategories WHERE category_id=%s AND name=%s",(cats[c],s))
            z=cur.fetchone(); sid=z[0] if z else None
        cur.execute("INSERT INTO mm_families(category_id,subcategory_id,name,display_order) VALUES(%s,%s,%s,(SELECT COALESCE(MAX(display_order),0)+1 FROM mm_families WHERE category_id=%s)) ON CONFLICT(category_id,name) DO UPDATE SET subcategory_id=COALESCE(EXCLUDED.subcategory_id,mm_families.subcategory_id)",(cats[c],sid,f,cats[c]))

def handle_get(path,query,send_json):
    if path!='/api/taxonomy': return False
    try:
        with db() as conn,conn.cursor() as cur:
            ensure(cur);conn.commit()
            cur.execute("SELECT id,name,description,icon,active,display_order FROM mm_categories ORDER BY COALESCE(display_order,2147483647),name")
            cats=[{'id':r[0],'name':r[1],'description':r[2],'icon':r[3],'active':r[4],'order':r[5],'products':0,'subcategories':[],'families':[]} for r in cur.fetchall()]
            by={x['id']:x for x in cats}
            cur.execute("SELECT id,category_id,name,active,display_order FROM mm_subcategories ORDER BY category_id,COALESCE(display_order,2147483647),name")
            for r in cur.fetchall():
                by[r[1]]['subcategories'].append({'id':r[0],'categoryId':r[1],'name':r[2],'active':r[3],'order':r[4],'products':0})
            cur.execute("SELECT id,category_id,subcategory_id,name,active,display_order FROM mm_families ORDER BY category_id,COALESCE(display_order,2147483647),name")
            for r in cur.fetchall():
                by[r[1]]['families'].append({'id':r[0],'categoryId':r[1],'subcategoryId':r[2],'name':r[3],'active':r[4],'order':r[5],'products':0})
            cur.execute("SELECT category,subcategory,attributes->>'family',COUNT(*) FROM catalog_products GROUP BY 1,2,3")
            for c,s,f,n in cur.fetchall():
                cat=next((x for x in cats if x['name']==c),None)
                if not cat: continue
                cat['products']+=n
                for x in cat['subcategories']:
                    if x['name']==s: x['products']+=n
                for x in cat['families']:
                    if x['name']==f: x['products']+=n
            send_json(200,{'ok':True,'categories':cats,'count':len(cats)});return True
    except Exception as e:
        send_json(503,{'ok':False,'error':f'API taxonomia: {e}'});return True

def handle_post(path,body,send_json):
    if path!='/api/taxonomy': return False
    try:
        kind=clean(body.get('kind'));name=clean(body.get('name'))
        cid=int(body.get('categoryId') or 0) if str(body.get('categoryId') or '').isdigit() else 0
        sid=int(body.get('subcategoryId') or 0) if str(body.get('subcategoryId') or '').isdigit() else None
        if kind not in ('category','subcategory','family') or not name: raise ValueError('Tipo e nome são obrigatórios')
        with db() as conn,conn.cursor() as cur:
            ensure(cur)
            if kind=='category':
                cur.execute("INSERT INTO mm_categories(name,description,icon,active,display_order) VALUES(%s,%s,%s,%s,(SELECT COALESCE(MAX(display_order),0)+1 FROM mm_categories)) RETURNING id",(name,clean(body.get('description')),clean(body.get('icon')),bool(body.get('active',True))))
            elif kind=='subcategory':
                if not cid: raise ValueError('Categoria obrigatória')
                cur.execute("INSERT INTO mm_subcategories(category_id,name,active,display_order) VALUES(%s,%s,%s,(SELECT COALESCE(MAX(display_order),0)+1 FROM mm_subcategories WHERE category_id=%s)) RETURNING id",(cid,name,bool(body.get('active',True)),cid))
            else:
                if not cid: raise ValueError('Categoria obrigatória')
                cur.execute("INSERT INTO mm_families(category_id,subcategory_id,name,active,display_order) VALUES(%s,%s,%s,%s,(SELECT COALESCE(MAX(display_order),0)+1 FROM mm_families WHERE category_id=%s)) RETURNING id",(cid,sid,name,bool(body.get('active',True)),cid))
            new=cur.fetchone()[0];conn.commit();send_json(201,{'ok':True,'id':new});return True
    except psycopg.errors.UniqueViolation:
        send_json(409,{'ok':False,'error':'Já existe um registo com esse nome neste nível.'});return True
    except ValueError as e:
        send_json(400,{'ok':False,'error':str(e)});return True
    except Exception as e:
        send_json(503,{'ok':False,'error':f'API taxonomia: {e}'});return True

def handle_patch(path,body,send_json):
    if path!='/api/taxonomy': return False
    try:
        if body.get('action')=='reorder':
            kind=clean(body.get('kind'));items=body.get('items') or []
            if kind not in ('category','subcategory','family') or not items: raise ValueError('Ordem inválida')
            table={'category':'mm_categories','subcategory':'mm_subcategories','family':'mm_families'}[kind]
            with db() as conn,conn.cursor() as cur:
                ensure(cur)
                for pos,item in enumerate(items,1):
                    rid=int(item.get('id') or 0)
                    if rid: cur.execute(f"UPDATE {table} SET display_order=%s,updated_at=NOW() WHERE id=%s",(pos,rid))
                conn.commit();send_json(200,{'ok':True,'count':len(items)});return True
        kind=clean(body.get('kind'));rid=int(body.get('id') or 0);name=clean(body.get('name'));active=bool(body.get('active',True))
        if kind not in ('category','subcategory','family') or not rid or not name: raise ValueError('Dados inválidos')
        with db() as conn,conn.cursor() as cur:
            ensure(cur)
            if kind=='category':
                cur.execute("UPDATE mm_categories SET name=%s,description=%s,icon=%s,active=%s,updated_at=NOW() WHERE id=%s",(name,clean(body.get('description')),clean(body.get('icon')),active,rid))
            elif kind=='subcategory':
                cur.execute("UPDATE mm_subcategories SET name=%s,active=%s,updated_at=NOW() WHERE id=%s",(name,active,rid))
            else:
                cur.execute("UPDATE mm_families SET name=%s,subcategory_id=%s,active=%s,updated_at=NOW() WHERE id=%s",(name,int(body.get('subcategoryId')) if str(body.get('subcategoryId') or '').isdigit() else None,active,rid))
            if cur.rowcount!=1: raise ValueError('Registo não encontrado')
            conn.commit();send_json(200,{'ok':True});return True
    except psycopg.errors.UniqueViolation:
        send_json(409,{'ok':False,'error':'Já existe um registo com esse nome neste nível.'});return True
    except ValueError as e:
        send_json(400,{'ok':False,'error':str(e)});return True
    except Exception as e:
        send_json(503,{'ok':False,'error':f'API taxonomia: {e}'});return True

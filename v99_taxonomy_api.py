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
    cur.execute("CREATE TABLE IF NOT EXISTS mm_categories (id BIGSERIAL PRIMARY KEY,name TEXT NOT NULL UNIQUE,description TEXT NOT NULL DEFAULT '',icon TEXT NOT NULL DEFAULT '',image TEXT NOT NULL DEFAULT '',active BOOLEAN NOT NULL DEFAULT TRUE,display_order INTEGER,created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW())")
    cur.execute("CREATE TABLE IF NOT EXISTS mm_subcategories (id BIGSERIAL PRIMARY KEY,category_id BIGINT NOT NULL REFERENCES mm_categories(id) ON DELETE CASCADE,name TEXT NOT NULL,active BOOLEAN NOT NULL DEFAULT TRUE,display_order INTEGER,created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),UNIQUE(category_id,name))")
    cur.execute("CREATE TABLE IF NOT EXISTS mm_families (id BIGSERIAL PRIMARY KEY,category_id BIGINT NOT NULL REFERENCES mm_categories(id) ON DELETE CASCADE,subcategory_id BIGINT REFERENCES mm_subcategories(id) ON DELETE SET NULL,name TEXT NOT NULL,active BOOLEAN NOT NULL DEFAULT TRUE,display_order INTEGER,created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),UNIQUE(category_id,name))")
    cur.execute("ALTER TABLE mm_categories ADD COLUMN IF NOT EXISTS image TEXT NOT NULL DEFAULT ''")
    cur.execute("ALTER TABLE mm_categories ADD COLUMN IF NOT EXISTS display_order INTEGER")
    cur.execute("ALTER TABLE mm_subcategories ADD COLUMN IF NOT EXISTS display_order INTEGER")
    cur.execute("ALTER TABLE mm_families ADD COLUMN IF NOT EXISTS display_order INTEGER")
    cur.execute("UPDATE mm_categories SET display_order=x.rn FROM (SELECT id,ROW_NUMBER() OVER(ORDER BY name) rn FROM mm_categories) x WHERE mm_categories.id=x.id AND mm_categories.display_order IS NULL")
    cur.execute("UPDATE mm_subcategories SET display_order=x.rn FROM (SELECT id,ROW_NUMBER() OVER(PARTITION BY category_id ORDER BY name) rn FROM mm_subcategories) x WHERE mm_subcategories.id=x.id AND mm_subcategories.display_order IS NULL")
    cur.execute("UPDATE mm_families SET display_order=x.rn FROM (SELECT id,ROW_NUMBER() OVER(PARTITION BY category_id ORDER BY name) rn FROM mm_families) x WHERE mm_families.id=x.id AND mm_families.display_order IS NULL")
    cur.execute("UPDATE mm_subcategories SET active=FALSE WHERE category_id=(SELECT id FROM mm_categories WHERE name='RIDA') AND lower(name) IN ('berbequins e aparafusadoras','rebarbadoras','serras','baterias e carregadores')")
    cur.execute("INSERT INTO mm_subcategories(category_id,name,active,display_order) SELECT id,'Máquinas a bateria',TRUE,1 FROM mm_categories WHERE lower(name)='rida' ON CONFLICT(category_id,name) DO UPDATE SET active=TRUE,display_order=1")
    # Imagens visuais das categorias no gestor (editáveis por URL).
    category_images={
      'Construção':'/assets/categories/construcao.svg','Ferramentas':'/assets/categories/ferramentas.svg',
      'Jardim & Agricultura':'/assets/categories/jardim.svg','Tintas':'/assets/categories/tintas.svg',
      'RIDA':'/assets/categories/rida.svg','Selantes & Colas':'/assets/categories/selantes.svg',
      'Eletricidade':'/assets/categories/eletricidade.svg','Iluminação':'/assets/categories/iluminacao.svg',
      'Casa':'/assets/categories/casa.svg','EPI':'/assets/categories/epi.svg',
      'Canalização':'/assets/categories/canalizacao.svg','Promoções':'/assets/categories/promocoes.svg'
    }
    for cname,cimg in category_images.items():
        cur.execute("UPDATE mm_categories SET image=%s WHERE lower(name)=lower(%s) AND COALESCE(image,'')=''",(cimg,cname))
    # A taxonomia do Backoffice espelha a taxonomia canónica de catalog_categories.
    cur.execute("SELECT id,name FROM catalog_categories WHERE kind='category' AND active IS DISTINCT FROM FALSE ORDER BY id")
    catalog_cats=cur.fetchall()
    for ccid,cname in catalog_cats:
        cur.execute("INSERT INTO mm_categories(name,display_order) VALUES(%s,(SELECT COALESCE(MAX(display_order),0)+1 FROM mm_categories)) ON CONFLICT(name) DO NOTHING",(cname,))
    # Desativar categorias/subcategorias/famílias legacy que já não existem na taxonomia canónica.
    cur.execute("UPDATE mm_categories m SET active=FALSE WHERE NOT EXISTS (SELECT 1 FROM catalog_categories c WHERE c.kind='category' AND c.active IS DISTINCT FROM FALSE AND lower(c.name)=lower(m.name))")
    cur.execute("SELECT id,name FROM mm_categories")
    mm_by_name={n:i for i,n in cur.fetchall()}
    cur.execute("SELECT id,name,parent_id FROM catalog_categories WHERE kind='subcategory' AND active IS DISTINCT FROM FALSE ORDER BY id")
    catalog_subs=cur.fetchall()
    for sid,sname,parent_id in catalog_subs:
        cur.execute("SELECT name FROM catalog_categories WHERE id=%s",(parent_id,))
        z=cur.fetchone(); cname=z[0] if z else None
        if cname not in mm_by_name: continue
        mcid=mm_by_name[cname]
        cur.execute("INSERT INTO mm_subcategories(category_id,name,display_order,active) VALUES(%s,%s,(SELECT COALESCE(MAX(display_order),0)+1 FROM mm_subcategories WHERE category_id=%s),TRUE) ON CONFLICT(category_id,name) DO UPDATE SET active=TRUE",(mcid,sname,mcid))
    cur.execute("UPDATE mm_subcategories m SET active=FALSE WHERE NOT EXISTS (SELECT 1 FROM catalog_categories c JOIN mm_categories mc ON mc.id=m.category_id WHERE c.kind='subcategory' AND c.active IS DISTINCT FROM FALSE AND c.parent_id IS NOT NULL AND lower(c.name)=lower(m.name) AND c.parent_id=(SELECT id FROM catalog_categories cc WHERE cc.kind='category' AND lower(cc.name)=lower(mc.name) LIMIT 1))")
    cur.execute("SELECT id,name,category_id FROM mm_subcategories")
    mm_sub_by_name={(cid,n):sid for sid,n,cid in cur.fetchall()}
    cur.execute("SELECT id,name,parent_id FROM catalog_categories WHERE kind='family' AND active IS DISTINCT FROM FALSE ORDER BY id")
    catalog_fams=cur.fetchall()
    for fid,fname,parent_sid in catalog_fams:
        cur.execute("SELECT s.name,c.name FROM catalog_categories s JOIN catalog_categories c ON c.id=s.parent_id WHERE s.id=%s",(parent_sid,))
        z=cur.fetchone()
        if not z: continue
        sname,cname=z
        mcid=mm_by_name.get(cname); msid=mm_sub_by_name.get((mcid,sname)) if mcid else None
        if not mcid: continue
        cur.execute("INSERT INTO mm_families(category_id,subcategory_id,name,display_order,active) VALUES(%s,%s,%s,(SELECT COALESCE(MAX(display_order),0)+1 FROM mm_families WHERE category_id=%s),TRUE) ON CONFLICT(category_id,name) DO UPDATE SET subcategory_id=EXCLUDED.subcategory_id, active=TRUE",(mcid,msid,fname,mcid))
    cur.execute("UPDATE mm_families m SET active=FALSE WHERE NOT EXISTS (SELECT 1 FROM catalog_categories f JOIN catalog_categories s ON s.id=f.parent_id JOIN catalog_categories c ON c.id=s.parent_id JOIN mm_categories mc ON lower(mc.name)=lower(c.name) WHERE f.kind='family' AND f.active IS DISTINCT FROM FALSE AND lower(f.name)=lower(m.name) AND mc.id=m.category_id)")
    # Limpeza final da árvore RIDA: apenas a taxonomia comercial/RIDA canónica.
    cur.execute("""
        UPDATE mm_families
        SET active=FALSE
        WHERE category_id=(SELECT id FROM mm_categories WHERE lower(name)='rida')
          AND lower(name)='rida'
    """)
    # Ordem comercial definida para as famílias RIDA.
    cur.execute("""
        UPDATE mm_families SET display_order=CASE lower(name)
            WHEN 'construção' THEN 1
            WHEN 'jardim' THEN 2
            WHEN 'acessórios' THEN 3
            ELSE display_order END
        WHERE category_id=(SELECT id FROM mm_categories WHERE lower(name)='rida')
          AND lower(name) IN ('construção','jardim','acessórios')
    """)
    # Garantia adicional: a antiga estrutura RIDA não volta a ser criada a partir de produtos legacy.
    cur.execute("UPDATE mm_subcategories SET active=FALSE WHERE category_id=(SELECT id FROM mm_categories WHERE lower(name)='rida') AND lower(name) IN ('berbequins e aparafusadoras','rebarbadoras','serras','baterias e carregadores')")
    cur.execute("UPDATE mm_subcategories SET active=TRUE,display_order=1 WHERE category_id=(SELECT id FROM mm_categories WHERE lower(name)='rida') AND lower(name)='máquinas a bateria'")
    cur.execute("UPDATE mm_families SET active=TRUE,display_order=CASE lower(name) WHEN 'construção' THEN 1 WHEN 'jardim' THEN 2 WHEN 'acessórios' THEN 3 ELSE display_order END,subcategory_id=(SELECT id FROM mm_subcategories WHERE category_id=(SELECT id FROM mm_categories WHERE lower(name)='rida') AND lower(name)='máquinas a bateria' LIMIT 1) WHERE category_id=(SELECT id FROM mm_categories WHERE lower(name)='rida') AND lower(name) IN ('construção','jardim','acessórios')")

def repair_rida(cur):
    # Reclassifica os produtos RIDA existentes na árvore RIDA canónica, sem criar produtos.
    cur.execute("SELECT id FROM catalog_categories WHERE kind='category' AND lower(name)='rida' LIMIT 1"); rc=cur.fetchone()
    cur.execute("SELECT id FROM catalog_categories WHERE kind='subcategory' AND parent_id=%s AND lower(name)='máquinas a bateria' LIMIT 1",(rc[0] if rc else 0,)); rs=cur.fetchone()
    if not rc or not rs: raise ValueError('Taxonomia RIDA canónica incompleta')
    cur.execute("SELECT id,name,sku FROM catalog_products WHERE active IS DISTINCT FROM FALSE AND upper(brand) LIKE '%RIDA%'")
    rows=cur.fetchall()
    for pid,name,sku in rows:
        text=(str(name or '')+' '+str(sku or '')).lower()
        family='Acessórios' if int(pid) in (54,55,56,57,58) or any(x in text for x in ('bateria 2ah','bateria 4ah','carregador','mala bmc')) else ('Jardim' if any(x in text for x in ('relva','corta-sebes','motosserra','tesoura de poda','soprador','vara extensível','serra de poda')) else 'Construção')
        cur.execute("SELECT id FROM catalog_categories WHERE kind='family' AND parent_id=%s AND lower(name)=lower(%s) LIMIT 1",(rs[0],family)); rf=cur.fetchone()
        if not rf: raise ValueError('Família RIDA não encontrada: '+family)
        cur.execute("SELECT id FROM mm_product_classifications WHERE product_id=%s AND classification_type='rida' LIMIT 1",(pid,)); old=cur.fetchone()
        if old:
            cur.execute("UPDATE mm_product_classifications SET category_id=%s,subcategory_id=%s,family_id=%s,updated_at=NOW() WHERE id=%s",(rc[0],rs[0],rf[0],old[0]))
        else:
            cur.execute("INSERT INTO mm_product_classifications(product_id,classification_type,category_id,subcategory_id,family_id) VALUES(%s,'rida',%s,%s,%s)",(pid,rc[0],rs[0],rf[0]))
        cur.execute("UPDATE catalog_products SET category_id=COALESCE(category_id,category_id) WHERE id=%s",(pid,))
    return len(rows)

def handle_get(path,query,send_json):
    if path!='/api/taxonomy': return False
    try:
        with db() as conn,conn.cursor() as cur:
            # A sincronização estrutural é feita apenas no carregamento final da
            # página de Categorias. Os restantes GET são estritamente de leitura,
            # evitando locks/escritas desnecessárias e tornando o Backoffice mais rápido.
            if 'final=1' in (query or ''):
                ensure(cur)
            cur.execute("SELECT id,name,description,icon,image,active,display_order FROM mm_categories ORDER BY COALESCE(display_order,2147483647),name")
            cats=[{'id':r[0],'name':r[1],'description':r[2],'icon':r[3],'image':r[4],'active':r[5],'order':r[6],'products':0,'subcategories':[],'families':[]} for r in cur.fetchall()]
            by={x['id']:x for x in cats}
            cur.execute("SELECT id,category_id,name,active,display_order FROM mm_subcategories ORDER BY category_id,COALESCE(display_order,2147483647),name")
            for r in cur.fetchall():
                by[r[1]]['subcategories'].append({'id':r[0],'categoryId':r[1],'name':r[2],'active':r[3],'order':r[4],'products':0})
            cur.execute("SELECT id,category_id,subcategory_id,name,active,display_order FROM mm_families ORDER BY category_id,COALESCE(display_order,2147483647),name")
            for r in cur.fetchall():
                by[r[1]]['families'].append({'id':r[0],'categoryId':r[1],'subcategoryId':r[2],'name':r[3],'active':r[4],'order':r[5],'products':0})

            # Contagens reais por classificação. RIDA usa a classificação RIDA;
            # as restantes categorias usam a classificação comercial.
            cur.execute("""
                SELECT pc.classification_type,pc.category_id,pc.subcategory_id,pc.family_id,
                       COUNT(DISTINCT pc.product_id)
                FROM mm_product_classifications pc
                JOIN catalog_products p ON p.id=pc.product_id
                WHERE p.active IS DISTINCT FROM FALSE
                  AND pc.classification_type IN ('commercial','rida')
                GROUP BY pc.classification_type,pc.category_id,pc.subcategory_id,pc.family_id
            """)
            counts={}
            for typ,cid,sid,fid,n in cur.fetchall():
                counts[(typ,cid,sid,fid)]=int(n or 0)

            cur.execute("SELECT id,name,kind,parent_id FROM catalog_categories")
            canonical={r[0]:(r[1],r[2],r[3]) for r in cur.fetchall()}

            for cat in cats:
                cur.execute("SELECT id,name FROM catalog_categories WHERE kind='category' AND lower(name)=lower(%s) LIMIT 1",(cat['name'],))
                cc=cur.fetchone()
                if not cc: continue
                ctype='rida' if cat['name'].strip().lower()=='rida' else 'commercial'
                ccid=cc[0]
                cat['products']=sum(n for (typ,cid,sid,fid),n in counts.items()
                                    if typ==ctype and cid==ccid)

                for sub in cat['subcategories']:
                    csid=next((i for i,(nm,k,parent) in canonical.items()
                               if k=='subcategory' and parent==ccid and nm.lower()==sub['name'].lower()),None)
                    if csid is None: continue
                    sub['products']=sum(n for (typ,cid,sid,fid),n in counts.items()
                                        if typ==ctype and cid==ccid and sid==csid)

                for fam in cat['families']:
                    mm_sub_id=fam.get('subcategoryId')
                    mm_sub=next((s for s in cat['subcategories'] if s['id']==mm_sub_id),None)
                    if not mm_sub: continue
                    csid=next((i for i,(nm,k,parent) in canonical.items()
                               if k=='subcategory' and parent==ccid and nm.lower()==mm_sub['name'].lower()),None)
                    if csid is None: continue
                    cfid=next((i for i,(nm,k,parent) in canonical.items()
                               if k=='family' and parent==csid and nm.lower()==fam['name'].lower()),None)
                    if cfid is None: continue
                    fam['products']=sum(n for (typ,cid,sid,fid),n in counts.items()
                                        if typ==ctype and cid==ccid and fid==cfid)

            send_json(200,{'ok':True,'categories':cats,'count':len(cats)});return True
    except Exception as e:
        send_json(503,{'ok':False,'error':f'API taxonomia: {e}'});return True

def slugify(v):
    import unicodedata,re
    s=unicodedata.normalize('NFKD',clean(v)).encode('ascii','ignore').decode('ascii').lower()
    return re.sub(r'-+','-',re.sub(r'[^a-z0-9]+','-',s)).strip('-')

def canonical_node(cur,kind,name,parent_id=None):
    if parent_id is None:
        cur.execute("SELECT id,slug FROM catalog_categories WHERE kind=%s AND lower(name)=lower(%s) AND parent_id IS NULL LIMIT 1",(kind,name))
    else:
        cur.execute("SELECT id,slug FROM catalog_categories WHERE kind=%s AND lower(name)=lower(%s) AND parent_id=%s LIMIT 1",(kind,name,parent_id))
    return cur.fetchone()

def canonical_upsert(cur,kind,name,parent_id=None,active=True,old_id=None):
    old=None
    if old_id:
        cur.execute("SELECT id,name,parent_id FROM catalog_categories WHERE id=%s AND kind=%s",(old_id,kind));old=cur.fetchone()
    existing=canonical_node(cur,kind,name,parent_id)
    if existing and (not old or existing[0]==old[0]):
        cid=existing[0]
        cur.execute("UPDATE catalog_categories SET active=%s WHERE id=%s",(active,cid))
        return cid
    base=slugify(name)
    if parent_id:
        cur.execute("SELECT slug FROM catalog_categories WHERE id=%s",(parent_id,))
        p=cur.fetchone()
        if p and p[0]: base=p[0]+'-'+base
    slug=base or 'categoria'
    n=1
    while True:
        cur.execute("SELECT id FROM catalog_categories WHERE slug=%s AND (%s IS NULL OR id<>%s)",(slug,old_id,old_id))
        hit=cur.fetchone()
        if not hit: break
        n+=1;slug=f"{base}-{n}"
    if old:
        cur.execute("UPDATE catalog_categories SET name=%s,parent_id=%s,slug=%s,active=%s WHERE id=%s",(name,parent_id,slug,active,old[0]))
        return old[0]
    cur.execute("INSERT INTO catalog_categories(name,kind,parent_id,slug,active) VALUES(%s,%s,%s,%s,%s) RETURNING id",(name,kind,parent_id,slug,active))
    return cur.fetchone()[0]

def handle_post(path,body,send_json):
    if path!='/api/taxonomy': return False
    try:
        kind=clean(body.get('kind'));name=clean(body.get('name'))
        cid=int(body.get('categoryId') or 0) if str(body.get('categoryId') or '').isdigit() else 0
        sid=int(body.get('subcategoryId') or 0) if str(body.get('subcategoryId') or '').isdigit() else None
        if kind not in ('category','subcategory','family') or not name: raise ValueError('Tipo e nome são obrigatórios')
        with db() as conn,conn.cursor() as cur:
            ensure(cur)
            active=bool(body.get('active',True))
            if kind=='category':
                canonical_upsert(cur,'category',name,None,active)
                cur.execute("INSERT INTO mm_categories(name,description,icon,image,active,display_order) VALUES(%s,%s,%s,%s,%s,(SELECT COALESCE(MAX(display_order),0)+1 FROM mm_categories)) RETURNING id",(name,clean(body.get('description')),clean(body.get('icon')),clean(body.get('image')),active))
            elif kind=='subcategory':
                if not cid: raise ValueError('Categoria obrigatória')
                cur.execute("SELECT name FROM mm_categories WHERE id=%s",(cid,));z=cur.fetchone()
                if not z: raise ValueError('Categoria não encontrada')
                cur.execute("SELECT id FROM catalog_categories WHERE kind='category' AND lower(name)=lower(%s) AND active=true LIMIT 1",(z[0],));pc=cur.fetchone()
                if not pc: raise ValueError('Categoria canónica não encontrada')
                canonical_upsert(cur,'subcategory',name,pc[0],active)
                cur.execute("INSERT INTO mm_subcategories(category_id,name,active,display_order) VALUES(%s,%s,%s,(SELECT COALESCE(MAX(display_order),0)+1 FROM mm_subcategories WHERE category_id=%s)) RETURNING id",(cid,name,active,cid))
            else:
                if not cid: raise ValueError('Categoria obrigatória')
                if sid:
                    cur.execute("SELECT s.name,c.name FROM mm_subcategories s JOIN mm_categories c ON c.id=s.category_id WHERE s.id=%s",(sid,));z=cur.fetchone()
                else:
                    z=None
                if not z: raise ValueError('Subcategoria obrigatória')
                cur.execute("SELECT id FROM catalog_categories WHERE kind='category' AND lower(name)=lower(%s) AND active=true LIMIT 1",(z[1],));pc=cur.fetchone()
                cur.execute("SELECT id FROM catalog_categories WHERE kind='subcategory' AND lower(name)=lower(%s) AND parent_id=%s AND active=true LIMIT 1",(z[0],pc[0] if pc else 0));ps=cur.fetchone()
                if not ps: raise ValueError('Subcategoria canónica não encontrada')
                canonical_upsert(cur,'family',name,ps[0],active)
                cur.execute("INSERT INTO mm_families(category_id,subcategory_id,name,active,display_order) VALUES(%s,%s,%s,%s,(SELECT COALESCE(MAX(display_order),0)+1 FROM mm_families WHERE category_id=%s)) RETURNING id",(cid,sid,name,active,cid))
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
                cur.execute("SELECT name FROM mm_categories WHERE id=%s",(rid,));z=cur.fetchone()
                if not z: raise ValueError('Registo não encontrado')
                cur.execute("SELECT id FROM catalog_categories WHERE kind='category' AND lower(name)=lower(%s) LIMIT 1",(z[0],));cc=cur.fetchone()
                canonical_upsert(cur,'category',name,None,active,cc[0] if cc else None)
                cur.execute("UPDATE mm_categories SET name=%s,description=%s,icon=%s,image=%s,active=%s,updated_at=NOW() WHERE id=%s",(name,clean(body.get('description')),clean(body.get('icon')),clean(body.get('image')),active,rid))
            elif kind=='subcategory':
                cur.execute("SELECT s.name,c.name FROM mm_subcategories s JOIN mm_categories c ON c.id=s.category_id WHERE s.id=%s",(rid,));z=cur.fetchone()
                if not z: raise ValueError('Registo não encontrado')
                cur.execute("SELECT id FROM catalog_categories WHERE kind='category' AND lower(name)=lower(%s) LIMIT 1",(z[1],));pc=cur.fetchone()
                if not pc: raise ValueError('Categoria canónica não encontrada')
                cur.execute("SELECT id FROM catalog_categories WHERE kind='subcategory' AND lower(name)=lower(%s) AND parent_id=%s LIMIT 1",(z[0],pc[0]));old=cur.fetchone()
                canonical_upsert(cur,'subcategory',name,pc[0],active,old[0] if old else None)
                cur.execute("UPDATE mm_subcategories SET name=%s,active=%s,updated_at=NOW() WHERE id=%s",(name,active,rid))
            else:
                cur.execute("SELECT f.name,s.name,c.name FROM mm_families f JOIN mm_categories c ON c.id=f.category_id LEFT JOIN mm_subcategories s ON s.id=f.subcategory_id WHERE f.id=%s",(rid,));z=cur.fetchone()
                if not z: raise ValueError('Registo não encontrado')
                if not z[1]: raise ValueError('Subcategoria obrigatória')
                cur.execute("SELECT id FROM catalog_categories WHERE kind='category' AND lower(name)=lower(%s) LIMIT 1",(z[2],));pc=cur.fetchone()
                cur.execute("SELECT id FROM catalog_categories WHERE kind='subcategory' AND lower(name)=lower(%s) AND parent_id=%s LIMIT 1",(z[1],pc[0] if pc else 0));ps=cur.fetchone()
                if not ps: raise ValueError('Subcategoria canónica não encontrada')
                cur.execute("SELECT id FROM catalog_categories WHERE kind='family' AND lower(name)=lower(%s) AND parent_id=%s LIMIT 1",(z[0],ps[0]));old=cur.fetchone()
                canonical_upsert(cur,'family',name,ps[0],active,old[0] if old else None)
                nsid=int(body.get('subcategoryId')) if str(body.get('subcategoryId') or '').isdigit() else None
                cur.execute("UPDATE mm_families SET name=%s,subcategory_id=%s,active=%s,updated_at=NOW() WHERE id=%s",(name,nsid,active,rid))
            if cur.rowcount!=1: raise ValueError('Registo não encontrado')
            conn.commit();send_json(200,{'ok':True});return True
    except psycopg.errors.UniqueViolation:
        send_json(409,{'ok':False,'error':'Já existe um registo com esse nome neste nível.'});return True
    except ValueError as e:
        send_json(400,{'ok':False,'error':str(e)});return True
    except Exception as e:
        send_json(503,{'ok':False,'error':f'API taxonomia: {e}'});return True

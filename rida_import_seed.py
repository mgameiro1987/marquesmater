# MarquesMater — importação inicial RIDA extraída do Excel
# Gerado a partir do Excel RIDA fornecido no projeto.
# A carga é idempotente: executa uma única vez por import_key e não substitui stock já existente.
import os, json, gzip, base64
_PAYLOAD = """PLACEHOLDER"""

def run():
    if not os.environ.get('DATABASE_URL'):
        return {'ok': False, 'skipped': True, 'reason': 'DATABASE_URL não configurado'}
    import psycopg
    data=json.loads(gzip.decompress(base64.b64decode(_PAYLOAD)).decode('utf-8'))
    with psycopg.connect(os.environ['DATABASE_URL']) as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE TABLE IF NOT EXISTS mm_rida_imports (id BIGSERIAL PRIMARY KEY, import_key TEXT UNIQUE NOT NULL, imported_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), product_count INTEGER NOT NULL DEFAULT 0)")
            cur.execute("SELECT 1 FROM mm_rida_imports WHERE import_key=%s", ('rida_excel_v37_initial',))
            if cur.fetchone(): return {'ok': True, 'already': True, 'products': len(data)}
            cur.execute("CREATE TABLE IF NOT EXISTS mm_categories (id BIGSERIAL PRIMARY KEY,name TEXT NOT NULL UNIQUE,description TEXT NOT NULL DEFAULT '',icon TEXT NOT NULL DEFAULT '',active BOOLEAN NOT NULL DEFAULT TRUE,created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW())")
            cur.execute("CREATE TABLE IF NOT EXISTS mm_subcategories (id BIGSERIAL PRIMARY KEY,category_id BIGINT NOT NULL REFERENCES mm_categories(id) ON DELETE CASCADE,name TEXT NOT NULL,active BOOLEAN NOT NULL DEFAULT TRUE,created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),UNIQUE(category_id,name))")
            cur.execute("CREATE TABLE IF NOT EXISTS mm_families (id BIGSERIAL PRIMARY KEY,category_id BIGINT NOT NULL REFERENCES mm_categories(id) ON DELETE CASCADE,subcategory_id BIGINT REFERENCES mm_subcategories(id) ON DELETE SET NULL,name TEXT NOT NULL,active BOOLEAN NOT NULL DEFAULT TRUE,created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),UNIQUE(category_id,name))")
            cur.execute("CREATE TABLE IF NOT EXISTS mm_product_stock (sku TEXT PRIMARY KEY,stock INTEGER NOT NULL DEFAULT 0,stock_min INTEGER NOT NULL DEFAULT 0,updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW())")
            cur.execute("CREATE TABLE IF NOT EXISTS mm_stock_movements (id BIGSERIAL PRIMARY KEY,sku TEXT NOT NULL,movement_type TEXT NOT NULL,delta INTEGER NOT NULL,resulting_stock INTEGER NOT NULL,reason TEXT,notes TEXT,created_by TEXT NOT NULL DEFAULT 'MarquesMater',created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())")
            cur.execute("INSERT INTO mm_categories(name) VALUES(%s) ON CONFLICT(name) DO NOTHING", ('RIDA',))
            cur.execute("SELECT id FROM mm_categories WHERE name=%s", ('RIDA',)); cid=cur.fetchone()[0]
            subids={}
            for name in ('Construção','Jardim','Acessórios'):
                cur.execute("INSERT INTO mm_subcategories(category_id,name) VALUES(%s,%s) ON CONFLICT(category_id,name) DO NOTHING", (cid,name))
                cur.execute("SELECT id FROM mm_subcategories WHERE category_id=%s AND name=%s", (cid,name)); subids[name]=cur.fetchone()[0]
            cur.execute("INSERT INTO mm_families(category_id,name) VALUES(%s,%s) ON CONFLICT(category_id,name) DO NOTHING", (cid,'Máquinas a Bateria'))
            cur.execute("SELECT id FROM mm_families WHERE category_id=%s AND name=%s", (cid,'Máquinas a Bateria')); fid=cur.fetchone()[0]
            for p in data:
                attrs={'family':'Máquinas a Bateria','cost':p.get('cost',0),'vatRate':23}
                cur.execute("""INSERT INTO catalog_products (sku,brand,name,category,subcategory,type,price,old_price,stock,image,badge,description,options,specs,active,category_id,subcategory_id,family_id,brand_id,attributes,barcode,created_at,updated_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s,%s,%s,%s,%s::jsonb,%s,NOW(),NOW())
                ON CONFLICT (sku) DO UPDATE SET brand=EXCLUDED.brand,name=EXCLUDED.name,category=EXCLUDED.category,subcategory=EXCLUDED.subcategory,type=EXCLUDED.type,image=EXCLUDED.image,description=EXCLUDED.description,active=EXCLUDED.active,category_id=EXCLUDED.category_id,subcategory_id=EXCLUDED.subcategory_id,family_id=EXCLUDED.family_id,attributes=EXCLUDED.attributes,updated_at=NOW()""",
                (p['sku'],'RIDA',p['name'],'RIDA',p['subcategory'],p['type'],0,0,'',p.get('image',''),'RIDA',p['description'],'[]','[]',True,cid,subids[p['subcategory']],fid,None,json.dumps(attrs,ensure_ascii=False),None))
                cur.execute("SELECT stock FROM mm_product_stock WHERE sku=%s", (p['sku'],)); existing=cur.fetchone()
                if existing is None:
                    cur.execute("INSERT INTO mm_product_stock(sku,stock,stock_min) VALUES(%s,20,0)", (p['sku'],))
                    cur.execute("INSERT INTO mm_stock_movements(sku,movement_type,delta,resulting_stock,reason,notes) VALUES(%s,'entrada',20,20,%s,%s)", (p['sku'],'Importação inicial RIDA','Stock inicial de 20 unidades importado do Excel RIDA.'))
            cur.execute("INSERT INTO mm_rida_imports(import_key,product_count) VALUES(%s,%s)", ('rida_excel_v37_initial',len(data)))
        conn.commit()
    return {'ok': True, 'already': False, 'products': len(data), 'images': sum(bool(p.get('image')) for p in data), 'stock': len(data)*20}

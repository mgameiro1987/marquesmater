import os
import json

try:
    import psycopg
    from psycopg.types.json import Jsonb
except ImportError:
    psycopg = None
    Jsonb = None

ROOT = os.path.dirname(os.path.abspath(__file__))

SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
  id BIGSERIAL PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL DEFAULT '',
  phone TEXT NOT NULL DEFAULT '',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS customer_addresses (
  id BIGSERIAL PRIMARY KEY,
  customer_id BIGINT NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
  label TEXT NOT NULL DEFAULT 'Principal',
  data JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS customer_favorites (
  customer_id BIGINT NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
  sku TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (customer_id, sku)
);
CREATE TABLE IF NOT EXISTS customer_carts (
  customer_id BIGINT PRIMARY KEY REFERENCES customers(id) ON DELETE CASCADE,
  data JSONB NOT NULL DEFAULT '[]'::jsonb,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS orders (
  id BIGSERIAL PRIMARY KEY,
  customer_id BIGINT REFERENCES customers(id) ON DELETE SET NULL,
  data JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS catalog_products (
  id BIGSERIAL PRIMARY KEY,
  sku TEXT UNIQUE NOT NULL,
  brand TEXT NOT NULL DEFAULT '',
  name TEXT NOT NULL DEFAULT '',
  category TEXT NOT NULL DEFAULT '',
  subcategory TEXT NOT NULL DEFAULT '',
  type TEXT NOT NULL DEFAULT '',
  price NUMERIC(12,2) NOT NULL DEFAULT 0,
  old_price NUMERIC(12,2),
  stock TEXT NOT NULL DEFAULT 'Em stock',
  image TEXT NOT NULL DEFAULT '',
  badge TEXT NOT NULL DEFAULT '',
  description TEXT NOT NULL DEFAULT '',
  options JSONB NOT NULL DEFAULT '{}'::jsonb,
  specs JSONB NOT NULL DEFAULT '[]'::jsonb,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_catalog_category ON catalog_products(category);
CREATE INDEX IF NOT EXISTS idx_catalog_brand ON catalog_products(brand);
CREATE INDEX IF NOT EXISTS idx_orders_customer_created ON orders(customer_id, created_at DESC);

CREATE TABLE IF NOT EXISTS catalog_categories (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  parent_id BIGINT REFERENCES catalog_categories(id) ON DELETE SET NULL,
  kind TEXT NOT NULL DEFAULT 'category' CHECK (kind IN ('category','subcategory','family')),
  active BOOLEAN NOT NULL DEFAULT TRUE,
  sort_order INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS catalog_brands (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS catalog_attributes (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  slug TEXT UNIQUE NOT NULL,
  type TEXT NOT NULL DEFAULT 'select',
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS catalog_attribute_values (
  id BIGSERIAL PRIMARY KEY,
  attribute_id BIGINT NOT NULL REFERENCES catalog_attributes(id) ON DELETE CASCADE,
  value TEXT NOT NULL,
  slug TEXT NOT NULL,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  sort_order INTEGER NOT NULL DEFAULT 0,
  UNIQUE(attribute_id, slug)
);
ALTER TABLE catalog_products ADD COLUMN IF NOT EXISTS category_id BIGINT REFERENCES catalog_categories(id) ON DELETE SET NULL;
ALTER TABLE catalog_products ADD COLUMN IF NOT EXISTS subcategory_id BIGINT REFERENCES catalog_categories(id) ON DELETE SET NULL;
ALTER TABLE catalog_products ADD COLUMN IF NOT EXISTS family_id BIGINT REFERENCES catalog_categories(id) ON DELETE SET NULL;
ALTER TABLE catalog_products ADD COLUMN IF NOT EXISTS brand_id BIGINT REFERENCES catalog_brands(id) ON DELETE SET NULL;
ALTER TABLE catalog_products ADD COLUMN IF NOT EXISTS attributes JSONB NOT NULL DEFAULT '{}'::jsonb;
CREATE INDEX IF NOT EXISTS idx_catalog_category_id ON catalog_products(category_id);
CREATE INDEX IF NOT EXISTS idx_catalog_subcategory_id ON catalog_products(subcategory_id);
CREATE INDEX IF NOT EXISTS idx_catalog_family_id ON catalog_products(family_id);
CREATE INDEX IF NOT EXISTS idx_catalog_brand_id ON catalog_products(brand_id);
"""


def get_conn():
    if not psycopg or not os.environ.get('DATABASE_URL'):
        return None
    return psycopg.connect(os.environ['DATABASE_URL'])


def slugify(value):
    import re
    import unicodedata
    s=unicodedata.normalize('NFKD',str(value or '')).encode('ascii','ignore').decode('ascii').lower()
    return re.sub(r'[^a-z0-9]+','-',s).strip('-') or 'item'


def sync_catalog_structure(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT DISTINCT category FROM catalog_products WHERE category<>''")
        for (name,) in cur.fetchall():
            cur.execute("INSERT INTO catalog_categories(name,slug,kind) VALUES(%s,%s,'category') ON CONFLICT(slug) DO NOTHING",(name,slugify(name)))
        cur.execute("SELECT DISTINCT brand FROM catalog_products WHERE brand<>''")
        for (name,) in cur.fetchall():
            cur.execute("INSERT INTO catalog_brands(name,slug) VALUES(%s,%s) ON CONFLICT(slug) DO NOTHING",(name,slugify(name)))
        cur.execute("SELECT DISTINCT category,subcategory FROM catalog_products WHERE subcategory<>''")
        for category,sub in cur.fetchall():
            cur.execute("SELECT id FROM catalog_categories WHERE slug=%s AND kind='category'",(slugify(category),)); parent=cur.fetchone()
            cur.execute("INSERT INTO catalog_categories(name,slug,parent_id,kind) VALUES(%s,%s,%s,'subcategory') ON CONFLICT(slug) DO NOTHING",(sub,slugify(f'{category}-{sub}'),parent[0] if parent else None))
        cur.execute("SELECT DISTINCT category,subcategory,type FROM catalog_products WHERE type<>''")
        for category,sub,family in cur.fetchall():
            cur.execute("SELECT id FROM catalog_categories WHERE slug=%s AND kind='subcategory'",(slugify(f'{category}-{sub}'),)); parent=cur.fetchone()
            cur.execute("INSERT INTO catalog_categories(name,slug,parent_id,kind) VALUES(%s,%s,%s,'family') ON CONFLICT(slug) DO NOTHING",(family,slugify(f'{category}-{sub}-{family}'),parent[0] if parent else None))
        cur.execute("""UPDATE catalog_products p SET category_id=c.id FROM catalog_categories c WHERE c.kind='category' AND c.slug=lower(regexp_replace(regexp_replace(p.category,'[^a-zA-Z0-9]+','-','g'),'^-+|-+$','','g')) AND p.category_id IS NULL""")
        cur.execute("""UPDATE catalog_products p SET brand_id=b.id FROM catalog_brands b WHERE b.slug=lower(regexp_replace(regexp_replace(p.brand,'[^a-zA-Z0-9]+','-','g'),'^-+|-+$','','g')) AND p.brand_id IS NULL""")
        cur.execute("""UPDATE catalog_products p SET subcategory_id=c.id FROM catalog_categories c WHERE c.kind='subcategory' AND c.slug=lower(regexp_replace(regexp_replace(p.category||'-'||p.subcategory,'[^a-zA-Z0-9]+','-','g'),'^-+|-+$','','g')) AND p.subcategory_id IS NULL""")
        cur.execute("""UPDATE catalog_products p SET family_id=c.id FROM catalog_categories c WHERE c.kind='family' AND c.slug=lower(regexp_replace(regexp_replace(p.category||'-'||p.subcategory||'-'||p.type,'[^a-zA-Z0-9]+','-','g'),'^-+|-+$','','g')) AND p.family_id IS NULL""")


def seed_catalog(conn):
    seed_path = os.path.join(ROOT, 'catalog_seed.json')
    if not os.path.isfile(seed_path):
        return 0
    with open(seed_path, 'r', encoding='utf-8') as f:
        products = json.load(f)
    with conn.cursor() as cur:
        cur.execute('SELECT COUNT(*) FROM catalog_products')
        if cur.fetchone()[0] != 0:
            return 0
        for p in products:
            cur.execute("""
                INSERT INTO catalog_products
                (sku,brand,name,category,subcategory,type,price,old_price,stock,image,badge,description,options,specs)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (sku) DO NOTHING
            """, (
                str(p.get('sku','')).strip(), str(p.get('brand','') or ''), str(p.get('name','') or ''),
                str(p.get('category','') or ''), str(p.get('subcategory','') or ''), str(p.get('type','') or ''),
                float(p.get('price') or 0), p.get('oldPrice'), str(p.get('stock','Em stock') or 'Em stock'),
                str(p.get('image','') or ''), str(p.get('badge','') or ''), str(p.get('description','') or ''),
                Jsonb(p.get('options') or {}) if Jsonb else json.dumps(p.get('options') or {}),
                Jsonb(p.get('specs') or []) if Jsonb else json.dumps(p.get('specs') or [])
            ))
    return len(products)


def ensure_variant_examples(conn):
    examples=[
      {
        'sku':'DEMO-VAR-SILICONE','brand':'Soudal','name':'EXEMPLO — Silicone: Cor igual, embalagem com preço diferente','category':'Selantes & Colas','subcategory':'Silicones','type':'sealant','price':3.50,'stock':'Em stock','image':'images/silicone.svg','description':'Exemplo de variantes: a cor não altera o preço; a embalagem altera o preço.','options':{
          'Cor':['Branco','Preto','Transparente'],'Embalagem':['300 ml','600 ml'],
          '__variant_config':{'version':2,'mode':'combination','pricing':'per-option-rule-plus-combination','basePrice':3.50,'attributes':[
            {'name':'Cor','values':['Branco','Preto','Transparente'],'priceMode':'none','valuePricing':{}},
            {'name':'Embalagem','values':['300 ml','600 ml'],'priceMode':'absolute','valuePricing':{'300 ml':3.50,'600 ml':5.20}}
          ],'variants':[]}
        },'specs':['Exemplo de configuração de variantes','Cor: não altera preço','Embalagem: preço próprio']
      },
      {
        'sku':'DEMO-VAR-RIDA-KIT','brand':'RIDA','name':'EXEMPLO — RIDA 20V: Máquina, Kit e Mala BMC','category':'RIDA','subcategory':'Berbequins e Aparafusadoras','type':'rida','price':89.90,'stock':'Em stock','image':'images/drill.svg','description':'Exemplo de combinação em que Kit e Bateria podem alterar o preço.','options':{
          'Kit':['Máquina','Máquina + 2 baterias + carregador','Kit + mala BMC'],'Bateria':['2 Ah','4 Ah','6 Ah'],
          '__variant_config':{'version':2,'mode':'combination','pricing':'per-option-rule-plus-combination','basePrice':89.90,'attributes':[
            {'name':'Kit','values':['Máquina','Máquina + 2 baterias + carregador','Kit + mala BMC'],'priceMode':'absolute','valuePricing':{'Máquina':89.90,'Máquina + 2 baterias + carregador':139.90,'Kit + mala BMC':159.90}},
            {'name':'Bateria','values':['2 Ah','4 Ah','6 Ah'],'priceMode':'delta','valuePricing':{'2 Ah':0,'4 Ah':20,'6 Ah':40}}
          ],'variants':[]}
        },'specs':['Exemplo de configuração de variantes','Kit: altera preço','Bateria: acréscimo']
      },
      {
        'sku':'DEMO-VAR-CAIXA','brand':'MarquesMater','name':'EXEMPLO — Caixa Organizadora: cores com o mesmo preço','category':'Casa','subcategory':'Organização','type':'home','price':8.90,'stock':'Em stock','image':'images/home.svg','description':'Exemplo de artigo em que a cor não altera o preço e o tamanho define o preço.','options':{
          'Cor':['Transparente','Preto'],'Tamanho':['5 L','12 L','25 L'],
          '__variant_config':{'version':2,'mode':'combination','pricing':'per-option-rule-plus-combination','basePrice':8.90,'attributes':[
            {'name':'Cor','values':['Transparente','Preto'],'priceMode':'none','valuePricing':{}},
            {'name':'Tamanho','values':['5 L','12 L','25 L'],'priceMode':'absolute','valuePricing':{'5 L':8.90,'12 L':12.90,'25 L':18.90}}
          ],'variants':[]}
        },'specs':['Exemplo de configuração de variantes','Cor: preço igual','Tamanho: preço próprio']
      }
    ]
    with conn.cursor() as cur:
        for p in examples:
            cur.execute('SELECT 1 FROM catalog_products WHERE sku=%s',(p['sku'],))
            if cur.fetchone():
                continue
            attrs=p['options']['__variant_config']['attributes']
            base=p['price']; generated=[{}]
            for a in attrs:
                generated=[{**r,a['name']:v} for r in generated for v in a['values']]
            for i,opts in enumerate(generated,1):
                price=base
                for a in attrs:
                    value=opts[a['name']]; mode=a.get('priceMode','none'); n=float(a.get('valuePricing',{}).get(value,0) or 0)
                    if mode=='absolute': price=n
                    elif mode=='delta': price+=n
                p['options']['__variant_config']['variants'].append({'id':f"{p['sku']}-V{i:02d}",'options':opts,'sku':f"{p['sku']}-V{i:02d}",'price':round(price,2),'oldPrice':None,'stockQty':10,'stock':'Em stock','weight':0,'image':p['image'],'active':True})
            cur.execute("""INSERT INTO catalog_products(sku,brand,name,category,subcategory,type,price,old_price,stock,image,badge,description,options,specs)
              VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT(sku) DO NOTHING""",
              (p['sku'],p['brand'],p['name'],p['category'],p['subcategory'],p['type'],p['price'],None,p['stock'],p['image'],'Exemplo',p['description'],Jsonb(p['options']) if Jsonb else json.dumps(p['options']),Jsonb(p['specs']) if Jsonb else json.dumps(p['specs'])))
    return len(examples)


def init_db():
    conn = get_conn()
    if not conn:
        return False
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(SCHEMA)
            seed_catalog(conn)
            sync_catalog_structure(conn)
            ensure_variant_examples(conn)
            sync_catalog_structure(conn)
        return True
    finally:
        conn.close()

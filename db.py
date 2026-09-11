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
"""


def get_conn():
    if not psycopg or not os.environ.get('DATABASE_URL'):
        return None
    return psycopg.connect(os.environ['DATABASE_URL'])


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


def init_db():
    conn = get_conn()
    if not conn:
        return False
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(SCHEMA)
            seed_catalog(conn)
        return True
    finally:
        conn.close()

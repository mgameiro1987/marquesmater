import os

try:
    import psycopg
except ImportError:
    psycopg = None

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
"""

def get_conn():
    if not psycopg or not os.environ.get('DATABASE_URL'):
        return None
    return psycopg.connect(os.environ['DATABASE_URL'])

def init_db():
    conn = get_conn()
    if not conn:
        return False
    with conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA)
    conn.close()
    return True

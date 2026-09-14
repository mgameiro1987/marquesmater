import os, json
from urllib.parse import parse_qs
import psycopg

def _db():
    url=os.environ.get('DATABASE_URL')
    if not url: raise RuntimeError('DATABASE_URL não configurado no Render')
    return psycopg.connect(url)

def _ensure_barcode():
    with _db() as conn, conn.cursor() as cur:
        cur.execute("ALTER TABLE catalog_products ADD COLUMN IF NOT EXISTS barcode TEXT")
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS catalog_products_barcode_uq ON catalog_products(barcode) WHERE barcode IS NOT NULL AND BTRIM(barcode)<>''")
        conn.commit()

def _valid_barcode(v):
    v=str(v or '').strip()
    if not v: return ''
    if not v.isdigit(): raise ValueError('O código de barras / EAN deve conter apenas números.')
    if len(v) not in (8,12,13,14): raise ValueError('Código de barras inválido: use EAN-8, UPC-12, EAN-13 ou EAN-14.')
    return v

def handle_get(path,query,send_json):
    if path!='/api/catalog/barcode': return False
    try:
        _ensure_barcode(); qs=parse_qs(query or ''); sku=str((qs.get('sku') or [''])[0]).strip()
        if not sku: send_json(400,{'ok':False,'error':'SKU obrigatório'}); return True
        with _db() as conn, conn.cursor() as cur:
            cur.execute('SELECT sku,barcode FROM catalog_products WHERE sku=%s LIMIT 1',(sku,)); row=cur.fetchone()
        if not row: send_json(404,{'ok':False,'error':'Produto não encontrado'}); return True
        send_json(200,{'ok':True,'sku':row[0],'barcode':row[1] or ''}); return True
    except Exception as e:
        send_json(503,{'ok':False,'error':f'API catálogo: {e}'}); return True

def handle_post(path,body,send_json):
    if path!='/api/catalog/barcode': return False
    try:
        _ensure_barcode(); sku=str(body.get('sku') or '').strip(); barcode=_valid_barcode(body.get('barcode'))
        if not sku: raise ValueError('SKU obrigatório')
        with _db() as conn, conn.cursor() as cur:
            cur.execute('SELECT id FROM catalog_products WHERE sku=%s LIMIT 1',(sku,)); row=cur.fetchone()
            if not row: raise ValueError('Produto não encontrado na base de dados')
            cur.execute('UPDATE catalog_products SET barcode=%s,updated_at=NOW() WHERE sku=%s',(barcode or None,sku)); conn.commit()
        send_json(200,{'ok':True,'sku':sku,'barcode':barcode}); return True
    except ValueError as e: send_json(400,{'ok':False,'error':str(e)}); return True
    except Exception as e:
        send_json(409 if 'duplicate key' in str(e).lower() else 503,{'ok':False,'error':'Código de barras já atribuído a outro produto.' if 'duplicate key' in str(e).lower() else f'API catálogo: {e}'}); return True

import os
from urllib.parse import parse_qs
import psycopg

def db():
    url = os.environ.get('DATABASE_URL')
    if not url:
        raise RuntimeError('DATABASE_URL não configurado')
    return psycopg.connect(url)

def _clean(v):
    return str(v or '').strip()

def handle_delete(path, query, send_json):
    if path != '/api/catalog/products':
        return False
    qs = parse_qs(query or '')
    sku = _clean((qs.get('sku') or [''])[0])
    pid = _clean((qs.get('id') or [''])[0])
    if not sku and not pid:
        send_json(400, {'ok': False, 'error': 'SKU ou ID obrigatório'})
        return True
    try:
        with db() as conn, conn.cursor() as cur:
            if pid:
                try:
                    pid_int = int(pid)
                except Exception:
                    send_json(400, {'ok': False, 'error': 'ID inválido'})
                    return True
                cur.execute('SELECT sku, name FROM catalog_products WHERE id=%s LIMIT 1', (pid_int,))
            else:
                cur.execute('SELECT sku, name FROM catalog_products WHERE sku=%s LIMIT 1', (sku,))
            row = cur.fetchone()
            if not row:
                send_json(404, {'ok': False, 'error': 'Produto não encontrado'})
                return True
            real_sku, name = row
            cur.execute('DELETE FROM mm_product_stock WHERE sku=%s', (real_sku,))
            cur.execute('DELETE FROM catalog_products WHERE sku=%s', (real_sku,))
            if cur.rowcount != 1:
                raise RuntimeError('Não foi possível apagar o produto')
            conn.commit()
        send_json(200, {'ok': True, 'sku': real_sku, 'name': name})
        return True
    except Exception as e:
        send_json(409, {'ok': False, 'error': f'Não foi possível apagar o produto: {e}'})
        return True

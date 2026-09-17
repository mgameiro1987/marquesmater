import os
import psycopg


def db():
    url = os.environ.get('DATABASE_URL')
    if not url:
        raise RuntimeError('DATABASE_URL não configurado no Render')
    return psycopg.connect(url)


def handle_delete(path, query, send_json):
    if path != '/api/catalog/products':
        return False
    try:
        from urllib.parse import parse_qs
        qs = parse_qs(query or '')
        sku = str((qs.get('sku') or [''])[0]).strip()
        product_id = str((qs.get('id') or [''])[0]).strip()
        if not sku and not product_id:
            send_json(400, {'ok': False, 'error': 'Indique o SKU ou ID do artigo a apagar'})
            return True
        with db() as conn, conn.cursor() as cur:
            if product_id:
                try:
                    pid = int(product_id)
                except Exception:
                    pid = None
                if pid:
                    cur.execute('SELECT id,sku,name FROM catalog_products WHERE id=%s LIMIT 1', (pid,))
                else:
                    cur.execute('SELECT id,sku,name FROM catalog_products WHERE sku=%s LIMIT 1', (sku,))
            else:
                cur.execute('SELECT id,sku,name FROM catalog_products WHERE sku=%s LIMIT 1', (sku,))
            row = cur.fetchone()
            if not row:
                send_json(404, {'ok': False, 'error': 'Artigo não encontrado'})
                return True
            pid, real_sku, name = row

            # Limpa dados auxiliares associados ao artigo antes da remoção definitiva.
            cur.execute('DELETE FROM mm_product_classifications WHERE product_id=%s', (pid,))
            cur.execute('DELETE FROM mm_product_stock WHERE sku=%s', (real_sku,))
            cur.execute('DELETE FROM mm_stock_movements WHERE sku=%s', (real_sku,))
            cur.execute('DELETE FROM catalog_products WHERE id=%s', (pid,))
            if cur.rowcount != 1:
                raise RuntimeError('O artigo não foi apagado')
            conn.commit()
        send_json(200, {'ok': True, 'id': pid, 'sku': real_sku, 'name': name, 'message': 'Artigo apagado com sucesso'})
        return True
    except Exception as e:
        send_json(409, {'ok': False, 'error': f'Não foi possível apagar o artigo: {e}'})
        return True

import json, re, time, html, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'data' / 'soudal_products.json'
UA = 'Mozilla/5.0 (compatible; MarquesMater-Soudal-Importer/1.0)'


def fetch(url, attempts=4):
    last = None
    for n in range(attempts):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'text/html,application/xhtml+xml,image/avif,image/webp,*/*'})
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read()
        except Exception as e:
            last = e
            time.sleep(2 + n * 2)
    raise RuntimeError(f'Falha ao obter {url}: {last}')


def absolute(base, value):
    value = html.unescape(value.strip())
    if value.startswith('//'):
        return 'https:' + value
    if value.startswith('/'):
        from urllib.parse import urljoin
        return urljoin(base, value)
    return value


def find_image(page_url, blob):
    text = blob.decode('utf-8', errors='ignore')
    patterns = [
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
        r'<img[^>]+src=["\']([^"\']+\.(?:jpg|jpeg|png|webp)(?:\?[^"\']*)?)["\']',
    ]
    for pat in patterns:
        m = re.search(pat, text, re.I)
        if m:
            u = absolute(page_url, m.group(1))
            if 'logo' not in u.lower() and 'icon' not in u.lower():
                return u
    raise RuntimeError(f'Não encontrei imagem principal em {page_url}')


def find_pdf(page_url, blob):
    text = blob.decode('utf-8', errors='ignore')
    urls = re.findall(r'(?:href|src)=["\']([^"\']+\.pdf(?:\?[^"\']*)?)["\']', text, re.I)
    if not urls:
        urls = re.findall(r'https?://[^"\'<> ]+\.pdf(?:\?[^"\'<> ]*)?', text, re.I)
    for raw in urls:
        u = absolute(page_url, raw)
        low = u.lower()
        if 'tds' in low or 'ficha' in low or 'document' in low or 'technical' in low:
            return u
    return absolute(page_url, urls[0]) if urls else None


def download(url, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    data = fetch(url)
    target.write_bytes(data)
    if target.stat().st_size < 1000:
        raise RuntimeError(f'Ficheiro demasiado pequeno: {target}')


def main():
    data = json.loads(CATALOG.read_text(encoding='utf-8'))
    products = data['products']
    for p in products:
        page = p['asset_page']
        print('A obter:', p['name'])
        blob = fetch(page)
        image_url = find_image(page, blob)
        pdf_url = find_pdf(page, blob)
        image_target = ROOT / p['asset_image']
        download(image_url, image_target)
        p['downloaded_image_url'] = image_url
        if pdf_url:
            pdf_target = ROOT / p['asset_doc']
            download(pdf_url, pdf_target)
            p['downloaded_doc_url'] = pdf_url
        else:
            print('AVISO: sem ficha PDF encontrada:', page)
        print('  imagem:', image_url)
        print('  ficha :', pdf_url or 'N/D')

    CATALOG.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    # Gera/atualiza a base SQLite que acompanha a versão do repositório.
    import sys
    sys.path.insert(0, str(ROOT))
    import server
    c = server.db()
    c.execute("INSERT OR IGNORE INTO brands(name) VALUES(?)", ('Soudal',))
    c.execute("INSERT OR IGNORE INTO categories(name,description,subcategories_json) VALUES(?,?,?)", ('Colas e Selantes', 'Colas, selantes, espumas adesivas e produtos Soudal.', '[\"Soudal\"]'))
    for p in products:
        server.put_product(c, p)
    c.commit()
    c.close()
    print(f'Base SQLite atualizada com {len(products)} produtos Soudal.')


if __name__ == '__main__':
    main()

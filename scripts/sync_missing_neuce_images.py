from pathlib import Path
import html
import json
import re
import sqlite3
import urllib.request
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets' / 'neuce'
OUT.mkdir(parents=True, exist_ok=True)


def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; MarquesMater/1.0)'})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), (r.headers.get('Content-Type') or '').lower()


def save(slug, data, content_type='', source_url=''):
    if len(data) < 5000:
        raise RuntimeError(f'Imagem inválida: {slug}')
    ext = '.png' if 'png' in content_type or source_url.lower().split('?')[0].endswith('.png') else '.jpg'
    path = OUT / f'{slug}{ext}'
    path.write_bytes(data)
    return f'assets/neuce/{path.name}'


def direct(slug, urls):
    last = None
    for url in urls:
        try:
            data, ct = fetch(url)
            rel = save(slug, data, ct, url)
            print('NEUCE OK', slug, url, '->', rel)
            return rel
        except Exception as exc:
            last = exc
    raise RuntimeError(f'Não foi possível obter {slug}: {last}')


def find_page(category_url, slug):
    data, _ = fetch(category_url)
    text = data.decode('utf-8', errors='ignore')
    hrefs = re.findall(r'href\s*=\s*["\']([^"\']+)["\']', text, re.I)
    for href in hrefs:
        u = urljoin(category_url, html.unescape(href))
        low = u.lower()
        if 'p180-p-' in low and slug.lower() in low:
            if not re.search(r'(selante|primario)', low):
                return u
    return ''


def image_from_page(slug, page):
    data, _ = fetch(page)
    text = data.decode('utf-8', errors='ignore')
    candidates = []
    candidates += re.findall(r'https?://www\.neuce\.com/files/products/[^"\'\s<>]+', text, re.I)
    candidates += re.findall(r'(?:src|data-src|content)\s*=\s*["\']([^"\']*?/files/products/[^"\']+)["\']', text, re.I)
    seen = set()
    for raw in candidates:
        u = html.unescape(raw)
        if u.startswith('/'):
            u = urljoin(page, u)
        if u in seen:
            continue
        seen.add(u)
        try:
            data, ct = fetch(u)
            rel = save(slug, data, ct, u)
            print('NEUCE PAGE OK', slug, u, '->', rel)
            return rel
        except Exception:
            pass
    raise RuntimeError(f'Imagem oficial não encontrada na página {page}')


# IDs/páginas oficiais. SuperNeuce é 883; BelNeuce é tentado como 880 e tem fallback por página.
paths = {}
paths['superneuce'] = direct('superneuce', [
    'https://www.neuce.com/files/products/883_1.jpg',
    'https://www.neuce.com/files/products/883_2.jpg',
])
try:
    paths['belneuce'] = direct('belneuce', [
        'https://www.neuce.com/files/products/880_1.jpg',
        'https://www.neuce.com/files/products/880_2.jpg',
    ])
except Exception:
    page = find_page('https://www.neuce.com/p179-cat-159-tinta-plastica-an_pt', 'belneuce')
    if not page:
        raise RuntimeError('Página oficial BelNeuce não encontrada')
    paths['belneuce'] = image_from_page('belneuce', page)

plio_page = find_page('https://www.neuce.com/p179-cat-161-fachada-se_pt', 'plioneuce')
if not plio_page:
    raise RuntimeError('Página oficial PlioNeuce de fachada não encontrada')
paths['plioneuce'] = image_from_page('plioneuce', plio_page)

# Atualizar o catálogo persistente para os três produtos que estavam sem imagem.
db = sqlite3.connect(ROOT / 'data' / 'catalog.db')
cur = db.cursor()
for slug, rel in paths.items():
    cur.execute('UPDATE products SET image=?, gallery_json=? WHERE slug=?', (rel, json.dumps([rel]), slug))
    if cur.rowcount != 1:
        raise RuntimeError(f'Produto não encontrado na base: {slug}')
    print('CATALOG OK', slug, rel)
db.commit()
db.close()

# Verificação final: os ficheiros e os registos têm de existir.
for slug, rel in paths.items():
    p = ROOT / rel
    if not p.is_file() or p.stat().st_size < 5000:
        raise RuntimeError(f'Imagem final em falta: {slug} -> {rel}')
print('NEUCE SYNC COMPLETE:', ', '.join(sorted(paths)))

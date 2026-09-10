import base64, hashlib, json, os, re, sqlite3, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets' / 'products'
ASSETS.mkdir(parents=True, exist_ok=True)
DB = ROOT / 'data' / 'catalog.db'
MAP_PATH = ASSETS / 'image-map.json'

IMAGE_RE = re.compile(r'https?://[^\s"\'<>\\]+?(?:\.(?:png|jpe?g|webp)(?:\?[^\s"\'<>\\]*)?)', re.I)

def clean_url(url):
    return url.rstrip('.,);]}')

def is_image_url(url):
    p = urllib.parse.urlparse(url)
    path = p.path.lower()
    return path.endswith(('.png', '.jpg', '.jpeg', '.webp')) or '/wp-content/uploads/' in path or '/files/products/' in path

def ext_from(url, content_type=''):
    ct = (content_type or '').split(';')[0].lower()
    if ct == 'image/jpeg': return '.jpg'
    if ct == 'image/png': return '.png'
    if ct == 'image/webp': return '.webp'
    e = Path(urllib.parse.urlparse(url).path).suffix.lower()
    return e if e in ('.jpg','.jpeg','.png','.webp') else '.jpg'

def download(url, mapping):
    url = clean_url(url)
    if not is_image_url(url): return None
    if url in mapping and (ROOT / mapping[url].lstrip('/')).exists(): return mapping[url]
    h = hashlib.sha1(url.encode()).hexdigest()[:12]
    req = urllib.request.Request(url, headers={'User-Agent':'MarquesMater image importer/1.0','Accept':'image/avif,image/webp,image/apng,image/*,*/*;q=0.8'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read()
            ct = r.headers.get('Content-Type','')
            final_url = r.geturl()
    except Exception as e:
        print(f'WARN download failed: {url} -> {e}')
        return None
    if not data or data[:20].lstrip().lower().startswith((b'<html', b'<!doctype', b'<head')):
        print(f'WARN non-image response: {url}')
        return None
    ext = ext_from(final_url or url, ct)
    name = h + ext
    out = ASSETS / name
    out.write_bytes(data)
    local = '/assets/products/' + name
    mapping[url] = local
    print(f'LOCAL {url} -> {local} ({len(data)} bytes)')
    return local

def replace_value(value, mapping):
    if isinstance(value, str):
        if value.startswith('http://') or value.startswith('https://'):
            return download(value, mapping) or value
        return value
    if isinstance(value, list):
        return [replace_value(x, mapping) for x in value]
    if isinstance(value, dict):
        return {k: replace_value(v, mapping) for k, v in value.items()}
    return value

def replace_urls_in_text(text, mapping):
    urls = list(dict.fromkeys(clean_url(x) for x in IMAGE_RE.findall(text)))
    for url in urls:
        local = download(url, mapping)
        if local:
            text = text.replace(url, local)
    return text

def process_text_files(mapping):
    exts = {'.html','.htm','.js','.json','.py','.css','.txt'}
    changed = 0
    for p in ROOT.rglob('*'):
        if not p.is_file() or p == MAP_PATH or p.is_relative_to(ROOT/'.git'):
            continue
        if p.suffix.lower() not in exts:
            continue
        try: text = p.read_text(encoding='utf-8')
        except Exception: continue
        new = replace_urls_in_text(text, mapping)
        if new != text:
            p.write_text(new, encoding='utf-8')
            changed += 1
            print('PATCHED', p.relative_to(ROOT))
    return changed

def process_db(mapping):
    if not DB.exists():
        print('No catalog.db found; skipping DB localization')
        return 0
    con = sqlite3.connect(DB)
    cur = con.cursor()
    changed = 0
    try:
        rows = cur.execute('SELECT slug,image,gallery_json,variants_json,related_json FROM products').fetchall()
    except Exception as e:
        print('DB read error:', e); con.close(); return 0
    for slug,image,gallery_json,variants_json,related_json in rows:
        vals = [image,gallery_json,variants_json,related_json]
        originals = list(vals)
        # Main image is plain text.
        if isinstance(image,str) and image.startswith(('http://','https://')):
            vals[0] = download(image, mapping) or image
        for idx in range(1,4):
            raw = vals[idx]
            if not raw: continue
            try:
                obj = json.loads(raw)
            except Exception:
                obj = raw
            obj2 = replace_value(obj, mapping)
            vals[idx] = json.dumps(obj2, ensure_ascii=False) if not isinstance(obj2,str) else obj2
        if vals != originals:
            cur.execute('UPDATE products SET image=?,gallery_json=?,variants_json=?,related_json=?,updated_at=CURRENT_TIMESTAMP WHERE slug=?', (*vals, slug))
            changed += 1
    con.commit(); con.close()
    print(f'DB products updated: {changed}')
    return changed

def main():
    mapping = {}
    if MAP_PATH.exists():
        try: mapping.update(json.loads(MAP_PATH.read_text(encoding='utf-8')))
        except Exception: pass
    db_changed = process_db(mapping)
    text_changed = process_text_files(mapping)
    MAP_PATH.write_text(json.dumps(dict(sorted(mapping.items())), ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Image localization complete. map={len(mapping)}, db={db_changed}, text={text_changed}')

if __name__ == '__main__':
    main()

import hashlib, json, re, sqlite3, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets' / 'products'
ASSETS.mkdir(parents=True, exist_ok=True)
DB = ROOT / 'data' / 'catalog.db'
MAP_PATH = ASSETS / 'image-map.json'
IMAGE_RE = re.compile(r'https?://[^\s"\'<>\\]+?(?:\.(?:png|jpe?g|webp)(?:\?[^\s"\'<>\\]*)?)', re.I)

def clean_url(url): return url.rstrip('.,);]}')

def is_image_url(url):
    p = urllib.parse.urlparse(url); path = p.path.lower()
    return path.endswith(('.png','.jpg','.jpeg','.webp')) or '/wp-content/uploads/' in path or '/files/products/' in path or '/cdn/shop/files/' in path

def ext_from(url, content_type=''):
    ct=(content_type or '').split(';')[0].lower()
    if ct=='image/jpeg': return '.jpg'
    if ct=='image/png': return '.png'
    if ct=='image/webp': return '.webp'
    e=Path(urllib.parse.urlparse(url).path).suffix.lower()
    return e if e in ('.jpg','.jpeg','.png','.webp') else '.jpg'

def download(url, mapping):
    url=clean_url(url)
    if not is_image_url(url): return None
    if url in mapping and (ROOT/mapping[url].lstrip('/')).exists(): return mapping[url]
    h=hashlib.sha1(url.encode()).hexdigest()[:12]
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; MarquesMater/1.0)','Accept':'image/avif,image/webp,image/apng,image/*,*/*;q=0.8'})
    try:
        with urllib.request.urlopen(req,timeout=15) as r:
            data=r.read(); ct=r.headers.get('Content-Type',''); final_url=r.geturl()
    except Exception as e:
        print(f'WARN download failed: {url} -> {e}'); return None
    if not data or data[:40].lstrip().lower().startswith((b'<html',b'<!doctype',b'<head')):
        print(f'WARN non-image response: {url}'); return None
    name=h+ext_from(final_url or url,ct); out=ASSETS/name; out.write_bytes(data)
    local='/assets/products/'+name; mapping[url]=local
    print(f'LOCAL {url} -> {local} ({len(data)} bytes)'); return local

def scrape_product_image(slug, mapping):
    if not slug: return None
    page=f'https://www.marquesmater.pt/novo/produto/{slug}/'
    try:
        req=urllib.request.Request(page,headers={'User-Agent':'Mozilla/5.0 (compatible; MarquesMater/1.0)'})
        with urllib.request.urlopen(req,timeout=15) as r: html=r.read().decode('utf-8','ignore')
    except Exception as e:
        print(f'WARN product page failed {slug}: {e}'); return None
    candidates=[]
    patterns=[
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
        r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)',
        r'<img[^>]+class=["\'][^"\']*wp-post-image[^"\']*["\'][^>]+src=["\']([^"\']+)'
    ]
    for pat in patterns: candidates += re.findall(pat,html,re.I)
    for candidate in candidates:
        candidate=urllib.parse.urljoin(page,candidate)
        local=download(candidate,mapping)
        if local:
            print(f'FALLBACK {slug} -> {local}')
            return local
    return None

def replace_value(value,mapping):
    if isinstance(value,str):
        if value.startswith(('http://','https://')): return download(value,mapping) or value
        return value
    if isinstance(value,list): return [replace_value(x,mapping) for x in value]
    if isinstance(value,dict): return {k:replace_value(v,mapping) for k,v in value.items()}
    return value

def process_db(mapping):
    if not DB.exists(): return 0
    con=sqlite3.connect(DB); cur=con.cursor(); changed=0
    rows=cur.execute('SELECT slug,image,gallery_json,variants_json,related_json FROM products').fetchall()
    for slug,image,gallery_json,variants_json,related_json in rows:
        vals=[image,gallery_json,variants_json,related_json]; originals=list(vals)
        if isinstance(image,str) and image.startswith(('http://','https://')):
            vals[0]=download(image,mapping)
            if not vals[0]: vals[0]=scrape_product_image(slug,mapping) or image
        for idx in range(1,4):
            raw=vals[idx]
            if not raw: continue
            try: obj=json.loads(raw)
            except Exception: obj=raw
            obj2=replace_value(obj,mapping)
            # If gallery still points to a broken remote URL, use the product main image as position 1.
            if idx==1 and isinstance(obj2,list) and obj2 and isinstance(obj2[0],str) and obj2[0].startswith(('http://','https://')) and vals[0].startswith('/assets/'):
                obj2[0]=vals[0]
            vals[idx]=json.dumps(obj2,ensure_ascii=False) if not isinstance(obj2,str) else obj2
        if vals!=originals:
            cur.execute('UPDATE products SET image=?,gallery_json=?,variants_json=?,related_json=?,updated_at=CURRENT_TIMESTAMP WHERE slug=?',(*vals,slug)); changed+=1
    con.commit(); con.close(); print(f'DB products updated: {changed}'); return changed

def process_catalog_slugs(mapping):
    p=ROOT/'catalogo.html'
    if not p.exists(): return 0
    text=p.read_text(encoding='utf-8'); changed=0
    # Localize hard-coded catalogue product images using the current MarquesMater product page as fallback.
    pat=re.compile(r'\{"slug":"([^"]+)"(?:(?!\}\]).)*?"image":"(https?://[^"\\]+)"',re.S)
    for slug,url in list(pat.findall(text)):
        local=mapping.get(clean_url(url))
        if not local: local=scrape_product_image(slug,mapping)
        if local:
            text=text.replace(url,local); changed+=1
    if changed: p.write_text(text,encoding='utf-8')
    print(f'Catalogue products localized: {changed}'); return changed

def replace_urls_in_text(text,mapping):
    for url in list(dict.fromkeys(clean_url(x) for x in IMAGE_RE.findall(text))):
        local=download(url,mapping)
        if local: text=text.replace(url,local)
    return text

def process_text_files(mapping):
    exts={'.html','.htm','.js','.json','.py','.css','.txt'}; changed=0
    for p in ROOT.rglob('*'):
        if not p.is_file() or p==MAP_PATH or p.is_relative_to(ROOT/'.git') or p.name=='catalog.db': continue
        if p.suffix.lower() not in exts: continue
        try: text=p.read_text(encoding='utf-8')
        except Exception: continue
        new=replace_urls_in_text(text,mapping)
        if new!=text: p.write_text(new,encoding='utf-8'); changed+=1; print('PATCHED',p.relative_to(ROOT))
    return changed

def main():
    mapping={}
    if MAP_PATH.exists():
        try: mapping.update(json.loads(MAP_PATH.read_text(encoding='utf-8')))
        except Exception: pass
    db_changed=process_db(mapping)
    catalog_changed=process_catalog_slugs(mapping)
    text_changed=process_text_files(mapping)
    MAP_PATH.write_text(json.dumps(dict(sorted(mapping.items())),ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'Image localization complete. map={len(mapping)}, db={db_changed}, catalog={catalog_changed}, text={text_changed}')

if __name__=='__main__': main()

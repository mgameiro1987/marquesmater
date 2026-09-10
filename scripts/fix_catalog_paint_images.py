import hashlib, re, sqlite3, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets' / 'products'
ASSETS.mkdir(parents=True, exist_ok=True)
DB = ROOT / 'data' / 'catalog.db'
UA = 'Mozilla/5.0 (compatible; MarquesMater/1.0)'

PRODUCTS = {
    'aquaneuce': {'name':'AquaNeuce','direct':['https://www.neuce.com/files/products/885_1.jpg'],'pages':['https://www.marquesmater.pt/novo/produto/aquaneuce/','https://www.neuce.com/p180-p-885-aquaneuce-pt_pt']},
    'belneuce': {'name':'BelNeuce','direct':[],'pages':['https://www.marquesmater.pt/novo/produto/belneuce/','https://www.neuce.com/p179-cat-159-tinta-plastica-an_pt']},
    'hydroneuce': {'name':'HydroNeuce','direct':['https://www.neuce.com/files/products/884_1.jpg'],'pages':['https://www.marquesmater.pt/novo/produto/hydroneuce/','https://www.neuce.com/p180-p-884-hydroneuce-primario-pt_pt']},
    'neucegold-ng': {'name':'NeuceGold NG','direct':['https://www.neuce.com/files/products/1128_1.png'],'pages':['https://www.marquesmater.pt/novo/produto/neucegold-ng/','https://www.neuce.com/p180-p-1128-neucegold-ng-pt_pt']},
    'neucetext': {'name':'NeuceText','direct':[],'pages':['https://www.marquesmater.pt/novo/produto/neucetext/','https://www.neuce.com/p179-cat-160-tinta-texturada-pt_pt']},
    'plioneuce': {'name':'PlioNeuce','direct':['https://www.neuce.com/files/products/898_1.jpg'],'pages':['https://www.marquesmater.pt/novo/produto/plioneuce/','https://www.neuce.com/p180-p-898-plioneuce-primario-pt_pt']},
    'primaneuce': {'name':'PrimaNeuce','direct':['https://www.neuce.com/files/products/1029_1.jpg'],'pages':['https://www.marquesmater.pt/novo/produto/primaneuce/','https://www.neuce.com/p180-p-1029-primaneuce-co_pt']},
    'superneuce': {'name':'SuperNeuce','direct':[],'pages':['https://www.marquesmater.pt/novo/produto/superneuce/','https://www.neuce.com/p179-cat-159-tinta-plastica-an_pt']},
    'superneuce-sn': {'name':'SuperNeuce SN','direct':['https://www.neuce.com/files/products/1144_1.jpg'],'pages':['https://www.marquesmater.pt/novo/produto/superneuce-sn/','https://www.neuce.com/p180-p-1144-superneuce-sn-ni_pt']},
    'textuneuce': {'name':'TextuNeuce','direct':['https://www.neuce.com/files/products/894_1.jpg'],'pages':['https://www.marquesmater.pt/novo/produto/textuneuce/','https://www.neuce.com/p180-p-894-textuneuce-pt_pt']},
    'woodneuce': {'name':'WoodNeuce','direct':['https://www.neuce.com/files/products/934_1.jpg'],'pages':['https://www.marquesmater.pt/novo/produto/woodneuce/','https://www.neuce.com/p180-p-934-woodneuce-mo_en']},
}


def fetch(url):
    try:
        req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'text/html,application/xhtml+xml'})
        with urllib.request.urlopen(req,timeout=20) as r:return r.read().decode('utf-8','ignore'),r.geturl()
    except Exception as e:
        print('WARN page',url,e); return None,url


def image_candidates(html,base):
    out=[]
    for pat in [r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)',r'<img[^>]+(?:src|data-src)=["\']([^"\']+)["\']',r'https?://[^"\'<> ]+/files/products/[^"\'<> ]+']:
        out += re.findall(pat,html,re.I)
    scored=[]
    for x in out:
        x=urllib.parse.urljoin(base,x).replace('&amp;','&'); xl=x.lower(); score=0
        if '/files/products/' in xl: score+=100
        if '/wp-content/uploads/' in xl: score+=80
        if any(z in xl for z in ('logo','icon','favicon','bg-','banner')): score-=100
        if re.search(r'\.(png|jpe?g|webp)(?:\?|$)',xl): score+=10
        scored.append((score,x))
    return [x for _,x in sorted(set(scored),key=lambda z:-z[0])]


def download(url,slug):
    try:
        req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'image/avif,image/webp,image/apng,image/*,*/*;q=0.8'})
        with urllib.request.urlopen(req,timeout=20) as r:
            data=r.read(); ct=(r.headers.get('Content-Type') or '').lower(); final=r.geturl()
        if len(data)<1000 or b'<html' in data[:500].lower() or b'<!doctype' in data[:500].lower(): return None
        if 'image/' not in ct and not re.search(r'\.(png|jpe?g|webp)(?:\?|$)',final,re.I): return None
        ext='.png' if 'png' in ct or '.png' in final.lower() else '.webp' if 'webp' in ct or '.webp' in final.lower() else '.jpg'
        name=hashlib.sha1((slug+'|'+url).encode()).hexdigest()[:12]+ext; out=ASSETS/name; out.write_bytes(data)
        local='/assets/products/'+name; print('LOCAL',slug,'->',local,len(data),'bytes'); return local
    except Exception as e:
        print('WARN image',slug,url,e); return None


def scrape(slug,info):
    for url in info.get('direct',[]):
        local=download(url,slug)
        if local:return local
    for page in info['pages']:
        h,final=fetch(page)
        if not h:continue
        candidates=image_candidates(h,final)
        pos=h.lower().find(info['name'].lower())
        if pos>=0:candidates=image_candidates(h[max(0,pos-7000):pos+7000],final)+candidates
        for url in candidates:
            local=download(url,slug)
            if local:return local
    return None


def update_db(slug,local):
    if not DB.exists(): return False
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row
    try:
        r=c.execute('SELECT gallery_json FROM products WHERE slug=?',(slug,)).fetchone()
        if not r:return False
        try: gallery=__import__('json').loads(r['gallery_json'] or '[]')
        except: gallery=[]
        gallery=[x for x in gallery if x!=local and not (isinstance(x,str) and x.startswith('http'))]
        gallery.insert(0,local)
        c.execute('UPDATE products SET image=?, gallery_json=?, updated_at=CURRENT_TIMESTAMP WHERE slug=?',(local,__import__('json').dumps(gallery,ensure_ascii=False),slug))
        c.commit(); print('DB',slug,'->',local); return True
    finally:c.close()


def main():
    updated=0
    for slug,info in PRODUCTS.items():
        local=scrape(slug,info)
        if local and update_db(slug,local): updated+=1
    print('NEUCE local images saved in DB:',updated)

if __name__=='__main__':main()

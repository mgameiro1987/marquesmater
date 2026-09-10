import hashlib, re, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets' / 'products'
ASSETS.mkdir(parents=True, exist_ok=True)
CATALOG = ROOT / 'catalogo.html'
UA = 'Mozilla/5.0 (compatible; MarquesMater/1.0)'

PRODUCTS = {
    'aquaneuce': {
        'name': 'AquaNeuce',
        'pages': ['https://www.marquesmater.pt/novo/produto/aquaneuce/', 'https://www.neuce.com/p180-p-885-aquaneuce-pt_pt']},
    'belneuce': {
        'name': 'BelNeuce',
        'pages': ['https://www.marquesmater.pt/novo/produto/belneuce/', 'https://www.neuce.com/p179-cat-159-tinta-plastica-an_pt']},
    'hydroneuce': {
        'name': 'HydroNeuce',
        'pages': ['https://www.marquesmater.pt/novo/produto/hydroneuce/', 'https://www.neuce.com/p180-p-884-hydroneuce-primario-pt_pt']},
    'neucegold-ng': {
        'name': 'NeuceGold NG',
        'pages': ['https://www.marquesmater.pt/novo/produto/neucegold-ng/', 'https://www.neuce.com/p180-p-1128-neucegold-ng-pt_pt']},
    'neucetext': {
        'name': 'NeuceText',
        'pages': ['https://www.marquesmater.pt/novo/produto/neucetext/', 'https://www.neuce.com/p179-cat-160-tinta-texturada-pt_pt']},
    'plioneuce': {
        'name': 'PlioNeuce',
        'pages': ['https://www.marquesmater.pt/novo/produto/plioneuce/', 'https://www.neuce.com/p180-p-898-plioneuce-primario-pt_pt']},
    'primaneuce': {
        'name': 'PrimaNeuce',
        'pages': ['https://www.marquesmater.pt/novo/produto/primaneuce/', 'https://www.neuce.com/p180-p-1029-primaneuce-co_pt']},
    'superneuce': {
        'name': 'SuperNeuce',
        'pages': ['https://www.marquesmater.pt/novo/produto/superneuce/', 'https://www.neuce.com/p179-cat-159-tinta-plastica-an_pt']},
    'superneuce-sn': {
        'name': 'SuperNeuce SN',
        'pages': ['https://www.marquesmater.pt/novo/produto/superneuce-sn/', 'https://www.neuce.com/p180-p-1144-superneuce-sn-ni_pt']},
    'textuneuce': {
        'name': 'TextuNeuce',
        'pages': ['https://www.marquesmater.pt/novo/produto/textuneuce/', 'https://www.neuce.com/p180-p-894-textuneuce-pt_pt']},
    'woodneuce': {
        'name': 'WoodNeuce',
        'pages': ['https://www.marquesmater.pt/novo/produto/woodneuce/', 'https://www.neuce.com/p180-p-934-woodneuce-mo_en']},
}


def fetch(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'text/html,application/xhtml+xml'})
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.read().decode('utf-8', 'ignore'), r.geturl()
    except Exception as e:
        print('WARN page', url, e)
        return None, url


def image_candidates(html, base):
    out = []
    patterns = [
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
        r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)',
        r'<img[^>]+(?:src|data-src)=["\']([^"\']+)["\']',
        r'https?://[^"\'<> ]+/files/products/[^"\'<> ]+',
    ]
    for pat in patterns:
        out += re.findall(pat, html, re.I)
    # Prefer NEUCE product assets, then normal image URLs.
    scored = []
    for x in out:
        x = urllib.parse.urljoin(base, x).replace('&amp;', '&')
        xl = x.lower()
        score = 0
        if '/files/products/' in xl: score += 100
        if '/wp-content/uploads/' in xl: score += 80
        if 'og:image' in xl: score += 10
        if any(z in xl for z in ('logo','icon','favicon','bg-','banner')): score -= 100
        if re.search(r'\.(png|jpe?g|webp)(?:\?|$)', xl): score += 10
        scored.append((score, x))
    return [x for _, x in sorted(set(scored), key=lambda z: -z[0])]


def download(url, slug):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8'})
        with urllib.request.urlopen(req, timeout=25) as r:
            data = r.read(); ct = (r.headers.get('Content-Type') or '').lower(); final = r.geturl()
        if not data or b'<html' in data[:500].lower() or b'<!doctype' in data[:500].lower():
            return None
        if 'image/' not in ct and not re.search(r'\.(png|jpe?g|webp)(?:\?|$)', final, re.I):
            return None
        ext = '.png' if 'png' in ct or '.png' in final.lower() else '.webp' if 'webp' in ct or '.webp' in final.lower() else '.jpg'
        name = hashlib.sha1((slug + '|' + url).encode()).hexdigest()[:12] + ext
        out = ASSETS / name
        out.write_bytes(data)
        print('LOCAL', slug, '->', '/assets/products/' + name, len(data), 'bytes')
        return '/assets/products/' + name
    except Exception as e:
        print('WARN image', slug, url, e)
        return None


def scrape(slug, info):
    for page in info['pages']:
        html, final = fetch(page)
        if not html: continue
        candidates = image_candidates(html, final)
        # For category pages, locate the product name and prioritize images nearby.
        pos = html.lower().find(info['name'].lower())
        if pos >= 0:
            nearby = html[max(0, pos-7000):pos+7000]
            candidates = image_candidates(nearby, final) + candidates
        for url in candidates:
            local = download(url, slug)
            if local:
                return local
    return None


def replace_catalog(slug, local):
    text = CATALOG.read_text(encoding='utf-8')
    pat = re.compile(r'(\{"slug":"' + re.escape(slug) + r'".*?"image":")([^"\\]+)(")', re.S)
    new, n = pat.subn(r'\1' + local + r'\3', text, count=1)
    if n and new != text:
        CATALOG.write_text(new, encoding='utf-8')
        print('CATALOG', slug, '->', local)
        return True
    return False


def main():
    changed = 0
    for slug, info in PRODUCTS.items():
        local = scrape(slug, info)
        if local and replace_catalog(slug, local):
            changed += 1
    print('Paint catalog images fixed:', changed)


if __name__ == '__main__':
    main()

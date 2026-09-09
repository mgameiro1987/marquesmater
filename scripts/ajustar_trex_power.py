from pathlib import Path
import json, sqlite3, subprocess

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'soudal_products.json'
DB = ROOT / 'data' / 'catalog.db'

# Imagens oficiais da Soudal Shop para cada embalagem/cor de T-Rex Power 290 ml.
IMAGES = {
    'Branco': ('assets/soudal/trex-power-290-branco.jpg', 'https://www.soudalshop.pt/cdn/shop/files/T-Rex_Power_96dpi_251x1181px_X_NR-32998_145082_09d0af68-e7d6-41ee-bb58-42114d8dbd0e.jpg?v=1768390083'),
    'Cinzento': ('assets/soudal/trex-power-290-cinzento.jpg', 'https://www.soudalshop.pt/cdn/shop/files/118693_346734-CARPI_T-Rex_Power_Grey_ES-PT_290ml_3a6dac32-ee27-45b2-bb1b-0c814c67c9db.jpg?v=1738171745'),
    'Preto': ('assets/soudal/trex-power-290-preto.jpg', 'https://www.soudalshop.pt/cdn/shop/files/121890_346735-CARPI_T-Rex_Power_Black_ES-PT_290ml_c6daec2d-83e2-49f6-8ac4-d76ea4c455f8.jpg?v=1738171746'),
    'Bege': ('assets/soudal/trex-power-290-bege.jpg', 'https://www.soudalshop.pt/cdn/shop/files/120896_346737-CARPI_T-Rex_Power_Beige_ES-PT_290ml_3a6d9baa-dac7-4b51-9f5d-b157aab10d63.jpg?v=1738171748'),
    'Terracota': ('assets/soudal/trex-power-290-terracota.jpg', 'https://www.soudalshop.pt/cdn/shop/files/122528_346736-CARPI_T-Rex_Power_Terracota_ES-PT_290ml_1927ae56-0d39-4bf1-ab5c-1a5dc0263a6e.jpg?v=1738171749'),
    'Transparente': ('assets/soudal/trex-power-290-transparente.jpg', 'https://www.soudalshop.pt/cdn/shop/files/131060_339424-CAR_T-Rex_Power_Clear_ES-PT_290ml_fd1fafe7-a662-4809-afb8-a4f3a688cf2b.jpg?v=1738171750'),
}


def download_images():
    for color, (local, url) in IMAGES.items():
        dest = ROOT / local
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists() and dest.stat().st_size > 5000:
            continue
        subprocess.run(['curl', '-L', '--fail', '--retry', '3', '--retry-delay', '2', '-A', 'Mozilla/5.0', url, '-o', str(dest)], check=True)


def update_data_and_db():
    data = json.loads(DATA.read_text(encoding='utf-8'))
    target = None
    for p in data.get('products', []):
        if 't-rex power' in p.get('name', '').lower() and '290ml' in p.get('name', '').lower():
            target = p
            break
    if not target:
        raise SystemExit('T-Rex Power 290ml não encontrado em soudal_products.json')

    target['price'] = 12.95
    target['price_display'] = '12,95 €'
    target['asset_image'] = IMAGES['Branco'][0]
    target['variants'] = []
    for color, (local, _url) in IMAGES.items():
        target['variants'].append({
            'label': f'290ml / {color}',
            'color': color,
            'price': 12.95,
            'image': local,
            'asset_image': local,
        })
    target['variant_images_local'] = {c: v[0] for c, v in IMAGES.items()}
    target['gallery_local'] = [v[0] for v in IMAGES.values()]
    DATA.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    db = sqlite3.connect(DB)
    slug = target.get('slug', '')
    variants = [
        {'name': c, 'color': c, 'label': c, 'price': 12.95, 'image': local}
        for c, (local, _url) in IMAGES.items()
    ]
    gallery = [v[0] for v in IMAGES.values()]
    db.execute('''UPDATE products SET price=?, price_display=?, image=?, gallery_json=?, variants_json=?, stock=?, updated_at=CURRENT_TIMESTAMP WHERE slug=?''',
               (12.95, '12,95 €', IMAGES['Branco'][0], json.dumps(gallery, ensure_ascii=False), json.dumps(variants, ensure_ascii=False), 1, slug))
    db.commit()
    db.close()


def add_before(path, marker, text, token):
    s = path.read_text(encoding='utf-8')
    if token in s:
        return
    path.write_text(s.replace(marker, text + marker, 1), encoding='utf-8')


def patch_product_page():
    path = ROOT / 'produto-wc.html'
    add_before(path, '</head>', '''<style id="MM_TrexPower290CSS">
.mm-trex-colors{display:flex;flex-wrap:wrap;gap:9px;margin-top:8px}.mm-trex-color{display:flex;align-items:center;gap:8px;border:1px solid #d6dbe0;background:#fff;border-radius:10px;padding:8px 11px;font-weight:800;cursor:pointer}.mm-trex-color.active{border-color:#f28c00;box-shadow:0 0 0 2px rgba(242,140,0,.14)}.mm-trex-dot{width:24px;height:24px;border-radius:50%;border:1px solid #c7ccd1;box-shadow:inset 0 0 0 2px #fff;flex:none}.mm-trex-pack-hidden{display:none!important}
</style>''', 'MM_TrexPower290CSS')
    add_before(path, '</body>', '''<script id="MM_TrexPower290JS">(function(){
let trex=null,selected=0;
function isTrex(){return /t-rex-power/i.test(new URLSearchParams(location.search).get('slug')||'')}
function esc2(s){return String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]))}
function imgFor(v){return '/'+String(v.image||v.asset_image||'').replace(/^\\//,'')}
function setMainImage(v){const src=imgFor(v);if(!src||src==='/')return;const imgs=[...document.images];const candidates=imgs.filter(im=>{const r=im.getBoundingClientRect();const s=(im.currentSrc||im.src||'');return r.width>=120 && (s.includes('paint-placeholder')||s.includes('produto')||s.includes('soudal')||im.alt.toLowerCase().includes('t-rex')||im.alt.toLowerCase().includes('produto'))});const main=candidates[0]||imgs.find(im=>im.getBoundingClientRect().width>=220);if(main){main.src=src;main.removeAttribute('srcset');main.onerror=null}const thumbs=imgs.filter(im=>im!==main&&im.getBoundingClientRect().width>=40&&im.getBoundingClientRect().width<180&&((im.src||'').includes('paint-placeholder')));thumbs.slice(0,1).forEach(im=>{im.src=src;im.removeAttribute('srcset');im.onerror=null})}
function apply(){if(!trex)return;const title=document.querySelector('.variant-title');const grid=document.querySelector('.variant-grid');if(!title||!grid)return;title.textContent='Escolha a cor';grid.className='mm-trex-colors';grid.innerHTML=trex.variants.map((v,i)=>{let c=(v.color||'').toLowerCase(),bg='#fff';if(c.includes('preto'))bg='#171717';else if(c.includes('cinz'))bg='#9da3a8';else if(c.includes('bege'))bg='#d7c2a2';else if(c.includes('terracota'))bg='#b65c43';else if(c.includes('transpar'))bg='linear-gradient(135deg,#fff,#dfe8ef)';return '<button type="button" class="mm-trex-color '+(i===selected?'active':'')+'" data-i="'+i+'"><span class="mm-trex-dot" style="background:'+bg+'"></span>'+esc2(v.color)+'</button>'}).join('');grid.querySelectorAll('.mm-trex-color').forEach(b=>b.addEventListener('click',()=>{selected=Number(b.dataset.i);if(typeof window.selectVariant==='function'){try{window.selectVariant(selected)}catch(e){}}setTimeout(()=>{setMainImage(trex.variants[selected]);apply()},40)}));setMainImage(trex.variants[selected]);}
async function boot(){if(!isTrex())return;try{const r=await fetch('/data/soudal_products.json?x='+Date.now(),{cache:'no-store'});const d=await r.json();trex=(d.products||[]).find(p=>/t-rex-power/i.test(p.slug||'')||(/t-rex power/i.test(p.name||'')&&/290ml/i.test(p.name||'')));if(!trex)return;trex.variants=(trex.variants||[]).filter(v=>v.image||v.asset_image);if(!trex.variants.length)return;window.__MMTrexPower=trex;let tries=0;const timer=setInterval(()=>{apply();if(++tries>30)clearInterval(timer)},250)}catch(e){console.warn('T-Rex Power',e)}}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();</script>''', 'MM_TrexPower290JS')


def patch_catalog():
    path = ROOT / 'catalogo.html'
    add_before(path, '</body>', '''<style id="MM_TrexCatalogCSS">.mm-hide-soudal-card-info{display:none!important}</style><script id="MM_TrexCatalogJS">(function(){
async function run(){try{const r=await fetch('/data/soudal_products.json?x='+Date.now(),{cache:'no-store'});const d=await r.json();const names=(d.products||[]).map(p=>String(p.name||'').trim());const hide=()=>document.querySelectorAll('.product').forEach(card=>{const n=card.querySelector('h3')?.textContent?.trim()||'';if(names.includes(n)){card.querySelectorAll('.stock,.more,.availability').forEach(x=>{x.classList.add('mm-hide-soudal-card-info');x.remove()})}});hide();new MutationObserver(hide).observe(document.getElementById('grid')||document.body,{childList:true,subtree:true})}catch(e){console.warn(e)}}if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',run);else run()})();</script>''', 'MM_TrexCatalogJS')


def main():
    download_images()
    update_data_and_db()
    patch_product_page()
    patch_catalog()
    print('T-Rex Power 290ml atualizado para 12,95 €, com imagens locais por cor e sem embalagem/stock/Ver produto no cartão.')

if __name__ == '__main__':
    main()
''
/* MarquesMater V10.6 — sincronização central + promoções + variantes + estilo Front Office */
(()=>{
  const accountKey='mm_demo_account_data_v1';
  const accountFallback='mm_demo_account_v87';
  const storeKey='mm_store_v85';
  const catalogKey='mm_v10_catalog_central_v1';
  const variantConfig=p=>p?.options?.__variant_config||null;
  const exactVariant=(p,o)=>{const vs=variantConfig(p)?.variants||[];return vs.find(v=>{const a=v.options||{},keys=Object.keys(a);return keys.length===Object.keys(o||{}).length&&keys.every(k=>String(a[k])===String(o?.[k]))})||null};
  function patchStoreVariantPrice(){try{if(!window.MMStore||window.MMStore.__mm106v)return;if(typeof window.MMStore.variantPrice!=='function')return;const old=window.MMStore.variantPrice;window.MMStore.variantPrice=(p,o)=>{const v=exactVariant(p,o);if(v&&v.active!==false&&Number(v.price)>0)return Number(v.price);return old(p,o)};window.MMStore.__mm106v=true}catch(e){console.warn('V10.6 variante/preço indisponível',e)}}
  function buildVariantMaps(){try{const maps={};for(const p of (window.MARQUES_CATALOG||[])){const vs=variantConfig(p)?.variants||[];if(!vs.length)continue;maps[p.sku]={};for(const v of vs){for(const [k,val] of Object.entries(v.options||{})){maps[p.sku][k]=maps[p.sku][k]||{};if(v.active!==false&&Number(v.price)>0)maps[p.sku][k][val]=Number(v.price)}}}window.MM_VARIANT_PRICES={...(window.MM_VARIANT_PRICES||{}),...maps}}catch(e){console.warn('V10.6 mapa de variantes indisponível',e)}}
  function loadFrontOfficeStyle(){try{if(document.getElementById('mm-v106-frontoffice-css'))return;const l=document.createElement('link');l.id='mm-v106-frontoffice-css';l.rel='stylesheet';l.href='/css/v10.6-frontoffice.css?v=106';document.head.appendChild(l)}catch(e){console.warn('V10.6 estilo Front Office indisponível',e)}}
  function loadVariantEngine(){try{if(document.getElementById('mm-v106-variant-engine'))return;const s=document.createElement('script');s.id='mm-v106-variant-engine';s.src='/js/v10.6-variant-engine.js?v=106';document.body.appendChild(s)}catch(e){console.warn('V10.6 motor de variantes indisponível',e)}}
  patchStoreVariantPrice();
  const email=()=>{try{const a=JSON.parse(localStorage.getItem(accountKey)||'{}');if(a.email)return String(a.email).trim().toLowerCase();const b=JSON.parse(localStorage.getItem(accountFallback)||'{}');return String(b.email||'').trim().toLowerCase()}catch(e){return ''}};
  const api=async(path,method='GET',body)=>{const e=email();const r=await fetch(path,{method,headers:{'Content-Type':'application/json',...(e?{'X-Customer-Email':e}:{})},body:body?JSON.stringify(body):undefined,cache:'no-store'});if(!r.ok)throw new Error('API '+r.status);return r.json()};
  const state=()=>{try{return JSON.parse(localStorage.getItem(storeKey))||{favorites:[],cart:[]}}catch(e){return{favorites:[],cart:[]}}};
  const save=s=>localStorage.setItem(storeKey,JSON.stringify(s));
  async function loadPromoEngine(){try{if(window.MMPromotion)return;const s=document.createElement('script');s.src='/js/v10.5-promotions.js?v=105';s.onload=()=>window.dispatchEvent(new Event('mm-v10-promo-ready'));document.body.appendChild(s)}catch(e){console.warn('V10.5 promo engine indisponível',e)}}
  async function pullCatalog(){try{
    const r=await api('/api/catalog');
    if(r?.ok&&Array.isArray(r.catalog)&&r.catalog.length){
      const sig=JSON.stringify(r.catalog.map(p=>[p.sku,p.updated_at,p.price,p.oldPrice,p.stock,p.active,p.options?.__promo,p.options?.__variant_config,p.category_id,p.subcategory_id,p.family_id,p.brand_id,p.attributes]));
      const old=localStorage.getItem('mm_v10_catalog_sig_v1');
      localStorage.setItem(catalogKey,JSON.stringify(r.catalog));
      localStorage.setItem('mm_v9_catalog_override_v1',JSON.stringify(r.catalog));
      localStorage.setItem('mm_v10_catalog_sig_v1',sig);
      window.MARQUES_CATALOG=r.catalog;
      buildVariantMaps();patchStoreVariantPrice();
      window.dispatchEvent(new Event('mm-v10-variant-ready'));
      if(old&&old!==sig){window.dispatchEvent(new Event('mm-v10-catalog'));location.reload()}
      if(!old) window.dispatchEvent(new Event('mm-v10-catalog'));
    }
  }catch(e){console.warn('V10 catálogo central indisponível; mantém-se o catálogo local.',e)} }
  async function pullUser(){if(!email())return;try{
    const [c,f]=await Promise.all([api('/api/cart'),api('/api/favorites')]);
    if(c?.ok&&Array.isArray(c.cart)){const s=state();if(c.cart.length||!s.cart.length){s.cart=c.cart;save(s);}}
    if(f?.ok&&Array.isArray(f.favorites)){const s=state();if(f.favorites.length||!s.favorites.length){s.favorites=f.favorites;save(s);}}
    const a=JSON.parse(localStorage.getItem(accountKey)||'{}');await api('/api/customer','POST',a);
  }catch(e){console.warn('V10 BD indisponível; mantém-se o armazenamento local.',e)} }
  let last='';
  async function push(){if(!email())return;const s=state(),sig=JSON.stringify([s.cart,s.favorites]);if(sig===last)return;last=sig;try{await api('/api/cart','POST',{cart:s.cart});await api('/api/favorites','POST',{favorites:s.favorites});}catch(e){console.warn('V10 sincronização adiada.',e)}}
  async function boot(){loadFrontOfficeStyle();patchStoreVariantPrice();await pullCatalog();buildVariantMaps();patchStoreVariantPrice();loadVariantEngine();await loadPromoEngine();await pullUser();setInterval(push,2500);window.addEventListener('storage',()=>setTimeout(push,50));window.addEventListener('mm-v10-sync',()=>setTimeout(push,50));}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();

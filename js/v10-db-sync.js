/* MarquesMater V10.5 — sincronização central + motor de promoções */
(()=>{
  const accountKey='mm_demo_account_data_v1';
  const accountFallback='mm_demo_account_v87';
  const storeKey='mm_store_v85';
  const catalogKey='mm_v10_catalog_central_v1';
  const email=()=>{try{const a=JSON.parse(localStorage.getItem(accountKey)||'{}');if(a.email)return String(a.email).trim().toLowerCase();const b=JSON.parse(localStorage.getItem(accountFallback)||'{}');return String(b.email||'').trim().toLowerCase()}catch(e){return ''}};
  const api=async(path,method='GET',body)=>{const e=email();const r=await fetch(path,{method,headers:{'Content-Type':'application/json',...(e?{'X-Customer-Email':e}:{})},body:body?JSON.stringify(body):undefined,cache:'no-store'});if(!r.ok)throw new Error('API '+r.status);return r.json()};
  const state=()=>{try{return JSON.parse(localStorage.getItem(storeKey))||{favorites:[],cart:[]}}catch(e){return{favorites:[],cart:[]}}};
  const save=s=>localStorage.setItem(storeKey,JSON.stringify(s));
  async function loadPromoEngine(){try{if(window.MMPromotion)return;const s=document.createElement('script');s.src='/js/v10.5-promotions.js?v=105';s.onload=()=>window.dispatchEvent(new Event('mm-v10-promo-ready'));document.body.appendChild(s)}catch(e){console.warn('V10.5 promo engine indisponível',e)}}
  async function pullCatalog(){try{
    const r=await api('/api/catalog');
    if(r?.ok&&Array.isArray(r.catalog)&&r.catalog.length){
      const sig=JSON.stringify(r.catalog.map(p=>[p.sku,p.updated_at,p.price,p.oldPrice,p.stock,p.active,p.options?.__promo]));
      const old=localStorage.getItem('mm_v10_catalog_sig_v1');
      localStorage.setItem(catalogKey,JSON.stringify(r.catalog));
      localStorage.setItem('mm_v9_catalog_override_v1',JSON.stringify(r.catalog));
      localStorage.setItem('mm_v10_catalog_sig_v1',sig);
      window.MARQUES_CATALOG=r.catalog;
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
  async function boot(){await pullCatalog();await loadPromoEngine();await pullUser();setInterval(push,2500);window.addEventListener('storage',()=>setTimeout(push,50));window.addEventListener('mm-v10-sync',()=>setTimeout(push,50));}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();

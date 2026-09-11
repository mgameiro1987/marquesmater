/* MarquesMater V10 — ponte entre a conta local atual e a base central PostgreSQL. */
(()=>{
  const accountKey='mm_demo_account_data_v1';
  const accountFallback='mm_demo_account_v87';
  const storeKey='mm_store_v85';
  const account=()=>{try{return JSON.parse(localStorage.getItem(accountKey)||'{}')}catch(e){return{}}};
  const email=()=>{const a=account();if(a.email)return String(a.email).trim().toLowerCase();try{return String(JSON.parse(localStorage.getItem(accountFallback)||'{}').email||'').trim().toLowerCase()}catch(e){return ''}};
  const api=async(path,method='GET',body)=>{const e=email();if(!e)return null;const r=await fetch(path,{method,headers:{'Content-Type':'application/json','X-Customer-Email':e},body:body?JSON.stringify(body):undefined});if(!r.ok)throw new Error('API '+r.status);return r.json()};
  const state=()=>{try{return JSON.parse(localStorage.getItem(storeKey))||{favorites:[],cart:[]}}catch(e){return{favorites:[],cart:[]}}};
  const save=s=>localStorage.setItem(storeKey,JSON.stringify(s));
  async function pull(){if(!email())return;try{
    const [c,f]=await Promise.all([api('/api/cart'),api('/api/favorites')]);
    if(c?.ok && Array.isArray(c.cart) && c.cart.length){const s=state();s.cart=c.cart;save(s);window.MMStore?.sync?.();window.dispatchEvent(new Event('mm-v10-sync'));}
    if(f?.ok && Array.isArray(f.favorites) && f.favorites.length){const s=state();s.favorites=f.favorites;save(s);window.MMStore?.sync?.();window.dispatchEvent(new Event('mm-v10-sync'));}
    await api('/api/customer','POST',account());
  }catch(e){console.warn('V10 BD indisponível; mantém-se o armazenamento local.',e)} }
  let last='';
  async function push(){if(!email())return;const s=state(),sig=JSON.stringify([s.cart,s.favorites]);if(sig===last)return;last=sig;try{await api('/api/cart','POST',{cart:s.cart});await api('/api/favorites','POST',{favorites:s.favorites});}catch(e){console.warn('V10 sincronização adiada.',e)}}
  function boot(){setTimeout(pull,300);setInterval(push,2500);window.addEventListener('storage',()=>{setTimeout(push,50)});window.addEventListener('mm-v10-sync',()=>setTimeout(push,50));}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();

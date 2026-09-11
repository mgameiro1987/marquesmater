/* V10.1 — repõe as encomendas centrais na conta local para manter a interface atual compatível. */
(()=>{
 const key='mm_demo_account_data_v1',fallback='mm_demo_account_v87',orders='mm_orders_v87';
 function email(){try{const a=JSON.parse(localStorage.getItem(key)||'{}');if(a.email)return String(a.email).trim().toLowerCase();const b=JSON.parse(localStorage.getItem(fallback)||'{}');return String(b.email||'').trim().toLowerCase()}catch(e){return ''}}
 async function sync(){const e=email();if(!e)return;try{const r=await fetch('/api/orders',{headers:{'X-Customer-Email':e},cache:'no-store'}),j=await r.json();if(j?.ok&&Array.isArray(j.orders)){
   const mapped=j.orders.map(x=>x.data||{}).filter(Boolean);
   if(mapped.length){localStorage.setItem(orders,JSON.stringify(mapped));window.MMAccount?.render?.()}
 }}catch(err){console.warn('V10 encomendas centrais indisponíveis.',err)}}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(sync,700));else setTimeout(sync,700);
})();

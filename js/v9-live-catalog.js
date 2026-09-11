/* MarquesMater V10.1 — catálogo partilhado entre Backoffice e Front Office, persistido em PostgreSQL. */
(()=>{
  const KEY='mm_v9_catalog_override_v1';
  const CENTRAL='mm_v10_catalog_central_v1';
  const base=Array.isArray(window.MARQUES_CATALOG)?window.MARQUES_CATALOG:[];
  let saved=[];
  try{ saved=JSON.parse(localStorage.getItem(CENTRAL)||localStorage.getItem(KEY)||'[]'); }catch(e){ saved=[]; }
  if(Array.isArray(saved)&&saved.length){
    const map=new Map(base.map(p=>[String(p.sku),p]));
    saved.forEach(p=>{if(p&&p.sku)map.set(String(p.sku),p);});
    window.MARQUES_CATALOG=Array.from(map.values());
  }
  window.MM_V9_CATALOG_KEY=KEY;
  const persistLocal=items=>{localStorage.setItem(KEY,JSON.stringify(items));localStorage.setItem(CENTRAL,JSON.stringify(items));window.MARQUES_CATALOG=items;return items};
  const apiSave=p=>{fetch('/api/catalog',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(p)}).catch(e=>console.warn('Catálogo central: alteração local mantida; sincronização pendente.',e))};
  window.MM_V9_CATALOG={
    all:()=>Array.isArray(window.MARQUES_CATALOG)?window.MARQUES_CATALOG:[],
    save:(items)=>{
      const clean=(items||[]).filter(p=>p&&p.sku).map(p=>({...p}));
      persistLocal(clean); clean.forEach(apiSave); return clean;
    },
    upsert:(product)=>{
      const items=[...((window.MM_V9_CATALOG&&window.MM_V9_CATALOG.all())||[])];
      const i=items.findIndex(p=>String(p.sku)===String(product.sku));
      if(i>=0)items[i]={...items[i],...product};else items.push(product);
      persistLocal(items); apiSave(items.find(p=>String(p.sku)===String(product.sku))); return items;
    },
    remove:(sku)=>{
      const items=((window.MM_V9_CATALOG&&window.MM_V9_CATALOG.all())||[]).filter(p=>String(p.sku)!==String(sku));
      persistLocal(items); fetch('/api/catalog?sku='+encodeURIComponent(sku),{method:'DELETE'}).catch(e=>console.warn('Catálogo central: eliminação pendente.',e)); return items;
    },
    reset:()=>{localStorage.removeItem(KEY);localStorage.removeItem(CENTRAL);location.reload();}
  };
})();

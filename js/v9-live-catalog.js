/* MarquesMater V9 — catálogo partilhado entre Backoffice e Front Office.
   Nesta fase a persistência é no navegador (localStorage), permitindo testar o fluxo completo.
   A camada está isolada para ser ligada à base central sem alterar as páginas da loja. */
(()=>{
  const KEY='mm_v9_catalog_override_v1';
  const base=Array.isArray(window.MARQUES_CATALOG)?window.MARQUES_CATALOG:[];
  let saved=[];
  try{ saved=JSON.parse(localStorage.getItem(KEY)||'[]'); }catch(e){ saved=[]; }
  if(Array.isArray(saved)&&saved.length){
    const map=new Map(base.map(p=>[String(p.sku),p]));
    saved.forEach(p=>{if(p&&p.sku)map.set(String(p.sku),p);});
    window.MARQUES_CATALOG=Array.from(map.values());
  }
  window.MM_V9_CATALOG_KEY=KEY;
  window.MM_V9_CATALOG={
    all:()=>Array.isArray(window.MARQUES_CATALOG)?window.MARQUES_CATALOG:[],
    save:(items)=>{
      const clean=(items||[]).filter(p=>p&&p.sku).map(p=>({...p}));
      localStorage.setItem(KEY,JSON.stringify(clean));
      window.MARQUES_CATALOG=clean;
      return clean;
    },
    upsert:(product)=>{
      const items=[...((window.MM_V9_CATALOG&&window.MM_V9_CATALOG.all())||[])];
      const i=items.findIndex(p=>String(p.sku)===String(product.sku));
      if(i>=0)items[i]={...items[i],...product};else items.push(product);
      window.MM_V9_CATALOG.save(items);
      return items;
    },
    remove:(sku)=>{
      const items=((window.MM_V9_CATALOG&&window.MM_V9_CATALOG.all())||[]).filter(p=>String(p.sku)!==String(sku));
      window.MM_V9_CATALOG.save(items);
      return items;
    },
    reset:()=>{localStorage.removeItem(KEY);location.reload();}
  };
})();
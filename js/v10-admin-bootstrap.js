/* MarquesMater V10.1 — carrega o catálogo central antes de iniciar o Backoffice. */
(async()=>{
  async function load(src){return new Promise((resolve,reject)=>{const s=document.createElement('script');s.src=src;s.onload=resolve;s.onerror=reject;document.body.appendChild(s)})}
  try{
    const r=await fetch('/api/catalog',{cache:'no-store'});
    const j=await r.json();
    if(j?.ok && Array.isArray(j.catalog) && j.catalog.length){
      window.MARQUES_CATALOG=j.catalog;
      localStorage.setItem('mm_v10_catalog_central_v1',JSON.stringify(j.catalog));
      localStorage.setItem('mm_v9_catalog_override_v1',JSON.stringify(j.catalog));
    }
  }catch(e){
    try{const saved=JSON.parse(localStorage.getItem('mm_v10_catalog_central_v1')||'null');if(Array.isArray(saved)&&saved.length)window.MARQUES_CATALOG=saved}catch(_){ }
    console.warn('Backoffice: catálogo central indisponível; foi usado o último catálogo local.',e);
  }
  await load('js/v9-live-catalog.js');
  await load('js/admin-v9.js');
  await load('js/v9-admin-live2.js');
})();

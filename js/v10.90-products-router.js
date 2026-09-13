(()=>{
'use strict';
if(window.__MM90_PRODUCTS_ROUTER)return;window.__MM90_PRODUCTS_ROUTER=true;
const openProducts=()=>{
  if(typeof window.MM76ProductsRender==='function') return window.MM76ProductsRender();
  const app=document.getElementById('app');
  if(app) app.innerHTML='<section class="page"><div class="card empty">Módulo Produtos não carregado.</div></section>';
};
const isProductsButton=b=>{
  if(!b)return false;
  const section=b.dataset?.section;
  const go=b.dataset?.go;
  const href=b.getAttribute?.('href')||'';
  return section==='products'||go==='products'||go==='products-v2'||href==='#products'||href==='#products-v2';
};
// Canonical route: every internal Products action opens the same V10.76 mosaic module.
const previous=window.MM104&&window.MM104.go;
window.MM104=window.MM104||{};
window.MM104.go=k=>{
  if(k==='products'||k==='products-v2') return openProducts();
  return typeof previous==='function' ? previous(k) : undefined;
};
// Final capture handler is intentionally loaded last so legacy Products handlers cannot win the race.
document.addEventListener('click',e=>{
  const b=e.target.closest?.('.navitem,[data-go],[href]');
  if(!isProductsButton(b))return;
  e.preventDefault();
  e.stopImmediatePropagation();
  openProducts();
  document.querySelectorAll('.navitem').forEach(x=>x.classList.toggle('active',x.dataset.section==='products'));
  document.getElementById('sidebar')?.classList.remove('open');
},true);
// Dashboard/quick-action buttons and any later calls to the old route always resolve to the canonical module.
document.addEventListener('DOMContentLoaded',()=>{
  document.querySelectorAll('[data-go="products"],[data-go="products-v2"]').forEach(b=>b.onclick=e=>{e.preventDefault();openProducts()});
});
})();

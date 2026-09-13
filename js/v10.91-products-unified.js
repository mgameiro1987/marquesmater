(()=>{
'use strict';
if(window.__MM91_PRODUCTS_UNIFIED)return;window.__MM91_PRODUCTS_UNIFIED=true;
const open=()=>typeof window.MM76ProductsRender==='function'?window.MM76ProductsRender():void 0;
const product=(el)=>{if(!el)return false;const s=el.dataset?.section,g=el.dataset?.go,h=el.getAttribute?.('href')||'';return s==='products'||g==='products'||g==='products-v2'||h==='#products'||h==='#products-v2'};
const go=k=>k==='products'||k==='products-v2'?open():void 0;
window.MM104=window.MM104||{};
window.MM104.go=go;
document.addEventListener('click',e=>{const el=e.target.closest?.('.navitem,[data-go],[href]');if(!product(el))return;e.preventDefault();e.stopImmediatePropagation();open();document.querySelectorAll('.navitem').forEach(x=>x.classList.toggle('active',x.dataset.section==='products'));document.getElementById('sidebar')?.classList.remove('open')},true);
})();
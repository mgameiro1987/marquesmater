/* MarquesMater V10.77 — reassert Produtos após os scripts dinâmicos do backoffice. */
(()=>{
'use strict';
const boot=()=>{
  const b=document.querySelector('.navitem[data-section="products-v2"]');
  if(!b)return;
  try{delete window.__MM76_PRODUCTS;}catch(e){window.__MM76_PRODUCTS=false}
  if(!document.querySelector('script[data-mm77-reload]')){
    const s=document.createElement('script');s.src='js/v10.76-products-new.js?v=771';s.dataset.mm77Reload='1';document.body.appendChild(s);
    setTimeout(()=>{const x=document.querySelector('.navitem[data-section="products-v2"]');if(x)x.click()},120);
  }
};
boot();
setTimeout(boot,500);
setTimeout(boot,1500);
setInterval(()=>{
 const a=document.getElementById('app');
 const b=document.querySelector('.navitem[data-section="products-v2"]');
 if(b&&a&&/Área do Backoffice|products-v2/.test(a.innerText||'')){
   try{delete window.__MM76_PRODUCTS;}catch(e){window.__MM76_PRODUCTS=false}
   const s=document.createElement('script');s.src='js/v10.76-products-new.js?v=772&x='+Date.now();document.body.appendChild(s);
   setTimeout(()=>b.click(),80);
 }
},2500);
})();

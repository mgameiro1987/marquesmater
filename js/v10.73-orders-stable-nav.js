/* MarquesMater V10.73 — navegação estável de Encomendas.
   Usa exatamente o padrão de captura do módulo Categorias:
   um único listener no document, na fase capture, sem reencaminhar para o router legado.
*/
(()=>{
  'use strict';
  if(window.__MM_ORDERS_STABLE_NAV)return;
  window.__MM_ORDERS_STABLE_NAV=true;

  function intercept(){
    document.addEventListener('click',e=>{
      const b=e.target.closest('.navitem');
      if(!b)return;
      if(b.dataset.section!=='orders')return;
      e.preventDefault();
      e.stopImmediatePropagation();

      const open=window.MMOrdersAdmin?.open;
      if(typeof open==='function'){
        open();
        b.classList.add('active');
        document.querySelectorAll('.navitem').forEach(x=>{if(x!==b)x.classList.remove('active')});
        document.getElementById('sidebar')?.classList.remove('open');
      }
    },true);
  }

  intercept();
})();

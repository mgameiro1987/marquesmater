/* MarquesMater V10.75 — navegação estável de Encomendas + limpeza de overlays antigos. */
(()=>{
'use strict';
if(window.__MM_ORDERS_STABLE_NAV)return;
window.__MM_ORDERS_STABLE_NAV=true;
function cleanupOverlays(){document.querySelectorAll('body > .mm72.modal,body > .mm104.modal,body > .mm75-modal').forEach(x=>x.remove());document.documentElement.classList.remove('mm64-mobile-view');document.body.classList.remove('modal-open','no-scroll','overflow-hidden')}
function intercept(){document.addEventListener('click',e=>{const b=e.target.closest?.('.navitem[data-section="orders"]');if(!b)return;e.preventDefault();e.stopImmediatePropagation();cleanupOverlays();const open=window.MMOrdersAdmin?.open;if(typeof open==='function'){open();b.classList.add('active');document.querySelectorAll('.navitem').forEach(x=>{if(x!==b)x.classList.remove('active')});document.getElementById('sidebar')?.classList.remove('open')}},true)}
intercept();
})();

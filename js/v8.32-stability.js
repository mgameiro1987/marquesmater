/* MarquesMater V8.32 — estabilização final do Front Office antes do Backoffice/BD */
(function(){
  if(window.__MM_V832_STABILITY)return;
  window.__MM_V832_STABILITY=true;
  function ready(fn){if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',fn,{once:true});else fn()}
  function cartCount(){return window.MMStore?MMStore.state().cart.reduce((n,x)=>n+Number(x.qty||0),0):0}
  function syncHeader(){
    const n=cartCount();
    document.querySelectorAll('#cartCount').forEach(e=>e.textContent=String(n));
    document.querySelectorAll('[data-fav-count]').forEach(e=>e.textContent=String(window.MMStore?MMStore.state().favorites.length:0));
    try{localStorage.setItem('mm_cart_count',String(n))}catch(_){ }
  }
  function fixHeaderLinks(){
    document.querySelectorAll('.actions a,.head-actions a').forEach(a=>{
      const text=(a.innerText||'').toLowerCase();
      if(text.includes('conta'))a.href='account.html';
      else if(text.includes('favoritos')||a.href.includes('favorites.html'))a.href='favorites.html';
      else if(text.includes('carrinho')||a.href.includes('cart.html'))a.href='cart.html';
    });
  }
  function fixFooterLinks(){
    document.querySelectorAll('footer a[href="#"]').forEach(a=>{
      const t=(a.textContent||'').trim().toLowerCase();
      if(t==='contactos')a.href='contact.html';
      else if(t==='entregas')a.href='delivery.html';
      else if(t==='faq')a.href='faq.html';
      else if(t==='conta')a.href='account.html';
    });
  }
  function fixSearch(){
    const q=document.querySelector('#q,#searchInput');if(!q||q.dataset.mm832Search)return;
    q.dataset.mm832Search='1';
    q.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();const x=q.value.trim();if(x)location.href='category.html?q='+encodeURIComponent(x)}});
  }
  function fixCategorySearch(){
    if(!document.getElementById('products'))return;
    const q=(new URLSearchParams(location.search).get('q')||'').trim();
    if(q){const sub=document.getElementById('subcats');if(sub)sub.style.display='none';}
  }
  function removeDemoAlert(){
    if(!document.getElementById('root')||window.__MM_V832_ALERT_PATCHED)return;
    window.__MM_V832_ALERT_PATCHED=true;
    const original=window.alert;
    window.alert=function(msg){if(typeof msg==='string'&&msg.toLowerCase().includes('variante selecionada adicionada ao carrinho'))return;return original.apply(window,arguments)};
  }
  function normalizeVersions(){
    document.querySelectorAll('body *').forEach(el=>{if(el.children.length===0&&/V8\.\d+/i.test(el.textContent||''))el.textContent=el.textContent.replace(/\s*[·•-]?\s*V8\.\d+(?:\.\d+)?/gi,'').trim()});
  }
  function ensureGlobalBottomLinks(){
    document.querySelectorAll('.v8-mobile-bottom a').forEach(a=>{const t=(a.textContent||'').toLowerCase();if(t.includes('categorias'))a.href='categories.html';if(t.includes('carrinho'))a.href='cart.html'});
  }
  function boot(){fixHeaderLinks();fixFooterLinks();fixSearch();fixCategorySearch();removeDemoAlert();ensureGlobalBottomLinks();if(window.MMStore){MMStore.sync();syncHeader()}normalizeVersions()}
  ready(boot);setTimeout(boot,250);setTimeout(boot,900);
})();

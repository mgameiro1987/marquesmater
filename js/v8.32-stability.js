/* MarquesMater V8.32 — estabilização final do Front Office antes do Backoffice/BD */
(function(){
  if(window.__MM_V832_STABILITY)return;
  window.__MM_V832_STABILITY=true;
  function ready(fn){if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',fn,{once:true});else fn()}
  const go=(url)=>{location.href=url};
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
  function fixLegacyHomepageCart(){
    if(!document.getElementById('featured')||!window.MMStore)return;
    document.querySelectorAll('.mmQuick').forEach(btn=>{
      if(btn.dataset.mm832)return;
      btn.dataset.mm832='1';
      btn.onclick=function(e){
        e.preventDefault();e.stopPropagation();
        const m=(this.getAttribute('onclick')||'').match(/addCart\(['\"]([^'\"]+)/);
        const sku=m?m[1]:null;
        if(!sku||!MMStore.product(sku))return;
        MMStore.addCart(sku,1);
        syncHeader();
        const old=this.textContent;this.textContent='ADICIONADO ✓';setTimeout(()=>this.textContent=old,900);
      };
    });
  }
  function fixSearch(){
    const q=document.querySelector('#q,#searchInput');
    if(!q)return;
    const fn=()=>{const x=q.value.trim();if(x)go('category.html?q='+encodeURIComponent(x));};
    q.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();fn()}});
  }
  function fixCategorySearch(){
    const products=document.getElementById('products');
    if(!products)return;
    const params=new URLSearchParams(location.search),q=(params.get('q')||'').trim();
    if(q){const sub=document.getElementById('subcats');if(sub)sub.style.display='none';}
  }
  function removeDemoAlert(){
    if(!document.getElementById('root'))return;
    const original=window.alert;
    if(window.__MM_V832_ALERT_PATCHED)return;
    window.__MM_V832_ALERT_PATCHED=true;
    window.alert=function(msg){if(typeof msg==='string'&&msg.toLowerCase().includes('variante selecionada adicionada ao carrinho'))return;return original.apply(window,arguments)};
  }
  function normalizeVersions(){
    document.querySelectorAll('body *').forEach(el=>{
      if(el.children.length===0&&/V8\.\d+/i.test(el.textContent||'')){
        el.textContent=el.textContent.replace(/\s*[·•-]?\s*V8\.\d+(?:\.\d+)?/gi,'').trim();
      }
    });
  }
  function ensureGlobalBottomLinks(){
    document.querySelectorAll('.v8-mobile-bottom a').forEach(a=>{
      const t=(a.textContent||'').toLowerCase();
      if(t.includes('categorias'))a.href='categories.html';
      if(t.includes('carrinho'))a.href='cart.html';
    });
  }
  function boot(){
    fixHeaderLinks();fixFooterLinks();fixLegacyHomepageCart();fixSearch();fixCategorySearch();removeDemoAlert();ensureGlobalBottomLinks();syncHeader();normalizeVersions();
    if(window.MMStore){MMStore.sync();syncHeader()}
  }
  ready(boot);
  setTimeout(boot,250);
  setTimeout(boot,900);
})();

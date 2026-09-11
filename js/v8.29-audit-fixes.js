/* MarquesMater V8.29 — auditoria funcional: quick-add, conta demo, cards e badge */
(function(){
  function whenReady(fn){
    if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',fn,{once:true});
    else fn();
  }

  function patchCart(){
    if(!window.MMStore) return setTimeout(patchCart,80);
    const refresh=()=>{
      const el=document.getElementById('cartCount');
      if(el) el.textContent=String((MMStore.state().cart||[]).reduce((n,x)=>n+Number(x.qty||0),0));
    };
    window.addCart=function(sku,qty){
      const p=MMStore.product(sku);
      if(!p) return;
      MMStore.addCart(sku,Number(qty||1));
      refresh();
    };
    refresh();
    document.addEventListener('click',e=>{
      const btn=e.target.closest('.mmQuick');
      if(!btn) return;
      e.preventDefault();
      e.stopPropagation();
      const m=btn.getAttribute('onclick')||'';
      const hit=m.match(/addCart\(['\"]([^'\"]+)/);
      if(hit){MMStore.addCart(hit[1],1);refresh();btn.textContent='ADICIONADO ✓';setTimeout(()=>btn.textContent='ADICIONAR AO CARRINHO',900)}
    },true);
  }

  function patchAccount(){
    const loginBtn=document.getElementById('demoLogin');
    const createBtn=document.getElementById('demoCreate');
    if(!loginBtn && !createBtn) return;
    const validate=(e)=>{
      const email=(document.getElementById('demoEmail')?.value||'').trim();
      const pass=document.getElementById('demoPass')?.value||'';
      if(email!=='demo@marquesmater.pt'||pass!=='1234'){
        e.preventDefault();e.stopImmediatePropagation();
        alert('Para a conta DEMO usa demo@marquesmater.pt e a palavra-passe 1234.');
        return true;
      }
      return false;
    };
    [loginBtn,createBtn].filter(Boolean).forEach(b=>b.addEventListener('click',validate,true));
  }

  function patchCategoryCards(){
    document.querySelectorAll('.v84-card').forEach(card=>{
      const link=card.querySelector(':scope > a');
      const button=card.querySelector('.v84-add');
      if(link&&button&&link.contains(button)){
        link.removeChild(button);
        card.appendChild(button);
      }
    });
    const mark=document.querySelector('.eyebrow.dark');
    if(mark&&mark.textContent.includes('V8.4')) mark.textContent='CATÁLOGO';
    const footer=document.querySelector('footer .copy');
    if(footer&&footer.textContent.includes('V8.4')) footer.textContent=footer.textContent.replace(' · V8.4','');
  }

  whenReady(()=>{
    patchCart();
    patchAccount();
    patchCategoryCards();
    const obs=new MutationObserver(()=>{patchAccount();patchCategoryCards()});
    obs.observe(document.body,{childList:true,subtree:true});
  });
})();

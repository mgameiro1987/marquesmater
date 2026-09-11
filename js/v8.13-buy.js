/* MarquesMater V8.13 — interação do botão de compra */
(function(){
  function boot(){
    const button=document.querySelector('.v6-cart');
    if(!button)return;
    button.classList.add('v813-buy-button');
    button.innerHTML='<span aria-hidden="true">🛒</span><span>ADICIONAR AO CARRINHO</span>';
    if(!document.querySelector('.v813-buy-note')){
      const note=document.createElement('div');
      note.className='v813-buy-note';
      note.textContent='✓ Disponível para envio e levantamento em loja';
      button.insertAdjacentElement('afterend',note);
    }
    if(window.__mmV813Wrapped)return;
    window.__mmV813Wrapped=true;
    const originalAdd=window.add;
    if(typeof originalAdd==='function'){
      window.add=function(){
        originalAdd.apply(this,arguments);
        const b=document.querySelector('.v6-cart');
        if(!b)return;
        b.classList.add('mm-added');
        b.innerHTML='<span aria-hidden="true">✓</span><span>ADICIONADO AO CARRINHO</span>';
        setTimeout(function(){
          b.classList.remove('mm-added');
          b.innerHTML='<span aria-hidden="true">🛒</span><span>ADICIONAR AO CARRINHO</span>';
        },1800);
      };
    }
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();

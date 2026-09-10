(function(){
  'use strict';
  const MARK='data-mm-woodneuce-catalog';
  const IMG='https://www.neuce.com/files/media/145_1.png?d=V1';
  const PDF='https://www.neuce.com/files/media/145_2.pdf?d=V1';
  function add(){
    document.querySelectorAll('.modal.open').forEach(function(modal){
      if(modal.getAttribute(MARK)) return;
      const text=(modal.innerText||'').toLowerCase();
      if(!/woodneuce/.test(text)) return;
      const card=modal.querySelector('.modal-card');
      if(!card) return;
      const anchor=card.querySelector('.mmv-overview') || card.querySelector('.tabs') || card.firstElementChild;
      if(!anchor) return;
      modal.setAttribute(MARK,'1');
      const style=document.createElement('style');
      style.textContent='.mm-wood-catalog{margin:0 22px 15px;background:#fff;border:1px solid #e0e6ea;border-radius:15px;padding:17px;box-shadow:0 4px 16px rgba(16,24,32,.04)}.mm-wood-catalog-head{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:10px}.mm-wood-catalog-title{font-size:15px;font-weight:900;color:#16212b}.mm-wood-catalog-sub{font-size:11px;color:#73808a;margin-top:3px}.mm-wood-catalog-link{display:inline-flex;align-items:center;gap:6px;padding:8px 11px;border-radius:9px;background:#f28c00;color:#fff!important;text-decoration:none;font-size:11px;font-weight:900}.mm-wood-catalog img{display:block;width:100%;max-height:520px;object-fit:contain;border:1px solid #e0e6ea;border-radius:12px;background:#fafbfc}.mm-wood-catalog-note{margin-top:8px;font-size:10px;color:#73808a}@media(max-width:800px){.mm-wood-catalog{margin:0 14px 14px}.mm-wood-catalog-head{align-items:flex-start;flex-direction:column}}';
      document.head.appendChild(style);
      const box=document.createElement('section');
      box.className='mm-wood-catalog';
      box.innerHTML='<div class="mm-wood-catalog-head"><div><div class="mm-wood-catalog-title">Carta de cores WOODNEUCE</div><div class="mm-wood-catalog-sub">Cores de catálogo · disponível em Acetinado e Mate</div></div><a class="mm-wood-catalog-link" href="'+PDF+'" target="_blank" rel="noopener">Abrir catálogo PDF</a></div><img src="'+IMG+'" alt="Carta de cores WOODNEUCE — NEUCE" loading="lazy"><div class="mm-wood-catalog-note">Carta de cores disponibilizada pela NEUCE. As tonalidades podem variar conforme a madeira e o número de demãos.</div>';
      anchor.parentNode.insertBefore(box,anchor);
    });
  }
  new MutationObserver(add).observe(document.documentElement,{subtree:true,childList:true,attributes:true,attributeFilter:['class']});
  setInterval(add,700); add();
})();

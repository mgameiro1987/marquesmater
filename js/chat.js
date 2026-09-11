/* MarquesMater V8.31 — bootstrap do catálogo expandido antes do render */
if(!window.__MM_V831_BOOTSTRAP){window.__MM_V831_BOOTSTRAP=true;document.write('<script src="js/v8.31-catalog-expansion.js"><\/script>');}
/* MarquesMater V8.23 — banner mobile: apenas setas */
(function(){
  const css=document.createElement('link');css.rel='stylesheet';css.href='v8.6.css';document.head.appendChild(css);
  const style=document.createElement('style');style.textContent=`@media(max-width:700px){
    .heroV7 .mmCarousel{overflow:hidden!important;touch-action:none!important;-webkit-overflow-scrolling:auto!important}
    .heroV7 .mmSlides{display:block!important;width:100%!important;height:100%!important;min-height:0!important;max-height:none!important;overflow:hidden!important}
    .heroV7 .mmSlide{position:absolute!important;inset:0!important;display:block!important;width:100%!important;min-width:100%!important;max-width:none!important;height:100%!important;min-height:0!important;max-height:none!important;opacity:0!important;pointer-events:none!important;transform:none!important}
    .heroV7 .mmSlide.active{opacity:1!important;pointer-events:auto!important}
    .heroV7 .mmControls{position:absolute!important;left:0!important;right:0!important;top:0!important;bottom:0!important;width:100%!important;height:100%!important;min-width:0!important;z-index:50!important;pointer-events:none!important;margin:0!important}
    .heroV7 .mmArrows{position:absolute!important;left:0!important;right:0!important;top:50%!important;transform:translateY(-50%)!important;width:100%!important;display:block!important;pointer-events:none!important}
    .heroV7 .mmArrow{position:absolute!important;width:40px!important;height:40px!important;pointer-events:auto!important;z-index:51!important}
    .heroV7 .mmArrow:first-child{left:8px!important}
    .heroV7 .mmArrow:last-child{right:8px!important}
    .heroV7 .mmDots{display:none!important}
    .heroV7 .mmProgress{display:none!important}
  }
  @media(max-width:380px){.heroV7 .mmArrow{width:36px!important;height:36px!important}.heroV7 .mmArrow:first-child{left:6px!important}.heroV7 .mmArrow:last-child{right:6px!important}}
  `;document.head.appendChild(style);
  const wrap=document.createElement('div');
  wrap.innerHTML=`<button class="mmChatBtn" id="mmChatBtn" aria-label="Abrir assistente">💬 Precisa de ajuda?</button><section class="mmChatPanel" id="mmChatPanel" aria-label="Assistente MarquesMater"><header class="mmChatHead"><div><strong>🤖 Assistente MarquesMater</strong><small>Ajuda a encontrar o produto certo</small></div><button class="mmChatClose" id="mmChatClose" aria-label="Fechar">×</button></header><div class="mmChatBody" id="mmChatBody"><div class="mmChatMsg">Olá! 👋 Posso ajudar-te a encontrar materiais, ferramentas, tintas, selantes e outros produtos.</div><div class="mmChatQuick"><button data-q="Preciso de ajuda a escolher um produto">Escolher produto</button><button data-q="Quero saber sobre entregas">Entregas</button><button data-q="Preciso de ajuda com tintas">Tintas</button><button data-q="Preciso de ajuda com ferramentas RIDA">Ferramentas RIDA</button></div></div><form class="mmChatForm" id="mmChatForm"><input id="mmChatInput" autocomplete="off" placeholder="Escreve a tua dúvida..."><button>Enviar</button></form></section>`;
  document.body.appendChild(wrap);
  const panel=document.getElementById('mmChatPanel'),body=document.getElementById('mmChatBody'),input=document.getElementById('mmChatInput');
  document.getElementById('mmChatBtn').onclick=()=>{panel.classList.toggle('open');if(panel.classList.contains('open'))input.focus()};
  document.getElementById('mmChatClose').onclick=()=>panel.classList.remove('open');
  function reply(text){const t=text.toLowerCase();if(t.includes('tinta'))return 'Claro. Posso ajudar a escolher por aplicação, embalagem, cor e acabamento. Na página do produto apresentamos as variantes.';if(t.includes('rida')||t.includes('ferrament'))return 'Posso ajudar a escolher uma ferramenta RIDA por voltagem, bateria, potência e kit.';if(t.includes('entrega'))return 'A loja está preparada para informação de entrega em Portugal Continental e levantamento em loja.';if(t.includes('silicone')||t.includes('cola')||t.includes('selante'))return 'Posso ajudar a escolher o tipo, cor e volume. As variantes ficam disponíveis na página do produto.';return 'Percebi. Posso ajudar-te a encontrar o produto certo.'}
  function send(text){if(!text.trim())return;body.insertAdjacentHTML('beforeend',`<div class="mmChatMsg user">${text.replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}</div>`);setTimeout(()=>{body.insertAdjacentHTML('beforeend',`<div class="mmChatMsg">${reply(text)}</div>`);body.scrollTop=body.scrollHeight},250);body.scrollTop=body.scrollHeight}
  document.getElementById('mmChatForm').onsubmit=e=>{e.preventDefault();send(input.value);input.value=''};
  body.querySelectorAll('.mmChatQuick button').forEach(b=>b.onclick=()=>send(b.dataset.q));
  const bottom=document.createElement('nav');bottom.className='v8-mobile-bottom';bottom.innerHTML='<a href="index.html"><b>⌂</b><span>Início</span></a><a href="categories.html"><b>▦</b><span>Categorias</span></a><a href="#" onclick="document.getElementById(\'mmChatBtn\').click();return false"><b>💬</b><span>Ajuda</span></a><a href="cart.html"><b>🛒</b><span>Carrinho</span></a>';document.body.appendChild(bottom);
  const carousel=document.getElementById('carousel');
  if(carousel){
    const blockSwipe=()=>window.matchMedia('(max-width:700px)').matches;
    carousel.addEventListener('touchstart',e=>{if(blockSwipe())e.stopImmediatePropagation()},{capture:true,passive:true});
    carousel.addEventListener('touchmove',e=>{if(blockSwipe())e.stopImmediatePropagation()},{capture:true,passive:true});
    carousel.addEventListener('touchend',e=>{if(blockSwipe())e.stopImmediatePropagation()},{capture:true,passive:true});
    carousel.addEventListener('touchcancel',e=>{if(blockSwipe())e.stopImmediatePropagation()},{capture:true,passive:true});
  }
  const s=document.createElement('script');s.src='js/store.js';s.onload=()=>{const a=document.createElement('script');a.src='js/v8.29-audit-fixes.js';document.body.appendChild(a)};document.body.appendChild(s);
})();

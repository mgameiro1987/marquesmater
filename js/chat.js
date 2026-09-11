/* MarquesMater V8.19 — Assistente + navegação mobile + swipe robusto */
(function(){
  const css=document.createElement('link');css.rel='stylesheet';css.href='v8.6.css';document.head.appendChild(css);
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
  const bottom=document.createElement('nav');bottom.className='v8-mobile-bottom';bottom.innerHTML='<a href="index.html"><b>⌂</b><span>Início</span></a><a href="category.html?cat=Construção"><b>▦</b><span>Categorias</span></a><a href="#" onclick="document.getElementById(\'mmChatBtn\').click();return false"><b>💬</b><span>Ajuda</span></a><a href="cart.html"><b>🛒</b><span>Carrinho</span></a>';document.body.appendChild(bottom);

  /* V8.19: swipe mobile com Touch Events + deteção de direção. Evita conflito com o handler antigo do index. */
  const carousel=document.getElementById('carousel');
  if(carousel){
    let startX=0,startY=0,lastX=0,lastY=0,tracking=false,locked=false;
    carousel.style.touchAction='pan-y pinch-zoom';
    carousel.addEventListener('touchstart',e=>{
      if(!e.changedTouches.length)return;
      const t=e.changedTouches[0];startX=lastX=t.clientX;startY=lastY=t.clientY;tracking=true;locked=false;
    },{capture:true,passive:true});
    carousel.addEventListener('touchmove',e=>{
      if(!tracking||!e.changedTouches.length)return;
      const t=e.changedTouches[0];lastX=t.clientX;lastY=t.clientY;
      const dx=lastX-startX,dy=lastY-startY;
      if(!locked&&Math.abs(dx)>12&&Math.abs(dx)>Math.abs(dy)*1.15){locked=true;}
      if(locked)e.stopImmediatePropagation();
    },{capture:true,passive:true});
    carousel.addEventListener('touchend',e=>{
      if(!tracking||!e.changedTouches.length)return;
      const t=e.changedTouches[0],dx=t.clientX-startX,dy=t.clientY;tracking=false;
      if(Math.abs(dx)>=40&&Math.abs(dx)>Math.abs(dy)*1.1){
        e.stopImmediatePropagation();
        const btn=document.getElementById(dx<0?'next':'prev');
        if(btn)btn.click();
      }
    },{capture:true,passive:true});
    carousel.addEventListener('touchcancel',()=>{tracking=false;locked=false},{capture:true,passive:true});
  }
  const s=document.createElement('script');s.src='js/store.js';document.body.appendChild(s);
})();

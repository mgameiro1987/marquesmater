/* MarquesMater V8.11 — separadores, variantes e galeria de produto */
(function(){
 function syncGallery(){
  const main=document.getElementById('mainProductImage');
  const thumbs=document.querySelectorAll('.v6-thumbs button');
  if(!main||!thumbs.length)return;
  thumbs.forEach(b=>{
   const img=b.querySelector('img');
   b.classList.toggle('active',!!img&&img.src===main.src);
  });
 }
 function setupGallery(){
  const wrap=document.querySelector('.v6-thumbs');
  const main=document.getElementById('mainProductImage');
  if(!wrap||!main)return;
  const entries=Object.entries((typeof variantImages!=='undefined'&&variantImages)||{});
  const unique=[];const seen=new Set();
  entries.forEach(([value,url])=>{if(url&&!seen.has(url)){seen.add(url);unique.push({value,url})}});
  if(!unique.length)unique.push({value:'Produto',url:main.src});
  wrap.innerHTML=unique.slice(0,5).map((x,i)=>`<button type="button" class="${i===0?'active':''}" data-gallery-value="${x.value.replace(/"/g,'&quot;')}"><img src="${x.url}" alt="${x.value}"></button>`).join('');
  wrap.querySelectorAll('button').forEach(btn=>btn.addEventListener('click',function(){
   const img=this.querySelector('img');if(!img)return;
   main.src=img.src;
   wrap.querySelectorAll('button').forEach(b=>b.classList.remove('active'));
   this.classList.add('active');
  }));
  const originalChoose=window.choose;
  if(typeof originalChoose==='function'&&!originalChoose.__mmGalleryWrapped){
   const wrapped=function(btn,value,key){originalChoose(btn,value,key);syncGallery()};
   wrapped.__mmGalleryWrapped=true;window.choose=wrapped;
  }
  syncGallery();
 }
 function boot(){
  const style='v8.10.css';
  if(!document.querySelector('link[href="'+style+'"]')){const l=document.createElement('link');l.rel='stylesheet';l.href=style;document.head.appendChild(l)}
  const footer=document.querySelector('.copyright');if(footer)footer.textContent='© MarquesMater · Produto V8.11';
  const optionBlocks=document.querySelectorAll('.v6-option');
  optionBlocks.forEach(block=>{
   const buttons=block.querySelectorAll('.option-buttons>button');
   if(buttons.length&&!block.querySelector('.v6-swatch'))buttons.forEach((b,i)=>b.classList.toggle('selected',i===0));
   const swatches=block.querySelectorAll('.v6-swatch');
   if(swatches.length)swatches.forEach((b,i)=>b.classList.toggle('selected',i===0));
  });
  setupGallery();
  const tabs=document.querySelectorAll('.v6-tabs button,.tabs button'),body=document.getElementById('tabbody');
  if(!tabs.length||!body)return;
  const params=new URLSearchParams(location.search),sku=params.get('sku')||'SIL001';
  const p=(window.MARQUES_CATALOG||[]).find(x=>x.sku===sku)||(window.MARQUES_CATALOG||[])[0];
  if(!p)return;
  const specs=p.specs||[];
  const options=p.options||{};
  const rows=specs.map(x=>{const a=x.split(':');return `<tr><td>${a[0]}</td><td>${a.slice(1).join(':').trim()}</td></tr>`}).join('');
  const optionRows=Object.entries(options).map(([k,v])=>`<tr><td>${k}</td><td>${v.join(' · ')}</td></tr>`).join('');
  const contents=[
   `<p>${p.description||''}</p><p>Consulte as características, especificações, aplicações e documentação disponíveis para este produto.</p>`,
   `<h3>Características</h3><table class="mm-spec-table">${optionRows||'<tr><td colspan="2">Informação de características conforme disponibilidade do produto.</td></tr>'}</table>`,
   `<h3>Especificações técnicas</h3><table class="mm-spec-table">${rows||'<tr><td colspan="2">Especificações técnicas a disponibilizar.</td></tr>'}</table>`,
   `<h3>Aplicações</h3><p>${p.application||p.applications||'Adequado às aplicações indicadas na descrição e ficha técnica do produto. A informação detalhada será apresentada aqui na versão final do catálogo.'}</p>`,
   `<h3>Documentação</h3><div class="v89-docs"><p>📄 Ficha técnica</p><p>📄 Informação de segurança e utilização</p><small>Os documentos oficiais serão ligados ao produto quando o catálogo final estiver integrado.</small></div>`,
   `<h3>Avaliações</h3><div class="v89-review"><strong>★★★★★</strong><span>4,8 / 5 · 24 avaliações</span><p>Área preparada para avaliações reais de clientes.</p></div>`
  ];
  tabs.forEach((tab,i)=>{tab.type='button';tab.addEventListener('click',function(){tabs.forEach(t=>t.classList.remove('active'));this.classList.add('active');body.innerHTML=contents[i]||contents[0];body.scrollIntoView({behavior:'smooth',block:'nearest'})})});
  body.innerHTML=contents[0];
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();

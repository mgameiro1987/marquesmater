/* MarquesMater V8.9 — separadores da ficha de produto */
(function(){
 function boot(){
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

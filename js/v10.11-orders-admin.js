/* MarquesMater V10.24 — Gestão de encomendas: guardar estado com timeout e feedback. */
(()=>{
  const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]));
  const money=n=>{const v=Number(n||0);return Number.isFinite(v)?v.toLocaleString('pt-PT',{style:'currency',currency:'EUR'}):'—'};
  const date=v=>{try{return new Date(v).toLocaleString('pt-PT',{dateStyle:'short',timeStyle:'short'})}catch(_){return String(v||'')}};
  const statuses=['Todas','Recebida','Em preparação','Enviada','Concluída','Cancelada'];
  const cls=s=>s==='Concluída'?'green':s==='Cancelada'?'red':s==='Enviada'?'blue':s==='Em preparação'?'orange':'';
  let orders=[]; let activeFilter='Todas';
  function name(o){return o.customer?.name||o.data?.customerName||o.data?.name||o.data?.email||'Cliente';}
  function email(o){return o.customer?.email||o.data?.email||'';}
  function total(o){return o.total ?? o.data?.total ?? o.data?.totalPrice ?? o.data?.amount ?? 0;}
  function items(o){return Array.isArray(o.items)?o.items:(Array.isArray(o.data?.items)?o.data.items:[])}
  async function jsonResponse(r){const text=await r.text();let j={};try{j=JSON.parse(text)}catch(_){throw new Error(`Resposta inválida do servidor (HTTP ${r.status})`)}if(!r.ok||j.ok===false)throw new Error(j.error||`Erro HTTP ${r.status}`);return j;}
  async function fetchWithTimeout(url,opts={},ms=15000){const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),ms);try{return await fetch(url,{...opts,signal:controller.signal,cache:'no-store'})}catch(e){if(e.name==='AbortError')throw new Error('O servidor demorou demasiado tempo a responder. Tenta novamente.');throw e}finally{clearTimeout(timer)}}
  async function load(){const r=await fetchWithTimeout('/api/admin/orders');const j=await jsonResponse(r);orders=j.orders||[];render();}
  async function setStatus(id,status,button){if(button){button.disabled=true;button.textContent='A guardar…';button.dataset.busy='1'}try{const r=await fetchWithTimeout('/api/admin/orders/status',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id,status})});const j=await jsonResponse(r);const o=orders.find(x=>x.id===id);if(o)o.status=j.status||status;render()}catch(e){if(button){button.disabled=false;button.textContent='Guardar';delete button.dataset.busy}alert(e.message||'Não foi possível guardar o estado.');}}
  function render(){const app=document.getElementById('app');if(!app)return;app.innerHTML=`<section class="page mm-orders-page"><div class="pagehead"><div><h1>Encomendas</h1><p>Gestão central das encomendas da loja.</p></div><div class="date">PostgreSQL · dados reais</div></div><div class="mm-order-toolbar"><div class="mm-order-filters">${statuses.map(s=>`<button class="mm-order-filter ${s===activeFilter?'active':''}" data-filter="${esc(s)}">${esc(s)} <b>${s==='Todas'?orders.length:orders.filter(o=>o.status===s).length}</b></button>`).join('')}</div><button class="btn" id="mmOrderRefresh">↻ Atualizar</button></div><div class="card"><div class="tablewrap"><table class="table mm-orders-table"><thead><tr><th>Encomenda</th><th>Cliente</th><th>Data</th><th>Artigos</th><th>Total</th><th>Estado</th><th>Ação</th></tr></thead><tbody id="mmOrdersBody"></tbody></table></div><div id="mmOrdersEmpty" class="mm-orders-empty" style="display:none">Não existem encomendas neste estado.</div></div></section>`;const body=document.getElementById('mmOrdersBody');function draw(filter=activeFilter){activeFilter=filter;const list=filter==='Todas'?orders:orders.filter(o=>o.status===filter);body.innerHTML=list.map(o=>`<tr><td><b>#${o.id}</b></td><td><b>${esc(name(o))}</b><br><small>${esc(email(o))}</small></td><td>${esc(date(o.created_at))}</td><td>${items(o).length||'—'}</td><td><b>${money(total(o))}</b></td><td><select class="mm-order-status status ${cls(o.status)}" data-id="${o.id}">${statuses.slice(1).map(s=>`<option value="${esc(s)}" ${s===o.status?'selected':''}>${esc(s)}</option>`).join('')}</select></td><td><button class="btn mm-order-save" data-id="${o.id}">Guardar</button></td></tr>`).join('');document.getElementById('mmOrdersEmpty').style.display=list.length?'none':'block';body.querySelectorAll('.mm-order-save').forEach(btn=>btn.onclick=async()=>{const select=body.querySelector(`.mm-order-status[data-id="${btn.dataset.id}"]`);if(!select)return;await setStatus(Number(btn.dataset.id),select.value,btn)});body.querySelectorAll('.mm-order-status').forEach(el=>el.onchange=()=>{el.className=`mm-order-status status ${cls(el.value)}`});}document.querySelectorAll('.mm-order-filter').forEach(b=>b.onclick=()=>{document.querySelectorAll('.mm-order-filter').forEach(x=>x.classList.remove('active'));b.classList.add('active');draw(b.dataset.filter)});document.getElementById('mmOrderRefresh').onclick=async()=>{try{await load()}catch(e){alert(e.message)}};draw(activeFilter);}
  function open(){load().catch(e=>{const app=document.getElementById('app');if(app)app.innerHTML=`<section class="page"><div class="pagehead"><div><h1>Encomendas</h1><p>Gestão central das encomendas da loja.</p></div></div><div class="card info"><h3>Não foi possível carregar as encomendas</h3><p>${esc(e.message)}</p><button class="btn" onclick="location.reload()">Tentar novamente</button></div></section>`})}
  function install(){const nav=document.querySelector('.navitem[data-section="orders"]');if(!nav)return false;nav.addEventListener('click',e=>{e.preventDefault();e.stopImmediatePropagation();open();document.querySelectorAll('.navitem').forEach(b=>b.classList.toggle('active',b===nav));document.getElementById('sidebar')?.classList.remove('open')},true);window.MMOrdersAdmin={open,load};return true;}
  const t=setInterval(()=>{if(install())clearInterval(t)},100);setTimeout(()=>clearInterval(t),20000);
})();

/* V10.32 — último nível de navegação: os botões e mosaicos usam os módulos reais já instalados. */
(()=>{
  function routeByNav(k){
    const b=document.querySelector(`.navitem[data-section="${k}"]`);
    if(!b)return false;
    b.click();
    return true;
  }
  const special=new Set(['categories','brands','attributes','variants','marketing','orders','users','chat']);
  const install=()=>{
    if(!window.MM104?.go)return false;
    const current=window.MM104.go;
    if(current.__mm32)return true;
    const go=function(k){
      if(special.has(k)&&routeByNav(k))return;
      return current(k);
    };
    go.__mm32=true;
    window.MM104.go=go;
    return true;
  };
  const t=setInterval(()=>{if(install())clearInterval(t)},100);
  setTimeout(()=>clearInterval(t),20000);
})();

/* V10.33 — UX do catálogo: mosaico de categorias + abertura robusta dos editores. */
(()=>{
  const style=document.createElement('style');
  style.id='mm33-ux-css';
  style.textContent=`
    .mm33-category-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin-top:14px}
    .mm33-category-card{background:#fff;border:1px solid #e3e9f2;border-radius:16px;overflow:hidden;box-shadow:0 4px 16px rgba(16,32,68,.055);transition:transform .16s,box-shadow .16s,border-color .16s;display:flex;flex-direction:column}
    .mm33-category-card:hover{transform:translateY(-2px);box-shadow:0 9px 25px rgba(16,32,68,.10);border-color:#cbd8ea}
    .mm33-cover{height:92px;display:flex;align-items:center;justify-content:space-between;padding:0 18px;background:linear-gradient(135deg,#eef6ff,#f8fbff);border-bottom:1px solid #edf1f6}
    .mm33-icon{width:54px;height:54px;border-radius:15px;display:grid;place-items:center;font-size:27px;background:#fff;border:1px solid #d9e6f7;box-shadow:0 3px 9px rgba(16,32,68,.06)}
    .mm33-more{background:#fff;border:1px solid #dce5f0;border-radius:9px;width:32px;height:32px;font-size:18px;cursor:pointer;color:#506176}
    .mm33-body{padding:15px 16px 16px;display:flex;flex-direction:column;gap:6px;flex:1}
    .mm33-name{font-size:16px;font-weight:800;color:#102044}
    .mm33-slug{font-size:11px;color:#8794a7}
    .mm33-meta{display:flex;gap:8px;flex-wrap:wrap;margin-top:5px}
    .mm33-badge{font-size:11px;padding:5px 8px;border-radius:999px;background:#eef5ff;color:#2454a6;font-weight:700}
    .mm33-active{background:#e8f8ef;color:#16803c}
    .mm33-actions{display:flex;gap:7px;margin-top:auto;padding-top:10px}
    .mm33-actions button{flex:1!important}
    .mm33-search{width:min(320px,100%);border:1px solid #d7dee8;border-radius:10px;padding:10px 12px;background:#fff;font:inherit;box-sizing:border-box}
    .mm33-list-source{display:none!important}
    @media(max-width:1100px){.mm33-category-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}
    @media(max-width:800px){.mm33-category-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
    @media(max-width:520px){.mm33-category-grid{grid-template-columns:1fr}.mm33-cover{height:82px}}
  `;
  document.head.appendChild(style);

  const iconFor=name=>{
    const n=String(name||'').toLowerCase();
    if(n.includes('constru'))return '🧱'; if(n.includes('jard')||n.includes('agric'))return '🌱';
    if(n.includes('tinta')||n.includes('verniz'))return '🎨'; if(n.includes('ferrament'))return '🔧';
    if(n.includes('elétr')||n.includes('electric'))return '🔌'; if(n.includes('ilum'))return '💡';
    if(n.includes('casa')||n.includes('brico'))return '🏠'; if(n.includes('epi')||n.includes('seguran'))return '🦺';
    if(n.includes('rida'))return 'R'; if(n.includes('promo'))return '%'; if(n.includes('novid'))return '★'; if(n.includes('saldo'))return '🏷️';
    return '▦';
  };
  const escapeHtml=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]));

  function mosaicCategories(root){
    if(!root||root.dataset.mm33==='1')return;
    const h=root.querySelector('h1');
    if(!h||h.textContent.trim()!=='Categorias')return;
    const table=root.querySelector('.table');
    if(!table)return;
    const rows=[...table.querySelectorAll('tbody tr')];
    if(!rows.length)return;
    const card=table.closest('.card');
    if(!card)return;
    const toolbar=root.querySelector('.toolbar');
    if(toolbar&&!toolbar.querySelector('.mm33-search')){
      const input=document.createElement('input');input.className='mm33-search';input.placeholder='Pesquisar categorias...';
      input.addEventListener('input',()=>{
        const q=input.value.toLowerCase().trim();root.querySelectorAll('.mm33-category-card').forEach(c=>c.style.display=c.dataset.q.includes(q)?'':'none');
      });
      toolbar.prepend(input);
    }
    const grid=document.createElement('div');grid.className='mm33-category-grid';
    rows.forEach(row=>{
      const cells=row.children;if(cells.length<5)return;
      const name=cells[0].querySelector('b')?.textContent?.trim()||'';
      const slug=cells[0].querySelector('.muted')?.textContent?.trim()||'';
      const type=cells[1].textContent.trim();const parent=cells[2].textContent.trim();const active=cells[3].textContent.trim();
      const originalEdit=cells[4].querySelector('[data-edit]');const originalDelete=cells[4].querySelector('[data-del]');
      const c=document.createElement('article');c.className='mm33-category-card';c.dataset.q=`${name} ${slug} ${type} ${parent}`.toLowerCase();
      const cover=document.createElement('div');cover.className='mm33-cover';cover.innerHTML=`<div class="mm33-icon">${escapeHtml(iconFor(name))}</div><button class="mm33-more" type="button" title="Mais opções">⋯</button>`;
      const body=document.createElement('div');body.className='mm33-body';
      body.innerHTML=`<div class="mm33-name">${escapeHtml(name)}</div><div class="mm33-slug">${escapeHtml(slug)}</div><div class="mm33-meta"><span class="mm33-badge">${escapeHtml(type)}</span>${parent!=='—'?`<span class="mm33-badge">↳ ${escapeHtml(parent)}</span>`:''}<span class="mm33-badge mm33-active">${escapeHtml(active)}</span></div>`;
      const actions=document.createElement('div');actions.className='mm33-actions';
      if(originalEdit){originalEdit.classList.add('mm33-real-edit');actions.appendChild(originalEdit)}
      if(originalDelete){actions.appendChild(originalDelete)}
      body.appendChild(actions);c.appendChild(cover);c.appendChild(body);grid.appendChild(c);
      cover.querySelector('.mm33-more').onclick=()=>originalEdit?.click();
    });
    card.classList.add('mm33-list-source');card.parentNode.insertBefore(grid,card.nextSibling);root.dataset.mm33='1';
  }

  function forceEditorClick(e){
    const b=e.target.closest?.('.mm106 [data-edit], .mm106 [data-be]');
    if(!b||b.dataset.mm33Handled==='1')return;
    if(typeof b.onclick==='function'){
      e.preventDefault();e.stopImmediatePropagation();b.dataset.mm33Handled='1';
      try{b.onclick(e)}finally{setTimeout(()=>delete b.dataset.mm33Handled,0)}
    }
  }
  document.addEventListener('click',forceEditorClick,true);

  const observer=new MutationObserver(()=>{
    const root=document.querySelector('#app .mm106');
    if(root)mosaicCategories(root);
  });
  observer.observe(document.getElementById('app')||document.body,{childList:true,subtree:true});
  setTimeout(()=>{const root=document.querySelector('#app .mm106');if(root)mosaicCategories(root)},300);
})();
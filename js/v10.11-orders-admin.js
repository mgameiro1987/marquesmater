/* MarquesMater V10.11 — Gestão real de encomendas. Remove o placeholder V9 e usa PostgreSQL. */
(()=>{
  const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]));
  const money=n=>{const v=Number(n||0);return Number.isFinite(v)?v.toLocaleString('pt-PT',{style:'currency',currency:'EUR'}):'—'};
  const date=v=>{try{return new Date(v).toLocaleString('pt-PT',{dateStyle:'short',timeStyle:'short'})}catch(_){return String(v||'')}};
  const statuses=['Todas','Recebida','Em preparação','Enviada','Concluída','Cancelada'];
  const cls=s=>s==='Concluída'?'green':s==='Cancelada'?'red':s==='Enviada'?'blue':s==='Em preparação'?'orange':'';
  let orders=[];
  function name(o){return o.customer?.name||o.data?.customerName||o.data?.name||o.data?.email||'Cliente';}
  function email(o){return o.customer?.email||o.data?.email||'';}
  function total(o){return o.total ?? o.data?.total ?? o.data?.totalPrice ?? o.data?.amount ?? 0;}
  function items(o){return Array.isArray(o.items)?o.items:(Array.isArray(o.data?.items)?o.data.items:[])}
  async function load(){
    const r=await fetch('/api/admin/orders',{cache:'no-store'}); const j=await r.json();
    if(!j.ok)throw new Error(j.error||'Erro ao ler encomendas'); orders=j.orders||[]; render();
  }
  async function setStatus(id,status){
    const r=await fetch('/api/admin/orders/status',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id,status})});
    const j=await r.json(); if(!j.ok)throw new Error(j.error||'Erro ao atualizar');
    const o=orders.find(x=>x.id===id); if(o)o.status=status; render();
  }
  function render(){
    const app=document.getElementById('app'); if(!app)return;
    app.innerHTML=`<section class="page mm-orders-page"><div class="pagehead"><div><h1>Encomendas</h1><p>Gestão central das encomendas da loja.</p></div><div class="date">PostgreSQL · dados reais</div></div>
      <div class="mm-order-toolbar"><div class="mm-order-filters">${statuses.map((s,i)=>`<button class="mm-order-filter ${i===0?'active':''}" data-filter="${esc(s)}">${esc(s)} <b>${s==='Todas'?orders.length:orders.filter(o=>o.status===s).length}</b></button>`).join('')}</div><button class="btn" id="mmOrderRefresh">↻ Atualizar</button></div>
      <div class="card"><div class="tablewrap"><table class="table mm-orders-table"><thead><tr><th>Encomenda</th><th>Cliente</th><th>Data</th><th>Artigos</th><th>Total</th><th>Estado</th></tr></thead><tbody id="mmOrdersBody"></tbody></table></div><div id="mmOrdersEmpty" class="mm-orders-empty" style="display:none">Não existem encomendas neste estado.</div></div></section>`;
    const body=document.getElementById('mmOrdersBody');
    function draw(filter='Todas'){
      const list=filter==='Todas'?orders:orders.filter(o=>o.status===filter);
      body.innerHTML=list.map(o=>`<tr><td><b>#${o.id}</b></td><td><b>${esc(name(o))}</b><br><small>${esc(email(o))}</small></td><td>${esc(date(o.created_at))}</td><td>${items(o).length||'—'}</td><td><b>${money(total(o))}</b></td><td><select class="mm-order-status status ${cls(o.status)}" data-id="${o.id}">${statuses.slice(1).map(s=>`<option ${s===o.status?'selected':''}>${esc(s)}</option>`).join('')}</select></td></tr>`).join('');
      document.getElementById('mmOrdersEmpty').style.display=list.length?'none':'block';
      body.querySelectorAll('.mm-order-status').forEach(el=>el.onchange=async()=>{try{await setStatus(Number(el.dataset.id),el.value)}catch(e){alert(e.message)}});
    }
    document.querySelectorAll('.mm-order-filter').forEach(b=>b.onclick=()=>{document.querySelectorAll('.mm-order-filter').forEach(x=>x.classList.remove('active'));b.classList.add('active');draw(b.dataset.filter)});
    document.getElementById('mmOrderRefresh').onclick=async()=>{try{await load()}catch(e){alert(e.message)}};
    draw('Todas');
  }
  function open(){load().catch(e=>{const app=document.getElementById('app');if(app)app.innerHTML=`<section class="page"><div class="pagehead"><div><h1>Encomendas</h1><p>Gestão central das encomendas da loja.</p></div></div><div class="card info"><h3>Não foi possível carregar as encomendas</h3><p>${esc(e.message)}</p><button class="btn" onclick="location.reload()">Tentar novamente</button></div></section>`})}
  function install(){
    const nav=document.querySelector('.navitem[data-section="orders"]');
    if(!nav)return false;
    nav.addEventListener('click',e=>{e.preventDefault();e.stopImmediatePropagation();open();document.querySelectorAll('.navitem').forEach(b=>b.classList.toggle('active',b===nav));document.getElementById('sidebar')?.classList.remove('open')},true);
    if(window.MMAdmin?.go){const old=window.MMAdmin.go;window.MMAdmin.go=(k)=>k==='orders'?open():old(k)}
    window.MMOrdersAdmin={open,load}; return true;
  }
  const t=setInterval(()=>{if(install())clearInterval(t)},100); setTimeout(()=>clearInterval(t),20000);
})();

/* MarquesMater V10.61 — camada final de apresentação do Backoffice.
   Não altera a lógica dos módulos. Corrige a apresentação mobile de Artigos
   e garante um filtro de estado visível nas Encomendas. */
(()=>{
  'use strict';
  const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]));

  const style=document.createElement('style');
  style.id='mm61-final-mobile-css';
  style.textContent=`
    /* ===== ARTIGOS / PRODUTOS ===== */
    .mm61-product-grid{display:grid;gap:12px;width:100%;box-sizing:border-box}
    .mm61-product-card{background:#fff;border:1px solid #dfe6ef;border-radius:16px;padding:14px;box-shadow:0 3px 12px rgba(16,32,68,.07);box-sizing:border-box;width:100%;overflow:hidden}
    .mm61-product-top{display:flex;align-items:center;gap:12px;padding-bottom:12px;border-bottom:1px solid #edf1f5}
    .mm61-product-image{width:64px;height:64px;object-fit:contain;flex:0 0 64px;border-radius:10px;background:#f8fafc}
    .mm61-product-name{font-size:15px;font-weight:800;color:#102044;line-height:1.25;overflow-wrap:anywhere}
    .mm61-product-main{min-width:0;flex:1}
    .mm61-product-sku{font-size:11px;color:#64748b;margin-top:4px;overflow-wrap:anywhere}
    .mm61-product-grid2{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px}
    .mm61-field{min-width:0;font-size:14px;color:#24344d;overflow-wrap:anywhere}
    .mm61-label{display:block;font-size:10px;font-weight:800;letter-spacing:.02em;text-transform:uppercase;color:#8794a7;margin-bottom:3px}
    .mm61-price{font-size:16px;font-weight:800}
    .mm61-state{display:inline-flex;padding:5px 9px;border-radius:999px;background:#dcfce7;color:#166534;font-size:11px;font-weight:800}
    .mm61-actions{display:flex;gap:8px;margin-top:13px;padding-top:12px;border-top:1px solid #edf1f5}
    .mm61-actions .btn{flex:1;min-width:0}
    .mm61-source-hidden{display:none!important}

    /* ===== ENCOMENDAS ===== */
    .mm61-order-filter-wrap{display:flex;align-items:center;gap:10px;flex-wrap:wrap;width:100%;margin:0 0 14px}
    .mm61-order-filter-label{font-size:12px;font-weight:800;color:#475569;white-space:nowrap}
    .mm61-order-state-select{height:42px;border:1px solid #cfd9e6;border-radius:10px;background:#fff;color:#102044;font:inherit;font-weight:700;padding:0 38px 0 12px;min-width:220px;max-width:100%;cursor:pointer}
    .mm61-order-count{font-size:12px;color:#64748b}
    @media(max-width:760px){
      .mm104 .tablewrap{overflow:visible!important}
      .mm104 .table{display:none!important}
      .mm104 .card{overflow:visible!important}
      .mm61-product-grid{display:grid!important}
      .mm61-product-grid2{grid-template-columns:1fr 1fr}
      .mm61-order-filter-wrap{display:grid;grid-template-columns:1fr;gap:7px}
      .mm61-order-state-select{width:100%;min-width:0;height:46px;font-size:15px}
      .mm61-order-count{font-size:11px}
    }
    @media(min-width:761px){.mm61-product-grid{display:none!important}}
  `;
  document.head.appendChild(style);

  function buildProductCards(root){
    if(!root||root.dataset.mm61Products==='1')return;
    const table=root.querySelector('.table');
    if(!table)return;
    const rows=[...table.querySelectorAll('tbody tr')];
    if(!rows.length)return;
    const card=table.closest('.card');
    if(!card)return;

    const grid=document.createElement('div');
    grid.className='mm61-product-grid';
    grid.id='mm61ProductGrid';

    rows.forEach((row,index)=>{
      const td=row.children;
      if(td.length<8)return;
      const image=td[0].querySelector('img');
      const name=td[0].querySelector('b')?.textContent?.trim()||td[0].textContent.trim();
      const sku=td[1].textContent.trim();
      const brand=td[2].textContent.trim();
      const category=td[3].childNodes[0]?.textContent?.trim()||td[3].textContent.trim();
      const sub=td[3].querySelector('small')?.textContent?.trim()||'';
      const price=td[4].textContent.trim();
      const stock=td[5].textContent.trim();
      const state=td[6].textContent.trim();

      const c=document.createElement('article');
      c.className='mm61-product-card';
      c.dataset.rowIndex=String(index);
      c.dataset.q=(row.dataset.q||`${name} ${sku} ${brand}`).toLowerCase();
      c.dataset.cat=row.dataset.c||'';
      c.innerHTML=`
        <div class="mm61-product-top">
          <img class="mm61-product-image" src="${esc(image?.getAttribute('src')||'images/drill.svg')}" alt="">
          <div class="mm61-product-main"><div class="mm61-product-name">${esc(name)}</div><div class="mm61-product-sku">SKU: ${esc(sku)}</div></div>
        </div>
        <div class="mm61-product-grid2">
          <div class="mm61-field"><span class="mm61-label">Marca</span>${esc(brand||'—')}</div>
          <div class="mm61-field"><span class="mm61-label">Preço</span><span class="mm61-price">${esc(price||'—')}</span></div>
          <div class="mm61-field"><span class="mm61-label">Categoria</span>${esc(category||'—')}${sub?`<br><small>${esc(sub)}</small>`:''}</div>
          <div class="mm61-field"><span class="mm61-label">Stock</span>${esc(stock||'—')}</div>
          <div class="mm61-field"><span class="mm61-label">Estado</span><span class="mm61-state">${esc(state||'—')}</span></div>
        </div>
        <div class="mm61-actions"></div>`;

      // Move the real buttons so the existing onclick handlers remain intact.
      const actions=c.querySelector('.mm61-actions');
      td[7].querySelectorAll('.btn').forEach(btn=>actions.appendChild(btn));
      grid.appendChild(c);
    });

    card.parentNode.insertBefore(grid,card.nextSibling);
    card.classList.add('mm61-source-hidden');
    root.dataset.mm61Products='1';

    const sync=()=>{
      const q=(root.querySelector('#mmq')?.value||'').toLowerCase().trim();
      const cat=root.querySelector('#mmc')?.value||'';
      grid.querySelectorAll('.mm61-product-card').forEach(c=>{
        c.style.display=(!q||c.dataset.q.includes(q))&&(!cat||c.dataset.cat===cat)?'':'none';
      });
    };
    root.querySelector('#mmq')?.addEventListener('input',sync);
    root.querySelector('#mmc')?.addEventListener('change',sync);
    sync();
  }

  function installOrderFilter(root){
    if(!root||root.querySelector('.mm61-order-filter-wrap'))return;
    const toolbar=root.querySelector('.mm-order-toolbar');
    const filters=root.querySelector('.mm-order-filters');
    if(!toolbar||!filters)return;
    const buttons=[...filters.querySelectorAll('.mm-order-filter')];
    if(!buttons.length)return;

    const wrap=document.createElement('div');
    wrap.className='mm61-order-filter-wrap';
    const label=document.createElement('span');
    label.className='mm61-order-filter-label';
    label.textContent='Estado a trabalhar:';
    const select=document.createElement('select');
    select.className='mm61-order-state-select';
    select.innerHTML=buttons.map(b=>`<option value="${esc(b.dataset.filter||b.textContent.replace(/\d/g,''))}">${esc((b.dataset.filter||b.textContent).replace(/\s*\d+\s*$/,''))}</option>`).join('');
    const count=document.createElement('span');
    count.className='mm61-order-count';

    const updateCount=()=>{
      const active=buttons.find(b=>b.classList.contains('active'))||buttons[0];
      const text=active?.textContent||'';
      const m=text.match(/(\d+)\s*$/);
      count.textContent=m?`${m[1]} encomenda(s)`:'';
      if(active)select.value=active.dataset.filter||'Todas';
    };
    select.onchange=()=>{
      const b=buttons.find(x=>(x.dataset.filter||'')===select.value);
      if(b)b.click();
      setTimeout(updateCount,0);
    };
    buttons.forEach(b=>b.addEventListener('click',()=>setTimeout(updateCount,0)));
    wrap.append(label,select,count);
    toolbar.insertBefore(wrap,toolbar.firstChild);
    updateCount();
  }

  function scan(){
    const app=document.getElementById('app');
    if(!app)return;
    const productsRoot=app.querySelector('.mm104');
    if(productsRoot&&productsRoot.querySelector('.table'))buildProductCards(productsRoot);
    const ordersRoot=app.querySelector('.mm-orders-page');
    if(ordersRoot)installOrderFilter(ordersRoot);
  }

  const observer=new MutationObserver(()=>setTimeout(scan,0));
  const app=document.getElementById('app');
  if(app)observer.observe(app,{childList:true,subtree:true});
  scan();
})();

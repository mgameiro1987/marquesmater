/* MarquesMater V10.63 — apresentação final do Backoffice.
   Produtos: cartões reais no telemóvel, sem tabela horizontal.
   Encomendas: filtro de estado visível no telemóvel. */
(()=>{
'use strict';

const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]));

function installCSS(){
 if(document.getElementById('mm63-css')) return;
 const s=document.createElement('style');
 s.id='mm63-css';
 s.textContent=`
.mm63-product-grid{display:none;width:100%;box-sizing:border-box;gap:12px}
.mm63-product-card{background:#fff;border:1px solid #dfe6ef;border-radius:16px;padding:14px;box-shadow:0 3px 12px rgba(16,32,68,.07);box-sizing:border-box;width:100%;overflow:hidden}
.mm63-product-top{display:flex;align-items:center;gap:12px;padding-bottom:12px;border-bottom:1px solid #edf1f5}
.mm63-product-image{width:64px;height:64px;object-fit:contain;flex:0 0 64px;border-radius:10px;background:#f8fafc}
.mm63-product-main{min-width:0;flex:1}
.mm63-product-name{font-size:15px;font-weight:800;color:#102044;line-height:1.25;overflow-wrap:anywhere}
.mm63-product-sku{font-size:11px;color:#64748b;margin-top:4px;overflow-wrap:anywhere}
.mm63-product-grid2{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px}
.mm63-field{min-width:0;font-size:14px;color:#24344d;overflow-wrap:anywhere}
.mm63-label{display:block;font-size:10px;font-weight:800;letter-spacing:.02em;text-transform:uppercase;color:#8794a7;margin-bottom:3px}
.mm63-price{font-size:16px;font-weight:800}
.mm63-state{display:inline-flex;padding:5px 9px;border-radius:999px;background:#dcfce7;color:#166534;font-size:11px;font-weight:800}
.mm63-state.off{background:#fee2e2;color:#991b1b}
.mm63-actions{display:flex;gap:8px;margin-top:13px;padding-top:12px;border-top:1px solid #edf1f5}
.mm63-actions .btn{flex:1;min-width:0}
.mm63-source-hidden{display:none!important}
.mm63-order-filter-wrap{display:flex;align-items:center;gap:10px;flex-wrap:wrap;width:100%;margin:0 0 14px}
.mm63-order-filter-label{font-size:12px;font-weight:800;color:#475569;white-space:nowrap}
.mm63-order-state-select{height:42px;border:1px solid #cfd9e6;border-radius:10px;background:#fff;color:#102044;font:inherit;font-weight:700;padding:0 38px 0 12px;min-width:220px;max-width:100%;cursor:pointer}
.mm63-order-count{font-size:12px;color:#64748b}
@media(max-width:760px){
 .mm104 .tablewrap{overflow:visible!important}
 .mm104 .table{display:none!important}
 .mm104 .card{overflow:visible!important}
 .mm63-product-grid{display:grid!important}
 .mm63-product-grid2{grid-template-columns:1fr 1fr}
 .mm63-order-filter-wrap{display:grid;grid-template-columns:1fr;gap:7px}
 .mm63-order-state-select{width:100%;min-width:0;height:46px;font-size:15px}
}
@media(min-width:761px){.mm63-product-grid{display:none!important}}
`;
 document.head.appendChild(s);
}

function buildProductCards(root){
 if(!root || root.dataset.mm63Products==='1') return;
 const table=root.querySelector('table.table');
 if(!table) return;
 const rows=[...table.querySelectorAll('tbody tr')];
 if(!rows.length) return;
 const sourceCard=table.closest('.card');
 if(!sourceCard) return;

 const grid=document.createElement('div');
 grid.className='mm63-product-grid';
 grid.id='mm63ProductGrid';

 rows.forEach((row,index)=>{
   const td=[...row.children];
   if(td.length<8) return;
   const img=td[0].querySelector('img');
   const name=td[0].querySelector('b')?.textContent?.trim() || td[0].textContent.trim();
   const sku=td[1].textContent.trim();
   const brand=td[2].textContent.trim();
   const category=td[3].childNodes[0]?.textContent?.trim() || td[3].textContent.trim();
   const sub=td[3].querySelector('small')?.textContent?.trim() || '';
   const price=td[4].textContent.trim();
   const stock=td[5].textContent.trim();
   const state=td[6].textContent.trim();
   const inactive=/inativo/i.test(state);

   const card=document.createElement('article');
   card.className='mm63-product-card';
   card.dataset.rowIndex=String(index);
   card.dataset.q=(row.dataset.q || `${name} ${sku} ${brand}`).toLowerCase();
   card.dataset.cat=row.dataset.c || '';
   card.innerHTML=`
    <div class="mm63-product-top">
      <img class="mm63-product-image" src="${esc(img?.getAttribute('src') || 'images/drill.svg')}" alt="">
      <div class="mm63-product-main">
        <div class="mm63-product-name">${esc(name)}</div>
        <div class="mm63-product-sku">SKU: ${esc(sku || '—')}</div>
      </div>
    </div>
    <div class="mm63-product-grid2">
      <div class="mm63-field"><span class="mm63-label">Marca</span>${esc(brand || '—')}</div>
      <div class="mm63-field"><span class="mm63-label">Preço</span><span class="mm63-price">${esc(price || '—')}</span></div>
      <div class="mm63-field"><span class="mm63-label">Categoria</span>${esc(category || '—')}${sub?`<br><small>${esc(sub)}</small>`:''}</div>
      <div class="mm63-field"><span class="mm63-label">Stock</span>${esc(stock || '—')}</div>
      <div class="mm63-field"><span class="mm63-label">Estado</span><span class="mm63-state ${inactive?'off':''}">${esc(state || '—')}</span></div>
    </div>
    <div class="mm63-actions"></div>`;

   // Os botões reais são movidos, preservando os onclick já instalados pelo módulo de Produtos.
   const actions=card.querySelector('.mm63-actions');
   td[7].querySelectorAll('.btn').forEach(btn=>actions.appendChild(btn));
   grid.appendChild(card);
 });

 if(!grid.children.length) return;
 sourceCard.parentNode.insertBefore(grid,sourceCard.nextSibling);
 sourceCard.classList.add('mm63-source-hidden');
 root.dataset.mm63Products='1';

 const sync=()=>{
   const q=(root.querySelector('#mmq')?.value || '').toLowerCase().trim();
   const cat=root.querySelector('#mmc')?.value || '';
   grid.querySelectorAll('.mm63-product-card').forEach(c=>{
     const okQ=!q || c.dataset.q.includes(q);
     const okC=!cat || c.dataset.cat===cat;
     c.style.display=okQ && okC ? '' : 'none';
   });
 };
 root.querySelector('#mmq')?.addEventListener('input',sync);
 root.querySelector('#mmc')?.addEventListener('change',sync);
 sync();
}

function installOrderFilter(root){
 if(!root || root.querySelector('.mm63-order-filter-wrap')) return;
 const toolbar=root.querySelector('.mm-order-toolbar');
 const filters=root.querySelector('.mm-order-filters');
 if(!toolbar || !filters) return;
 const buttons=[...filters.querySelectorAll('.mm-order-filter')];
 if(!buttons.length) return;

 const wrap=document.createElement('div');
 wrap.className='mm63-order-filter-wrap';
 const label=document.createElement('span');
 label.className='mm63-order-filter-label';
 label.textContent='Estado a trabalhar:';
 const select=document.createElement('select');
 select.className='mm63-order-state-select';
 const opts=buttons.map(b=>{
   const value=b.dataset.filter || b.textContent.replace(/\d/g,'').trim();
   const text=(b.dataset.filter || b.textContent).replace(/\s*\d+\s*$/,'').trim();
   return `<option value="${esc(value)}">${esc(text)}</option>`;
 }).join('');
 select.innerHTML=opts;
 const count=document.createElement('span');
 count.className='mm63-order-count';

 const sync=()=>{
   const active=buttons.find(b=>b.classList.contains('active')) || buttons[0];
   if(active){
     select.value=active.dataset.filter || active.textContent.replace(/\d/g,'').trim();
     const m=(active.textContent||'').match(/(\d+)\s*$/);
     count.textContent=m ? `${m[1]} encomenda(s)` : '';
   }
 };
 select.onchange=()=>{
   const b=buttons.find(x=>(x.dataset.filter || x.textContent.replace(/\d/g,'').trim())===select.value);
   if(b) b.click();
   setTimeout(sync,30);
 };
 buttons.forEach(b=>b.addEventListener('click',()=>setTimeout(sync,30)));
 wrap.append(label,select,count);
 toolbar.insertBefore(wrap,toolbar.firstChild);
 sync();
}

function scan(){
 const app=document.getElementById('app');
 if(!app) return;
 const products=app.querySelector('.mm104');
 if(products && products.querySelector('table.table')) buildProductCards(products);
 const orders=app.querySelector('.mm-orders-page');
 if(orders) installOrderFilter(orders);
}

installCSS();

const app=document.getElementById('app');
if(app){
 const observer=new MutationObserver(()=>setTimeout(scan,20));
 observer.observe(app,{childList:true,subtree:true});
}
scan();
// Reforço: o módulo de Produtos reconstrói o conteúdo ao abrir/atualizar. Esta verificação
// garante que a camada mobile entra sempre depois dessa reconstrução, sem depender de cache.
setInterval(scan,500);
})();
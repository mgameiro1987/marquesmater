/* MarquesMater V10.64 — apresentação final do Backoffice.
   Produtos: cartões em telemóvel, tablet e vista computador-forçada.
   Encomendas: filtro de estado visível. Suporta também a tabela antiga de Produtos. */
(()=>{
'use strict';
const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]));

function installCSS(){
 if(document.getElementById('mm64-css')) return;
 const s=document.createElement('style');s.id='mm64-css';
 s.textContent=`
.mm64-product-grid{display:none;width:100%;box-sizing:border-box;gap:12px}
.mm64-product-card{background:#fff;border:1px solid #dfe6ef;border-radius:16px;padding:14px;box-shadow:0 3px 12px rgba(16,32,68,.07);box-sizing:border-box;width:100%;overflow:hidden}
.mm64-product-top{display:flex;align-items:center;gap:12px;padding-bottom:12px;border-bottom:1px solid #edf1f5}
.mm64-product-image{width:64px;height:64px;object-fit:contain;flex:0 0 64px;border-radius:10px;background:#f8fafc}
.mm64-product-main{min-width:0;flex:1}
.mm64-product-name{font-size:15px;font-weight:800;color:#102044;line-height:1.25;overflow-wrap:anywhere}
.mm64-product-sku{font-size:11px;color:#64748b;margin-top:4px;overflow-wrap:anywhere}
.mm64-product-grid2{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px}
.mm64-field{min-width:0;font-size:14px;color:#24344d;overflow-wrap:anywhere}
.mm64-label{display:block;font-size:10px;font-weight:800;letter-spacing:.02em;text-transform:uppercase;color:#8794a7;margin-bottom:3px}
.mm64-price{font-size:16px;font-weight:800}
.mm64-state{display:inline-flex;padding:5px 9px;border-radius:999px;background:#dcfce7;color:#166534;font-size:11px;font-weight:800}
.mm64-state.off{background:#fee2e2;color:#991b1b}
.mm64-actions{display:flex;gap:8px;margin-top:13px;padding-top:12px;border-top:1px solid #edf1f5}
.mm64-actions .btn{flex:1;min-width:0}
.mm64-source-hidden{display:none!important}
.mm64-mobile-view .mm104 .tablewrap{overflow:visible!important}
.mm64-mobile-view .mm104 .table{display:none!important}
.mm64-mobile-view .mm64-product-grid{display:grid!important}
@media(max-width:1100px){
 .mm104 .tablewrap{overflow:visible!important}
 .mm104 .table{display:none!important}
 .mm64-product-grid{display:grid!important}
}
@media(min-width:1101px){.mm64-product-grid{display:none!important}}
.mm64-order-filter-wrap{display:flex;align-items:center;gap:10px;flex-wrap:wrap;width:100%;margin:0 0 14px}
.mm64-order-filter-label{font-size:12px;font-weight:800;color:#475569;white-space:nowrap}
.mm64-order-state-select{height:42px;border:1px solid #cfd9e6;border-radius:10px;background:#fff;color:#102044;font:inherit;font-weight:700;padding:0 38px 0 12px;min-width:220px;max-width:100%;cursor:pointer}
.mm64-order-count{font-size:12px;color:#64748b}
@media(max-width:760px){.mm64-product-grid2{grid-template-columns:1fr 1fr}.mm64-order-filter-wrap{display:grid;grid-template-columns:1fr;gap:7px}.mm64-order-state-select{width:100%;min-width:0;height:46px;font-size:15px}}
`;
 document.head.appendChild(s);
}

function isMobileDevice(){
 const ua=navigator.userAgent||'';
 const mobileUA=/Android|iPhone|iPad|iPod|Mobile/i.test(ua);
 const coarse=window.matchMedia?.('(pointer:coarse)').matches;
 return mobileUA || coarse;
}
function applyMode(){
 const app=document.getElementById('app');if(!app)return;
 const mobile=isMobileDevice() || window.innerWidth<=1100;
 document.documentElement.classList.toggle('mm64-mobile-view',mobile);
}

function buildProductCards(root){
 if(!root)return;
 const table=root.querySelector('table.table');if(!table)return;
 if(root.dataset.mm64Products==='1')return;
 const rows=[...table.querySelectorAll('tbody tr')];if(!rows.length)return;
 const sourceCard=table.closest('.card');if(!sourceCard)return;

 const headers=[...table.querySelectorAll('thead th')].map(x=>x.textContent.trim().toLowerCase());
 const idx=(...names)=>{for(const n of names){const i=headers.findIndex(h=>h===n||h.includes(n));if(i>=0)return i}return -1};
 const iProduct=idx('produto','artigo');
 const iSku=idx('sku');
 const iBrand=idx('marca');
 const iCategory=idx('categoria');
 const iPrice=idx('preço','preco');
 const iStock=idx('stock');
 const iState=idx('estado');
 const iActions=idx('ações','acoes');
 if(iProduct<0||iActions<0)return;

 const grid=document.createElement('div');grid.className='mm64-product-grid';grid.id='mm64ProductGrid';
 rows.forEach((row,index)=>{
   const td=[...row.children];if(!td.length)return;
   const cell=i=>i>=0&&td[i]?td[i]:null;
   const productCell=cell(iProduct),skuCell=cell(iSku),brandCell=cell(iBrand),catCell=cell(iCategory),priceCell=cell(iPrice),stockCell=cell(iStock),stateCell=cell(iState),actionsCell=cell(iActions);
   const img=productCell?.querySelector('img');
   const name=productCell?.querySelector('b')?.textContent?.trim()||productCell?.textContent?.trim()||'Produto';
   const sku=skuCell?.textContent?.trim()||'';
   const brand=brandCell?.textContent?.trim()||'';
   const category=catCell?.childNodes[0]?.textContent?.trim()||catCell?.textContent?.trim()||'';
   const sub=catCell?.querySelector('small')?.textContent?.trim()||'';
   const price=priceCell?.textContent?.trim()||'';
   const stock=stockCell?.textContent?.trim()||'';
   const state=stateCell?.textContent?.trim()||'';
   const inactive=/inativo|inact/i.test(state);
   const card=document.createElement('article');card.className='mm64-product-card';
   card.dataset.q=(row.dataset.q||`${name} ${sku} ${brand}`).toLowerCase();card.dataset.cat=row.dataset.c||'';card.dataset.rowIndex=String(index);
   card.innerHTML=`<div class="mm64-product-top"><img class="mm64-product-image" src="${esc(img?.getAttribute('src')||'images/drill.svg')}" alt=""><div class="mm64-product-main"><div class="mm64-product-name">${esc(name)}</div><div class="mm64-product-sku">SKU: ${esc(sku||'—')}</div></div></div><div class="mm64-product-grid2"><div class="mm64-field"><span class="mm64-label">Marca</span>${esc(brand||'—')}</div><div class="mm64-field"><span class="mm64-label">Preço</span><span class="mm64-price">${esc(price||'—')}</span></div><div class="mm64-field"><span class="mm64-label">Categoria</span>${esc(category||'—')}${sub?`<br><small>${esc(sub)}</small>`:''}</div><div class="mm64-field"><span class="mm64-label">Stock</span>${esc(stock||'—')}</div><div class="mm64-field"><span class="mm64-label">Estado</span><span class="mm64-state ${inactive?'off':''}">${esc(state||'—')}</span></div></div><div class="mm64-actions"></div>`;
   const actions=card.querySelector('.mm64-actions');
   actionsCell?.querySelectorAll('.btn').forEach(btn=>actions.appendChild(btn));
   grid.appendChild(card);
 });
 if(!grid.children.length)return;
 sourceCard.parentNode.insertBefore(grid,sourceCard.nextSibling);
 sourceCard.classList.add('mm64-source-hidden');root.dataset.mm64Products='1';
 const sync=()=>{const q=(root.querySelector('#mmq')?.value||'').toLowerCase().trim();const cat=root.querySelector('#mmc')?.value||'';grid.querySelectorAll('.mm64-product-card').forEach(c=>{c.style.display=(!q||c.dataset.q.includes(q))&&(!cat||c.dataset.cat===cat)?'':'none'})};
 root.querySelector('#mmq')?.addEventListener('input',sync);root.querySelector('#mmc')?.addEventListener('change',sync);sync();
}

function installOrderFilter(root){
 if(!root||root.querySelector('.mm64-order-filter-wrap'))return;
 const toolbar=root.querySelector('.mm-order-toolbar'),filters=root.querySelector('.mm-order-filters');if(!toolbar||!filters)return;
 const buttons=[...filters.querySelectorAll('.mm-order-filter')];if(!buttons.length)return;
 const wrap=document.createElement('div');wrap.className='mm64-order-filter-wrap';
 const label=document.createElement('span');label.className='mm64-order-filter-label';label.textContent='Estado a trabalhar:';
 const select=document.createElement('select');select.className='mm64-order-state-select';
 select.innerHTML=buttons.map(b=>{const v=b.dataset.filter||b.textContent.replace(/\d/g,'').trim();const t=(b.dataset.filter||b.textContent).replace(/\s*\d+\s*$/,'').trim();return `<option value="${esc(v)}">${esc(t)}</option>`}).join('');
 const count=document.createElement('span');count.className='mm64-order-count';
 const sync=()=>{const active=buttons.find(b=>b.classList.contains('active'))||buttons[0];if(active){select.value=active.dataset.filter||active.textContent.replace(/\d/g,'').trim();const m=(active.textContent||'').match(/(\d+)\s*$/);count.textContent=m?`${m[1]} encomenda(s)`:''}};
 select.onchange=()=>{const b=buttons.find(x=>(x.dataset.filter||x.textContent.replace(/\d/g,'').trim())===select.value);if(b)b.click();setTimeout(sync,30)};buttons.forEach(b=>b.addEventListener('click',()=>setTimeout(sync,30)));wrap.append(label,select,count);toolbar.insertBefore(wrap,toolbar.firstChild);sync();
}

function scan(){installCSS();applyMode();const app=document.getElementById('app');if(!app)return;const products=app.querySelector('.mm104');if(products&&products.querySelector('table.table'))buildProductCards(products);const orders=app.querySelector('.mm-orders-page');if(orders)installOrderFilter(orders)}
window.addEventListener('resize',applyMode);
scan();
const app=document.getElementById('app');if(app){const observer=new MutationObserver(()=>setTimeout(scan,20));observer.observe(app,{childList:true,subtree:true})}
setInterval(scan,500);
})();
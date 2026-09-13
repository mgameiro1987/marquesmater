/* MarquesMater V10.67 — Produtos: bloqueio definitivo do renderer antigo */
(()=>{
'use strict';
const app=document.getElementById('app');
if(!app)return;
const esc=s=>String(s??'').replace(/[&<>\"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#039;'}[m]));
const money=n=>Number(n||0).toLocaleString('pt-PT',{style:'currency',currency:'EUR'});
const api=async u=>{const r=await fetch(u,{cache:'no-store'});const j=await r.json();if(!r.ok||j.ok===false)throw Error(j.error||`Erro ${r.status}`);return j};
let rendering=false;
function css(){if(document.getElementById('mm67-css'))return;const s=document.createElement('style');s.id='mm67-css';s.textContent=`
.mm65-page{padding-bottom:30px}.mm65-toolbar{display:flex;gap:9px;flex-wrap:wrap;margin-bottom:14px}.mm65-toolbar input,.mm65-toolbar select{border:1px solid #d7dee8;border-radius:9px;padding:10px;background:#fff;font:inherit}.mm65-toolbar input{flex:1;min-width:220px}.mm65-btn{border:0;border-radius:9px;padding:10px 14px;font-weight:700;cursor:pointer;background:#1677f9;color:#fff}.mm65-btn.alt{background:#64748b}.mm65-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.mm65-card{background:#fff;border:1px solid #dfe6ef;border-radius:16px;overflow:hidden;box-shadow:0 3px 12px rgba(16,32,68,.07);min-width:0}.mm65-head{height:108px;background:#f6f9fd;display:flex;align-items:center;justify-content:center}.mm65-img{width:72px;height:72px;object-fit:contain;border-radius:12px;background:#fff;padding:5px;box-sizing:border-box}.mm65-body{padding:13px}.mm65-name{font-weight:800;font-size:14px;line-height:1.3;color:#102044;min-height:36px;overflow-wrap:anywhere}.mm65-sku{font-size:10px;color:#64748b;margin-top:4px;overflow-wrap:anywhere}.mm65-meta{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin-top:12px}.mm65-field{min-width:0;font-size:12px;color:#24344d;overflow-wrap:anywhere}.mm65-label{display:block;font-size:9px;font-weight:800;text-transform:uppercase;color:#8794a7;margin-bottom:3px}.mm65-price{font-size:15px;font-weight:800}.mm65-pill{display:inline-flex;padding:4px 7px;border-radius:99px;background:#dcfce7;color:#166534;font-size:9px;font-weight:800}.mm65-pill.off{background:#fee2e2;color:#991b1b}.mm65-actions{display:flex;gap:6px;margin-top:12px;padding-top:10px;border-top:1px solid #edf1f5}.mm65-actions .btn{flex:1;min-width:0}.mm65-empty{padding:30px;text-align:center;color:#64748b;background:#fff;border:1px solid #dfe6ef;border-radius:14px}.mm65-page .notice{margin-bottom:14px}
@media(max-width:1100px){.mm65-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:760px){.mm65-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.mm65-head{height:92px}.mm65-body{padding:11px}.mm65-name{font-size:13px}.mm65-toolbar input{min-width:160px;width:100%}}
@media(max-width:480px){.mm65-grid{grid-template-columns:1fr}}
`;document.head.appendChild(s)}
function nav(){document.querySelectorAll('.navitem').forEach(x=>x.classList.toggle('active',x.dataset.section==='products'))}
async function render(){
 if(rendering)return; rendering=true; nav(); css();
 app.innerHTML=`<section class="page mm65-page"><div class="pagehead"><div><h1>Produtos</h1><p>Gestão real do catálogo central.</p></div></div><div class="notice">Produtos apresentados em cartões responsivos. A mesma informação e ações do catálogo central.</div><div class="mm65-toolbar"><input id="mm65q" placeholder="Pesquisar por nome ou SKU..."><select id="mm65c"><option value="">Todas as categorias</option></select><button class="mm65-btn" id="mm65new">＋ Novo produto</button><button class="mm65-btn alt" id="mm65exp">⇩ Exportar catálogo</button></div><div id="mm65grid" class="mm65-grid"><div class="mm65-empty">A carregar catálogo...</div></div></section>`;
 try{
  const ps=(await api('/api/catalog?include_inactive=1')).catalog||[];
  if(!document.querySelector('.mm65-page'))return;
  const cats=[...new Set(ps.map(p=>p.category).filter(Boolean))].sort((a,b)=>String(a).localeCompare(String(b),'pt'));
  const sel=document.getElementById('mm65c');if(sel)sel.innerHTML='<option value="">Todas as categorias</option>'+cats.map(c=>`<option value="${esc(c)}">${esc(c)}</option>`).join('');
  const grid=document.getElementById('mm65grid');if(!grid)return;
  grid.innerHTML=ps.map((p,i)=>{const inactive=p.active===false;return `<article class="mm65-card" data-q="${esc(`${p.name||''} ${p.sku||''} ${p.brand||''}`.toLowerCase())}" data-c="${esc(p.category||'')}"><div class="mm65-head"><img class="mm65-img" src="${esc(p.image||'images/drill.svg')}" alt=""></div><div class="mm65-body"><div class="mm65-name">${esc(p.name||'Sem nome')}</div><div class="mm65-sku">SKU: ${esc(p.sku||'—')}</div><div class="mm65-meta"><div class="mm65-field"><span class="mm65-label">Marca</span>${esc(p.brand||'—')}</div><div class="mm65-field"><span class="mm65-label">Preço</span><span class="mm65-price">${money(p.price)}</span></div><div class="mm65-field"><span class="mm65-label">Categoria</span>${esc(p.category||'—')}<br><small>${esc(p.subcategory||'')}</small></div><div class="mm65-field"><span class="mm65-label">Stock</span>${esc(p.stock||'Em stock')}<br><small>${Number(p.stockQty??0)} un.</small></div><div class="mm65-field"><span class="mm65-label">Estado</span><span class="mm65-pill ${inactive?'off':''}">${inactive?'Inativo':'Ativo'}</span></div></div><div class="mm65-actions"><button class="btn small" data-edit="${i}">Editar</button><button class="btn small red" data-toggle="${i}">${inactive?'Ativar':'Desativar'}</button></div></div></article>`}).join('')||'<div class="mm65-empty">Não existem produtos.</div>';
  const filter=()=>{const q=(document.getElementById('mm65q')?.value||'').toLowerCase().trim(),c=document.getElementById('mm65c')?.value||'';grid.querySelectorAll('.mm65-card').forEach(x=>x.style.display=(!q||x.dataset.q.includes(q))&&(!c||x.dataset.c===c)?'':'none')};
  document.getElementById('mm65q')?.addEventListener('input',filter);document.getElementById('mm65c')?.addEventListener('change',filter);
  document.getElementById('mm65new').onclick=()=>{const old=originalGo;if(old){old('products');setTimeout(()=>document.getElementById('mmnew')?.click(),30)}};
  document.getElementById('mm65exp').onclick=()=>{const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(ps,null,2)],{type:'application/json'}));a.download='marquesmater-catalogo.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)};
  document.querySelectorAll('#mm65grid [data-toggle]').forEach(b=>b.onclick=async()=>{const p=ps[+b.dataset.toggle];try{await api('/api/catalog',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...p,active:p.active===false})});render()}catch(e){alert(e.message)}});
 }catch(e){const g=document.getElementById('mm65grid');if(g)g.innerHTML=`<div class="mm65-empty">${esc(e.message)}</div>`}
 finally{rendering=false}
}
const originalGo=window.MM104?.go;
const productGo=k=>{if(k==='products')render();else if(originalGo)originalGo(k)};
try{Object.defineProperty(window.MM104,'go',{value:productGo,writable:false,configurable:false,enumerable:true})}catch(e){window.MM104.go=productGo}
document.addEventListener('click',e=>{const b=e.target.closest('.navitem[data-section="products"]');if(!b)return;e.preventDefault();e.stopImmediatePropagation();productGo('products');document.getElementById('sidebar')?.classList.remove('open')},true);
const guard=()=>{const active=document.querySelector('.navitem[data-section="products"].active');if(active&&!document.querySelector('.mm65-page')&&!rendering)render()};
if(document.querySelector('.navitem[data-section="products"].active'))render();
new MutationObserver(guard).observe(app,{childList:true,subtree:true});
setInterval(guard,250);
})();

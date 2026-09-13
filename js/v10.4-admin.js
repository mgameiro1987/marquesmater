(()=>{
'use strict';
const app=document.getElementById('app');
const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]));
const api=async(path,opts={})=>{const r=await fetch(path,{cache:'no-store',...opts,headers:{'Content-Type':'application/json',...(opts.headers||{})}});const j=await r.json().catch(()=>({}));if(!r.ok||j.ok===false)throw Error(j.error||`Erro ${r.status}`);return j};
const shell=(t,s,b,a='')=>`<section class="page mm104"><div class="pagehead"><div><h1>${t}</h1><p>${s}</p></div><div>${a}</div></div>${b}</section>`;
function nav(k){document.querySelectorAll('.navitem').forEach(x=>x.classList.toggle('active',x.dataset.section===k))}
async function loadProducts(){const j=await api('/api/catalog?include_inactive=1');return j.catalog||[]}
async function dashboard(){nav('dashboard');try{const ps=await loadProducts();app.innerHTML=shell('Dashboard','Backoffice central MarquesMater.',`<div class="statgrid"><div class="card stat"><small>Produtos ativos</small><strong>${ps.filter(p=>p.active!==false).length}</strong></div><div class="card stat"><small>Produtos total</small><strong>${ps.length}</strong></div><div class="card stat"><small>Promoções</small><strong>${ps.filter(p=>p.oldPrice!=null).length}</strong></div><div class="card stat"><small>Base de dados</small><strong>Online</strong></div></div><div class="card" style="margin-top:14px;padding:18px"><h2>Gestão central</h2><p>O Backoffice está ligado ao catálogo central PostgreSQL. A área Produtos é apresentada exclusivamente pelo módulo atual de Produtos.</p><button class="btn" onclick="document.querySelector('.navitem[data-section=\"products-v2\"]')?.click()">Gerir produtos</button></div>`)}catch(e){app.innerHTML=shell('Dashboard','',`<div class="card empty">${esc(e.message)}</div>`)}}
function prepared(k,title){nav(k);app.innerHTML=shell(title,'Área do Backoffice.',`<div class="card" style="padding:20px"><h3>${esc(title)}</h3><p>Esta área mantém a navegação central do Backoffice sem apresentar dados fictícios.</p></div>`)}
async function forceProducts(){
  const b=document.querySelector('.navitem[data-section="products-v2"]');
  if(!b)return;
  if(window.MM76ProductsRender){window.MM76ProductsRender();return;}
  try{
    if(!window.__MM76_PRODUCTS){
      await new Promise((resolve,reject)=>{const s=document.createElement('script');s.src='js/v10.76-products-new.js?v=778';s.onload=resolve;s.onerror=reject;document.body.appendChild(s)});
    }
    if(window.MM76ProductsRender)window.MM76ProductsRender();
    else b.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));
  }catch(e){app.innerHTML=shell('Produtos','Catálogo central.',`<div class="card empty">Não foi possível carregar o módulo de Produtos: ${esc(e.message)}</div>`)}
}
window.MM104={go:k=>{if(k==='dashboard')dashboard();else if(k==='products'||k==='products-v2')forceProducts();else prepared(k,k)}};
document.querySelectorAll('.navitem').forEach(b=>b.onclick=e=>{e.preventDefault();if(b.dataset.section==='products'||b.dataset.section==='products-v2'){forceProducts();document.getElementById('sidebar').classList.remove('open');return}MM104.go(b.dataset.section);document.getElementById('sidebar').classList.remove('open')});
const gs=document.getElementById('globalSearch');if(gs)gs.onkeydown=e=>{if(e.key==='Enter'&&gs.value.trim()){forceProducts().then(()=>setTimeout(()=>{const q=document.getElementById('mm76-q');if(q){q.value=gs.value;q.dispatchEvent(new Event('input'))}},150))}};
})();
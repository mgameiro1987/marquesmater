(()=>{
'use strict';
const app=document.getElementById('app');
const esc=s=>String(s??'').replace(/[&<>\"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#039;'}[m]));
const shell=(t,s,b,a='')=>`<section class="page mm104"><div class="pagehead"><div><h1>${t}</h1><p>${s}</p></div><div>${a}</div></div>${b}</section>`;
function nav(k){document.querySelectorAll('.navitem').forEach(x=>x.classList.toggle('active',x.dataset.section===k))}
async function loadProducts(){const r=await fetch('/api/catalog?include_inactive=1',{cache:'no-store'});const j=await r.json().catch(()=>({}));if(!r.ok||j.ok===false)throw Error(j.error||`Erro ${r.status}`);return j.catalog||[]}
async function dashboard(){nav('dashboard');try{const ps=await loadProducts();app.innerHTML=shell('Dashboard','Backoffice central MarquesMater.',`<div class="statgrid"><div class="card stat"><small>Produtos ativos</small><strong>${ps.filter(p=>p.active!==false).length}</strong></div><div class="card stat"><small>Produtos total</small><strong>${ps.length}</strong></div><div class="card stat"><small>Promoções</small><strong>${ps.filter(p=>p.oldPrice!=null).length}</strong></div><div class="card stat"><small>Base de dados</small><strong>Online</strong></div></div><div class="card" style="margin-top:14px;padding:18px"><h2>Gestão central</h2><p>O Backoffice está ligado ao catálogo central PostgreSQL.</p></div>`)}catch(e){app.innerHTML=shell('Dashboard','',`<div class="card empty">${esc(e.message)}</div>`)}}
function prepared(k,title){nav(k);app.innerHTML=shell(title,'Área do Backoffice.',`<div class="card" style="padding:20px"><h3>${esc(title)}</h3><p>Esta área está disponível através do módulo correspondente.</p></div>`)}
function products(){nav('products');if(typeof window.MM76ProductsRender==='function')return window.MM76ProductsRender();return prepared('products','Produtos')}
function variants(){nav('variants');if(typeof window.MMVariantsRender==='function')return window.MMVariantsRender();return prepared('variants','Variantes e preços')}
window.MM104={go:k=>{if(k==='dashboard')return dashboard();if(k==='products'||k==='products-v2')return products();if(k==='variants')return variants();prepared(k,k)}};
})();
(()=>{'use strict';if(window.__MM1013FOCUSYNC)return;window.__MM1013FOCUSYNC=1;
const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
const money=n=>Number(n||0).toFixed(2).replace('.',',')+' €';
async function run(){try{
 const sku=new URLSearchParams(location.search).get('sku');if(!sku)return;
 const pr=await fetch('/api/catalog/products?sku='+encodeURIComponent(sku)+'&v=1024',{cache:'no-store'});const pj=await pr.json();if(!pr.ok||!pj.item)return;
 const p=pj.item,a=p.attributes&&typeof p.attributes==='object'?p.attributes:{};
 let cls={};try{const cr=await fetch('/api/catalog/classification?productId='+encodeURIComponent(p.id)+'&v=1024',{cache:'no-store'});const cj=await cr.json();cls=Object.fromEntries((cj.classifications||[]).map(x=>[x.type,x]));}catch(e){}
 const com=cls.commercial||{},rid=cls.rida||{};
 const desc=p.description||'',chars=String(a.characteristics||''),specs=Array.isArray(p.specs)?p.specs:[],apps=String(a.applications||'');
 const price=document.getElementById('currentPrice');if(price)price.textContent=money(p.price);
 const subtitle=document.querySelector('.v6-subtitle');if(subtitle)subtitle.textContent=desc;
 const catLink=document.getElementById('catLink');if(catLink&&com.category){catLink.href='category.html?cat='+encodeURIComponent(com.category);catLink.textContent=com.category}
 const tabs=[...document.querySelectorAll('.v6-tabs button')],body=document.getElementById('tabbody');if(!body)return;
 const html={0:'<p>'+esc(desc)+'</p>',1:'<div class="mm-front-content">'+(chars?'<p>'+esc(chars).replace(/\n/g,'<br>')+'</p>':'<p>Consulte as características disponíveis para este produto.</p>')+'</div>',2:'<table class="mm-spec-table">'+(specs.length?specs.map(x=>{const z=String(x).split(':');return '<tr><td>'+esc(z[0])+'</td><td>'+esc(z.slice(1).join(':').trim())+'</td></tr>'}).join(''):'<tr><td>Informação</td><td>A confirmar</td></tr>')+'</table>',3:'<p>'+esc(apps||'Consulte as aplicações recomendadas para este produto.')+'</p>',4:'<p>Documentação técnica disponível em função do artigo.</p>',5:'<p>Avaliações do produto.</p>'};
 function show(i){body.innerHTML=html[i]||html[0];tabs.forEach((b,n)=>b.classList.toggle('active',n===i))}
 tabs.forEach((b,i)=>b.onclick=()=>show(i));show(0);
 const old=document.querySelector('.mm-front-classification');if(old)old.remove();
 if(com.category||rid.category){const d=document.createElement('div');d.className='mm-front-classification';d.innerHTML='<span>'+esc(com.category||'')+(com.subcategory?' · '+esc(com.subcategory):'')+'</span>'+(rid.category?'<span>RIDA · '+esc(rid.family||rid.subcategory||'')+'</span>':'');const del=document.querySelector('.delivery');if(del)del.before(d)}
 }catch(e){console.warn('Frontoffice sync indisponível',e)}}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',run);else run();
})();
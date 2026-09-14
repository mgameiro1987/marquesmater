/* MarquesMater V9.3.25 — estado de stock público sem revelar quantidades. */
(()=>{'use strict';
if(window.__MM9325PublicStock)return;window.__MM9325PublicStock=1;
const API='/api/stock';
const label=n=>Number(n)>2?'Stock':Number(n)>0?'Pouco stock':'Sem stock';
const cls=n=>Number(n)>2?'in':Number(n)>0?'low':'out';
const catalog=()=>window.MARQUES_CATALOG||[];
function css(){if(document.getElementById('mm9325publicstockcss'))return;const s=document.createElement('style');s.id='mm9325publicstockcss';s.textContent='.mm9325-public-stock{font-weight:800}.mm9325-public-stock.in{color:#15803d}.mm9325-public-stock.low{color:#d97706}.mm9325-public-stock.out{color:#dc2626}';document.head.appendChild(s)}
async function load(){try{const r=await fetch(API,{cache:'no-store'});const j=await r.json();if(!r.ok||j.ok===false)return;const map=new Map((j.items||[]).map(x=>[String(x.sku),Number(x.stock||0)]));document.querySelectorAll('.product').forEach(card=>{const a=card.querySelector('a[href*="product.html?sku="]');if(!a)return;const sku=new URL(a.href,location.href).searchParams.get('sku');if(!map.has(sku))return;const n=map.get(sku);let el=card.querySelector('.v83-stock,.mm9325-public-stock');if(!el){el=document.createElement('span');el.className='v83-stock mm9325-public-stock';const actions=card.querySelector('.v83-card-actions');if(actions)actions.insertBefore(el,actions.firstChild);else card.querySelector('a')?.appendChild(el)}el.className='v83-stock mm9325-public-stock '+cls(n);el.textContent='● '+label(n)});const sku=new URLSearchParams(location.search).get('sku');if(sku&&map.has(sku)){const el=document.querySelector('[data-variant-stock]');if(el){el.textContent=label(map.get(sku));el.className='mm9325-public-stock '+cls(map.get(sku))}}}catch(e){}}
css();if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',load);else load();setTimeout(load,500);setInterval(load,30000);
})();

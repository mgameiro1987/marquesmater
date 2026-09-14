(()=>{'use strict';
if(window.__MMFINALNAV23)return;window.__MMFINALNAV23=1;

const wait=fn=>{let n=0;(function w(){if(fn())return;if(++n<200)setTimeout(w,100)})()};
const hasProducts=()=>!!window.MMForceProducts?.render;
const hasStock=()=>!!window.MM9318Stock?.render;

function css(){
 if(document.getElementById('mmfinalnavcss23'))return;
 const s=document.createElement('style');s.id='mmfinalnavcss23';
 s.textContent=`
 .mmf-products-wrap{margin:0}
 .mmf-products-toggle{display:flex!important;align-items:center;width:100%;min-height:42px;padding:10px 12px;border:0;border-radius:8px;background:transparent;color:#cbd5e1;font:inherit;font-size:14px;text-align:left;cursor:pointer}
 .mmf-products-toggle:hover,.mmf-products-toggle.open{background:rgba(59,130,246,.12);color:#fff}
 .mmf-arrow{margin-left:auto;font-size:16px;transition:transform .18s ease}.mmf-products-toggle.open .mmf-arrow{transform:rotate(90deg)}
 .mmf-submenu{display:none!important;margin:2px 0 8px 12px;padding:4px 0 4px 12px;border-left:1px solid rgba(148,163,184,.24)}
 .mmf-submenu.open{display:block!important}
 .mmf-subitem{display:flex!important;align-items:center;width:100%;min-height:38px;padding:8px 10px;border:0;border-radius:7px;background:transparent;color:#b8c3d4;font:inherit;font-size:13px;text-align:left;cursor:pointer}
 .mmf-subitem:hover,.mmf-subitem.active{background:rgba(37,99,235,.16);color:#fff}.mmf-subicon{width:20px;color:#8291a8;font-size:11px}
 `;
 document.head.appendChild(s)
}

function openProducts(){if(!hasProducts())return false;window.MMForceProducts.render();return true}
function openNew(){if(!openProducts())return false;setTimeout(()=>{const b=document.getElementById('mm17new');if(b)b.click();},120);return true}
function openStock(){if(!hasStock())return false;window.MM9318Stock.render('stock');return true}

function buildMenu(){
 const nav=document.querySelector('.sidebar nav');if(!nav)return false;
 css();
 let p=nav.querySelector('.navitem[data-section="products"]');
 if(!p){
   p=[...nav.querySelectorAll('.navitem')].find(x=>/Produtos/i.test(x.textContent||''));
 }
 if(!p)return false;
 let wrap=nav.querySelector('.mmf-products-wrap');
 if(!wrap){
   const oldStock=nav.querySelector('.navitem[data-section="stock"]');if(oldStock)oldStock.remove();
   wrap=document.createElement('div');wrap.className='mmf-products-wrap';p.parentNode.insertBefore(wrap,p);wrap.appendChild(p);
 }
 p.classList.remove('navitem');p.classList.add('mmf-products-toggle');p.removeAttribute('data-section');p.setAttribute('type','button');p.setAttribute('aria-controls','mmf-products-submenu');
 if(!p.querySelector('.mmf-arrow'))p.innerHTML='<span>▣</span><span style="margin-left:10px">Produtos</span><span class="mmf-arrow">›</span>';
 let sub=wrap.querySelector('.mmf-submenu');
 if(!sub){
   sub=document.createElement('div');sub.id='mmf-products-submenu';sub.className='mmf-submenu';
   sub.innerHTML='<button type="button" class="mmf-subitem" data-mm="products"><span class="mmf-subicon">▦</span><span>Todos os produtos</span></button><button type="button" class="mmf-subitem" data-mm="new"><span class="mmf-subicon">＋</span><span>Novo produto</span></button><button type="button" class="mmf-subitem" data-mm="stock"><span class="mmf-subicon">▤</span><span>Stock produtos</span></button>';
   wrap.appendChild(sub);
 }
 const setActive=v=>sub.querySelectorAll('.mmf-subitem').forEach(x=>x.classList.toggle('active',x.dataset.mm===v));
 const showMenu=()=>{sub.classList.add('open');p.classList.add('open');p.setAttribute('aria-expanded','true')};
 p.onclick=e=>{e.preventDefault();e.stopPropagation();const open=!sub.classList.contains('open');sub.classList.toggle('open',open);p.classList.toggle('open',open);p.setAttribute('aria-expanded',String(open))};
 const one=sub.querySelector('[data-mm="products"]');if(one)one.onclick=e=>{e.preventDefault();e.stopPropagation();setActive('products');openProducts()};
 const two=sub.querySelector('[data-mm="new"]');if(two)two.onclick=e=>{e.preventDefault();e.stopPropagation();setActive('new');openNew()};
 const three=sub.querySelector('[data-mm="stock"]');if(three)three.onclick=e=>{e.preventDefault();e.stopPropagation();setActive('stock');openStock()};
 return true
}

function patchGo(){
 const a=window.MMAdmin;if(!a||typeof a.go!=='function')return false;
 if(a.go.__mm23)return true;
 const original=a.go.bind(a);
 const routed=function(k){
   if(k==='products'){return openProducts()||original(k)}
   if(k==='new-product'||k==='newProduct'){return openNew()||original('products')}
   if(k==='stock'){return openStock()||original(k)}
   return original(k)
 };
 routed.__mm23=true;routed.__original=original;a.go=routed;window.MMFinalOriginalGo=original;return true
}

function dashboardButtons(){
 document.querySelectorAll('.quick button').forEach(b=>{
   if(b.__mm23)return;
   const box=b.closest('.quick'),title=(box?.querySelector('h3')?.textContent||'').trim().toLowerCase();
   if(title.includes('novo produto')){
     b.__mm23=true;
     b.onclick=e=>{e.preventDefault();e.stopPropagation();buildMenu();openNew()};
   }
 });
}

function setup(){
 buildMenu();patchGo();dashboardButtons();
 return !!document.querySelector('.mmf-products-wrap') && !!window.MMAdmin;
}

wait(setup);
setInterval(()=>{buildMenu();patchGo();dashboardButtons()},500);

})();
(()=>{'use strict';if(window.__MM92MOSAIC2)return;window.__MM92MOSAIC2=1;
const products=()=>window.MM_V9_CATALOG?.all?.()||window.MARQUES_CATALOG||[];
function install(){
 if(!document.getElementById('mm92mosaiccss2')){const s=document.createElement('style');s.id='mm92mosaiccss2';s.textContent=`
/* V9.2 — cartões de produto profissionais e responsivos */
.mm92 .pagehead{margin-bottom:24px!important}.mm92 .pagehead h1{margin:0 0 6px!important}.mm92 .pagehead p{margin:0!important;color:#64748b!important}
.mm92 .mm92stats{display:grid!important;grid-template-columns:repeat(4,minmax(0,1fr))!important;gap:14px!important;margin:0 0 18px!important}
.mm92 .mm92stat{display:block!important;background:#fff!important;border:1px solid #e5eaf0!important;border-radius:14px!important;padding:15px 16px!important;box-shadow:0 2px 8px rgba(15,23,42,.05)!important;min-width:0!important}
.mm92 .mm92stat .mm92muted{display:block!important;margin-bottom:5px!important}.mm92 .mm92count{display:block!important;font-size:25px!important;line-height:1.1!important;font-weight:800!important}
.mm92 .mm92bar{display:flex!important;align-items:center!important;gap:10px!important;flex-wrap:wrap!important;margin:0 0 18px!important}
.mm92 .mm92bar input,.mm92 .mm92bar select{height:44px!important;box-sizing:border-box!important;border:1px solid #d8e0e8!important;border-radius:9px!important;background:#fff!important;padding:0 12px!important;min-width:0!important}
.mm92 .mm92bar input{flex:1 1 300px!important}.mm92 .mm92bar select{flex:0 1 240px!important}.mm92 .mm92bar .btn{height:44px!important;white-space:nowrap!important}
.mm92 #mm92pg.mm92grid{display:grid!important;grid-template-columns:repeat(4,minmax(0,1fr))!important;gap:18px!important;align-items:stretch!important}
.mm92 #mm92pg .mm92-product-card{display:flex!important;flex-direction:column!important;min-width:0!important;overflow:hidden!important;padding:0!important;background:#fff!important;border:1px solid #e5eaf0!important;border-radius:14px!important;box-shadow:0 2px 8px rgba(15,23,42,.05)!important}
.mm92 .mm92-product-image{height:205px!important;width:100%!important;background:#f8fafc!important;border:0!important;border-bottom:1px solid #e5eaf0!important;display:flex!important;align-items:center!important;justify-content:center!important;overflow:hidden!important;flex:0 0 205px!important}
.mm92 .mm92-product-image img{display:block!important;width:100%!important;height:100%!important;object-fit:contain!important;padding:18px!important;box-sizing:border-box!important}
.mm92 .mm92-product-body{padding:15px 16px 16px!important;display:flex!important;flex-direction:column!important;flex:1 1 auto!important;min-width:0!important}
.mm92 .mm92-product-body h3{font-size:18px!important;line-height:1.25!important;margin:7px 0 9px!important;color:#172554!important}
.mm92 .mm92-product-body .mm92-actions{margin-top:auto!important;padding-top:12px!important}
.mm92 .mm92-product-body .mm92muted{line-height:1.4!important}.mm92 .mm92-product-body .mm92ok{margin-top:7px!important}
@media(max-width:1050px){.mm92 .mm92stats{grid-template-columns:repeat(2,minmax(0,1fr))!important}.mm92 #mm92pg.mm92grid{grid-template-columns:repeat(2,minmax(0,1fr))!important}}
@media(max-width:620px){.mm92 .pagehead{margin-bottom:18px!important}.mm92 .mm92stats{grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:10px!important}.mm92 .mm92stat{padding:12px!important}.mm92 .mm92count{font-size:22px!important}.mm92 .mm92bar{display:grid!important;grid-template-columns:1fr!important;gap:9px!important}.mm92 .mm92bar input,.mm92 .mm92bar select,.mm92 .mm92bar .btn{width:100%!important;min-width:0!important;flex:none!important}.mm92 #mm92pg.mm92grid{grid-template-columns:1fr!important;gap:14px!important}.mm92 .mm92-product-image{height:220px!important;flex-basis:220px!important}.mm92 .mm92-product-body{padding:14px!important}.mm92 .mm92-product-body h3{font-size:18px!important}}
`;document.head.appendChild(s)}
 const grid=document.getElementById('mm92pg');if(!grid)return false;
 const list=products();
 grid.querySelectorAll('.mm92card').forEach(card=>{if(card.classList.contains('mm92-product-card'))return;const text=card.textContent||'';const p=list.find(x=>x.sku&&text.includes(String(x.sku)));if(!p)return;
  const body=document.createElement('div');body.className='mm92-product-body';while(card.firstChild)body.appendChild(card.firstChild);
  const image=document.createElement('div');image.className='mm92-product-image';
  if(p.image){const im=document.createElement('img');im.src=p.image;im.alt=p.name||p.sku||'Produto';im.loading='lazy';im.onerror=()=>{im.remove();image.innerHTML='<div style="color:#94a3b8;font-size:13px">Imagem indisponível</div>'};image.appendChild(im)}else image.innerHTML='<div style="color:#94a3b8;font-size:13px">Sem imagem</div>';
  card.classList.add('mm92-product-card');card.appendChild(image);card.appendChild(body);
 });return true}
install();const ob=new MutationObserver(()=>{if(document.getElementById('mm92pg'))install()});ob.observe(document.getElementById('app')||document.body,{childList:true,subtree:true});window.addEventListener('load',install);setInterval(()=>{if(document.getElementById('mm92pg'))install()},1200);
})();
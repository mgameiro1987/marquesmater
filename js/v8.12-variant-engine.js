/* MarquesMater V8.12 — motor universal de variantes
   Funciona com qualquer categoria e qualquer número de opções.
   Uma combinação pode definir imagem, preço, referência e stock.
*/
(function(){
  function sku(){return new URLSearchParams(location.search).get('sku')||'SIL001'}
  function product(){return (window.MARQUES_CATALOG||[]).find(p=>p.sku===sku())||null}
  function selections(){
    const out={};
    document.querySelectorAll('.v6-option').forEach(block=>{
      const label=block.querySelector('label'); if(!label)return;
      const selected=block.querySelector('button.selected');
      if(selected)out[label.textContent.trim()]=(selected.dataset.value||selected.querySelector('em')?.textContent||selected.textContent||'').trim();
    });
    return out;
  }
  function key(obj){return Object.entries(obj||{}).sort((a,b)=>a[0].localeCompare(b[0])).map(([k,v])=>k+'='+v).join('|')}
  function resolve(p,sel){
    const matrix=(window.MM_VARIANT_MATRIX||{})[p.sku]||{};
    const direct=matrix[key(sel)];
    if(direct)return direct;
    // Fallback universal: se existir uma imagem associada a qualquer valor selecionado,
    // usa-a sem obrigar a criar uma matriz manual para cada produto.
    const images=(window.MM_VARIANT_IMAGES||{})[p.sku]||{};
    let image=null;
    for(const v of Object.values(sel)){if(images[v]){image=images[v];break}}
    const entry={image:image,price:p.price,sku:p.sku,stock:p.stock};
    if(Object.keys(sel).length)entry.sku=p.sku+'-'+Object.values(sel).map(v=>String(v).replace(/[^a-zA-Z0-9]+/g,'').toUpperCase()).join('-');
    return entry;
  }
  function sync(){
    const p=product(); if(!p)return;
    const r=resolve(p,selections());
    const main=document.getElementById('mainProductImage');
    if(main&&r.image)main.src=r.image;
    const price=document.getElementById('currentPrice');
    if(price&&r.price!=null)price.textContent=Number(r.price).toFixed(2).replace('.',',')+' €';
    document.querySelectorAll('[data-variant-sku]').forEach(el=>el.textContent=r.sku||p.sku);
    document.querySelectorAll('[data-variant-stock]').forEach(el=>el.textContent=r.stock||p.stock||'Em stock');
    const thumbs=document.querySelectorAll('.v6-thumbs button');
    thumbs.forEach(b=>{const i=b.querySelector('img');b.classList.toggle('active',!!i&&main&&i.src===main.src)});
  }
  window.MMVariantEngine={sync:sync,comboKey:key,getSelections:selections,resolve:resolve};
  function boot(){
    document.querySelectorAll('.v6-option button').forEach(b=>b.addEventListener('click',()=>setTimeout(sync,0)));
    setTimeout(sync,0);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();

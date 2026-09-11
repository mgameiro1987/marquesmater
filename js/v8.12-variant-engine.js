/* MarquesMater V8.12 — motor genérico de variantes combinadas
   Preparado para lâmpadas, projetores, luminárias e qualquer produto
   com combinações como potência + temperatura + acabamento + cor + tamanho.
*/
(function(){
  function getSku(){return new URLSearchParams(location.search).get('sku')||'SIL001'}
  function getSelections(){
    const out={};
    document.querySelectorAll('.v6-option').forEach(block=>{
      const label=block.querySelector('label');
      if(!label)return;
      const key=label.textContent.trim();
      const selected=block.querySelector('.option-buttons button.selected');
      if(selected)out[key]=(selected.dataset.value||selected.querySelector('em')?.textContent||selected.textContent||'').trim();
    });
    return out;
  }
  function comboKey(obj){return Object.entries(obj).sort((a,b)=>a[0].localeCompare(b[0])).map(([k,v])=>k+'='+v).join('|')}
  function sync(){
    const data=window.MM_VARIANT_MATRIX?.[getSku()];
    if(!data)return;
    const key=comboKey(getSelections());
    const entry=data[key];
    if(!entry)return;
    const main=document.getElementById('mainProductImage');
    if(main&&entry.image)main.src=entry.image;
    const thumbs=document.querySelectorAll('.v6-thumbs button');
    thumbs.forEach(b=>b.classList.remove('active'));
    if(entry.image){
      const match=[...thumbs].find(b=>b.querySelector('img')?.src.endsWith(entry.image));
      if(match)match.classList.add('active');
    }
    if(entry.price!=null){const price=document.getElementById('currentPrice');if(price)price.textContent=Number(entry.price).toFixed(2).replace('.',',')+' €'}
  }
  window.MMVariantEngine={sync:sync,comboKey:comboKey,getSelections:getSelections};
  function boot(){
    document.querySelectorAll('.v6-option button').forEach(b=>b.addEventListener('click',()=>setTimeout(sync,0)));
    sync();
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();

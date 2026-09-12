(()=>{
'use strict';
const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]));
const api=async(path,opts={})=>{const r=await fetch(path,{cache:'no-store',...opts,headers:{'Content-Type':'application/json',...(opts.headers||{})}});const j=await r.json().catch(()=>({}));if(!r.ok||j.ok===false)throw Error(j.error||`Erro ${r.status}`);return j};
function modal(kind,item){
 const edit=!!item,m=document.createElement('div');m.className='modal mm106';
 const parentKind=kind==='family'?'subcategory':'category';
 m.innerHTML=`<form><h2>${edit?'Editar':'Nova'} ${kind==='category'?'categoria':kind==='subcategory'?'subcategoria':'família'}</h2><label>Nome<input name="name" required value="${esc(edit?item.name:'')}"></label><label>Slug<input name="slug" value="${esc(edit?item.slug:'')}"></label>${kind==='category'?'':`<label>${kind==='family'?'Subcategoria':'Categoria'}<select name="parent_id" required><option value="">Selecionar...</option></select></label>`}<div class="actions"><button type="button" class="btn alt" data-cancel>Cancelar</button><button class="btn">Guardar</button></div></form>`;
 document.body.appendChild(m);
 const sel=m.querySelector('select[name=parent_id]');
 if(sel){api('/api/catalog-structure').then(s=>{(s.categories||[]).filter(x=>x.kind===parentKind&&x.active).forEach(x=>{const o=document.createElement('option');o.value=x.id;o.textContent=x.name;if(edit&&String(x.id)===String(item.parent_id))o.selected=true;sel.appendChild(o)})}).catch(e=>alert(e.message))}
 m.querySelector('[data-cancel]').onclick=()=>m.remove();
 m.querySelector('form').onsubmit=async e=>{e.preventDefault();const f=new FormData(e.target);try{await api('/api/categories',{method:'POST',body:JSON.stringify({id:edit?item.id:undefined,name:f.get('name'),slug:f.get('slug'),parent_id:f.get('parent_id')||null})});m.remove();window.MM106CatalogReload?window.MM106CatalogReload():window.MM104?.go('categories')}catch(err){alert(err.message)}};
}
function actionSheet(id,name){
 const m=document.createElement('div');m.className='modal mm106';m.innerHTML=`<div style="width:min(430px,100%);background:#fff;border-radius:18px;padding:22px"><h2 style="margin-top:0">${esc(name)}</h2><p style="color:#64748b">Escolha a ação que pretende executar.</p><div class="actions" style="flex-direction:column"><button class="btn alt" data-off>Desativar</button><button class="btn red" data-hard>Eliminar permanentemente</button><button class="btn" data-cancel>Cancelar</button></div></div>`;document.body.appendChild(m);
 m.querySelector('[data-cancel]').onclick=()=>m.remove();
 m.querySelector('[data-off]').onclick=async()=>{if(!confirm('Desativar este elemento?'))return;try{await api('/api/categories?id='+encodeURIComponent(id),{method:'DELETE'});m.remove();window.MM106CatalogReload?window.MM106CatalogReload():window.MM104?.go('categories')}catch(e){alert(e.message)}};
 m.querySelector('[data-hard]').onclick=async()=>{if(!confirm('Eliminar permanentemente este elemento? Esta ação não pode ser anulada.'))return;try{await api('/api/admin/catalog-structure/delete',{method:'POST',body:JSON.stringify({id:Number(id)})});m.remove();window.MM106CatalogReload?window.MM106CatalogReload():window.MM104?.go('categories')}catch(e){alert(e.message)}};
}
function boot(){
 document.addEventListener('click',e=>{
  const b=e.target.closest?.('#newcat,#newsub,#newfam');
  if(b){e.preventDefault();e.stopImmediatePropagation();modal(b.id==='newcat'?'category':b.id==='newsub'?'subcategory':'family');return;}
  const d=e.target.closest?.('[data-del]');
  if(d){e.preventDefault();e.stopImmediatePropagation();const id=d.dataset.del;const row=d.closest('tr,.card');const name=row?.querySelector('b')?.textContent||'Elemento';actionSheet(id,name)}
 },true);
 const old=window.MM106CatalogReload;
 window.MM106CatalogReload=()=>window.MM104?.go('categories');
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();

(()=>{'use strict';if(window.__MM1013NAVFINAL)return;window.__MM1013NAVFINAL=1;
function activate(section){document.querySelectorAll('.navitem[data-section]').forEach(b=>b.classList.toggle('active',b.dataset.section===section));document.getElementById('sidebar')?.classList.remove('open')}
async function open(section){
 activate(section);
 try{
  if(section==='products'){if(window.MM98ForceProducts)return window.MM98ForceProducts();throw Error('Gestor de Produtos não disponível.')}
  if(section==='categories'){if(window.MM99Taxonomy)return window.MM99Taxonomy();throw Error('Gestor de Categorias não disponível.')}
  if(section==='brands'){if(window.MMForceBrands?.render)return window.MMForceBrands.render();throw Error('Gestor de Marcas não disponível.')}
  if(section==='attributes'){if(window.MM95AttributesRender)return window.MM95AttributesRender();throw Error('Gestor de Atributos não disponível.')}
  if(window.MMAdmin?.go)return window.MMAdmin.go(section);
 }catch(e){console.error('MM navigation final',e);const a=document.getElementById('app');if(a)a.innerHTML='<section class="page"><div class="card info"><h2>Não foi possível abrir esta área</h2><p>'+String(e.message||e)+'</p><button class="btn" onclick="location.reload()">Recarregar</button></div></section>'}
}
function install(){const old=document.querySelector('.sidebar nav');if(!old||old.__mmFinal)return false;const nav=old.cloneNode(true);nav.__mmFinal=true;old.replaceWith(nav);nav.addEventListener('click',e=>{const b=e.target.closest?.('.navitem[data-section]');if(!b)return;const k=b.dataset.section;e.preventDefault();e.stopPropagation();open(k)},false);return true}
let n=0;(function boot(){if(!install()&&n++<120)setTimeout(boot,100)})();
window.MMFinalNavigation={open};
})();
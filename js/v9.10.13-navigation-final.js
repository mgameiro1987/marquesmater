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
function patchGo(){const a=window.MMAdmin;if(!a||typeof a.go!=='function'||a.go.__mmUniversal)return false;return true}
function installGo(){const a=window.MMAdmin;if(!a||typeof a.go!=='function')return false;if(a.go.__mmUniversal)return true;const fallback=a.go.bind(a);const go=function(section){if(section==='products'&&window.MM98ForceProducts)return window.MM98ForceProducts();if(section==='categories'&&window.MM99Taxonomy)return window.MM99Taxonomy();if(section==='brands'&&window.MMForceBrands?.render)return window.MMForceBrands.render();if(section==='attributes'&&window.MM95AttributesRender)return window.MM95AttributesRender();if(section==='import'&&window.MM1012FileImport?.render)return window.MM1012FileImport.render();if((section==='purchases'||section==='suppliers')&&window.MM99PUR?.open)return window.MM99PUR.open(section);if(section==='customers'&&window.MM99Customers?.render)return window.MM99Customers.render();if(section==='reports'&&typeof window.MMAdmin?.go==='function'&&section!=='reports')return fallback(section);return fallback(section)};go.__mmUniversal=true;a.go=go;return true}
function install(){const nav=document.querySelector('.sidebar nav');if(!nav||nav.__mmFinal)return false;nav.__mmFinal=true;nav.addEventListener('click',e=>{const b=e.target.closest?.('.navitem[data-section]');if(!b)return;const k=b.dataset.section;e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();open(k)},true);return true}
let n=0;(function boot(){install();installGo();if(n++<120)setTimeout(boot,100)})();
window.MMFinalNavigation={open};
})();
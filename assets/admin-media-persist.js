(function(){
const files={};
const brandNames=['RIDA','NEUCE','SOUDAL','VITO','BOSCH','Makita','STANLEY','DEWALT'];
function keyFrom(s){const m=String(s||'').match(/mmPick\(this\.files\[0\],'([^']+)'\)/);return m?m[1]:null}
function put(h,key,url){
  h=h||{};
  if(key==='hero1'){let a=Array.isArray(h.slides)?h.slides.slice():[];if(!a.length)a=[{tag:'MarquesMater',title:'Tudo para os seus projetos',text:'',button:'Ver produtos →',link:'catalogo.html',enabled:true}];a[0]=Object.assign({},a[0],{image:url});h.slides=a}
  else if(key==='rida1')h.rida_banner=Object.assign({},h.rida_banner||{},{image:url});
  else if(key.startsWith('promos')){let i=Number(key.slice(6))-1,a=Array.isArray(h.promo_banners)?h.promo_banners.slice():[];while(a.length<3)a.push({});a[i]=Object.assign({},a[i],{image:url});h.promo_banners=a}
  else if(key.startsWith('brands')){let i=Number(key.slice(6))-1, n=brandNames[i],o=(h.brand_logos&&typeof h.brand_logos==='object'&&!Array.isArray(h.brand_logos))?Object.assign({},h.brand_logos):{};o[n]=url;h.brand_logos=o}
  return h;
}
async function save(key,button){const f=files[key];if(!f)return;const st=button?.parentElement?.nextElementSibling;try{button.disabled=true;const fd=new FormData();fd.append('file',f);const ur=await fetch('/api/admin/upload',{method:'POST',body:fd});const uj=await ur.json();if(!uj.url)throw Error('Upload sem URL');const sr=await fetch('/api/site?adminmedia=1',{cache:'no-store'});const sd=await sr.json();const h=sd?.settings?.homepage||{};const nh=put(h,key,uj.url);const wr=await fetch('/api/admin/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({homepage:nh})});const wj=await wr.json();if(!wr.ok||wj.error)throw Error(wj.error||'Não foi possível guardar');if(st)st.textContent='Guardada e aplicada na homepage.';files[key]=null}catch(e){if(st)st.textContent='Erro: '+e.message}finally{button.disabled=false}}
document.addEventListener('change',e=>{const i=e.target;if(i.matches('input[type=file][onchange*="mmPick"]')){const k=keyFrom(i.getAttribute('onchange'));if(k&&i.files[0])files[k]=i.files[0]}},true);
document.addEventListener('click',e=>{const b=e.target.closest('.mm-media-actions button');if(!b)return;const m=String(b.getAttribute('onclick')||'').match(/mmSave\('([^']+)'\)/);if(!m)return;e.preventDefault();e.stopImmediatePropagation();save(m[1],b)},true);
})();
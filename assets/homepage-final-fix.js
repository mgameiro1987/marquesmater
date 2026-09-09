(function(){
const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]));
const img=v=>{v=String(v||'').trim();if(!v)return '';if(v.startsWith('/'))return v;return '/'+v.replace(/^\.\//,'')};
const first=(o,...ks)=>{for(const k of ks){if(o&&o[k])return o[k]}return null};
function arr3(h){let a=first(h,'promo_banners','promoBanners','banners','cards');return Array.isArray(a)?a.slice(0,3):[]}
function render(h){
  const r=document.getElementById('rida-section'); if(!r)return;
  document.getElementById('promo-section')?.remove(); document.querySelector('.about-home')?.remove();
  document.getElementById('mmFinalPromos')?.remove(); document.getElementById('mmFinalBrands')?.remove();
  const banners=arr3(h); const fallback=[
    {title:'Tintas NEUCE',tag:'PINTURAS',text:'Cores e soluções para interior e exterior.',image:'assets/family-icons/paint-neuce.png',link:'catalogo.html?cat=Pinturas'},
    {title:'SOUDAL',tag:'COLAS E SELANTES',text:'Soluções profissionais para vedação, colagem e montagem.',image:'soudal/soudal-pega-tudo.jpg',link:'catalogo.html?brand=Soudal'},
    {title:'Tudo para o jardim',tag:'JARDIM / AGRICULTURA',text:'Ferramentas e equipamentos para cuidar do seu espaço.',image:'assets/family-icons/garden-vito.png',link:'catalogo.html?cat=Jardim%2FAgricultura'}
  ];
  const cards=fallback.map((f,i)=>Object.assign({},f,banners[i]||{}));
  const sec=document.createElement('section');sec.id='mmFinalPromos';sec.className='mm-final-promos';
  sec.innerHTML='<div class="container"><div class="section-head"><div><div class="eyebrow">DESTAQUES</div><h2>Explore as nossas soluções</h2></div></div><div class="mm-promo-grid">'+cards.map(x=>'<a class="mm-promo-card" href="'+esc(x.link||'catalogo.html')+'">'+(x.image?'<img src="'+esc(img(x.image))+'" alt="">':'')+'<div class="mm-promo-copy"><small>'+esc(x.tag||'MarquesMater')+'</small><h3>'+esc(x.title||'')+'</h3><span>'+esc(x.text||'')+'</span></div></a>').join('')+'</div></div>';
  r.insertAdjacentElement('afterend',sec);
  const names=['RIDA','NEUCE','SOUDAL','VITO','BOSCH','Makita','STANLEY','DEWALT'];
  const logos=h.brand_logos||h.brandLogos||{};
  const bsec=document.createElement('section');bsec.id='mmFinalBrands';bsec.className='mm-final-brands';
  bsec.innerHTML='<div class="container"><div class="section-head"><div><div class="eyebrow">AS NOSSAS MARCAS</div><h2>Marcas em destaque</h2></div><a class="section-link" href="catalogo.html">Ver todas as marcas →</a></div><div class="mm-final-brand-grid">'+names.map((n,i)=>{let v=Array.isArray(logos)?logos[i]:logos[n]||logos[n.toLowerCase()];return '<a class="mm-final-brand '+n.toLowerCase()+'" href="catalogo.html?brand='+encodeURIComponent(n)+'">'+(v?'<img src="'+esc(img(typeof v==='string'?v:v.image||v.src))+'" alt="'+esc(n)+'">':'<strong>'+esc(n)+'</strong>')+'</a>'}).join('')+'</div></div>';
  sec.insertAdjacentElement('afterend',bsec);
}
async function boot(){try{const r=await fetch('/api/site?finalfix=1',{cache:'no-store'});const d=await r.json();const h=d?.settings?.homepage||{};render(h)}catch(e){render({})}}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();
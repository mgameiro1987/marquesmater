/* MarquesMater V24 — menu profissional + rodapé corrigido */
(function(){
  if(window.__MM_NAV_V24__) return;
  window.__MM_NAV_V24__=true;

  const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));

  function normalise(f){
    return typeof f==='string' ? {name:f,subs:[]} : (f||{});
  }

  function render(site){
    const hosts=document.querySelectorAll('#global-menu');
    if(!hosts.length) return;

    const families=(site?.families||[])
      .map(normalise)
      .filter(f=>f.name && f.show_menu !== false);

    const items=families.map(f=>{
      const name=f.name;
      const subs=Array.isArray(f.subs) ? f.subs.filter(Boolean) : [];
      const href=name==='Máquinas'
        ? 'catalogo-rida.html'
        : 'catalogo.html?cat='+encodeURIComponent(name);

      return `
        <div class="mm-nav-family">
          <a href="${href}" class="mm-nav-link">
            ${esc(name)}
            ${subs.length ? '<span class="mm-nav-arrow">⌄</span>' : ''}
          </a>
          ${subs.length ? `
            <div class="mm-nav-dropdown">
              <div class="mm-nav-dropdown-title">${esc(name)}</div>
              ${subs.map(sub=>`
                <a href="catalogo.html?cat=${encodeURIComponent(name)}&sub=${encodeURIComponent(sub)}">
                  <span>${esc(sub)}</span><span>›</span>
                </a>
              `).join('')}
            </div>
          ` : ''}
        </div>`;
    }).join('');

    hosts.forEach(host=>{
      host.innerHTML=`<nav class="mm-nav" aria-label="Categorias e famílias">${items}</nav>`;
    });
  }

  function styles(){
    if(document.getElementById('mm-nav-v20')) return;

    const st=document.createElement('style');
    st.id='mm-nav-v20';
    st.textContent=`
      /* MENU */
      .menu{border-top:1px solid #edf0f3;background:#fff;position:relative;z-index:1000}
      .menu>.container{max-width:1400px;overflow:visible!important}
      .mm-nav{display:flex;align-items:center;justify-content:center;gap:4px;min-height:52px;overflow:visible!important;scrollbar-width:none}
      .mm-nav::-webkit-scrollbar{display:none}
      .mm-nav-family{position:relative;flex:0 0 auto}
      .mm-nav-link{display:flex;align-items:center;gap:6px;padding:16px 13px;color:#111820;text-decoration:none;font-size:13px;font-weight:800;white-space:nowrap;border-bottom:3px solid transparent}
      .mm-nav-link:hover{color:#243b91;border-bottom-color:#f28c00}
      .mm-nav-arrow{font-size:12px;color:#6d7780}
      .mm-nav-dropdown{display:none;position:absolute;top:52px;left:0;min-width:245px;background:#fff;border:1px solid #e3e7eb;border-radius:0 0 12px 12px;box-shadow:0 18px 42px rgba(20,30,40,.16);padding:8px;z-index:100000}
      @media (hover:hover) and (pointer:fine){
        .mm-nav-family:hover>.mm-nav-dropdown,
        .mm-nav-family:focus-within>.mm-nav-dropdown{display:block}
      }
      .mm-nav-family.mm-open>.mm-nav-dropdown{display:block}
      .mm-nav-dropdown-title{padding:9px 10px 7px;color:#7b858d;text-transform:uppercase;font-size:10px;letter-spacing:.11em;font-weight:900}
      .mm-nav-dropdown a{display:flex!important;justify-content:space-between;align-items:center;width:100%;box-sizing:border-box;padding:10px;border-radius:8px;text-decoration:none;color:#18212a;font-size:12px;font-weight:700;line-height:1.35}
      .mm-nav-dropdown a:hover{background:#f5f7f9;color:#243b91}

      /* RODAPÉ */
      .mm-footer-v17{background:#101923!important;color:#fff;padding:46px 0 0!important;margin-top:0;border-top:4px solid #f28c00}
      .mm-footer-main-v17{display:grid;grid-template-columns:1.5fr 1fr 1fr 1.35fr 1.25fr;gap:30px;padding:0 0 38px}
      .mm-footer-brand-v17{min-width:0}
      .mm-footer-logo-v17{width:205px;max-width:100%;filter:brightness(0) invert(1);margin:0 0 14px}
      .mm-footer-brand-v17 p,.mm-footer-address-v17 p{color:#aeb8c2;font-size:13px;line-height:1.7;margin:0 0 14px;white-space:pre-line}
      .mm-footer-contact-mini-v17{display:flex;flex-direction:column;gap:6px;color:#d7dde3;font-size:12px}
      .mm-footer-col-v17{display:flex!important;flex-direction:column!important;align-items:flex-start!important;gap:9px!important}
      .mm-footer-col-v17 h4{margin:0 0 5px;color:#fff;font-size:14px;font-weight:900}
      .mm-footer-col-v17 a{display:block!important;width:auto!important;margin:0!important;padding:0!important;color:#aeb8c2!important;font-size:12px!important;line-height:1.5!important;text-decoration:none!important;white-space:normal!important}
      .mm-footer-col-v17 a:hover{color:#f28c00!important}
      .mm-footer-address-v17 a{color:#d7dde3!important}
      .mm-footer-book-v17{display:flex!important;align-items:center!important;gap:8px!important}
      .mm-footer-book-icon-v17{width:27px;height:27px;flex:0 0 27px;border-radius:6px;background:#b51e2b;color:#fff;display:inline-flex;align-items:center;justify-content:center;font-size:15px}
      .mm-footer-bottom-v17{border-top:1px solid #29333e;padding:17px 0;display:flex;justify-content:space-between;gap:15px;flex-wrap:wrap;color:#77838e;font-size:10px}

      @media(max-width:1100px){
        .mm-footer-main-v17{grid-template-columns:1.5fr 1fr 1fr 1.35fr}
        .mm-footer-address-v17{grid-column:2/-1}
      }
      @media(max-width:900px){
        .mm-nav{justify-content:flex-start;overflow-x:auto!important;overflow-y:visible!important}
        .mm-nav-link{padding:14px 10px;font-size:11px}
        .menu>.container{overflow:visible!important}
      }
      @media(max-width:700px){
        .mm-footer-v17{padding:34px 0 0!important}
        .mm-footer-main-v17{grid-template-columns:1fr 1fr;gap:28px 20px;padding-bottom:30px}
        .mm-footer-brand-v17{grid-column:1/-1}
        .mm-footer-address-v17{grid-column:auto}
        .mm-footer-logo-v17{width:185px}
        .mm-footer-col-v17 h4{font-size:13px}
        .mm-footer-col-v17 a{font-size:12px!important}
      }
      @media(max-width:430px){
        .mm-footer-main-v17{grid-template-columns:1fr}
        .mm-footer-brand-v17,.mm-footer-address-v17{grid-column:auto}
      }
    `;
    document.head.appendChild(st);
  }

  function footer(site){
    const c=site?.settings?.company||{};
    let f=document.querySelector('footer');
    if(!f){
      f=document.createElement('footer');
      document.body.appendChild(f);
    }

    f.className='mm-footer-v17';
    f.innerHTML=`
      <div class="container mm-footer-main-v17">
        <div class="mm-footer-brand-v17">
          <img src="assets/marquesmater-logo.svg" alt="MarquesMater" class="mm-footer-logo-v17">
          <p>Materiais de construção, pinturas, ferramentas, jardim e muito mais.</p>
          <div class="mm-footer-contact-mini-v17">
            ${c.phone?`<span>☎ ${esc(c.phone)}</span>`:''}
            ${c.email?`<span>✉ ${esc(c.email)}</span>`:''}
          </div>
        </div>

        <div class="mm-footer-col-v17">
          <h4>MarquesMater</h4>
          <a href="empresa.html">Quem somos</a>
          <a href="contactos.html">Contactos</a>
        </div>

        <div class="mm-footer-col-v17">
          <h4>Informação</h4>
          <a href="termos-condicoes.html">Termos e Condições</a>
          <a href="politica-privacidade.html">Política de Privacidade</a>
          <a href="politica-cookies.html">Política de Cookies</a>
          <a href="entregas-devolucoes.html">Entregas, Trocas e Devoluções</a>
          <a class="mm-footer-book-v17" href="livro-reclamacoes.html"><span class="mm-footer-book-icon-v17">📕</span><span>Livro de Reclamações</span></a>
        </div>

        <div class="mm-footer-col-v17 mm-footer-address-v17">
          <h4>Contactos</h4>
          <p>${esc(c.address||'')}</p>
          ${c.postal?`<p>${esc(c.postal)}</p>`:''}
          ${c.phone?`<a href="tel:${esc(c.phone)}">${esc(c.phone)}</a>`:''}
          ${c.email?`<a href="mailto:${esc(c.email)}">${esc(c.email)}</a>`:''}
          ${c.maps_url?`<a href="${esc(c.maps_url)}" target="_blank" rel="noopener">📍 Como chegar</a>`:''}
        </div>
      </div>
      <div class="container mm-footer-bottom-v17">
        <span>© ${new Date().getFullYear()} MarquesMater — Materiais de Construção e Pinturas, Lda.</span>
        <span>Todos os direitos reservados.</span>
      </div>`;
  }

  function bindSecret(){
    let clicks=0,timer;
    document.addEventListener('click',e=>{
      const img=e.target.closest('img.logo');
      if(!img) return;
      const a=img.closest('a');
      if(!a) return;
      e.preventDefault();
      clicks++;
      clearTimeout(timer);
      if(clicks>=3){
        clicks=0;
        window.open('/admin.html','_blank','noopener');
        return;
      }
      timer=setTimeout(()=>{
        clicks=0;
        location.href='index.html';
      },650);
    });
  }

  function bindMobileMenu(){
    document.addEventListener('click',e=>{
      const link=e.target.closest('.mm-nav-link');
      if(!link) return;
      const item=link.closest('.mm-nav-family');
      if(!item || !item.querySelector('.mm-nav-dropdown')) return;
      if(window.matchMedia('(max-width: 900px)').matches){
        document.querySelectorAll('.mm-nav-family.mm-open').forEach(x=>x.classList.remove('mm-open'));
        // A família é clicável: não bloquear a navegação para o catálogo.
      }
    });
  }

  document.addEventListener('DOMContentLoaded',()=>{
    styles();
    bindSecret();
    bindMobileMenu();
    fetch('/api/site',{cache:'no-store'})
      .then(r=>r.json())
      .then(site=>{render(site);footer(site)})
      .catch(()=>{render({families:[]});footer({settings:{}})});
  });
})();

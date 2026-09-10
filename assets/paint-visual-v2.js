(function(){
  'use strict';
  const STYLE_ID='mm-paint-visual-v2-css';
  const MARK='data-mm-paint-v2';
  const WOODNEUCE_IMAGE='https://www.jonobras.pt/admin/APP/upload/artigos/5fad1bfa1dc83woodneuce.png';
  function isPaintModal(modal){
    const t=(modal.innerText||'').toLowerCase();
    const vals=[...modal.querySelectorAll('input,select,textarea')].map(x=>(x.value||x.placeholder||'').toLowerCase()).join(' ');
    return /neuce|woodneuce|neucegold|pintura|tinta|lasur/.test(t+' '+vals);
  }
  function addCss(){
    if(document.getElementById(STYLE_ID))return;
    const s=document.createElement('style');s.id=STYLE_ID;s.textContent=`
      .mm-paint-v2 .modal-card{width:min(1180px,96vw)!important;max-height:94vh!important;padding:0!important;border-radius:20px!important;overflow:auto!important;background:#f5f7f9!important;box-shadow:0 24px 80px rgba(16,24,32,.28)!important}
      .mm-paint-v2 .mmv-head{position:sticky;top:0;z-index:30;display:flex;align-items:center;justify-content:space-between;gap:16px;padding:18px 24px;background:linear-gradient(135deg,#111c26,#1e2d3a);color:#fff}
      .mm-paint-v2 .mmv-title{font-size:22px;font-weight:900;letter-spacing:-.02em}.mm-paint-v2 .mmv-sub{font-size:12px;opacity:.7;margin-top:4px}.mm-paint-v2 .mmv-head-actions{display:flex;gap:8px;align-items:center}.mm-paint-v2 .mmv-head-actions button{border:1px solid #ffffff2e!important;background:#ffffff12!important;color:#fff!important;border-radius:10px!important;padding:9px 13px!important;font-weight:800!important}.mm-paint-v2 .mmv-head-actions button:last-child{background:#f28c00!important;border-color:#f28c00!important}
      .mm-paint-v2 .tabs{position:sticky!important;top:72px;z-index:25;background:#fff!important;padding:0 20px!important;margin:0!important;border-bottom:1px solid #dfe5e9!important;gap:2px!important;overflow:auto!important;white-space:nowrap!important}.mm-paint-v2 .tab{padding:14px 13px!important;border:0!important;border-bottom:3px solid transparent!important;color:#65737d!important;font-size:12px!important}.mm-paint-v2 .tab.active{color:#16212b!important;border-bottom-color:#f28c00!important}
      .mm-paint-v2 .tabpane{padding:20px 22px!important}.mm-paint-v2 .tabpane.active{background:#f5f7f9!important}
      .mm-paint-v2 .grid,.mm-paint-v2 .modal-section,.mm-paint-v2 .panel{background:#fff!important;border:1px solid #e0e6ea!important;border-radius:15px!important;box-shadow:0 4px 16px rgba(16,24,32,.045)!important}
      .mm-paint-v2 .grid{padding:18px!important;gap:15px!important}.mm-paint-v2 label,.mm-paint-v2 .label{font-weight:800!important;color:#4d5b65!important;font-size:11px!important}.mm-paint-v2 input,.mm-paint-v2 select,.mm-paint-v2 textarea{border:1px solid #ccd5db!important;border-radius:10px!important;background:#fff!important;min-height:42px!important;transition:.15s!important}.mm-paint-v2 input:focus,.mm-paint-v2 select:focus,.mm-paint-v2 textarea:focus{outline:0!important;border-color:#f28c00!important;box-shadow:0 0 0 3px #f28c001c!important}
      .mm-paint-v2 .mmv-overview{display:grid;grid-template-columns:150px 1fr auto;gap:18px;align-items:center;margin:20px 22px 0;padding:15px;background:#fff;border:1px solid #e0e6ea;border-radius:15px}.mm-paint-v2 .mmv-photo{width:150px;height:120px;border:1px solid #e0e6ea;border-radius:12px;background:#fafbfc;display:flex;align-items:center;justify-content:center;overflow:hidden}.mm-paint-v2 .mmv-photo img{max-width:92%;max-height:92%;object-fit:contain}.mm-paint-v2 .mmv-meta strong{font-size:18px;display:block}.mm-paint-v2 .mmv-meta span{font-size:12px;color:#6b7782;display:block;margin-top:4px}.mm-paint-v2 .mmv-badges{display:flex;gap:6px;flex-wrap:wrap;margin-top:10px}.mm-paint-v2 .mmv-badge{padding:5px 8px;border-radius:999px;background:#eef3f7;color:#53616b;font-size:10px;font-weight:900}.mm-paint-v2 .mmv-badge.ok{background:#e8f7ef;color:#167442}
      .mm-paint-v2 .mmv-card{background:#fff;border:1px solid #e0e6ea;border-radius:15px;padding:17px;margin-bottom:15px;box-shadow:0 4px 16px rgba(16,24,32,.04)}.mm-paint-v2 .mmv-card h3{margin:0 0 5px;font-size:15px}.mm-paint-v2 .mmv-card small{color:#73808a}
      .mm-paint-v2 .table-wrap,.mm-paint-v2 table{border-radius:12px!important}.mm-paint-v2 th{background:#f6f8f9!important;font-size:11px!important;text-transform:none!important}.mm-paint-v2 td,.mm-paint-v2 th{padding:11px!important}.mm-paint-v2 .btn{border-radius:9px!important}.mm-paint-v2 .btn.primary{background:#f28c00!important;border-color:#f28c00!important}
      .mm-paint-v2 .mmv-footer{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:15px 22px;background:#fff;border-top:1px solid #dfe5e9;position:sticky;bottom:0;z-index:20}.mm-paint-v2 .mmv-footer .danger{color:#b42318!important;font-weight:800}.mm-paint-v2 .mmv-footer button{border-radius:10px!important;padding:10px 15px!important;font-weight:850!important}.mm-paint-v2 .mmv-footer button:last-child{background:#f28c00!important;color:#fff!important;border-color:#f28c00!important}
      @media(max-width:800px){.mm-paint-v2 .mmv-overview{grid-template-columns:92px 1fr}.mm-paint-v2 .mmv-photo{width:92px;height:92px}.mm-paint-v2 .mmv-head{padding:14px}.mm-paint-v2 .mmv-title{font-size:18px}.mm-paint-v2 .tabpane{padding:14px!important}}
    `;document.head.appendChild(s);
  }
  function imageFor(modal){
    const urls=[...modal.querySelectorAll('input')].map(x=>x.value).filter(v=>/^https?:\/\//i.test(v));
    const good=urls.find(v=>/neuce|wood|paint|1128/i.test(v));
    if(good)return good;
    const text=(modal.innerText||'').toLowerCase();
    return /woodneuce|lasur/.test(text)?WOODNEUCE_IMAGE:(urls[0]||'/assets/woodneuce.svg');
  }
  function enhance(modal){
    if(!modal||modal.getAttribute(MARK)||!isPaintModal(modal))return;
    const card=modal.querySelector('.modal-card');if(!card)return;
    modal.setAttribute(MARK,'1');modal.classList.add('mm-paint-v2');addCss();
    const oldTitle=card.querySelector('h2')||card.querySelector('h1');
    const title=oldTitle?.textContent?.trim()||'Editar Produto';
    const sub=[...card.querySelectorAll('input')].map(x=>x.value).find(v=>v&&v.length<80&&!/^https?:/i.test(v))||'Gestão de tinta';
    if(oldTitle)oldTitle.style.display='none';
    const head=document.createElement('div');head.className='mmv-head';head.innerHTML=`<div><div class="mmv-title">Editar produto</div><div class="mmv-sub">${title!== 'Editar Produto'?title:sub} · Gestão profissional de tintas</div></div><div class="mmv-head-actions"><button type="button" data-mmv-close>× Fechar</button><button type="button" data-mmv-save>Guardar produto</button></div>`;
    card.insertBefore(head,card.firstChild);
    const ov=document.createElement('div');ov.className='mmv-overview';ov.innerHTML=`<div class="mmv-photo"><img src="${imageFor(modal)}" onerror="this.src='${WOODNEUCE_IMAGE}'"></div><div class="mmv-meta"><strong>${title}</strong><span>Produto do setor de tintas</span><div class="mmv-badges"><span class="mmv-badge ok">● Ativo</span><span class="mmv-badge">NEUCE</span><span class="mmv-badge">Pinturas</span></div></div><div><span class="mmv-badge">Editor de produto</span></div>`;
    const tabs=card.querySelector('.tabs');if(tabs)tabs.parentNode.insertBefore(ov,tabs);else card.insertBefore(ov,head.nextSibling);
    const footer=document.createElement('div');footer.className='mmv-footer';footer.innerHTML='<button type="button" class="danger" data-mmv-delete>Apagar produto</button><div><button type="button" data-mmv-cancel>Cancelar</button><button type="button" data-mmv-save2>Guardar produto</button></div>';
    card.appendChild(footer);
    const close=()=>{modal.classList.remove('open');};
    head.querySelector('[data-mmv-close]').onclick=close;
    head.querySelector('[data-mmv-save]').onclick=()=>{const b=[...card.querySelectorAll('button')].find(x=>/Guardar produto/i.test(x.textContent)&&!x.hasAttribute('data-mmv-save')&&!x.hasAttribute('data-mmv-save2'));if(b)b.click();};
    footer.querySelector('[data-mmv-cancel]').onclick=close;
    footer.querySelector('[data-mmv-save2]').onclick=()=>head.querySelector('[data-mmv-save]').click();
    footer.querySelector('[data-mmv-delete]').onclick=()=>{const b=[...card.querySelectorAll('button')].find(x=>/Apagar produto/i.test(x.textContent)&&!x.hasAttribute('data-mmv-delete'));if(b)b.click();};
    card.querySelectorAll('.tabpane').forEach(p=>{if(!p.querySelector('.mmv-card')&&p.children.length){const wrap=document.createElement('div');wrap.className='mmv-card';while(p.firstChild)wrap.appendChild(p.firstChild);p.appendChild(wrap);}});
  }
  function scan(){document.querySelectorAll('.modal.open').forEach(enhance);}
  new MutationObserver(scan).observe(document.documentElement,{subtree:true,childList:true,attributes:true,attributeFilter:['class']});
  setInterval(scan,500);scan();
})();

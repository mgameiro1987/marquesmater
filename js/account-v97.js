/* MarquesMater V9.7 — conta real, arranque robusto */
(function(){
  'use strict';
  var KEY='mm_demo_account_v87';
  function get(){try{return JSON.parse(localStorage.getItem(KEY)||'null')}catch(e){return null}}
  function save(v){localStorage.setItem(KEY,JSON.stringify(v))}
  function esc(v){return String(v==null?'':v).replace(/[&<>"']/g,function(m){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]})}
  function css(){
    if(document.getElementById('mm97accountcss'))return;
    var s=document.createElement('style');s.id='mm97accountcss';
    s.textContent='.mm97-auth{max-width:620px;margin:20px auto}.mm97-card{background:#fff;border:1px solid #e5eaf0;border-radius:18px;padding:24px;box-shadow:0 8px 28px rgba(15,23,42,.05)}.mm97-card h1{margin:0 0 6px}.mm97-card p{color:#64748b}.mm97-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.mm97-field{display:grid;gap:6px}.mm97-field.full{grid-column:1/-1}.mm97-field label{font-size:13px;font-weight:700}.mm97-field input{width:100%;box-sizing:border-box;padding:12px 13px;border:1px solid #d9e0e8;border-radius:9px;font:inherit}.mm97-submit{width:100%;margin-top:18px}.mm97-google{width:100%;margin-top:10px;padding:12px;border:1px solid #d9e0e8;background:#fff;border-radius:9px;font-weight:800;opacity:.65}.mm97-sep{display:flex;align-items:center;gap:10px;margin:18px 0;color:#94a3b8;font-size:12px}.mm97-sep:before,.mm97-sep:after{content:"";height:1px;background:#e5eaf0;flex:1}.mm97-switch{text-align:center;margin-top:18px}.mm97-switch button{border:0;background:none;color:#c56b00;font-weight:800;cursor:pointer}.mm97-note{font-size:12px;color:#64748b;margin-top:14px}.mm97-error{background:#fff1f2;color:#be123c;border:1px solid #fecdd3;padding:11px;border-radius:9px;margin-top:12px}.mm97-account{display:grid;gap:16px}.mm97-account-top{display:flex;justify-content:space-between;align-items:center;gap:15px;background:#fff;border:1px solid #e5eaf0;border-radius:15px;padding:18px}.mm97-account-top h2{margin:0}.mm97-account-top p{margin:4px 0 0;color:#64748b}.mm97-logout{border:1px solid #d9e0e8;background:#fff;border-radius:9px;padding:10px 13px;font-weight:800;cursor:pointer}@media(max-width:600px){.mm97-grid{grid-template-columns:1fr}.mm97-field.full{grid-column:auto}.mm97-account-top{align-items:flex-start;flex-direction:column}}';
    document.head.appendChild(s);
  }
  function accountData(){try{return JSON.parse(localStorage.getItem('mm_demo_account_data_v1')||'{}')}catch(e){return {}}}
  function storeSession(a){
    save({id:a.id,name:a.name,email:a.email,phone:a.phone||'',token:a.token});
    localStorage.setItem('mm_demo_account_data_v1',JSON.stringify({name:a.name,email:a.email,phone:a.phone||'',nif:''}));
  }
  function authForm(register){
    return '<div class="mm97-auth"><div class="mm97-card"><h1>'+(register?'Criar conta':'Entrar na minha conta')+'</h1><p>'+(register?'Cria a tua conta MarquesMater para acompanhares encomendas e guardares os teus dados.':'Entra para veres as tuas encomendas e os teus dados.')+'</p><form id="mm97Form"><div class="mm97-grid">'+
      (register?'<div class="mm97-field full"><label>Nome completo</label><input name="name" required autocomplete="name"></div>':'')+
      '<div class="mm97-field full"><label>Email</label><input name="email" type="email" required autocomplete="email"></div>'+
      (register?'<div class="mm97-field"><label>Telefone <span>(opcional)</span></label><input name="phone" autocomplete="tel"></div>':'')+
      '<div class="mm97-field '+(register?'':'full')+'"><label>Palavra-passe</label><input name="password" type="password" required minlength="8" autocomplete="'+(register?'new-password':'current-password')+'"></div>'+
      (register?'<div class="mm97-field"><label>Confirmar palavra-passe</label><input name="confirm" type="password" required minlength="8" autocomplete="new-password"></div>':'')+
      '</div><div id="mm97Error"></div><button class="btn orange mm97-submit" type="submit">'+(register?'CRIAR CONTA':'ENTRAR')+'</button></form><div class="mm97-sep"><span>ou</span></div><button class="mm97-google" type="button">Continuar com Google — em breve</button><div class="mm97-switch">'+(register?'Já tens conta?':'Ainda não tens conta?')+' <button type="button" id="mm97Switch">'+(register?'Entrar':'Criar conta')+'</button></div><div class="mm97-note">As compras como convidado continuam disponíveis no checkout. A conta não é obrigatória para comprar.</div></div></div>';
  }
  function render(){
    var box=document.getElementById('accountApp');if(!box)return;
    css();var u=get();
    if(!u || !u.token){
      var d=accountData(),register=location.hash==='#criar-conta';
      box.innerHTML=authForm(register);
      var email=document.querySelector('#mm97Form input[name="email"]');if(email)email.value=d.email||'';
      document.getElementById('mm97Switch').onclick=function(){location.hash=register?'':'criar-conta';render()};
      document.getElementById('mm97Form').onsubmit=submit;return;
    }
    box.innerHTML='<div class="mm97-account"><div class="mm97-account-top"><div><h2>A minha conta</h2><p>'+esc(u.name||'')+' · '+esc(u.email||'')+'</p></div><button class="mm97-logout" id="mm97Logout" type="button">Terminar sessão</button></div><div class="v832-breadcrumb"><span>A minha conta</span><b>›</b><span>As minhas encomendas</span></div><div class="v832-layout"><aside class="v832-sidebar"><a href="account.html" class="active">⌂ <span>A minha conta</span></a><a href="account-data.html">♙ <span>Os meus dados</span></a><a href="account.html#orders" class="active2">▣ <span>As minhas encomendas</span></a><a href="favorites.html">♡ <span>Os meus favoritos</span></a><a href="addresses.html">⌖ <span>Os meus endereços</span></a><button id="logoutSide" type="button">↪ <span>Terminar sessão</span></button></aside><section class="v832-main"><div class="v832-title"><div><h1>As minhas encomendas</h1><p>Acompanha aqui todas as tuas encomendas e o respetivo estado.</p></div></div><div id="orderHistory"></div></section></div></div>';
    document.getElementById('mm97Logout').onclick=logout;document.getElementById('logoutSide').onclick=logout;
  }
  async function submit(e){
    e.preventDefault();var f=e.currentTarget,d=Object.fromEntries(new FormData(f).entries()),register=location.hash==='#criar-conta',err=document.getElementById('mm97Error');
    if(register&&d.password!==d.confirm){err.innerHTML='<div class="mm97-error">As palavras-passe não coincidem.</div>';return}
    var b=f.querySelector('button[type="submit"]');b.disabled=true;b.textContent='A processar…';
    try{
      var r=await fetch(register?'/api/account/register':'/api/account/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:d.name||'',email:d.email,password:d.password,phone:d.phone||''}),cache:'no-store'});
      var j=await r.json().catch(function(){return {}});if(!r.ok||!j.ok)throw new Error(j.error||'Não foi possível concluir a operação.');
      storeSession(j.account);location.hash='';render();
    }catch(x){err.innerHTML='<div class="mm97-error">'+esc(x.message)+'</div>';b.disabled=false;b.textContent=register?'CRIAR CONTA':'ENTRAR'}
  }
  async function logout(){var u=get();try{if(u&&u.token)await fetch('/api/account/logout',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({token:u.token}),cache:'no-store'})}catch(e){}localStorage.removeItem(KEY);render()}
  window.MMAccount={get:get,render:render,login:function(){render()}};
  function boot(){try{render()}catch(e){var box=document.getElementById('accountApp');if(box)box.innerHTML='<div class="mm97-error">Não foi possível carregar a conta. Atualiza a página e tenta novamente.</div>';console.error(e)}}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();

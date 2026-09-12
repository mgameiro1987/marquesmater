(function(){
  'use strict';
  function esc(v){return String(v==null?'':v).replace(/[&<>\"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[c]})}
  function ensureStyles(){
    if(document.getElementById('mmNotifStyles')) return;
    var s=document.createElement('style'); s.id='mmNotifStyles';
    s.textContent='.mm-notif-panel{position:fixed;top:62px;right:24px;width:min(390px,calc(100vw - 24px));background:#fff;border:1px solid #dfe6ef;border-radius:14px;box-shadow:0 18px 45px #182b4626;z-index:1000;overflow:hidden}.mm-notif-head{display:flex;align-items:center;justify-content:space-between;padding:15px 16px;border-bottom:1px solid #edf1f5}.mm-notif-head strong{font-size:15px}.mm-notif-close{border:0;background:transparent;font-size:22px;line-height:1;color:#71819a;cursor:pointer}.mm-notif-list{max-height:430px;overflow:auto}.mm-notif-item{display:flex;gap:11px;padding:13px 16px;border-bottom:1px solid #f0f3f7;cursor:pointer}.mm-notif-item:hover{background:#f8fafc}.mm-notif-icon{width:38px;height:38px;flex:0 0 38px;border-radius:10px;display:grid;place-items:center;background:#e9f2ff;font-size:18px}.mm-notif-item.warning .mm-notif-icon{background:#fff3df}.mm-notif-item.success .mm-notif-icon{background:#eaf8ef}.mm-notif-item.info .mm-notif-icon{background:#f0eaff}.mm-notif-copy strong{display:block;font-size:12px;color:#172746;margin-bottom:3px}.mm-notif-copy span{display:block;font-size:11px;color:#73839a;line-height:1.4}.mm-notif-empty{padding:28px 18px;text-align:center;color:#73839a;font-size:12px}.mm-notif-foot{padding:11px 16px;background:#f8fafc;color:#1677f9;font-size:11px;font-weight:700;text-align:center;cursor:pointer}.bell.mm-notif-active{color:#1677f9}.bell i:empty{display:none}@media(max-width:600px){.mm-notif-panel{top:58px;right:8px;width:calc(100vw - 16px);border-radius:12px}.mm-notif-list{max-height:55vh}}';
    document.head.appendChild(s);
  }
  function closePanel(){var p=document.getElementById('mmNotifPanel');if(p)p.remove();var b=document.querySelector('.bell');if(b)b.classList.remove('mm-notif-active')}
  function go(section){closePanel();var el=document.querySelector('.navitem[data-section="'+section+'"]');if(el)el.click()}
  function makePanel(items){
    closePanel(); ensureStyles();
    var p=document.createElement('div');p.id='mmNotifPanel';p.className='mm-notif-panel';
    var html='<div class="mm-notif-head"><strong>Notificações</strong><button class="mm-notif-close" type="button" aria-label="Fechar">×</button></div><div class="mm-notif-list">';
    if(!items.length) html+='<div class="mm-notif-empty">Não há notificações pendentes.</div>';
    items.forEach(function(n){html+='<div class="mm-notif-item '+esc(n.type||'info')+'" data-section="'+esc(n.section||'')+'"><div class="mm-notif-icon">'+esc(n.icon||'•')+'</div><div class="mm-notif-copy"><strong>'+esc(n.title)+'</strong><span>'+esc(n.text)+'</span></div></div>'});
    html+='</div><div class="mm-notif-foot">Abrir gestão de encomendas</div>';
    p.innerHTML=html;document.body.appendChild(p);
    p.querySelector('.mm-notif-close').onclick=closePanel;
    p.querySelector('.mm-notif-foot').onclick=function(){go('orders')};
    p.querySelectorAll('.mm-notif-item').forEach(function(el){el.onclick=function(){var sec=el.getAttribute('data-section');if(sec)go(sec)}});
  }
  function setCount(n){var b=document.querySelector('.bell');if(!b)return;var i=b.querySelector('i');if(!i){i=document.createElement('i');b.appendChild(i)}i.textContent=n>0?String(n):''}
  function loadData(){
    var items=[];
    var catalogPromise=fetch('/api/catalog',{cache:'no-store'}).then(function(r){return r.ok?r.json():{}}).catch(function(){return {}});
    var ordersPromise=fetch('/api/orders',{cache:'no-store'}).then(function(r){return r.ok?r.json():{}}).catch(function(){return {}});
    return Promise.all([catalogPromise,ordersPromise]).then(function(res){
      var cat=res[0], ord=res[1];
      var products=Array.isArray(cat)?cat:(cat.catalog||cat.products||[]);
      var orders=Array.isArray(ord)?ord:(ord.orders||[]);
      var pending=orders.filter(function(o){var s=String(o.status||'').toLowerCase();return !/conclu|cancel|entregue|levant/.test(s)});
      if(pending.length) items.push({type:'info',icon:'🛒',title:pending.length+' encomenda'+(pending.length===1?'':'s')+' a acompanhar',text:'Existem encomendas que ainda não estão concluídas.',section:'orders'});
      var low=products.filter(function(p){var q=Number(p.stockQty!=null?p.stockQty:(p.stock!=null?p.stock:0));return Number.isFinite(q)&&q>0&&q<=3}).length;
      if(low) items.push({type:'warning',icon:'⚠',title:low+' produto'+(low===1?'':'s')+' com stock baixo',text:'Verifica as quantidades e repõe o stock quando necessário.',section:'products'});
      var inactive=products.filter(function(p){return p.active===false||String(p.active).toLowerCase()==='false'}).length;
      if(inactive) items.push({type:'warning',icon:'▣',title:inactive+' produto'+(inactive===1?'':'s')+' inativo'+(inactive===1?'':'s'),text:'Há artigos desativados no catálogo central.',section:'products'});
      if(!items.length) items.push({type:'success',icon:'✓',title:'Backoffice sem pendências',text:'Não foram encontrados avisos de encomendas ou stock.',section:'dashboard'});
      setCount(items.length); return items;
    });
  }
  function init(){
    ensureStyles();
    var b=document.querySelector('.bell');if(!b)return;
    b.type='button';b.setAttribute('aria-label','Abrir notificações');
    loadData();
    b.addEventListener('click',function(e){e.stopPropagation();loadData().then(makePanel)});
    document.addEventListener('click',function(e){var p=document.getElementById('mmNotifPanel');if(p&&!p.contains(e.target)&&!b.contains(e.target))closePanel()});
    document.addEventListener('keydown',function(e){if(e.key==='Escape')closePanel()});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
(()=>{'use strict';
const install=()=>{
 const side=document.getElementById('sidebar'),btn=document.getElementById('openMenu'),close=document.getElementById('closeMenu');
 if(!side||!btn)return false;
 if(document.getElementById('mm46menuStyle'))document.getElementById('mm46menuStyle').remove();
 const st=document.createElement('style');st.id='mm46menuStyle';st.textContent=`
 @media(max-width:900px){
  #openMenu{display:flex!important;align-items:center!important;justify-content:center!important;width:52px!important;height:52px!important;margin:0 8px 0 4px!important;padding:0!important;border:0!important;background:transparent!important;color:#172033!important;font-size:30px!important;line-height:1!important;cursor:pointer!important;pointer-events:auto!important;position:relative!important;z-index:2147483646!important;-webkit-tap-highlight-color:transparent!important;touch-action:manipulation!important}
  #sidebar{z-index:2147483645!important}
  #sidebar.open{transform:translateX(0)!important;visibility:visible!important;opacity:1!important;pointer-events:auto!important}
  #sidebar:not(.open){pointer-events:none!important}
  #closeMenu{pointer-events:auto!important;cursor:pointer!important}
  body.mm46-lock{overflow:hidden!important}
  #mm46shade{position:fixed;inset:0;background:rgba(15,23,42,.42);z-index:2147483640;display:none}
  #mm46shade.open{display:block}
 }
 `;document.head.appendChild(st);
 let shade=document.getElementById('mm46shade');if(!shade){shade=document.createElement('div');shade.id='mm46shade';document.body.appendChild(shade)}
 const show=()=>{side.classList.add('open');shade.classList.add('open');document.body.classList.add('mm46-lock');btn.setAttribute('aria-expanded','true')};
 const hide=()=>{side.classList.remove('open');shade.classList.remove('open');document.body.classList.remove('mm46-lock');btn.setAttribute('aria-expanded','false')};
 btn.type='button';btn.setAttribute('aria-label','Abrir menu');btn.setAttribute('aria-expanded','false');btn.onclick=e=>{e.preventDefault();e.stopPropagation();show()};
 close&&(close.type='button',close.onclick=e=>{e.preventDefault();e.stopPropagation();hide()});
 shade.onclick=hide;
 side.querySelectorAll('.navitem').forEach(x=>{x.addEventListener('click',hide,true);x.addEventListener('touchend',hide,true)});
 document.addEventListener('pointerdown',e=>{if(e.target.closest&&e.target.closest('#openMenu')){e.preventDefault();show()}else if(side.classList.contains('open')&&!e.target.closest('#sidebar')&&!e.target.closest('#openMenu'))hide()},true);
 document.addEventListener('touchend',e=>{if(e.target.closest&&e.target.closest('#openMenu')){e.preventDefault();show()}},true);
 window.addEventListener('keydown',e=>{if(e.key==='Escape')hide()});
 return true;
};
if(!install()){const t=setInterval(()=>{if(install())clearInterval(t)},100);setTimeout(()=>clearInterval(t),15000)}
})();

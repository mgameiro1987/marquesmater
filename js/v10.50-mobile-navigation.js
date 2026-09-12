(()=>{'use strict';
let routing=false;
const route=k=>{
 if(routing)return;
 routing=true;
 try{
  const go=window.MM104?.go;
  if(go)go(k);
  else document.querySelector(`.navitem[data-section="${CSS.escape(k)}"]`)?.click();
 }catch(e){console.error('MarquesMater navigation error:',e)}
 setTimeout(()=>{
  document.getElementById('sidebar')?.classList.remove('open');
  document.getElementById('mm46shade')?.classList.remove('open');
  document.body.classList.remove('mm46-lock');
  routing=false;
 },80);
};
const install=()=>{
 const items=document.querySelectorAll('.navitem');
 if(!items.length)return false;
 document.querySelectorAll('.navitem').forEach(b=>{
  if(b.dataset.mm50==='1')return;
  b.dataset.mm50='1';
 });
 return true;
};
document.addEventListener('click',e=>{
 const b=e.target.closest?.('.navitem');
 if(!b)return;
 if(routing)return;
 e.preventDefault();
 e.stopImmediatePropagation();
 route(b.dataset.section);
},true);
document.addEventListener('pointerup',e=>{
 const b=e.target.closest?.('.navitem');
 if(!b||routing)return;
 e.preventDefault();
 e.stopImmediatePropagation();
 route(b.dataset.section);
},true);
if(!install()){const t=setInterval(()=>{if(install())clearInterval(t)},100);setTimeout(()=>clearInterval(t),15000)}
})();

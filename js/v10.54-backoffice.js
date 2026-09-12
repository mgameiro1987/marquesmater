(()=>{'use strict';
/* MarquesMater V10.54 — router central: evita que chamadas diretas ao MM104 voltem a abrir módulos antigos. */
const navButton=k=>document.querySelector(`.navitem[data-section="${CSS.escape(k)}"]`);
const routedClick=k=>{const b=navButton(k);if(!b)return false;const e=new MouseEvent('click',{bubbles:true,cancelable:true});Object.defineProperty(e,'__mm54pass',{value:true});b.dispatchEvent(e);return true};
function install(){if(window.MM54Router)return true;if(!window.MM104?.go)return false;const legacy=window.MM104.go;const go=function(k){
  if(k==='products')return window.MMCurrent?.products?.();
  if(k==='orders')return window.MMOrdersAdmin?.open?.()||routedClick(k);
  if(['categories','brands','attributes','users','chat','marketing'].includes(k))return routedClick(k);
  return legacy.apply(this,arguments);
};go.__mm54=true;window.MM104.go=go;window.MM54Router=true;return true}
const t=setInterval(()=>{if(install())clearInterval(t)},100);setTimeout(()=>clearInterval(t),20000);install();
})();

(()=>{'use strict';
// MarquesMater — versão global única do Backoffice.
// Todas as áreas apresentam sempre a versão global atual.
const VERSION='V9.3.6';
window.MM_CURRENT_VERSION=VERSION;
function replaceText(root=document.body){
  const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);
  const nodes=[];let n;
  while(n=walker.nextNode())nodes.push(n);
  nodes.forEach(x=>{x.nodeValue=x.nodeValue.replace(/V9\.3(?!\.\d)/g,VERSION).replace(/v9\.3(?!\.\d)/g,VERSION)});
}
function apply(){
  document.title=document.title.replace(/V9\.3(?!\.\d)/g,VERSION).replace(/v9\.3(?!\.\d)/g,VERSION);
  if(document.body)replaceText(document.body);
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',apply);else apply();
new MutationObserver(mutations=>mutations.forEach(m=>m.addedNodes.forEach(node=>{if(node.nodeType===1)replaceText(node);else if(node.nodeType===3)node.nodeValue=node.nodeValue.replace(/V9\.3(?!\.\d)/g,VERSION).replace(/v9\.3(?!\.\d)/g,VERSION)}))).observe(document.documentElement,{childList:true,subtree:true});
})();
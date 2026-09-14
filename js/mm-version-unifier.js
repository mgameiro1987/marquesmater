(()=>{'use strict';
// MarquesMater — versão global única do Backoffice.
const VERSION='V9.3.17';
window.MM_CURRENT_VERSION=VERSION;
const OLD=/V9\.3\.16|V9\.3\.15|V9\.3\.14|V9\.3\.13|V9\.3\.12|V9\.3\.11|V9\.3\.10|V9\.3\.9/g,OLDLOW=/v9\.3\.16|v9\.3\.15|v9\.3\.14|v9\.3\.13|v9\.3\.12|v9\.3\.11|v9\.3\.10|v9\.3\.9/g;
function replaceText(root=document.body){const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);const nodes=[];let n;while(n=walker.nextNode())nodes.push(n);nodes.forEach(x=>{x.nodeValue=x.nodeValue.replace(OLD,VERSION).replace(OLDLOW,VERSION)})}
function apply(){document.title=document.title.replace(OLD,VERSION).replace(OLDLOW,VERSION);if(document.body)replaceText(document.body)}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',apply);else apply();
new MutationObserver(m=>m.forEach(x=>x.addedNodes.forEach(n=>{if(n.nodeType===1)replaceText(n);else if(n.nodeType===3)n.nodeValue=n.nodeValue.replace(OLD,VERSION).replace(OLDLOW,VERSION)}))).observe(document.documentElement,{childList:true,subtree:true});
})();
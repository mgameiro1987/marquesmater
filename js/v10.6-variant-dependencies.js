(()=>{
'use strict';
const getCfg=p=>p?.options?.__variant_config||null;
const getRoot=()=>document.getElementById('root');
function rules(p){return getCfg(p)?.dependencies||[]}
function selected(root){const out={};root?.querySelectorAll('.v6-option,.option').forEach(block=>{const label=block.querySelector('label')?.textContent?.trim();if(!label)return;const b=block.querySelector('button.selected,.v6-swatch.selected');if(!b)return;const em=b.querySelector('em');out[label]=(em?.textContent||b.dataset.value||b.textContent||'').trim()});return out}
function matches(cond,sel){return Object.entries(cond||{}).every(([name,vals])=>{const a=Array.isArray(vals)?vals:[vals];return a.includes(String(sel[name]??''))})}
function visible(attr,sel,rs){const show=rs.filter(r=>r.option===attr.name&&r.type==='showIf');if(!show.length)return true;return show.some(r=>matches(r.when,sel))}
function apply(p,root){const rs=rules(p),sel=selected(root);root.querySelectorAll('.v6-option,.option').forEach(block=>{const label=block.querySelector('label')?.textContent?.trim();if(!label)return;const ok=visible({name:label},sel,rs);block.hidden=!ok;block.setAttribute('data-mm-dependency-visible',ok?'1':'0');if(!ok){block.querySelectorAll('button.selected,.v6-swatch.selected').forEach(b=>b.classList.remove('selected'))}})}
function boot(){const sku=new URLSearchParams(location.search).get('sku'),p=(window.MARQUES_CATALOG||[]).find(x=>String(x.sku)===String(sku));const root=getRoot();if(!p||!root)return;if(!getCfg(p)?.dependencies?.length)return;const run=()=>apply(p,root);root.addEventListener('click',e=>{if(e.target.closest('.option-buttons button,.v6-option button'))setTimeout(run,30)});setTimeout(run,100)}
window.MMVariantDependencies={matches,apply};boot();
})();
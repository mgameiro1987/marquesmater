(()=>{'use strict';if(window.__MM96ORDERADDRESS)return;window.__MM96ORDERADDRESS=1;
const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]));
const clean=v=>String(v??'').trim();
function pick(o,keys){for(const k of keys){if(o&&o[k]!=null&&clean(o[k]))return clean(o[k])}return ''}
function addressText(c){if(!c)return '';
  const nested=c.address||c.morada||c.shipping_address||c.billing_address||c.delivery_address;
  if(typeof nested==='string'&&clean(nested))return clean(nested);
  const a=(nested&&typeof nested==='object')?nested:{};
  const street=pick(a,['street','address','address1','line1','morada','rua','logradouro'])||pick(c,['street','address','address1','line1','morada','rua']);
  const line2=pick(a,['address2','line2','complement','complemento','porta','door'])||pick(c,['address2','line2','complement','complemento','porta','door']);
  const cp=pick(a,['postalCode','postal_code','postcode','zip','zipCode','codigoPostal','codPostal'])||pick(c,['postalCode','postal_code','postcode','zip','zipCode','codigoPostal','codPostal']);
  const city=pick(a,['city','locality','town','concelho','localidade','cidade'])||pick(c,['city','locality','town','concelho','localidade','cidade']);
  const district=pick(a,['district','state','region','distrito'])||pick(c,['district','state','region','distrito']);
  const country=pick(a,['country','countryName','pais'])||pick(c,['country','countryName','pais']);
  return [street,line2,[cp,city].filter(Boolean).join(' '),district,country].filter(Boolean).join(', ');
}
function inject(){document.querySelectorAll('.mm96-box').forEach(box=>{if(box.querySelector('[data-mm96-address]'))return;
  const detail=box.querySelector('.mm96-detail');if(!detail)return;
  const text=Array.from(detail.querySelectorAll('div')).find(x=>x.textContent.trim()==='Telefone')?.parentElement;
  const customerWindow=window.__MM96_CURRENT_ORDER;
  const addr=addressText(customerWindow?.customer||customerWindow?.order?.customer||{});
  if(!addr)return;
  const node=document.createElement('div');node.className='mm96-full';node.dataset.mm96Address='1';node.innerHTML='<label>Morada da encomenda</label><div>'+esc(addr)+'</div>';
  if(text&&text.parentElement===detail)text.insertAdjacentElement('afterend',node);else detail.insertBefore(node,detail.firstElementChild);
});}
const oldFetch=window.fetch;window.fetch=async function(...args){const r=await oldFetch.apply(this,args);try{const url=String(args[0]?.url||args[0]||'');if(/\/api\/orders\/\d+$/.test(url)){const clone=r.clone();clone.json().then(j=>{if(j?.order)window.__MM96_CURRENT_ORDER=j.order;setTimeout(inject,20);setTimeout(inject,150)}).catch(()=>{})}}catch(_){}return r};
new MutationObserver(()=>inject()).observe(document.body,{childList:true,subtree:true});setTimeout(inject,500);
})();
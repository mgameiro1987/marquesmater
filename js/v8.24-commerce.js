/* MarquesMater V8.25 — cupões + guest checkout + pagamentos demo, estável no mobile */
(function(){
 const COUPON_KEY='mm_coupon_v824';
 const CODES={
  MARQUES10:{type:'percent',value:10,label:'10% de desconto'},
  BEMVINDO5:{type:'percent',value:5,label:'5% de desconto'},
  OBRA50:{type:'fixed',value:50,min:250,label:'50,00 € de desconto em compras desde 250,00 €'}
 };
 function money(n){return Number(n||0).toFixed(2).replace('.',',')+' €'}
 function getCoupon(){try{return JSON.parse(localStorage.getItem(COUPON_KEY))||null}catch(e){return null}}
 function setCoupon(c){if(c)localStorage.setItem(COUPON_KEY,JSON.stringify(c));else localStorage.removeItem(COUPON_KEY)}
 function cartData(){const s=window.MMStore?.state?.()||{cart:[]};let subtotal=0;const items=s.cart||[];items.forEach(x=>{const p=window.MMStore?.product?.(x.sku);if(!p)return;let price=p.price;if(x.options?.Embalagem&&p.variantPrices?.Embalagem?.[x.options.Embalagem])price=p.variantPrices.Embalagem[x.options.Embalagem];subtotal+=price*(x.qty||1)});return{subtotal,items}}
 function discountFor(sub,c){if(!c||!CODES[c.code])return 0;const rule=CODES[c.code];if(rule.min&&sub<rule.min)return 0;return Math.min(sub,rule.type==='percent'?sub*rule.value/100:rule.value)}
 function couponUI(){
  const box=document.getElementById('cartApp');if(!box||!box.querySelector('.v85-summary'))return;
  const summary=box.querySelector('.v85-summary');if(summary.querySelector('.mm-coupon'))return;
  const coupon=getCoupon(),wrap=document.createElement('div');wrap.className='mm-coupon';
  wrap.innerHTML='<h3>Código promocional</h3><div class="mm-coupon-row"><input id="mmCouponInput" placeholder="Ex.: MARQUES10" value="'+(coupon?.code||'')+'"><button id="mmCouponApply" type="button">APLICAR</button></div><span id="mmCouponMsg" class="mm-coupon-msg">'+(coupon?('Cupão '+coupon.code+' aplicado.'): 'Introduz um código de desconto.')+'</span>';
  const checkout=summary.querySelector('.btn.orange');summary.insertBefore(wrap,checkout||null);
  const input=wrap.querySelector('#mmCouponInput'),msg=wrap.querySelector('#mmCouponMsg');
  wrap.querySelector('#mmCouponApply').addEventListener('click',function(){
   const code=input.value.trim().toUpperCase(),rule=CODES[code];
   if(!rule){setCoupon(null);msg.className='mm-coupon-msg err';msg.textContent='Código inválido ou expirado.';return}
   const sub=cartData().subtotal;
   if(rule.min&&sub<rule.min){msg.className='mm-coupon-msg err';msg.textContent='Este código requer uma compra mínima de '+money(rule.min)+'.';return}
   setCoupon({code});msg.className='mm-coupon-msg ok';msg.textContent='Cupão '+code+' aplicado: '+rule.label+'.';renderCartDiscount(summary);
  });
  renderCartDiscount(summary);
 }
 function renderCartDiscount(summary){
  const data=cartData(),c=getCoupon(),disc=discountFor(data.subtotal,c);let line=summary.querySelector('.mm-discount-line');
  if(disc){if(!line){line=document.createElement('div');line.className='mm-discount-line';const coupon=summary.querySelector('.mm-coupon');if(coupon)coupon.insertAdjacentElement('afterend',line);else summary.insertBefore(line,summary.querySelector('.btn.orange')||null)}line.innerHTML='<span>Desconto '+c.code+'</span><strong>− '+money(disc)+'</strong>'}
  else if(line)line.remove();
  let total=summary.querySelector('.mm-v824-total');if(!total){total=document.createElement('div');total.className='mm-v824-total';total.innerHTML='<span>Total estimado</span><strong></strong>';summary.insertBefore(total,summary.querySelector('.btn.orange')||null)}
  total.querySelector('strong').textContent=money(data.subtotal-disc);
 }
 function checkoutUI(){
  const box=document.getElementById('checkoutApp');if(!box)return;
  const form=box.querySelector('#checkoutForm');if(!form)return;
  const paymentSection=[...form.querySelectorAll('.v871-panel')].find(x=>/Pagamento/.test(x.textContent));
  if(paymentSection&&!paymentSection.querySelector('.mm-payment-grid')){
   paymentSection.innerHTML='<h2>3. Pagamento</h2><div class="mm-payment-grid"><label class="mm-payment-option"><input type="radio" name="payment" value="Cartão" checked><span><b>💳 Cartão</b><small>Visa, Mastercard e outros cartões</small></span></label><label class="mm-payment-option"><input type="radio" name="payment" value="MB WAY"><span><b>📱 MB WAY</b><small>Pagamento rápido através do telemóvel</small></span></label><label class="mm-payment-option"><input type="radio" name="payment" value="Multibanco"><span><b>🏦 Multibanco</b><small>Referência de pagamento</small></span></label><label class="mm-payment-option"><input type="radio" name="payment" value="PayPal"><span><b>🅿️ PayPal</b><small>Pagamento através da tua conta PayPal</small></span></label><label class="mm-payment-option"><input type="radio" name="payment" value="Klarna"><span><b>🛍️ Klarna</b><small>Pagamento faseado, quando disponível</small></span><em class="mm-payment-badge">Preparado</em></label></div><div class="mm-pay-note">DEMO: os métodos apresentados são preparação visual. Nenhum pagamento real é processado nesta versão.</div>';
  }
  const summary=box.querySelector('.v871-summary');if(!summary)return;
  let guest=box.querySelector('.mm-guest');
  if(!guest){guest=document.createElement('div');guest.className='mm-guest';guest.innerHTML='<strong>🛒 Comprar como convidado</strong><span>Não precisas de criar uma conta para concluir a compra. Podes preencher os dados necessários e seguir diretamente para o pagamento.</span><label class="mm-guest-check"><input type="checkbox" name="guest" checked> Comprar sem criar conta</label>';form.insertBefore(guest,form.firstChild)}
  updateCheckoutTotals(box,form,summary);
  if(form.dataset.v825Bound)return;
  form.dataset.v825Bound='1';
  form.querySelectorAll('input[name="delivery"]').forEach(x=>x.addEventListener('change',function(){updateCheckoutTotals(box,form,summary)}));
  form.addEventListener('submit',function(e){
   e.preventDefault();
   if(!form.reportValidity())return;
   const f=Object.fromEntries(new FormData(form).entries()),fresh=cartData(),cc=getCoupon(),dd=discountFor(fresh.subtotal,cc),fee=f.delivery==='Entrega em Portugal Continental'?4.9:0,total=fresh.subtotal-dd+fee,number='MM-DEMO-'+String(Date.now()).slice(-7);
   let all=[];try{all=JSON.parse(localStorage.getItem('mm_orders_v87'))||[]}catch(_){}
   all.push({number,date:new Date().toLocaleString('pt-PT'),total,subtotal:fresh.subtotal,discount:dd,coupon:cc?.code||null,status:'Recebida · DEMO',items:fresh.items,customer:f});localStorage.setItem('mm_orders_v87',JSON.stringify(all));
   if(window.MMStore)MMStore.clearCart();setCoupon(null);
   box.innerHTML='<div class="v871-success"><div class="v871-check">✓</div><span class="eyebrow dark">ENCOMENDA DEMO · V8.25</span><h2>Encomenda confirmada!</h2><p>Obrigado, '+(f.name||'cliente')+'. A tua encomenda foi registada apenas para simulação.</p><div class="v871-order-number"><small>Número da encomenda</small><strong>'+number+'</strong></div><div class="v89-success-timeline"><div class="v89-timeline-step done"><b>✓</b>Encomenda<br>registada</div><div class="v89-timeline-step"><b>2</b>Preparação</div><div class="v89-timeline-step"><b>3</b>Entrega / levantamento</div><div class="v89-timeline-step"><b>4</b>Concluída</div></div><div class="v871-success-info"><b>Total: '+money(total)+'</b><span>'+f.delivery+'</span><span>'+f.payment+'</span>'+(dd?'<span class="v88-delivery-badge">✓ Desconto '+money(dd)+' ('+cc.code+')</span>':'')+'<span class="v88-delivery-badge">✓ Compra como '+(f.guest?'convidado':'cliente')+'</span></div><div class="v89-order-customer"><strong>Dados da encomenda</strong><br>'+f.name+' · '+f.email+'<br>'+(f.delivery==='Entrega em Portugal Continental'?(f.address||'')+' · '+(f.zip||'')+' '+(f.city||''):'Levantamento em loja')+'</div><div class="v88-success-actions"><a class="btn orange" href="account.html">VER A MINHA ENCOMENDA</a><a class="btn dark" href="index.html">CONTINUAR A COMPRAR</a></div></div>';
  });
 }
 function updateCheckoutTotals(box,form,summary){
  const data=cartData(),c=getCoupon(),disc=discountFor(data.subtotal,c),delivery=form.querySelector('input[name="delivery"]:checked')?.value==='Entrega em Portugal Continental',fee=delivery?4.9:0;
  const addr=form.querySelector('#addressBox'),dp=summary.querySelector('#deliveryPrice'),tp=summary.querySelector('#totalPrice');
  if(addr)addr.style.display=delivery?'block':'none';if(dp)dp.textContent=fee?money(fee):'Grátis';if(tp)tp.textContent=money(data.subtotal-disc+fee);
  let line=summary.querySelector('.mm-discount-line');if(disc){if(!line){line=document.createElement('div');line.className='mm-discount-line';const hr=summary.querySelector('hr');if(hr)hr.insertAdjacentElement('afterend',line);else summary.insertBefore(line,summary.firstChild)}line.innerHTML='<span>Desconto '+c.code+'</span><strong>− '+money(disc)+'</strong>'}else if(line)line.remove();
 }
 function boot(){couponUI();checkoutUI();}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else setTimeout(boot,0);
})();

/* MarquesMater V8.31 — catálogo/variantes: preços demo coerentes por opção */
(function(){
  const P=window.MM_VARIANT_PRICES=window.MM_VARIANT_PRICES||{};
  const set=(sku,option,values)=>{P[sku]=P[sku]||{};P[sku][option]=Object.assign(P[sku][option]||{},values)};
  // Preços DEMO por variante: substituem apenas quando há uma diferença comercial clara.
  set('LAMP-E27-10W','Potência',{'10 W':2.49,'12 W':2.89,'15 W':3.49});
  set('LAMP-E27-10W','Temperatura de cor',{'3000 K':2.49,'4000 K':2.49,'6500 K':2.59});
  set('FERR-M8-50','Medida',{'M6 x 40 mm':3.90,'M8 x 50 mm':4.90,'M10 x 60 mm':6.50});
  set('FERR-M8-50','Material',{'Aço zincado':4.90,'Inox':7.90});
  set('FERR-M8-50','Quantidade',{'10 un.':4.90,'25 un.':9.90,'50 un.':17.90});
  set('CAN-PPR-25','Diâmetro',{'20 mm':6.90,'25 mm':8.90,'32 mm':12.90});
  set('CAN-PPR-25','Comprimento',{'2 m':8.90,'4 m':16.90});
  set('CAN-PPR-25','Pressão',{'PN16':8.90,'PN20':10.90});
  set('EPI-CAP-001','Cor',{'Branco':12.90,'Amarelo':12.90,'Azul':13.50});
  set('CIM-25-001','Embalagem',{'25 kg':6.50,'35 kg':8.90});
  set('CASA-ORG-001','Tamanho',{'5 L':5.90,'12 L':8.90,'25 L':13.90});
  set('PROMO-DISC-125','Diâmetro',{'115 mm':12.90,'125 mm':14.90,'230 mm':29.90});
  set('SIL001','Volume',{'280 ml':7.95,'300 ml':8.45});
  set('SOU-PU-001','Aplicação',{'Pistola':9.90,'Manual':8.90});
  set('JARD-SERRA-001','Lâmina',{'6"':119.90,'8"':129.90});
  set('RHD01075-B22','Bateria',{'2 Ah':119.90,'4 Ah':139.90,'6 Ah':159.90});
  set('RHD01075-B22','Kit',{'Máquina':119.90,'Máquina + 2 baterias + carregador':189.90,'Kit + mala BMC':219.90});
  set('CAB-3G15-25','Secção',{'3G1,5 mm²':24.90,'3G2,5 mm²':34.90});
  set('CAB-3G15-25','Comprimento',{'25 m':24.90,'50 m':44.90,'100 m':79.90});
})();

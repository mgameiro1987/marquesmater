/* MarquesMater V8.31 — expansão DEMO do catálogo + preços de variantes */
(function(){
  const extra=[
    {sku:'TOOL-MECH-001',brand:'MarquesMater',name:'Berbequim Elétrico 850W',category:'Ferramentas',subcategory:'Ferramentas Elétricas',type:'tool',price:69.90,stock:'Em stock',image:'images/drill.svg',description:'Berbequim elétrico para perfuração e trabalhos de bricolage.',options:{'Potência':['650 W','850 W'],'Mandril':['10 mm','13 mm']},specs:['Potência: conforme versão','Mandril: conforme versão','Uso: bricolage e manutenção']},
    {sku:'TOOL-GRIND-001',brand:'MarquesMater',name:'Rebarbadora 900W 125 mm',category:'Ferramentas',subcategory:'Corte e Desbaste',type:'tool',price:59.90,stock:'Em stock',image:'images/disc.svg',description:'Rebarbadora compacta para corte e desbaste.',options:{'Potência':['750 W','900 W'],'Diâmetro':['115 mm','125 mm']},specs:['Potência: conforme versão','Disco: 115/125 mm','Uso: corte e desbaste']},
    {sku:'TOOL-HAND-001',brand:'MarquesMater',name:'Alicate Universal Profissional',category:'Ferramentas',subcategory:'Ferramentas Manuais',type:'tool',price:9.90,stock:'Em stock',image:'images/hardware.svg',description:'Alicate universal para manutenção e montagem.',options:{'Tamanho':['160 mm','180 mm','200 mm'],'Acabamento':['Standard','Profissional']},specs:['Tipo: universal','Uso: manutenção']},
    {sku:'CONST-IMP-001',brand:'MarquesMater',name:'Impermeabilizante Acrílico 5 kg',category:'Construção',subcategory:'Impermeabilização',type:'construction',price:29.90,stock:'Em stock',image:'images/paint.svg',description:'Impermeabilizante para proteção de superfícies de construção.',options:{'Embalagem':['1 kg','5 kg','15 kg']},specs:['Aplicação: impermeabilização','Embalagem: conforme versão']},
    {sku:'CONST-ISO-001',brand:'MarquesMater',name:'Placa de Isolamento Térmico',category:'Construção',subcategory:'Isolamentos',type:'construction',price:18.90,stock:'Em stock',image:'images/home.svg',description:'Placa para soluções de isolamento térmico.',options:{'Espessura':['20 mm','40 mm','60 mm'],'Área':['1 m²','2 m²']},specs:['Aplicação: isolamento','Espessura: conforme versão']},
    {sku:'CONST-MAT-001',brand:'MarquesMater',name:'Argamassa de Reparação 25 kg',category:'Construção',subcategory:'Materiais de Obra',type:'construction',price:8.90,stock:'Em stock',image:'images/cement.svg',description:'Argamassa para reparação e trabalhos gerais de construção.',options:{'Embalagem':['5 kg','25 kg']},specs:['Aplicação: reparação','Embalagem: conforme versão']},
    {sku:'RIDA-GRIND-001',brand:'RIDA',name:'Rebarbadora RIDA 20V',category:'RIDA',subcategory:'Rebarbadoras',type:'rida',price:129.90,stock:'Em stock',image:'images/disc.svg',description:'Rebarbadora sem fios RIDA para corte e desbaste.',options:{'Bateria':['2 Ah','4 Ah','6 Ah'],'Kit':['Máquina','Máquina + bateria + carregador']},specs:['Tensão: 20 V','Uso: profissional']},
    {sku:'RIDA-BATT-001',brand:'RIDA',name:'Bateria RIDA 20V',category:'RIDA',subcategory:'Baterias e Carregadores',type:'rida',price:39.90,stock:'Em stock',image:'images/drill.svg',description:'Bateria compatível com a plataforma RIDA 20V.',options:{'Capacidade':['2 Ah','4 Ah','6 Ah']},specs:['Tensão: 20 V','Capacidade: conforme versão']},
    {sku:'RIDA-SAW-002',brand:'RIDA',name:'Serra Circular RIDA 20V',category:'RIDA',subcategory:'Serras',type:'rida',price:159.90,stock:'Em stock',image:'images/garden.svg',description:'Serra circular sem fios para trabalhos de corte.',options:{'Bateria':['2 Ah','4 Ah','6 Ah'],'Lâmina':['165 mm','190 mm']},specs:['Tensão: 20 V','Lâmina: conforme versão']}
  ];
  window.MARQUES_CATALOG=window.MARQUES_CATALOG||[];
  extra.forEach(p=>{if(!window.MARQUES_CATALOG.some(x=>x.sku===p.sku))window.MARQUES_CATALOG.push(p)});
  const P=window.MM_VARIANT_PRICES=window.MM_VARIANT_PRICES||{};
  const set=(sku,o,v)=>{P[sku]=P[sku]||{};P[sku][o]=v};
  set('TOOL-MECH-001','Potência',{'650 W':59.90,'850 W':69.90});set('TOOL-MECH-001','Mandril',{'10 mm':59.90,'13 mm':69.90});
  set('TOOL-GRIND-001','Potência',{'750 W':54.90,'900 W':59.90});set('TOOL-GRIND-001','Diâmetro',{'115 mm':54.90,'125 mm':59.90});
  set('TOOL-HAND-001','Tamanho',{'160 mm':8.90,'180 mm':9.90,'200 mm':11.90});
  set('CONST-IMP-001','Embalagem',{'1 kg':8.90,'5 kg':29.90,'15 kg':69.90});
  set('CONST-ISO-001','Espessura',{'20 mm':12.90,'40 mm':18.90,'60 mm':25.90});
  set('CONST-MAT-001','Embalagem',{'5 kg':3.90,'25 kg':8.90});
  set('RIDA-GRIND-001','Bateria',{'2 Ah':129.90,'4 Ah':149.90,'6 Ah':169.90});set('RIDA-GRIND-001','Kit',{'Máquina':129.90,'Máquina + bateria + carregador':179.90});
  set('RIDA-BATT-001','Capacidade',{'2 Ah':39.90,'4 Ah':59.90,'6 Ah':79.90});
  set('RIDA-SAW-002','Bateria',{'2 Ah':159.90,'4 Ah':179.90,'6 Ah':199.90});
  set('RIDA-SAW-002','Lâmina',{'165 mm':159.90,'190 mm':179.90});
})();

import sqlite3, json
p='data/catalog.db'
c=sqlite3.connect(p)
v=[{'name':'1L','price':'','stock':'Consultar','ref':''},{'name':'5L','price':'','stock':'Consultar','ref':'5602920280071','ean':'5602920280071'},{'name':'15L','price':'','stock':'Consultar','ref':'5602920280088','ean':'5602920280088'}]
tech=['Tinta aquosa 100% acrílica de alta qualidade','Acabamento liso mate','Elevada resistência à água','Excelente retenção de cor','Máxima durabilidade','Aplicação: trincha, rolo ou pistola','Demãos recomendadas: 3','Rendimento: 12 m²/L por demão (valor orientativo)','Diluição: água — 1.ª demão 10%; restantes 5%','Secagem superficial: aproximadamente 30 minutos','Repintura: 3 a 4 horas']
img='https://www.neuce.com/files/products/1128_1.png?dp=20260319193436'
page='https://www.neuce.com/p180-p-1128-neucegold-ng-pt_pt'
pdf='https://www.neuce.com/files/ficha_tec/neucegold_ng_ft_0511_vr3_PT.pdf?dp=20260319193436'
sds='https://www.neuce.com/files/ficha_seg/1051101200139696-NEUCEGOLD%20NG-Acrilica_Nova_Geracao_9007-%28EU%29.pdf?dp=20260523145400%3F'
war='https://www.neuce.com/p221-warranty-terms-and-conditions-neucegold-ng-pt_en?site_lingua=pt_pt'
desc='Tinta aquosa 100% acrílica de alta qualidade, indicada para proteção de fachadas. Apresenta elevada resistência à água, excelente retenção de cor e máxima durabilidade. Indicada para fachadas em reboco areado ou liso, betão e cimento.'
docs=[{'title':'Página oficial NEUCE','url':page},{'title':'Ficha Técnica NEUCEGOLD NG','url':pdf},{'title':'Ficha de Segurança','url':sds},{'title':'Garantia NEUCEGOLD NG','url':war}]
c.execute("""INSERT OR REPLACE INTO products (slug,id,name,ref,ean,family,category,subfamily,brand,price_display,price,promo_price,stock,min_stock,state,featured,description,description_html,tech,image,gallery_json,permalink,doc,docs_json,variants_json,related_json,seo_title,seo_description,vat_rate,promo_enabled,supplier,manufacturer_url,allow_backorder,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)""",('neucegold-ng','neucegold-ng','Neucegold NG','','','Pinturas','Pinturas','Tinta Exterior','NEUCE','Preço por variante',0,None,0,5,'active',0,desc,'',json.dumps(tech,ensure_ascii=False),img,json.dumps([img]),'/produto/neucegold-ng',page,json.dumps(docs,ensure_ascii=False),json.dumps(v,ensure_ascii=False),json.dumps(['neucebel','neucematt']),'Neucegold NG — Tinta 100% Acrílica','Tinta 100% acrílica para proteção de fachadas.',23,0,'NEUCE',page,1))
c.commit(); c.close()

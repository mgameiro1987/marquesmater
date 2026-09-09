from pathlib import Path
import json, sqlite3
# V25 final: apenas o T-Rex Power 290ml fica ativo na marca Soudal.
ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'/'soudal_products.json'
DB=ROOT/'data'/'catalog.db'
TARGET='soudal-t-rex-power-290ml'
IMAGES={'Branco':'assets/soudal/trex-power-290-branco.jpg','Cinzento':'assets/soudal/trex-power-290-cinzento.jpg','Preto':'assets/soudal/trex-power-290-preto.jpg','Bege':'assets/soudal/trex-power-290-bege.jpg','Terracota':'assets/soudal/trex-power-290-terracota.jpg','Transparente':'assets/soudal/trex-power-290-transparente.jpg'}
d=json.loads(DATA.read_text(encoding='utf-8'))
items=[p for p in d.get('products',[]) if p.get('slug')==TARGET]
if not items: raise SystemExit('T-Rex Power não encontrado')
t=items[0]
t['price']=12.95
t['price_display']='12,95 €'
t['promo_price']=None
t['promo_enabled']=False
t['variants']=[{'name':c,'color':c,'label':'290ml / '+c,'price':12.95,'image':img,'asset_image':img} for c,img in IMAGES.items()]
t['asset_image']=IMAGES['Branco']
t['gallery_local']=list(IMAGES.values())
DATA.write_text(json.dumps({'source_checked':d.get('source_checked'),'source_note':d.get('source_note'),'products':[t]},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
c=sqlite3.connect(DB)
c.execute("DELETE FROM products WHERE brand='Soudal' AND slug<>?",(TARGET,))
c.execute("UPDATE products SET price=?,price_display=?,promo_price=NULL,promo_enabled=0,image=?,gallery_json=?,variants_json=?,stock=1,updated_at=CURRENT_TIMESTAMP WHERE slug=?",(12.95,'12,95 €',IMAGES['Branco'],json.dumps(list(IMAGES.values()),ensure_ascii=False),json.dumps(t['variants'],ensure_ascii=False),TARGET))
c.commit()
assert c.execute("SELECT COUNT(*) FROM products WHERE brand='Soudal'").fetchone()[0]==1
c.close()
print('OK')

from pathlib import Path
from urllib.request import Request,urlopen
import sqlite3,json
ROOT=Path(__file__).resolve().parents[1]
AS=ROOT/'assets/neuce'; DOC=ROOT/'docs/neuce'; AS.mkdir(parents=True,exist_ok=True); DOC.mkdir(parents=True,exist_ok=True)

def get(url,out):
    req=Request(url,headers={'User-Agent':'Mozilla/5.0'})
    with urlopen(req,timeout=30) as r: Path(out).write_bytes(r.read())

get('https://templodastintas.pt/cdn/shop/files/neucebel.png?v=1705605720&width=533',AS/'neucebel.png')
get('https://cdn-shopkit.com/usercontent/tintas-vital/media/images/square/37a3a6a-neucesoft.jpeg',AS/'neucesoft.jpeg')
get('https://www.saniluz.pt/cdn/shop/files/5602920000587.jpg?v=1733586586',AS/'neucematt.jpg')
get('https://www.neuce.com/files/ficha_tec/ft_03-03_vr8_pt.pdf',DOC/'neucebel-ficha-tecnica.pdf')
get('https://filedn.eu/lSlvke6ltvtSSvzVtcrnBbk/4669636861735465636e69636173/5602920000570.pdf',DOC/'neucematt-ficha-tecnica.pdf')
get('https://cdn-shopkit.com/usercontent/tintas-vital/media/files/5fba0a4-neucesoft-ficha-tecnica.pdf',DOC/'neucesoft-ficha-tecnica.pdf')

db=sqlite3.connect(ROOT/'data/catalog.db')
info={'NeuceBel':('Tinta Exterior','assets/neuce/neucebel.png',[('1L',''),('5L',''),('15L','')],'docs/neuce/neucebel-ficha-tecnica.pdf'),'NeuceMatt':('Tinta Interior','assets/neuce/neucematt.jpg',[('5L',''),('15L','')],'docs/neuce/neucematt-ficha-tecnica.pdf'),'NeuceSoft':('Tinta Interior','assets/neuce/neucesoft.jpeg',[('1L',''),('5L',''),('15L','')],'docs/neuce/neucesoft-ficha-tecnica.pdf')}
for name,(sub,img,vals,doc) in info.items():
    v=[{'name':x,'price':p,'stock':0} for x,p in vals]
    docs=json.dumps([{'title':'Ficha técnica '+name,'url':doc}],ensure_ascii=False)
    db.execute("UPDATE products SET family='Pinturas',category='Pinturas',subfamily=?,brand='NEUCE',supplier='NEUCE',price=0,price_display='Preço por variante',image=?,gallery_json=?,docs_json=?,doc=?,variants_json=? WHERE lower(name)=lower(?)",(sub,img,json.dumps([img]),docs,doc,json.dumps(v,ensure_ascii=False),name))
db.execute("INSERT OR IGNORE INTO brands(name) VALUES('NEUCE')")
db.commit();db.close()

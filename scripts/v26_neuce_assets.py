from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import quote
import sqlite3,json
ROOT=Path(__file__).resolve().parents[1]
AS=ROOT/'assets/neuce'; DOC=ROOT/'docs/neuce'; AS.mkdir(parents=True,exist_ok=True); DOC.mkdir(parents=True,exist_ok=True)

def get(url,out):
    req=Request(url,headers={'User-Agent':'Mozilla/5.0'})
    with urlopen(req,timeout=30) as r: Path(out).write_bytes(r.read())

def shopify_image(term,out):
    u='https://templodastintas.pt/search/suggest.json?q='+quote(term)+'&resources[type]=product&resources[limit]=10'
    req=Request(u,headers={'User-Agent':'Mozilla/5.0','Accept':'application/json'})
    data=json.loads(urlopen(req,timeout=30).read().decode('utf-8'))
    products=data.get('resources',{}).get('results',{}).get('products',[])
    hit=next((p for p in products if term.lower() in p.get('title','').lower()),products[0] if products else None)
    if not hit: raise RuntimeError('Produto não encontrado: '+term)
    img=hit.get('featured_image') or hit.get('image')
    if not img: raise RuntimeError('Imagem não encontrada: '+term)
    if img.startswith('//'): img='https:'+img
    elif img.startswith('/'): img='https://templodastintas.pt'+img
    get(img,out)

shopify_image('NeuceBel',AS/'neucebel.png')
shopify_image('NeuceMatt',AS/'neucematt.jpg')
shopify_image('NeuceSoft',AS/'neucesoft.jpeg')
get('https://www.neuce.com/files/ficha_tec/ft_03-03_vr8_pt.pdf',DOC/'neucebel-ficha-tecnica.pdf')

db=sqlite3.connect(ROOT/'data/catalog.db')
info={
 'NeuceBel':('Tinta Exterior','assets/neuce/neucebel.png',[('1L',''),('5L',''),('15L','')],'docs/neuce/neucebel-ficha-tecnica.pdf','https://www.neuce.com/p180-p-881-neucebel-pt_pt'),
 'NeuceMatt':('Tinta Interior','assets/neuce/neucematt.jpg',[('5L',''),('15L','')],'https://www.neuce.com/p180-p-1026-neucematt-pt_pt','https://www.neuce.com/p180-p-1026-neucematt-pt_pt'),
 'NeuceSoft':('Tinta Interior','assets/neuce/neucesoft.jpeg',[('1L',''),('5L',''),('15L','')],'https://www.neuce.com/p180-p-886-neucesoft-mo_pt','https://www.neuce.com/p180-p-886-neucesoft-mo_pt')}
for name,(sub,img,vals,doc,official) in info.items():
    v=[{'name':x,'price':p,'stock':0} for x,p in vals]
    docs=json.dumps([{'title':'Ficha técnica / produto '+name,'url':doc},{'title':'Produto oficial NEUCE','url':official}],ensure_ascii=False)
    db.execute("UPDATE products SET family='Pinturas',category='Pinturas',subfamily=?,brand='NEUCE',supplier='NEUCE',manufacturer_url=?,price=0,price_display='Preço por variante',image=?,gallery_json=?,docs_json=?,doc=?,variants_json=? WHERE lower(name)=lower(?)",(sub,official,img,json.dumps([img]),docs,doc,json.dumps(v,ensure_ascii=False),name))
db.execute("INSERT OR IGNORE INTO brands(name) VALUES('NEUCE')")
db.commit();db.close()

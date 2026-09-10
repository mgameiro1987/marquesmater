import json, re, sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/'data/catalog.db'
MAP=ROOT/'assets/products/image-map.json'
FORCED={
 'neucebel':'/assets/products/814c809e7143.png',
 'neucematt':'/assets/neucematt-real.png',
 'neucesoft':'/assets/neucesoft-real.jpg',
 'multineuce':'/assets/products/cd1ccfe26cad.jpg',
 'pistola-gravidade-h-827-copo-aluminio-17mm':'/assets/products/8207981dcd44.jpg',
 'pistola-lavagem-profissional-dg-10-ecb':'/assets/products/b7cef3ea20cf.jpg',
 'pistola-para-pintura-com-copo-baixo':'/assets/products/05fd97566286.jpg',
 'spray-alta-temperatura-antracite-600c-400-ml':'/assets/products/b494fe0e3397.png',
 'spray-alta-temperatura-prata-800c-400-ml':'/assets/products/bc8e68382f55.png',
 'spray-alta-temperatura-preto-800c-400-ml':'/assets/products/04e43eff1ce7.png',
 'mangueira-ar-comprimido-ahc-40-pu':'/assets/products/e5ccffd856be.jpg',
}
def main():
 con=sqlite3.connect(DB); cur=con.cursor(); n=0
 for slug,path in FORCED.items():
  if not (ROOT/path.lstrip('/')).exists():
   print('MISSING',slug,path); continue
  row=cur.execute('SELECT gallery_json FROM products WHERE slug=?',(slug,)).fetchone()
  if not row: print('NOT IN DB',slug); continue
  try: gallery=json.loads(row[0] or '[]')
  except: gallery=[]
  gallery=[path]+[x for x in gallery if x!=path and not (isinstance(x,str) and x.startswith(('http://','https://')))]
  cur.execute('UPDATE products SET image=?,gallery_json=?,updated_at=CURRENT_TIMESTAMP WHERE slug=?',(path,json.dumps(gallery,ensure_ascii=False),slug)); n+=1
 con.commit(); con.close()
 p=ROOT/'catalogo.html'
 if p.exists():
  text=p.read_text(encoding='utf-8')
  for slug,path in FORCED.items():
   # Replace image immediately associated with the product slug inside the catalogue data.
   text=re.sub(r'("slug":"'+re.escape(slug)+r'".*?"image":")[^"]+"',lambda m:m.group(1)+path+'"',text,count=1,flags=re.S)
  p.write_text(text,encoding='utf-8')
 print('Forced local product images:',n)
if __name__=='__main__': main()

from pathlib import Path
p=Path('server.py')
s=p.read_text(encoding='utf-8')
old=""" variants=p.get('variants',[]); docs=p.get('docs',[]); related=p.get('related',p.get('related_slugs',[]))
 tech=p.get('tech',[]);"""
new=""" variants=p.get('variants',[]); docs=p.get('docs',[]); related=p.get('related',p.get('related_slugs',[]))
 # Default rule for new paint articles: create the standard 1L/5L/15L sizes
 # and always show the cheapest available package as \"Desde X\".
 is_paint=str(p.get('family',p.get('category',''))).strip().lower()=='pinturas' or str(p.get('category',p.get('family',''))).strip().lower()=='pinturas'
 if is_paint:
  if not variants:
   variants=[{'name':'1L','price':'8,90 €','stock':0},{'name':'5L','price':'24,90 €','stock':0},{'name':'15L','price':'69,90 €','stock':0}]
  priced=[num(v.get('price')) for v in variants if isinstance(v,dict) and num(v.get('price'))>0]
  if priced and p.get('price_display') in (None,'','Preço sob consulta','Preço por variante'):
   p['price_display']='Desde '+price_text(min(priced))
  if priced and p.get('price') in (None,'',0):
   p['price']=min(priced)
 tech=p.get('tech',[]);"""
if old not in s:
 raise SystemExit('Trecho put_product não encontrado')
p.write_text(s.replace(old,new,1),encoding='utf-8')

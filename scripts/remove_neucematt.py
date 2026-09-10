import sqlite3, json, pathlib, re

# Remove NeuceMatt from the persistent catalogue and all related references.
c=sqlite3.connect('data/catalog.db')
c.execute("DELETE FROM products WHERE lower(slug)='neucematt' OR lower(name)='neucematt'")
rows=c.execute('SELECT slug, related_json FROM products').fetchall()
for slug, raw in rows:
    try: rel=json.loads(raw or '[]')
    except Exception: rel=[]
    new=[]
    for x in rel if isinstance(rel,list) else []:
        if str(x).strip().lower() not in ('neucematt',): new.append(x)
    if new != rel:
        c.execute('UPDATE products SET related_json=? WHERE slug=?',(json.dumps(new,ensure_ascii=False),slug))
c.commit()
assert c.execute("SELECT COUNT(*) FROM products WHERE lower(slug)='neucematt' OR lower(name)='neucematt'").fetchone()[0] == 0
c.close()

# Remove it from local_products if present.
p=pathlib.Path('data/site_data.json')
if p.exists():
    try:
        d=json.loads(p.read_text(encoding='utf-8'))
        lp=d.get('local_products',[])
        if isinstance(lp,list):
            d['local_products']=[x for x in lp if not (isinstance(x,dict) and (str(x.get('slug','')).lower()=='neucematt' or str(x.get('name','')).lower()=='neucematt'))]
        p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
    except Exception:
        pass

# Patch server.py so startup migrations can never restore NeuceMatt.
p=pathlib.Path('server.py')
s=p.read_text(encoding='utf-8')
orig=s
s=s.replace("{'slug':'neucematt','name':'NeuceMatt','family':'Pinturas','category':'Pinturas','subfamily':'Tinta Interior','brand':'Neuce','price_display':'Preço por variante','stock':0,'description':'Tinta plástica mate para interiores e exteriores, indicada para reboco liso, areado e vários outros suportes. Boa cobertura, rendimento e resistência à lavagem.','variants':[{'name':'5L','price':'','stock':0},{'name':'15L','price':'','stock':0}], 'docs':[{'title':'Informação oficial NEUCE','url':'https://www.neuce.com/p180-p-1026-neucematt-pt_pt'}]},\n",'')
s=s.replace("'related':['neucematt','neucesoft']", "'related':['neucesoft']")
s=s.replace("json.dumps(['neucematt','neucesoft'],ensure_ascii=False)", "json.dumps(['neucesoft'],ensure_ascii=False)")
s=s.replace("      'neucematt':(79.0,'Desde 79,00 €','https://www.marquesmater.pt/novo/wp-content/uploads/2024/03/Neucematt-600x638.png'),\n",'')
s=s.replace("        \"neucematt\":(69.9,\"69,90 €\",\"https://wsrv.nl/?url=https%3A%2F%2Fwww.saniluz.pt%2Fcdn%2Fshop%2Ffiles%2F5602920000587.jpg%3Fv%3D1733586586&w=600&h=600&fit=inside\"),\n",'')
s=s.replace("'neucematt': ('https://www.saniluz.pt/cdn/shop/files/5602920000587.jpg?v=1733586586','assets/neucematt-real.png'),\n",'')
# Guard against any pre-existing legacy row as an extra safety net.
marker='ensure_neuce_final()\nensure_v26_runtime_fixes()'
replacement="ensure_neuce_final()\n# NeuceMatt was intentionally removed; purge any legacy row left in an older DB.\ntry:\n    _c=db(); _c.execute(\"DELETE FROM products WHERE lower(slug)='neucematt' OR lower(name)='neucematt'\"); _c.execute(\"UPDATE products SET related_json=REPLACE(related_json, 'neucematt', '') WHERE related_json LIKE '%neucematt%'\"); _c.commit(); _c.close()\nexcept Exception as _e:\n    print('[NEUCEMATT CLEANUP]',_e)\nensure_v26_runtime_fixes()"
s=s.replace(marker,replacement)
if s==orig:
    raise SystemExit('No server.py changes detected')
p.write_text(s,encoding='utf-8')

import sqlite3, json
from pathlib import Path
p=Path('data/catalog.db')
c=sqlite3.connect(p)
prices={'1L':'8,90 €','5L':'24,90 €','15L':'69,90 €'}
for slug in ('neucebel','neucegold-ng','neucesoft'):
    row=c.execute('SELECT variants_json FROM products WHERE slug=?',(slug,)).fetchone()
    if not row:
        raise SystemExit(f'Produto não encontrado: {slug}')
    try: variants=json.loads(row[0] or '[]')
    except Exception: variants=[]
    for v in variants:
        name=str(v.get('name','')).strip().upper()
        if name in prices: v['price']=prices[name]
    c.execute('UPDATE products SET variants_json=?, price_display=? WHERE slug=?',
              (json.dumps(variants,ensure_ascii=False), 'Desde 8,90 €', slug))
c.commit()
for slug in ('neucebel','neucegold-ng','neucesoft'):
    print(slug,c.execute('SELECT price_display,variants_json FROM products WHERE slug=?',(slug,)).fetchone())
c.close()

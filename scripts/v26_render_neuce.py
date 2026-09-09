from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'server.py'
s=p.read_text(encoding='utf-8')
if 'ensure_v26_neuce_images' not in s:
    block='''\n\ndef ensure_v26_neuce_images():\n    c=db()\n    m={"NeuceBel":"https://templodastintas.pt/cdn/shop/files/neucebel.png?v=1705605720&width=533","NeuceMatt":"https://www.saniluz.pt/cdn/shop/files/5602920000587.jpg?v=1733586586","NeuceSoft":"https://cdn-shopkit.com/usercontent/tintas-vital/media/images/square/37a3a6a-neucesoft.jpeg"}\n    for name,img in m.items(): c.execute("UPDATE products SET brand='NEUCE',supplier='NEUCE',price_display='Preço por variante',image=?,gallery_json=? WHERE lower(name)=lower(?)",(img,json.dumps([img]),name))\n    c.commit(); c.close()\n\nensure_v26_neuce_images()\n'''
    s=s.replace('\nnormalize_product_taxonomy()\n','\nnormalize_product_taxonomy()\n'+block,1)
    p.write_text(s,encoding='utf-8')

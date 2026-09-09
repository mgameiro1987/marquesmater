from pathlib import Path
import hashlib,json,sqlite3

ROOT=Path(__file__).resolve().parents[1]

def main():
    h=hashlib.sha256(b'admin').hexdigest()
    (ROOT/'data/admin.json').write_text(json.dumps({'username':'admin','password_sha256':h},indent=2)+'\n',encoding='utf-8')
    p=ROOT/'nav.js'
    s=p.read_text(encoding='utf-8')
    s=s.replace(".filter(f=>f.name && f.show_menu !== false);",".filter(f=>f.name && f.show_menu !== false && f.show_top !== false);",1)
    p.write_text(s,encoding='utf-8')
    db=ROOT/'data/catalog.db'
    c=sqlite3.connect(db)
    variants=[('Branco','assets/soudal/trex-power-290-branco.jpg'),('Cinzento','assets/soudal/trex-power-290-cinzento.jpg'),('Preto','assets/soudal/trex-power-290-preto.jpg'),('Bege','assets/soudal/trex-power-290-bege.jpg'),('Terracota','assets/soudal/trex-power-290-terracota.jpg'),('Transparente','assets/soudal/trex-power-290-transparente.jpg')]
    v=[{'name':n,'color':n,'label':'290ml / '+n,'price':12.95,'image':img,'asset_image':img} for n,img in variants]
    c.execute("UPDATE products SET brand='Soudal',price=12.95,price_display='12,95 €',image=?,gallery_json=?,variants_json=? WHERE slug='soudal-t-rex-power-290ml'",(variants[0][1],json.dumps([x[1] for x in variants]),json.dumps(v,ensure_ascii=False)))
    ne={'NeuceBel':('Tinta Exterior','assets/neuce/neucebel.png',[('1L',''),('5L',''),('15L','')]),'NeuceMatt':('Tinta Interior','assets/neuce/neucematt.jpg',[('5L',''),('15L','')]),'NeuceSoft':('Tinta Interior','assets/neuce/neucesoft.jpeg',[('1L',''),('5L',''),('15L','')])}
    for name,(sub,img,vals) in ne.items():
        vv=[{'name':x,'price':pr,'stock':0} for x,pr in vals]
        c.execute("UPDATE products SET name=?,family='Pinturas',category='Pinturas',subfamily=?,brand='NEUCE',supplier='NEUCE',price=0,price_display='Preço por variante',image=?,gallery_json=?,variants_json=? WHERE lower(name)=lower(?)",(name,sub,img,json.dumps([img]),json.dumps(vv,ensure_ascii=False),name))
    c.execute("INSERT OR IGNORE INTO brands(name) VALUES('NEUCE')")
    c.commit(); c.close()
    p=ROOT/'data/site_data.json'
    d=json.loads(p.read_text(encoding='utf-8')) if p.exists() else {'settings':{},'families':[]}
    st=d.setdefault('settings',{})
    top={'Ferramentas','Pinturas','Máquinas','Colas e Selantes','Sprays e Aerossóis'}
    if not st.get('v26_top_visibility_initialized'):
        for f in d.get('families',[]):
            if isinstance(f,dict): f['show_top']=f.get('name') in top
        st['v26_top_visibility_initialized']=True
        p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
    sp=ROOT/'server.py'
    s=sp.read_text(encoding='utf-8')
    if 'ensure_v26_runtime_fixes' not in s:
        block='''\n\ndef ensure_v26_runtime_fixes():\n    c=db(); h=hashlib.sha256(b"admin").hexdigest(); c.execute("UPDATE admin_users SET password_sha256=? WHERE username='admin'",(h,)); c.execute("INSERT OR IGNORE INTO brands(name) VALUES('NEUCE')"); c.execute("UPDATE products SET image='assets/soudal/trex-power-290-branco.jpg',brand='Soudal',price=12.95,price_display='12,95 €' WHERE slug='soudal-t-rex-power-290ml'"); d=site_data(); top={"Ferramentas","Pinturas","Máquinas","Colas e Selantes","Sprays e Aerossóis"}; st=d.setdefault('settings',{})\n    if not st.get('v26_top_visibility_initialized'):\n        for f in d.get('families',[]):\n            if isinstance(f,dict): f['show_top']=f.get('name') in top\n        st['v26_top_visibility_initialized']=True; write_json(DATA/'site_data.json',d)\n    c.commit(); c.close()\n\nensure_v26_runtime_fixes()\n'''
        s=s.replace('\nnormalize_product_taxonomy()\n','\nnormalize_product_taxonomy()\n'+block,1)
    s=s.replace('MarquesMater V25 server:','MarquesMater V26 server:').replace("'version':'V25'","'version':'V26'")
    sp.write_text(s,encoding='utf-8')
    a=ROOT/'admin.html'; a.write_text(a.read_text(encoding='utf-8').replace('value="admin123"','value="admin"').replace('Back Office V25','Back Office V26'),encoding='utf-8')
    (ROOT/'VERSAO.txt').write_text('MarquesMater V26 — tópicos 1 a 5\n',encoding='utf-8')

if __name__=='__main__': main()

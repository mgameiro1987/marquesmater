import http.server, urllib.parse, urllib.request, json, re, html, time, os, secrets, hashlib, sqlite3
from http.server import ThreadingHTTPServer
from pathlib import Path
ROOT=Path(__file__).resolve().parent; DATA=ROOT/'data'; UPLOADS=ROOT/'uploads'; DB=DATA/'catalog.db'
DATA.mkdir(exist_ok=True); UPLOADS.mkdir(exist_ok=True); sessions={}
DEFAULT_FAMILIES=[
 {'name':'Ferramentas','subs':['Ferramentas a Bateria','Ferramentas Eléctricas','Ferramentas Pneumáticas','Medição'],'icon':'assets/family-icons/tools.png'},
 {'name':'Construção','subs':['Materiais de Construção','Colas e Fitas','Níveis','Silicone','Máquinas de cortar azulejo'],'icon':'assets/family-icons/construction.png'},
 {'name':'Jardim/Agricultura','subs':['Rega','Poda','Máquinas de Jardim','Pulverização'],'icon':'assets/family-icons/garden-vito.png'},
 {'name':'Pinturas','subs':['Tinta Interior','Tinta Exterior','Acessórios','Diluentes','Tintas em Spray'],'icon':'assets/family-icons/paint-neuce.png'},
 {'name':'Ferragens','subs':['Fixação','Diferenciais','Acessórios'],'icon':'assets/family-icons/hardware.png'}, {'name':'Iluminação','subs':['Interior','Exterior','LED'],'icon':'assets/family-icons/lighting.png'},
 {'name':'Casa','subs':['Limpeza','Organização'],'icon':'assets/family-icons/home.png'}, {'name':'Bricolage','subs':['Consumíveis','Acessórios'],'icon':'assets/family-icons/diy.png'},
 {'name':'Material Elétrico','subs':['Cabos','Tomadas','Acessórios'],'icon':'assets/family-icons/electric.png'}, {'name':'Protecção Individual','subs':['Luvas','Calçado','Vestuário'],'icon':'assets/family-icons/ppe.png'},
 {'name':'Máquinas','subs':['Máquinas com fio','Máquinas sem fio'],'icon':'assets/family-icons/machines-rida.png'},]

def read_json(p,d):
 try:return json.loads(p.read_text(encoding='utf-8'))
 except:return d
def write_json(p,o):
 p.parent.mkdir(exist_ok=True); tmp=p.with_suffix('.tmp'); tmp.write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf-8'); tmp.replace(p)
def family_icon_default(name):
 return {'Ferramentas':'assets/family-icons/tools.png','Construção':'assets/family-icons/construction.png','Jardim/Agricultura':'assets/family-icons/garden-vito.png','Pinturas':'assets/family-icons/paint-neuce.png','Ferragens':'assets/family-icons/hardware.png','Iluminação':'assets/family-icons/lighting.png','Casa':'assets/family-icons/home.png','Bricolage':'assets/family-icons/diy.png','Material Elétrico':'assets/family-icons/electric.png','Protecção Individual':'assets/family-icons/ppe.png','Máquinas':'assets/family-icons/machines-rida.png'}.get(name,'assets/family-icons/tools.png')
def site_data():
 d=read_json(DATA/'site_data.json',{}); d.setdefault('settings',{}); d.setdefault('families',DEFAULT_FAMILIES);
 d['families']=[(dict(x, icon=x.get('icon') or family_icon_default(x.get('name'))) if isinstance(x,dict) else {'name':x,'subs':[],'icon':family_icon_default(x)}) for x in d.get('families',DEFAULT_FAMILIES)]
 # V23: visibilidade independente por família, migrando os valores globais anteriores
 hp=d.get('settings',{}).get('homepage',{})
 for f in d['families']:
  if isinstance(f,dict):
   if 'show_menu' not in f: f['show_menu']=True
   if 'show_top' not in f: f['show_top']=bool(hp.get('show_families_top',False))
   if 'show_bottom' not in f: f['show_bottom']=bool(hp.get('show_families_bottom',True))
 d.setdefault('family_icon_library',[])
 d.setdefault('categories',[]); d.setdefault('payments',[]); d.setdefault('promotions',[]); d.setdefault('brands',[]); d.setdefault('local_products',[])
 s=d['settings']; s.setdefault('company',{'name':'MarquesMater - Materiais de Construção e Pinturas, Lda.','phone':'236 961 569','email':'loja@marquesmater.pt','address':'R. Sociedade Filarmónica, Ed. Estrada Nova, Louriçal','hours':'Segunda a sexta: 08:30–18:30','maps_url':'','whatsapp':''}); s.setdefault('homepage',{'show_families':True,'show_families_top':False,'show_families_bottom':True,'show_featured':True,'show_promotions':True})
 s['homepage'].setdefault('show_families_top', False); s['homepage'].setdefault('show_families_bottom', True); s.setdefault('seo',{'title':'MarquesMater — Materiais de Construção e Pinturas','description':'Materiais de construção, pinturas, ferramentas, jardim e muito mais.'}); s.setdefault('chat',{'enabled':True,'welcome':'Olá 👋 Como podemos ajudar?'}); s.setdefault('shipping',{'enabled':True,'free_above':'','continental':'','pickup':True,'carrier':'','notes':''}); s.setdefault('payment_settings',{'providers':[]})
 cpy=s['company']; cpy.setdefault('maps_embed_url',''); cpy.setdefault('postal','3105-165 Louriçal - Pombal'); cpy.setdefault('nif',''); cpy.setdefault('whatsapp','')
 legal=s.setdefault('legal',{})
 legal.setdefault('terms_title','Termos e Condições')
 legal.setdefault('terms_text','TERMOS E CONDIÇÕES\n\n1. Identificação\nA presente loja online é explorada pela empresa indicada na página Empresa/Contactos.\n\n2. Encomendas\nA encomenda é submetida pelo cliente através do checkout e fica sujeita à confirmação da disponibilidade e do pagamento.\n\n3. Preços e pagamento\nOs preços e meios de pagamento aplicáveis são apresentados no checkout.\n\n4. Entrega\nOs prazos e custos de entrega são apresentados antes da confirmação da encomenda.\n\n5. Cancelamento, devolução e garantia\nSão respeitados os direitos legais do consumidor aplicáveis às compras à distância e à falta de conformidade dos bens.\n\n6. Contactos\nUtilize os contactos publicados no site para questões sobre encomendas ou produtos.\n\nNOTA: texto modelo. Deve ser revisto pela empresa antes da entrada em produção.')
 legal.setdefault('privacy_title','Política de Privacidade')
 legal.setdefault('privacy_text','POLÍTICA DE PRIVACIDADE\n\n1. Responsável pelo tratamento\nO responsável pelo tratamento dos dados pessoais é a empresa identificada em Empresa/Contactos.\n\n2. Dados tratados\nPodem ser tratados nome, email, telefone, morada de entrega e outros dados necessários à gestão de encomendas e atendimento.\n\n3. Finalidades\nOs dados são utilizados para gerir contas e encomendas, pagamentos, entregas, apoio ao cliente e cumprimento de obrigações legais.\n\n4. Conservação\nOs dados são conservados durante os períodos necessários às finalidades e aos prazos legais aplicáveis.\n\n5. Direitos\nO titular pode exercer os direitos previstos no RGPD, incluindo acesso, retificação, apagamento, limitação, portabilidade e oposição, quando aplicável.\n\n6. Contacto\nPedidos relativos a dados pessoais podem ser enviados para o email da empresa indicado em Contactos.\n\nNOTA: texto modelo. Deve ser adaptado aos tratamentos e prestadores efetivamente utilizados.')
 legal.setdefault('cookies_title','Política de Cookies')
 legal.setdefault('cookies_text','POLÍTICA DE COOKIES\n\nO site pode utilizar cookies estritamente necessários ao funcionamento da loja, sessão, carrinho e preferências. Cookies opcionais de análise ou marketing só devem ser ativados quando exista base legal adequada e, quando necessário, consentimento do utilizador.\n\nOs tipos de cookies e prazos devem ser atualizados quando forem adicionados novos serviços.\n\nNOTA: texto modelo. Deve ser ajustado aos cookies efetivamente utilizados.')
 legal.setdefault('returns_title','Entregas, Trocas e Devoluções')
 legal.setdefault('returns_text','ENTREGAS, TROCAS E DEVOLUÇÕES\n\nAs condições de entrega, prazos e custos são apresentadas antes da conclusão da encomenda.\n\nNas compras à distância aplicam-se os direitos legais do consumidor, incluindo o direito de livre resolução quando legalmente aplicável, sem prejuízo das exceções previstas na lei.\n\nEm caso de produto não conforme, contacte a empresa para análise e aplicação dos direitos legais correspondentes.\n\nNOTA: texto modelo. Deve ser completado e revisto antes da entrada em produção.')
 legal.setdefault('complaints_title','Livro de Reclamações')
 legal.setdefault('complaints_url','https://www.livroreclamacoes.pt/INICIO/')
 legal.setdefault('complaints_text','Para apresentar uma reclamação, o consumidor pode utilizar os meios legalmente disponibilizados pela empresa, incluindo o Livro de Reclamações Eletrónico quando aplicável. Consulte os contactos da empresa para apoio.')
 return d
def db():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row
 c.executescript('''CREATE TABLE IF NOT EXISTS products(slug TEXT PRIMARY KEY,id TEXT,name TEXT NOT NULL,ref TEXT DEFAULT '',family TEXT DEFAULT '',category TEXT DEFAULT '',subfamily TEXT DEFAULT '',brand TEXT DEFAULT '',price_display TEXT DEFAULT '',price REAL DEFAULT 0,promo_price REAL,stock REAL DEFAULT 0,min_stock REAL DEFAULT 5,state TEXT DEFAULT 'active',featured INTEGER DEFAULT 0,description TEXT DEFAULT '',description_html TEXT DEFAULT '',tech TEXT DEFAULT '',image TEXT DEFAULT '',gallery_json TEXT DEFAULT '[]',permalink TEXT DEFAULT '',doc TEXT DEFAULT '',docs_json TEXT DEFAULT '[]',variants_json TEXT DEFAULT '[]',related_json TEXT DEFAULT '[]',created_at TEXT DEFAULT CURRENT_TIMESTAMP,updated_at TEXT DEFAULT CURRENT_TIMESTAMP); CREATE TABLE IF NOT EXISTS categories(name TEXT PRIMARY KEY,description TEXT DEFAULT '',subcategories_json TEXT DEFAULT '[]'); CREATE TABLE IF NOT EXISTS brands(name TEXT PRIMARY KEY); CREATE TABLE IF NOT EXISTS chats(id TEXT PRIMARY KEY,customer_name TEXT DEFAULT '',customer_email TEXT DEFAULT '',customer_phone TEXT DEFAULT '',page TEXT DEFAULT '',product_slug TEXT DEFAULT '',status TEXT DEFAULT 'waiting',assigned_to TEXT DEFAULT '',queue_position INTEGER DEFAULT 0,unread_count INTEGER DEFAULT 0,created_at TEXT DEFAULT CURRENT_TIMESTAMP,updated_at TEXT DEFAULT CURRENT_TIMESTAMP); CREATE TABLE IF NOT EXISTS messages(id INTEGER PRIMARY KEY AUTOINCREMENT,chat_id TEXT NOT NULL,sender TEXT NOT NULL,message TEXT NOT NULL,created_at TEXT DEFAULT CURRENT_TIMESTAMP); CREATE TABLE IF NOT EXISTS orders(id TEXT PRIMARY KEY,customer_name TEXT DEFAULT '',customer_email TEXT DEFAULT '',total REAL DEFAULT 0,status TEXT DEFAULT 'new',payment_status TEXT DEFAULT 'pending',items_json TEXT DEFAULT '[]',created_at TEXT DEFAULT CURRENT_TIMESTAMP); CREATE TABLE IF NOT EXISTS customers(email TEXT PRIMARY KEY,name TEXT DEFAULT '',phone TEXT DEFAULT '',orders_count INTEGER DEFAULT 0,created_at TEXT DEFAULT CURRENT_TIMESTAMP,updated_at TEXT DEFAULT CURRENT_TIMESTAMP);''')
 # migrate old dbs
 cols={r[1] for r in c.execute('PRAGMA table_info(products)')}
 chat_cols={r[1] for r in c.execute('PRAGMA table_info(chats)')}
 for col,typ in [('assigned_to',"TEXT DEFAULT ''"),('queue_position','INTEGER DEFAULT 0'),('unread_count','INTEGER DEFAULT 0')]:
  if col not in chat_cols:c.execute(f'ALTER TABLE chats ADD COLUMN {col} {typ}')
 c.execute("CREATE TABLE IF NOT EXISTS admin_users(username TEXT PRIMARY KEY,password_sha256 TEXT NOT NULL,role TEXT DEFAULT 'agent',display_name TEXT DEFAULT '',online INTEGER DEFAULT 0)")
 admin_count=c.execute("SELECT COUNT(*) FROM admin_users").fetchone()[0]
 if admin_count==0:
  base=read_json(DATA/'admin.json',{}); c.execute('INSERT OR IGNORE INTO admin_users(username,password_sha256,role,display_name,online) VALUES(?,?,?,?,0)',(base.get('username','admin'),base.get('password_sha256',''),'owner','Administrador'))
  c.execute('INSERT OR IGNORE INTO admin_users(username,password_sha256,role,display_name,online) VALUES(?,?,?,?,0)',('atendimento','240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9','agent','Atendimento'))

 for col,typ in [('gallery_json','TEXT DEFAULT \'[]\''),('related_json','TEXT DEFAULT \'[]\''),('seo_title','TEXT DEFAULT \'\''),('seo_description','TEXT DEFAULT \'\'')]:
  if col not in cols:c.execute(f'ALTER TABLE products ADD COLUMN {col} {typ}')
 for col,typ in [('ean',"TEXT DEFAULT ''"),('vat_rate','REAL DEFAULT 23'),('promo_enabled','INTEGER DEFAULT 0'),('supplier',"TEXT DEFAULT ''"),('manufacturer_url',"TEXT DEFAULT ''"),('allow_backorder','INTEGER DEFAULT 0')]:
  if col not in cols:c.execute(f'ALTER TABLE products ADD COLUMN {col} {typ}')
 return c
def num(v):
 try:
  if isinstance(v,(int,float)): return float(v)
  s=str(v).replace('€','').replace(' ','').strip()
  if ',' in s: s=s.replace('.','').replace(',','.')
  return float(s)
 except:return 0.0
def price_text(v):
 if v in (None,''):return ''
 if isinstance(v,(int,float)):return ('€ %.2f'%v).replace('.',',')
 return str(v)
def put_product(c,p):
 slug=str(p.get('slug') or p.get('id') or '').strip()
 if not slug:return
 price=num(p.get('price') if p.get('price') not in (None,'') else p.get('price_display','')); promo=p.get('promo_price',p.get('promo'))
 imgs=p.get('images') or []; gallery=p.get('gallery') or [x.get('src','') for x in imgs if isinstance(x,dict) and x.get('src')]
 img=str(p.get('image') or (gallery[0] if gallery else ''))
 if img and img not in gallery:gallery.insert(0,img)
 variants=p.get('variants',[]); docs=p.get('docs',[]); related=p.get('related',p.get('related_slugs',[]))
 # Default rule for new paint articles: create the standard 1L/5L/15L sizes
 # and always show the cheapest available package as "Desde X".
 is_paint=str(p.get('family',p.get('category',''))).strip().lower()=='pinturas' or str(p.get('category',p.get('family',''))).strip().lower()=='pinturas'
 if is_paint:
  if not variants:
   variants=[{'name':'1L','price':'8,90 €','stock':0},{'name':'5L','price':'24,90 €','stock':0},{'name':'15L','price':'69,90 €','stock':0}]
  priced=[num(v.get('price')) for v in variants if isinstance(v,dict) and num(v.get('price'))>0]
  if priced and p.get('price_display') in (None,'','Preço sob consulta','Preço por variante'):
   p['price_display']='Desde '+price_text(min(priced))
  if priced and p.get('price') in (None,'',0):
   p['price']=min(priced)
 tech=p.get('tech',[]); tech=json.dumps(tech,ensure_ascii=False) if isinstance(tech,(list,dict)) else str(tech or '')
 c.execute('''INSERT OR REPLACE INTO products(slug,id,name,ref,ean,family,category,subfamily,brand,price_display,price,promo_price,promo_enabled,vat_rate,stock,min_stock,state,featured,supplier,manufacturer_url,allow_backorder,description,description_html,tech,image,gallery_json,permalink,doc,docs_json,variants_json,related_json,seo_title,seo_description,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)''',(
    slug,str(p.get('id',slug)),str(p.get('name','')),str(p.get('ref',p.get('sku',''))),str(p.get('ean','')),str(p.get('family',p.get('category',''))),str(p.get('category',p.get('family',''))),str(p.get('subfamily','')),str(p.get('brand','')),price_text(p.get('price_display',price_text(price))),price,num(promo) if promo not in (None,'') else None,1 if p.get('promo_enabled') else 0,num(p.get('vat_rate',23)),num(p.get('stock',1 if p.get('is_in_stock',True) else 0)),num(p.get('minStock',p.get('min_stock',5))),str(p.get('state','active')),1 if p.get('featured') else 0,str(p.get('supplier',p.get('manufacturer',''))),str(p.get('manufacturer_url','')),1 if p.get('allow_backorder') else 0,str(p.get('description',p.get('desc',''))),str(p.get('description_html','')),tech,img,json.dumps(gallery,ensure_ascii=False),str(p.get('permalink','')),str(p.get('doc','')),json.dumps(docs,ensure_ascii=False),json.dumps(variants,ensure_ascii=False),json.dumps(related,ensure_ascii=False),str(p.get('seo_title','')),str(p.get('seo_description',''))))

def row_product(r):
 if not r:return None
 p=dict(r); p['sku']=p.get('ref',''); p['minStock']=p.get('min_stock',5); p['is_in_stock']=p.get('stock',0)>0 and p.get('state')!='inactive'
 for k,j in [('gallery','gallery_json'),('docs','docs_json'),('variants','variants_json'),('related','related_json')]:
  try:p[k]=json.loads(p.get(j) or '[]')
  except:p[k]=[]

 def official_image(x):
  return '/api/soudal-image?url='+urllib.parse.quote(x[12:],safe='') if isinstance(x,str) and x.startswith('soudal-page:') else x
 if isinstance(p.get('image'),str) and p['image'].startswith('soudal-page:'): p['image']=official_image(p['image'])
 p['gallery']=[official_image(x) for x in p.get('gallery',[])]
 for v in p.get('variants',[]):
  if isinstance(v,dict):
   if v.get('image'): v['image']=official_image(v['image'])
   elif v.get('page'): v['image']=official_image('soudal-page:'+str(v['page']))
 p['images']=[{'src':x} for x in p['gallery']]
 p.pop('gallery_json',None);p.pop('docs_json',None);p.pop('variants_json',None);p.pop('related_json',None);p.pop('min_stock',None)
 return p
def all_products(category='',sub='',search='',brand=''):
 c=db();sql='SELECT * FROM products WHERE 1=1';args=[]
 if category:sql+=' AND (family=? OR category=?)';args += [category,category]
 if sub:sql+=' AND subfamily=?';args.append(sub)
 if search:sql+=' AND (name LIKE ? OR slug LIKE ? OR ref LIKE ? OR brand LIKE ?)';q='%'+search+'%';args += [q,q,q,q]
 if brand:sql+=' AND brand=?';args.append(brand)
 rows=c.execute(sql+' ORDER BY featured DESC,name COLLATE NOCASE',args).fetchall();c.close();return [row_product(x) for x in rows]
def categories():
 c=db();rows=c.execute('SELECT * FROM categories ORDER BY rowid').fetchall();c.close();return [{'name':r['name'],'description':r['description'],'subcategories':json.loads(r['subcategories_json'] or '[]')} for r in rows]
def save_categories(items):
 c=db();c.execute('DELETE FROM categories')
 for x in items:c.execute('INSERT INTO categories VALUES(?,?,?)',(x.get('name',''),x.get('description',''),json.dumps(x.get('subcategories',[]),ensure_ascii=False)))
 c.commit();c.close()
def current_admin(h):
 cookie=h.headers.get('Cookie',''); sid=cookie.split('mm_admin=',1)[-1].split(';',1)[0] if 'mm_admin=' in cookie else ''; v=sessions.get(sid); return v.get('username','') if v and v.get('expires',0)>time.time() else ''

def auth(h):
 cookie=h.headers.get('Cookie',''); sid=cookie.split('mm_admin=',1)[-1].split(';',1)[0] if 'mm_admin=' in cookie else ''; v=sessions.get(sid); return bool(sid and v and v.get('expires',0)>time.time())
def body(h):n=int(h.headers.get('Content-Length','0'));return json.loads(h.rfile.read(n) or b'{}')
def seed_db():
 d=site_data(); c=db()
 if c.execute('SELECT COUNT(*) FROM products').fetchone()[0]==0:
  # Existing local products
  for p in d.get('local_products',[]):put_product(c,p)
  # RIDA: all 40 source products; brand RIDA; requested machine hierarchy
  for p in read_json(ROOT/'rida-products.json',[]):
   if isinstance(p,dict):
    p=dict(p); p.setdefault('slug',p.get('sku')); p['brand']='RIDA'; p['family']='Máquinas'; p['category']='Máquinas'; p['subfamily']='Máquinas sem fio' if ('sem fio' in str(p.get('name','')).lower() or 'bateria' in str(p.get('name','')).lower() or p.get('kit')) else 'Máquinas sem fio'; p['price_display']=p.get('price','Preço sob consulta'); p['description']=p.get('description') or p.get('desc',''); p['tech']=p.get('spec',''); put_product(c,p)
  # Paint examples, with configurable variants and official docs. Prices per size can be edited in BO.
  paints=[
   {'slug':'neucebel','name':'NeuceBel','family':'Pinturas','category':'Pinturas','subfamily':'Tinta Interior','brand':'Neuce','price_display':'Preço por variante','stock':0,'image':'assets/paint-placeholder.svg','description':'Tinta estireno-acrílica extra mate para interiores e exteriores, com boa cobertura, rendimento e resistência ao desenvolvimento de fungos e algas.','tech':['Densidade: 1,380 ± 0,030 (cor branca)','Teor de sólidos em peso: 53 ± 2 %','Viscosidade: 109 ± 3 Ku (25 ºC)','Cor: Branca e outras','Acabamento: Liso mate','Secagem superficial: ± 30 minutos','Repintura: 3–4 horas','Ponto de inflamação: Não inflamável','Resistência à esfrega húmida: Classe 1','Poder de cobertura: Classe 3'],'variants':[{'name':'1L','price':'','stock':0},{'name':'5L','price':'','stock':0},{'name':'15L','price':'','stock':0}], 'related':['neucesoft'], 'docs':[{'title':'Ficha técnica NEUCEBEL (PDF)','url':'https://www.neuce.com/files/ficha_tec/ft_03-03_vr8_pt.pdf'},{'title':'NeuceBel no site NEUCE','url':'https://www.neuce.com/p180-p-881-neucebel-pt_pt'}]},
      {'slug':'neucesoft','name':'NeuceSoft','family':'Pinturas','category':'Pinturas','subfamily':'Tinta Interior','brand':'Neuce','price_display':'Preço por variante','stock':0,'description':'Tinta plástica sedosa de alta qualidade para paredes interiores. Boa lacagem, opacidade e brancura, fácil aplicação e elevada resistência à esfrega húmida.','variants':[{'name':'1L','price':'','stock':0},{'name':'5L','price':'','stock':0},{'name':'15L','price':'','stock':0}], 'docs':[{'title':'NeuceSoft no site MarquesMater','url':'https://www.marquesmater.pt/novo/produto/neucesoft/'}]},
  ]
  for p in paints:put_product(c,p)
 # V3 migration: make the existing NeuceBel record presentable even when the
 # local SQLite database already existed from V2.
 nb=c.execute("SELECT slug FROM products WHERE slug='neucebel'").fetchone()
 if nb:
  c.execute("UPDATE products SET image=?, tech=?, related_json=?, description=? WHERE slug='neucebel'",(
   'assets/paint-placeholder.svg',
   json.dumps(['Densidade: 1,380 ± 0,030 (cor branca)','Teor de sólidos em peso: 53 ± 2 %','Viscosidade: 109 ± 3 Ku (25 ºC)','Cor: Branca e outras','Acabamento: Liso mate','Secagem superficial: ± 30 minutos','Repintura: 3–4 horas','Ponto de inflamação: Não inflamável','Resistência à esfrega húmida: Classe 1','Poder de cobertura: Classe 3'],ensure_ascii=False),
   json.dumps(['neucesoft'],ensure_ascii=False),
   'Tinta estireno-acrílica extra mate para interiores e exteriores, com boa cobertura, rendimento e resistência ao desenvolvimento de fungos e algas.'
  ))
 # categories
 if c.execute('SELECT COUNT(*) FROM categories').fetchone()[0]==0:
  fam=d.get('families') or DEFAULT_FAMILIES
  # Replace legacy RIDA family with proper Máquinas structure
  fam=[x for x in fam if (x.get('name') if isinstance(x,dict) else x)!='RIDA']
  if not any((x.get('name') if isinstance(x,dict) else x)=='Máquinas' for x in fam):fam.append({'name':'Máquinas','subs':['Máquinas com fio','Máquinas sem fio']})
  c.execute('DELETE FROM categories')
  for x in fam:
   if isinstance(x,str): x={'name':x,'subcategories':[]}
   c.execute('INSERT INTO categories VALUES(?,?,?)',(x.get('name',''),x.get('description',''),json.dumps(x.get('subcategories',x.get('subs',[])),ensure_ascii=False)))
  d['families']=fam; write_json(DATA/'site_data.json',d)
 if c.execute('SELECT COUNT(*) FROM brands').fetchone()[0]==0:
  brands=set(d.get('brands',[]));brands.add('RIDA');brands.add('Neuce')
  for b in brands:c.execute('INSERT OR IGNORE INTO brands VALUES(?)',(b,))
 c.commit();c.close()

def ensure_rida_pricing():
 c=db()
 prices={
  'RB2020':29.90,'RB2040':49.90,'RFC24':24.90,'RDC30':39.90,
  'RHD01075':69.90,'RHD01075-B22':129.90,'RCG07115':69.90,'RCG07115-B24':119.90,
  'RCG07125':74.90,'RCG07125-B24':124.90,'RCH072D6':119.90,'RCH072D6-B24':189.90,
  'RBL06650':79.90,'RBL06650-C22':139.90,'RBP01040':69.90,'RBP01040-C12':119.90,
  'RCC00190':99.90,'RCC00190-C14':159.90,'RCC08150':94.90,'RCC08150-C14':154.90,
  'RCJ08025':64.90,'RCJ08025-C22':114.90,'RCL1250H':44.90,'RCL1250H-C12':79.90,
  'RCO11125':69.90,'RCO11125-C12':119.90,'RCO13150':74.90,'RCO13150-C12':124.90,
  'RCR11022':89.90,'RCS03V016':119.90,'RCS03V016-C24':189.90,'RCS06006':129.90,
  'RCS06006-C12':199.90,'REP16245':59.90,'RGG11310':69.90,'RGT11280':99.90,
  'RGT11280-C12':159.90,'RHT09025':89.90,'RHT09025-C12':149.90,'RJR12000':69.90
 }
 for sku,price in prices.items():
  c.execute("UPDATE products SET price=?,price_display=? WHERE ref=? AND (price IS NULL OR price<=0 OR price_display='Preço sob consulta')",(price,price_text(price),sku))
 featured=['RHD01075-B22','RCG07125-B24','RCH072D6-B24','RCS06006-C12','RGT11280-C12','RBP01040-C12']
 c.execute("UPDATE products SET featured=0 WHERE brand='RIDA'")
 c.executemany("UPDATE products SET featured=1 WHERE ref=?",[(x,) for x in featured])
 c.commit();c.close()

seed_db()
ensure_rida_pricing()
def ensure_v18_catalog():
 d=site_data()
 fams=d.get('families') or DEFAULT_FAMILIES
 def fam(name,subs,icon):
  return {'name':name,'subs':subs,'icon':icon}
 wanted=[
  fam('Colas e Selantes',['Colas','Silicones','Selantes','Espumas PU','Adesivos de Montagem'],'assets/family-icons/construction.png'),
  fam('Sprays e Aerossóis',['Tintas em Spray','Lubrificantes','Desbloqueantes','Limpeza','Proteção','Outros Sprays Técnicos'],'assets/family-icons/paint-neuce.png'),
 ]
 for f in fams:
  if isinstance(f,dict) and f.get('name')=='Construção':
   f['subs']=[x for x in (f.get('subs') or []) if str(x).strip().lower()!='silicone']
 for w in wanted:
  existing=next((f for f in fams if isinstance(f,dict) and f.get('name')==w['name']),None)
  if existing:
   existing['subs']=w['subs']; existing['icon']=existing.get('icon') or w['icon']
  else:
   fams.append(w)
 d['families']=fams
 brands=set(d.get('brands') or []); brands.add('Soudal'); d['brands']=sorted(brands)
 write_json(DATA/'site_data.json',d)
 save_categories(fams)
 c=db()
 c.execute("DELETE FROM products WHERE slug IN ('soudal-fix-all-x-treme-power-express')")
 for b in brands: c.execute('INSERT OR IGNORE INTO brands(name) VALUES(?)',(b,))
 def up(p): put_product(c,p)
 t_rex_page='https://www.soudal.pt/pro/produtos/gama-t-rex/cola-veda-t-rex/t-rex-power'
 soudafoam_page='https://www.soudal.pt/pro/produtos/gama-construcao/espumas-pu/soudafoam-tt-manual'
 oil_page='https://www.soudal.pt/pro/produtos/produtos-de-limpeza-sprays-e-primarios/sprays-tecnicos/01l'
 soudabond_page='https://www.soudal.com/nl-nl/pro/producten/lijmen/lijmschuim/soudabond-easy-click-fix'
 rex_variants=[
  {'name':'Branco 290ml','price':'','stock':0,'ref':'145082','ean':'5411183160804'},
  {'name':'Cinzento 290ml','price':'','stock':0,'ref':'118693','ean':'5411183087576'},
  {'name':'Preto 290ml','price':'','stock':0,'ref':'121890','ean':'5411183101685'},
  {'name':'Terracota 290ml','price':'','stock':0,'ref':'122528','ean':'5411183105829'},
  {'name':'Bege 290ml','price':'','stock':0,'ref':'120896','ean':'5411183096615'},
  {'name':'Transparente 290ml','price':'','stock':0,'ref':'131060','ean':'5411183137578'},
 ]
 up({'slug':'soudal-t-rex-power-290ml','name':'Soudal T-Rex Power 290ml — Cola e Veda','ref':'145082 / 118693 / 121890 / 122528 / 120896 / 131060','family':'Colas e Selantes','category':'Colas e Selantes','subfamily':'Adesivos de Montagem','brand':'Soudal','price_display':'Preço sob consulta','stock':0,'min_stock':5,'state':'active','featured':False,
     'description':'Cola e veda Soudal T-Rex Power, selante-adesivo de polímero híbrido para colagem, selagem e fixação. Disponível em várias cores e formato de 290 ml.',
     'tech':['Tecnologia: polímero híbrido SMX','Formato: cartucho 290 ml','Interior e exterior','Elevada adesão inicial','Adequado para superfícies porosas e não porosas','Pode ser aplicado em superfícies húmidas e debaixo de água','Resistente à humidade, raios UV e produtos químicos','Flexível, inodoro e pintável','Temperatura de aplicação: +5 °C a +35 °C','Resistência à temperatura após cura: -40 °C a +90 °C'],
     'image':'soudal-page:'+t_rex_page,'gallery':['soudal-page:'+t_rex_page],'variants':rex_variants,
     'docs':[{'title':'Página oficial Soudal — T-Rex Power','url':t_rex_page},{'title':'Ficha técnica oficial Soudal — T-Rex Power','url':'https://www.soudal.pt/sites/default/files/soudal_api/document/900009480/TDS_Soudal_T-Rex_Power_9901099_Portuguese_Soudal_Portugal.pdf'}],
     'seo_title':'Soudal T-Rex Power 290ml | MarquesMater','seo_description':'Cola e veda Soudal T-Rex Power 290ml, em várias cores.'})
 up({'slug':'soudal-soudafoam-tt-manual-telhas-750ml-terracota','name':'Soudal Soudafoam TT Manual Telhas 750ml — Terracota','ref':'','family':'Colas e Selantes','category':'Colas e Selantes','subfamily':'Espumas PU','brand':'Soudal','price_display':'Preço sob consulta','stock':0,'min_stock':5,'state':'active','featured':False,
     'description':'Espuma PU adesiva monocomponente, pronta a usar, com alto poder adesivo e baixa expansão, especialmente desenvolvida para colagem e fixação de telhas.',
     'tech':['Base: poliuretano','Capacidade: 750 ml','Cor: terracota','Aplicação manual','Boa aderência a madeira, cimento, betão, tijolo, metal e painéis de isolamento','Exceto PE e PP','Resistente à geada e ao calor','Rendimento aproximado: 29 l de espuma por lata de 750 ml'],
     'image':'soudal-page:'+soudafoam_page,'gallery':['soudal-page:'+soudafoam_page],
     'docs':[{'title':'Página oficial Soudal — Soudafoam TT Manual','url':soudafoam_page},{'title':'Ficha técnica oficial Soudal — Soudafoam TT','url':'https://www.soudal.pt/sites/default/files/soudal_api/document/36392/F0036392_0001.pdf'}],
     'seo_title':'Soudal Soudafoam TT Manual 750ml Terracota | MarquesMater','seo_description':'Espuma PU adesiva Soudal Soudafoam TT Manual 750ml para telhas.'})
 up({'slug':'soudal-01l-oil-400ml','name':'Soudal 01L Oil 400ml — The Number 01 Lubrification','ref':'','family':'Sprays e Aerossóis','category':'Sprays e Aerossóis','subfamily':'Lubrificantes','brand':'Soudal','price_display':'Preço sob consulta','stock':0,'min_stock':5,'state':'active','featured':False,
     'description':'Spray técnico Soudal 01L com ação 4 em 1: liberta, limpa, lubrifica e protege.',
     'tech':['Capacidade: 400 ml','Lubrifica, protege, limpa e desbloqueia','Fórmula sem silicone','Resiste à ferrugem e corrosão','Reduz a humidade','Repele a água','Uso interior e exterior','Aerossol utilizável a 360°'],
     'image':'soudal-page:'+oil_page,'gallery':['soudal-page:'+oil_page],'variants':[{'name':'400ml','price':'','stock':0,'ref':''}],
     'docs':[{'title':'Página oficial Soudal — 01L','url':oil_page},{'title':'Ficha técnica oficial Soudal — 01L','url':'https://www.soudal.pt/sites/default/files/soudal_api/document/9901864/TDS_Soudal_01L_9901864_Portuguese_Soudal_Portugal.pdf'}],
     'seo_title':'Soudal 01L Oil 400ml | MarquesMater','seo_description':'Spray lubrificante multiusos Soudal 01L 400ml.'})
 up({'slug':'soudal-soudabond-easy-click-fix-750ml','name':'Soudal Soudabond Easy Click & Fix 750ml','ref':'121398','family':'Colas e Selantes','category':'Colas e Selantes','subfamily':'Espumas PU','brand':'Soudal','price_display':'Preço sob consulta','stock':0,'min_stock':5,'state':'active','featured':False,
     'description':'Cola espuma PU pronta a usar para montagem e colagem de placas de isolamento, gesso e outros materiais de construção.',
     'tech':['Referência: 121398','Capacidade: 750 ml','Base: poliuretano monocomponente','Pronta a usar','Aplicação precisa com sistema Click & Fix','Boa aderência à maioria dos materiais, exceto PE, PP e PTFE','Secagem rápida','Sem solventes'],
     'image':'soudal-page:'+soudabond_page,'gallery':['soudal-page:'+soudabond_page],
     'variants':[{'name':'750ml','price':'','stock':0,'ref':'121398'}],
     'docs':[{'title':'Página oficial Soudal — Soudabond Easy Click & Fix','url':soudabond_page},{'title':'Catálogo oficial Soudal — Gama Profissional','url':'https://www.soudal.pt/diy/file/42713/download?token=KO3Fenxa'}],
     'seo_title':'Soudal Soudabond Easy Click & Fix 750ml | MarquesMater','seo_description':'Cola espuma PU Soudal Soudabond Easy Click & Fix 750ml.'})
 c.commit();c.close()

ensure_v18_catalog()

def ensure_v19_catalog():
 c=db()
 def fam(name,subs,icon):
  d=site_data(); fs=d.get('families',[]); hit=next((x for x in fs if isinstance(x,dict) and x.get('name')==name),None)
  if hit: hit['subs']=subs; hit['icon']=icon
  else: fs.append({'name':name,'subs':subs,'icon':icon})
  d['families']=fs; write_json(DATA/'site_data.json',d)
 fam('Colas e Selantes',['Colas','Silicones','Selantes','Espumas PU','Adesivos de Montagem'],'assets/family-icons/construction.png')
 fam('Sprays e Aerossóis',['Tintas em Spray','Lubrificantes','Desbloqueantes','Limpeza','Proteção','Outros Sprays Técnicos'],'assets/family-icons/spray-aerosol.svg')
 d=site_data(); lib=d.get('family_icon_library',[])
 for nm,ic in [('Silicones','assets/family-icons/silicone.svg'),('Sprays e Aerossóis','assets/family-icons/spray-aerosol.svg')]:
  if not any(x.get('name')==nm and x.get('icon')==ic for x in lib): lib.append({'name':nm,'icon':ic,'source_url':'local'})
 d['family_icon_library']=lib; write_json(DATA/'site_data.json',d)
 def up(slug,name,ref,sub,page,desc,variants=None):
  v=variants or []
  put_product(c,{'slug':slug,'name':name,'ref':ref,'family':'Colas e Selantes','category':'Colas e Selantes','subfamily':sub,'brand':'Soudal','price_display':'PVP Soudal por confirmar','stock':0,'min_stock':5,'state':'active','featured':False,'description':desc,'image':'soudal-page:'+page,'gallery':['soudal-page:'+page],'variants':v,'docs':[{'title':'Página oficial Soudal','url':page}]})
 up('soudal-t-rex-x-treme-express-280ml','Soudal T-Rex X-Treme Express 280ml — Branco','', 'Adesivos de Montagem','https://www.soudal.pt/diy/t-rex','Cola de montagem de polímero híbrido com aderência inicial extrema.')
 up('soudal-t-rex-turbo-290ml','Soudal T-Rex Turbo 290ml — Branco','145079','Adesivos de Montagem','https://www.soudal.pt/diy/produtos/gama-t-rex/cola-veda-t-rex/t-rex-turbo','Selante adesivo de polímero híbrido de fixação super rápida.',[{'name':'Branco 290ml','price':'','stock':0,'ref':'145079'},{'name':'Branco 125ml','price':'','stock':0,'ref':'131074'}])
 up('soudal-t-rex-flex','Soudal T-Rex Flex — Branco e Transparente','9901420 / 9901579','Selantes','https://www.soudal.pt/diy/produtos/gama-t-rex/cola-veda-t-rex/t-rex-flex','Selante adesivo de polímero híbrido, extremamente flexível e resistente aos fungos.',[{'name':'Branco 290ml','price':'','stock':0,'page':'https://www.soudal.pt/diy/produtos/gama-t-rex/cola-veda-t-rex/t-rex-flex'},{'name':'Transparente Vidro 290ml','price':'','stock':0,'page':'https://www.soudal.pt/pro/produtos/gama-t-rex/cola-veda-t-rex/t-rex-flex-transparente'}])
 up('soudal-pega-tudo','Soudal Pega Tudo — Branco, Cinzento, Castanho e Cristal','','Adesivos de Montagem','https://www.soudal.pt/diy/produtos/cola-veda/cola-veda-ms/pega-tudo','Cola e veda MS de uso geral.',[{'name':'Branco','price':'','stock':0},{'name':'Cinzento','price':'','stock':0},{'name':'Castanho','price':'','stock':0},{'name':'Cristal','price':'','stock':0}])
 up('soudal-soudaflex-40fc','Soudal Soudaflex 40FC — Preto, Cinzento, Terracota e Branco','','Selantes','https://www.soudal.pt/diy/produtos/colas/colas-de-montagem-e-para-construcao/soudaflex-40fc','Selante adesivo de poliuretano para construção e juntas.',[{'name':'Preto','price':'','stock':0},{'name':'Cinzento','price':'','stock':0},{'name':'Terracota','price':'','stock':0},{'name':'Branco','price':'','stock':0}])
 up('soudal-selante-fendas','Soudal Selante Fendas — Branco','','Selantes','https://www.soudal.pt/diy/faq/3-como-selecionar-o-selante-adequado','Selante acrílico plasto-elástico para fissuras em betão e estuque.',[{'name':'Branco 290ml','price':'','stock':0}])
 up('soudal-selante-fendas-granulado','Soudal Selante Fendas Granulado — Branco','','Selantes','https://www.soudal.pt/diy/faq/3-como-selecionar-o-selante-adequado','Selante acrílico plasto-elástico com estrutura granulada para fissuras.',[{'name':'Branco 290ml','price':'','stock':0}])
 c.commit(); c.close()
ensure_v19_catalog()

def ensure_soudal_only_trex():
    """Remove legacy Soudal products from persistent SQLite data, keeping only T-Rex Power 290ml."""
    c = db()
    c.execute("DELETE FROM products WHERE brand='Soudal' AND slug <> 'soudal-t-rex-power-290ml'")
    c.execute("DELETE FROM brands WHERE name='Soudal'")
    if c.execute("SELECT 1 FROM products WHERE brand='Soudal' LIMIT 1").fetchone():
        c.execute("INSERT OR IGNORE INTO brands(name) VALUES('Soudal')")
    c.commit()
    c.close()

ensure_soudal_only_trex()

def normalize_product_taxonomy():
 c=db(); d=site_data(); mapping={f.get('name'): (f.get('subs') or []) for f in d.get('families',[]) if isinstance(f,dict)}
 for family,subs in mapping.items():
  if subs: c.execute("UPDATE products SET subfamily=? WHERE family=? AND (subfamily IS NULL OR TRIM(subfamily)='')",(subs[0],family))
 c.commit(); c.close()
normalize_product_taxonomy()







def ensure_v26_runtime_fixes():
    c=db(); h=hashlib.sha256(b"admin").hexdigest(); c.execute("UPDATE admin_users SET password_sha256=? WHERE username='admin'",(h,)); c.execute("INSERT OR IGNORE INTO brands(name) VALUES('NEUCE')"); c.execute("UPDATE products SET image='assets/soudal/trex-power-290-branco.jpg',brand='Soudal',price=12.95,price_display='12,95 €' WHERE slug='soudal-t-rex-power-290ml'"); d=site_data(); top={"Ferramentas","Pinturas","Máquinas","Colas e Selantes","Sprays e Aerossóis"}; st=d.setdefault('settings',{})
    if not st.get('v26_top_visibility_initialized'):
        for f in d.get('families',[]):
            if isinstance(f,dict): f['show_top']=f.get('name') in top
        st['v26_top_visibility_initialized']=True; write_json(DATA/'site_data.json',d)
    c.commit(); c.close()


# NeuceMatt was intentionally removed; purge any legacy row left in an older DB.
try:
    _c=db(); _c.execute("DELETE FROM products WHERE lower(slug)='neucematt' OR lower(name)='neucematt'"); _c.execute("UPDATE products SET related_json=REPLACE(related_json, 'neucematt', '') WHERE related_json LIKE '%neucematt%'"); _c.commit(); _c.close()
except Exception as _e:
    print('[NEUCEMATT CLEANUP]',_e)

# MM-NEUCE-FINAL-SERVER
def ensure_neuce_final():
    c=db(); vals={"neucebel":(89.9,"89,90 €","https://wsrv.nl/?url=https%3A%2F%2Ftemplodastintas.pt%2Fcdn%2Fshop%2Ffiles%2Fneucebel.png%3Fv%3D1705605720%26width%3D533&w=600&h=600&fit=inside"),"neucematt":(69.9,"69,90 €","https://wsrv.nl/?url=https%3A%2F%2Fwww.saniluz.pt%2Fcdn%2Fshop%2Ffiles%2F5602920000587.jpg%3Fv%3D1733586586&w=600&h=600&fit=inside"),"neucesoft":(129.9,"129,90 €","https://wsrv.nl/?url=https%3A%2F%2Fcdn-shopkit.com%2Fusercontent%2Ftintas-vital%2Fmedia%2Fimages%2Fsquare%2F37a3a6a-neucesoft.jpeg&w=600&h=600&fit=inside")};
    for slug,(price,display,image) in vals.items(): c.execute("UPDATE products SET price=?,price_display=?,image=?,updated_at=CURRENT_TIMESTAMP WHERE slug=?",(price,display,image,slug))
    c.execute("INSERT OR IGNORE INTO brands(name) VALUES(?)",("NEUCE",)); c.commit(); c.close()

ensure_neuce_final()
ensure_v26_runtime_fixes()
_SOUDAL_CACHE={}
def fetch_soudal_image(page_url):
    """Fetch the main image from an official Soudal product page."""
    if not page_url or not page_url.startswith(('https://www.soudal.pt/','https://www.soudal.com/','https://www.soudal.co.uk/')):
        return None
    if page_url in _SOUDAL_CACHE:
        return _SOUDAL_CACHE[page_url]
    try:
        req=urllib.request.Request(page_url,headers={
            'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/138 Safari/537.36',
            'Accept':'text/html,application/xhtml+xml,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language':'pt-PT,pt;q=0.9,en;q=0.8'
        })
        with urllib.request.urlopen(req,timeout=20) as r:
            raw=r.read(1500000).decode('utf-8','ignore')
        patterns=[
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
            r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']twitter:image["\']'
        ]
        m=None
        for pat in patterns:
            m=re.search(pat,raw,re.I)
            if m: break
        if not m:
            m=re.search(r'["\']image["\']\s*:\s*["\']([^"\']+)',raw,re.I)
        if not m:
            return None
        image=html.unescape(m.group(1)).strip()
        if image.startswith('//'): image='https:'+image
        elif image.startswith('/'): image=urllib.parse.urljoin(page_url,image)
        if not image.startswith(('https://www.soudal.pt/','https://www.soudal.com/','https://www.soudal.co.uk/')):
            return None
        _SOUDAL_CACHE[page_url]=image
        return image
    except Exception as e:
        print('[SOUDAL IMAGE]',e)
        return None

class Handler(http.server.SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT),**kw)
 def log_message(self,f,*a):print('[SITE]',f%a)
 def send_json(self,o,status=200):
  raw=json.dumps(o,ensure_ascii=False).encode();self.send_response(status);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
 def do_GET(self):
  u=urllib.parse.urlsplit(self.path);path=u.path;q=urllib.parse.parse_qs(u.query)
  if path=='/api/health':self.send_json({'ok':True,'version':'V26','database':'sqlite','architecture':'backoffice-commerce-chat'});return
  if path=='/admin':self.send_response(302);self.send_header('Location','/admin.html');self.end_headers();return
  if path=='/api/site':
   d=site_data();c=db();brands=[x['name'] for x in c.execute('SELECT name FROM brands ORDER BY name').fetchall()];c.close(); public_settings=json.loads(json.dumps(d.get('settings',{}))); ps=public_settings.get('payment_settings',{}); ps['providers']=[{k:v for k,v in x.items() if k not in ('api_key','token','secret')} for x in ps.get('providers',[])]; public_settings['payment_settings']=ps; self.send_json({'settings':public_settings,'families':d.get('families',DEFAULT_FAMILIES),'family_icon_library':d.get('family_icon_library',[]),'categories':categories(),'payments':d.get('payments',[]),'promotions':d.get('promotions',[]),'brands':brands});return
  if path=='/api/admin/me':
   ok=auth(self);self.send_json({'ok':ok,'username':current_admin(self)} if ok else {'ok':False},200 if ok else 401);return
  if path=='/api/admin/state':
   if not auth(self):self.send_json({'error':'unauthorized'},401);return
   d=site_data();c=db();brands=[x['name'] for x in c.execute('SELECT name FROM brands ORDER BY name').fetchall()];c.close();self.send_json({'settings':d.get('settings',{}),'families':d.get('families',DEFAULT_FAMILIES),'family_icon_library':d.get('family_icon_library',[]),'categories':categories(),'payments':d.get('payments',[]),'promotions':d.get('promotions',[]),'brands':brands,'products':all_products()});return
  if path=='/api/admin/dashboard':
   if not auth(self):self.send_json({'error':'unauthorized'},401);return
   ps=all_products();c=db();now=time.strftime('%Y-%m-%d');period=q.get('period',['today'])[0]
   if period=='month': start=now[:7]+'-01'
   elif period=='year': start=now[:4]+'-01-01'
   elif period=='7days': start=time.strftime('%Y-%m-%d',time.localtime(time.time()-6*86400))
   elif period=='yesterday': start=time.strftime('%Y-%m-%d',time.localtime(time.time()-86400))
   else: start=now
   rows=c.execute("SELECT * FROM orders WHERE substr(created_at,1,10)>=? ORDER BY created_at DESC",(start,)).fetchall(); allrows=c.execute("SELECT * FROM orders ORDER BY created_at DESC").fetchall()
   ch=c.execute("SELECT COUNT(*) FROM chats WHERE status IN ('waiting','open')").fetchone()[0]; customers=c.execute('SELECT COUNT(*) FROM customers').fetchone()[0]
   revenue=sum(float(r['total'] or 0) for r in rows); counts={k:0 for k in ['new','processing','triage','shipped','delivered','cancelled']}; aliases={'preparacao':'processing','em processamento':'processing','triagem':'triage','enviado':'shipped','enviada':'shipped','entregue':'delivered','cancelada':'cancelled'}
   for r in rows:
    st=str(r['status'] or 'new').lower(); counts[aliases.get(st,st) if aliases.get(st,st) in counts else 'new']+=1
   recent=[]
   for r in rows[:10]:
    x=dict(r)
    try:x['items']=json.loads(x.get('items_json') or '[]')
    except:x['items']=[]
    recent.append(x)
   product_sales={}
   for r in rows:
    try:items=json.loads(r['items_json'] or '[]')
    except:items=[]
    for it in items if isinstance(items,list) else []:
     if not isinstance(it,dict):continue
     name=str(it.get('name') or it.get('product_name') or it.get('sku') or 'Produto'); qty=float(it.get('qty',it.get('quantity',1)) or 1); val=float(it.get('total',it.get('price',0)) or 0)*qty; z=product_sales.setdefault(name,{'name':name,'qty':0,'value':0}); z['qty']+=qty; z['value']+=val
   top=sorted(product_sales.values(),key=lambda x:x['value'],reverse=True)[:5]
   daily=[]
   for i in range(7):
    day=time.strftime('%Y-%m-%d',time.localtime(time.time()-(6-i)*86400)); val=sum(float(r['total'] or 0) for r in allrows if str(r['created_at'])[:10]==day); daily.append({'date':day,'value':val})
   c.close();self.send_json({'period':period,'products':{'total':len(ps)},'paintings':sum(1 for p in ps if p.get('family')=='Pinturas'),'rida':sum(1 for p in ps if p.get('brand')=='RIDA'),'low_stock':sum(1 for p in ps if float(p.get('stock',0))<=float(p.get('minStock',5))),'open_chats':ch,'orders':len(allrows),'customers':customers,'revenue':revenue,'period_orders':len(rows),'status_counts':counts,'recent_orders':recent,'top_products':top,'daily':daily});return
  if path=='/api/admin/products':
   if not auth(self):self.send_json({'error':'unauthorized'},401);return
   self.send_json(all_products(q.get('category',[''])[0],q.get('sub',[''])[0],q.get('search',[''])[0],q.get('brand',[''])[0]));return
  if path=='/api/products':
   self.send_json(all_products(q.get('category',[''])[0],q.get('sub',[''])[0],q.get('search',[''])[0],q.get('brand',[''])[0]));return
  if path.startswith('/api/product/slug/'):
   slug=urllib.parse.unquote(path.split('/api/product/slug/',1)[1]).strip('/');c=db();r=c.execute('SELECT * FROM products WHERE slug=?',(slug,)).fetchone();c.close();self.send_json(row_product(r) if r else {'error':'product_unavailable'},200 if r else 404);return
  if path=='/api/soudal-image':
   raw_url=q.get('url',[''])[0]
   page_url=raw_url[12:] if raw_url.startswith('soudal-page:') else raw_url
   image_url=fetch_soudal_image(page_url)
   if not image_url:
    self.send_json({'error':'official_image_unavailable'},502);return
   try:
    req=urllib.request.Request(image_url,headers={'User-Agent':'Mozilla/5.0 (compatible; MarquesMater/1.0; +https://marquesmater.pt)'})
    with urllib.request.urlopen(req,timeout=15) as r:
     data=r.read()
     ctype=r.headers.get('Content-Type','image/jpeg')
    self.send_response(200);self.send_header('Content-Type',ctype);self.send_header('Cache-Control','public, max-age=86400');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
   except Exception as e:
    print('[SOUDAL IMAGE DOWNLOAD]',e);self.send_json({'error':'official_image_download_failed'},502)
   return
  if path=='/api/chat/messages':
   sid=q.get('session_id',[''])[0]; c=db(); rows=c.execute('SELECT sender,message,created_at FROM messages WHERE chat_id=? ORDER BY id',(sid,)).fetchall(); c.close(); self.send_json({'messages':[dict(x) for x in rows]}); return
  if path=='/api/admin/chats':
   if not auth(self):self.send_json({'error':'unauthorized'},401);return
   c=db(); rows=c.execute("SELECT * FROM chats ORDER BY CASE status WHEN 'waiting' THEN 0 WHEN 'open' THEN 1 ELSE 2 END, updated_at DESC").fetchall(); out=[]
   for r in rows:
    x=dict(r); lm=c.execute('SELECT message FROM messages WHERE chat_id=? ORDER BY id DESC LIMIT 1',(r['id'],)).fetchone(); x['last_message']=lm[0] if lm else ''; out.append(x)
   c.close(); self.send_json(out); return
  if path=='/api/admin/agents':
   if not auth(self):self.send_json({'error':'unauthorized'},401);return
   c=db();rows=c.execute('SELECT username,role,display_name,online FROM admin_users ORDER BY role DESC,display_name').fetchall();c.close();self.send_json([dict(x) for x in rows]);return
  if path=='/api/admin/chat/messages':
   if not auth(self):self.send_json({'error':'unauthorized'},401);return
   sid=q.get('session_id',[''])[0];c=db();rows=c.execute('SELECT sender,message,created_at FROM messages WHERE chat_id=? ORDER BY id',(sid,)).fetchall();c.close();self.send_json({'messages':[dict(x) for x in rows]});return
  if path=='/api/admin/orders':
   if not auth(self):self.send_json({'error':'unauthorized'},401);return
   c=db();rows=c.execute('SELECT * FROM orders ORDER BY created_at DESC').fetchall();c.close();self.send_json([dict(x) for x in rows]);return
  if path=='/api/admin/customers':
   if not auth(self):self.send_json({'error':'unauthorized'},401);return
   c=db();rows=c.execute('SELECT * FROM customers ORDER BY updated_at DESC').fetchall();c.close();self.send_json([dict(x) for x in rows]);return
  return super().do_GET()
 def do_POST(self):
  path=urllib.parse.urlsplit(self.path).path
  if path=='/api/admin/login':
   try:
    b=body(self); u=str(b.get('username','')); pw=hashlib.sha256(str(b.get('password','')).encode()).hexdigest(); c=db(); a=c.execute('SELECT username,role,display_name FROM admin_users WHERE username=? AND password_sha256=?',(u,pw)).fetchone(); c.close(); ok=bool(a)
   except:ok=False; a=None
   if not ok:self.send_json({'ok':False,'error':'Credenciais inválidas'},401);return
   sid=secrets.token_urlsafe(32);sessions[sid]={'username':a['username'],'role':a['role'],'expires':time.time()+8*3600}; c=db(); c.execute('UPDATE admin_users SET online=1 WHERE username=?',(a['username'],)); c.commit(); c.close(); self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Set-Cookie',f'mm_admin={sid}; Path=/; HttpOnly; SameSite=Lax');self.end_headers();self.wfile.write(json.dumps({'ok':True,'username':a['username'],'role':a['role']}).encode());return
  if path=='/api/admin/logout':
   u=current_admin(self); c=db(); c.execute('UPDATE admin_users SET online=0 WHERE username=?',(u,)); c.commit(); c.close(); self.send_response(200);self.send_header('Set-Cookie','mm_admin=; Path=/; Max-Age=0');self.end_headers();return
  if path=='/api/chat/session':
   b=body(self);sid=str(b.get('session_id') or secrets.token_urlsafe(12));c=db(); exists=c.execute('SELECT 1 FROM chats WHERE id=?',(sid,)).fetchone()
   if not exists:
    pos=c.execute("SELECT COALESCE(MAX(queue_position),0)+1 FROM chats WHERE status='waiting'").fetchone()[0]; c.execute('INSERT INTO chats(id,customer_name,customer_email,customer_phone,page,product_slug,status,queue_position,unread_count) VALUES(?,?,?,?,?,?,?,?,?)',(sid,str(b.get('name','')),str(b.get('email','')),str(b.get('phone','')),str(b.get('page','')),str(b.get('product','')),'waiting',pos,0))
    c.execute('INSERT INTO messages(chat_id,sender,message) VALUES(?,?,?)',(sid,'system',site_data()['settings'].get('chat',{}).get('welcome','Olá 👋 Como podemos ajudar?')))
   else:
    c.execute("UPDATE chats SET customer_name=COALESCE(NULLIF(?,''),customer_name),customer_email=COALESCE(NULLIF(?,''),customer_email),customer_phone=COALESCE(NULLIF(?,''),customer_phone),page=COALESCE(NULLIF(?,''),page),product_slug=COALESCE(NULLIF(?,''),product_slug),updated_at=CURRENT_TIMESTAMP WHERE id=?",(str(b.get('name','')),str(b.get('email','')),str(b.get('phone','')),str(b.get('page','')),str(b.get('product','')),sid))
   c.commit();rows=c.execute('SELECT sender,message,created_at FROM messages WHERE chat_id=? ORDER BY id',(sid,)).fetchall();c.close();self.send_json({'ok':True,'session_id':sid,'messages':[dict(x) for x in rows]});return
  if path=='/api/chat/message':
   b=body(self);sid=str(b.get('session_id') or secrets.token_urlsafe(12));msg=str(b.get('message','')).strip()
   if not msg:self.send_json({'error':'mensagem vazia'},400);return
   c=db();
   if not c.execute('SELECT 1 FROM chats WHERE id=?',(sid,)).fetchone():c.execute('INSERT INTO chats(id,page,product_slug) VALUES(?,?,?)',(sid,str(b.get('page','')),str(b.get('product',''))))
   c.execute('INSERT INTO messages(chat_id,sender,message) VALUES(?,?,?)',(sid,'customer',msg));c.execute("UPDATE chats SET updated_at=CURRENT_TIMESTAMP,status=CASE WHEN status='closed' OR assigned_to='' THEN 'waiting' ELSE status END,assigned_to=CASE WHEN status='closed' THEN '' ELSE assigned_to END,unread_count=unread_count+1,page=COALESCE(NULLIF(?,''),page),product_slug=COALESCE(NULLIF(?,''),product_slug) WHERE id=?",(str(b.get('page','')),str(b.get('product','')),sid));c.commit();c.close();self.send_json({'ok':True,'session_id':sid});return
  if not auth(self):self.send_json({'error':'unauthorized'},401);return
  if path=='/api/admin/chat/reply':
   b=body(self);sid=str(b.get('session_id',''));msg=str(b.get('message','')).strip();
   if not sid or not msg:self.send_json({'error':'dados em falta'},400);return
   c=db();u=current_admin(self); c.execute('INSERT INTO messages(chat_id,sender,message) VALUES(?,?,?)',(sid,'admin',msg));c.execute("UPDATE chats SET updated_at=CURRENT_TIMESTAMP,status='open',assigned_to=CASE WHEN assigned_to='' THEN ? ELSE assigned_to END,unread_count=0 WHERE id=?",(u,sid));c.commit();c.close();self.send_json({'ok':True});return
  if path=='/api/admin/chat/claim':
   b=body(self);sid=str(b.get('session_id',''));u=current_admin(self);
   if not u:self.send_json({'error':'unauthorized'},401);return
   c=db();r=c.execute('SELECT assigned_to,status FROM chats WHERE id=?',(sid,)).fetchone();
   if not r:self.send_json({'error':'Conversa não encontrada'},404);c.close();return
   if r['assigned_to'] and r['assigned_to']!=u:self.send_json({'error':'Esta conversa já está atribuída a outro administrador'},409);c.close();return
   c.execute("UPDATE chats SET assigned_to=?,status='open',queue_position=0,updated_at=CURRENT_TIMESTAMP WHERE id=?",(u,sid));c.commit();c.close();self.send_json({'ok':True,'assigned_to':u});return
  if path=='/api/admin/chat/release':
   b=body(self);sid=str(b.get('session_id',''));u=current_admin(self);c=db();r=c.execute('SELECT assigned_to FROM chats WHERE id=?',(sid,)).fetchone();
   if not r or (r['assigned_to'] and r['assigned_to']!=u):self.send_json({'error':'Sem permissão'},403);c.close();return
   pos=c.execute("SELECT COALESCE(MAX(queue_position),0)+1 FROM chats WHERE status='waiting'").fetchone()[0];c.execute("UPDATE chats SET assigned_to='',status='waiting',queue_position=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",(pos,sid));c.commit();c.close();self.send_json({'ok':True});return
  if path=='/api/admin/chat/status':
   b=body(self);c=db();status=str(b.get('status','closed')); c.execute("UPDATE chats SET status=?,assigned_to=CASE WHEN ?='closed' THEN '' ELSE assigned_to END,updated_at=CURRENT_TIMESTAMP WHERE id=?",(status,status,str(b.get('session_id',''))));c.commit();c.close();self.send_json({'ok':True});return
  if path=='/api/admin/settings':b=body(self);d=site_data();d.setdefault('settings',{}).update(b);write_json(DATA/'site_data.json',d);self.send_json({'ok':True,'settings':d['settings']});return
  if path=='/api/admin/families':
   b=body(self);d=site_data();fams=b.get('families',d.get('families',DEFAULT_FAMILIES));
   for f in fams:
    if isinstance(f,dict): f.setdefault('show_menu',True); f.setdefault('show_top',False); f.setdefault('show_bottom',True)
   d['families']=fams;write_json(DATA/'site_data.json',d);save_categories(d['families']);self.send_json({'ok':True,'families':d['families']});return
  if path=='/api/admin/categories':b=body(self);save_categories(b.get('categories',[]));self.send_json({'ok':True,'categories':categories()});return
  if path=='/api/admin/promotions':b=body(self);d=site_data();d['promotions']=b.get('promotions',[]);write_json(DATA/'site_data.json',d);self.send_json({'ok':True,'promotions':d['promotions']});return
  if path=='/api/admin/brands':
   b=body(self);c=db();c.execute('DELETE FROM brands');[c.execute('INSERT OR IGNORE INTO brands VALUES(?)',(str(x),)) for x in b.get('brands',[])];c.commit();c.close();self.send_json({'ok':True,'brands':b.get('brands',[])});return
  if path=='/api/admin/product':
   b=body(self);slug=str(b.get('slug') or '').strip()
   if not slug:self.send_json({'error':'slug obrigatório'},400);return
   c=db(); old=c.execute('SELECT * FROM products WHERE slug=?',(slug,)).fetchone()
   if b.get('_delete'):c.execute('DELETE FROM products WHERE slug=?',(slug,));c.commit();c.close();self.send_json({'ok':True,'deleted':slug});return
   if old:
    merged=dict(old)
    # Partial admin saves preserve every field that was not edited.
    for k,v in b.items(): merged[k]=v
    if 'sku' in b: merged['ref']=b['sku']
    if 'minStock' in b: merged['min_stock']=b['minStock']
    b=merged
   existed=bool(old);put_product(c,b);c.commit();r=c.execute('SELECT * FROM products WHERE slug=?',(slug,)).fetchone();c.close();self.send_json({'ok':True,'created':not existed,'product':row_product(r)});return
  if path=='/api/admin/family-icon-download':
   if not auth(self):self.send_json({'error':'unauthorized'},401);return
   try:
    b=body(self); url=str(b.get('url','')).strip(); name=str(b.get('name','Ícone')).strip() or 'Ícone'
    u=urllib.parse.urlsplit(url)
    if u.scheme not in ('http','https') or not u.hostname: raise ValueError('URL inválido')
    import socket, ipaddress
    host_ips=socket.getaddrinfo(u.hostname,None)
    for item in host_ips:
     ip=ipaddress.ip_address(item[4][0])
     if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast: raise ValueError('URL não permitida')
    req=urllib.request.Request(url,headers={'User-Agent':'MarquesMater/11'})
    with urllib.request.urlopen(req,timeout=15) as r:
     ctype=(r.headers.get('Content-Type') or '').split(';')[0].lower()
     data=r.read(5*1024*1024+1)
    if len(data)>5*1024*1024: raise ValueError('Imagem demasiado grande (máx. 5 MB)')
    if ctype not in ('image/jpeg','image/png','image/webp','image/gif','image/svg+xml'):
     ext=Path(u.path).suffix.lower(); mime_ext={'.jpg':'.jpg','.jpeg':'.jpg','.png':'.png','.webp':'.webp','.gif':'.gif','.svg':'.svg'}
     if ext not in mime_ext: raise ValueError('O endereço não parece ser uma imagem')
    else: mime_ext={'image/jpeg':'.jpg','image/png':'.png','image/webp':'.webp','image/gif':'.gif','image/svg+xml':'.svg'}
    ext=mime_ext.get(ctype,Path(u.path).suffix.lower() or '.png')
    safe=secrets.token_hex(6)+ext; (UPLOADS/safe).write_bytes(data)
    d=site_data(); lib=d.get('family_icon_library',[]); entry={'name':name,'icon':'uploads/'+safe,'source_url':url}
    lib=[x for x in lib if x.get('icon')!=entry['icon']]; lib.append(entry); d['family_icon_library']=lib; write_json(DATA/'site_data.json',d)
    self.send_json({'ok':True,'icon':entry['icon'],'item':entry,'library':lib})
   except Exception as e:self.send_json({'error':str(e)},400)
   return
  if path=='/api/admin/upload':
   ctype=self.headers.get('Content-Type','')
   if 'multipart/form-data' not in ctype:self.send_json({'error':'multipart obrigatório'},400);return
   n=int(self.headers.get('Content-Length','0'));raw=self.rfile.read(n);m=re.search(r'boundary=([^;]+)',ctype)
   if not m:self.send_json({'error':'boundary em falta'},400);return
   boundary=m.group(1).strip().strip('"').encode();parts=raw.split(b'--'+boundary);filename=None;content=None
   for part in parts:
    if b'Content-Disposition:' not in part:continue
    hdr,_,dat=part.partition(b'\r\n\r\n');fm=re.search(br'filename="([^"]+)"',hdr)
    if fm:filename=os.path.basename(fm.group(1).decode('utf-8','replace'));content=dat.rsplit(b'\r\n',1)[0];break
   if not filename or content is None:self.send_json({'error':'ficheiro em falta'},400);return
   ext=Path(filename).suffix.lower();allowed={'.jpg','.jpeg','.png','.webp','.gif','.pdf','.doc','.docx'}
   if ext not in allowed:self.send_json({'error':'Formato não suportado'},400);return
   safe=secrets.token_hex(5)+ext;(UPLOADS/safe).write_bytes(content);self.send_json({'ok':True,'url':'uploads/'+safe,'filename':filename});return
  self.send_json({'error':'not_found'},404)

def admin_data():return read_json(DATA/'admin.json',{})
if __name__=='__main__':
 host=os.environ.get('MM_HOST','0.0.0.0');port=int(os.environ.get('PORT') or os.environ.get('MM_PORT','8000'));print(f'MarquesMater V26 server: http://{host}:{port}',flush=True);ThreadingHTTPServer((host,port),Handler).serve_forever()

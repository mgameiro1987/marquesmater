import csv, io, json, re, base64, zipfile, xml.etree.ElementTree as ET
from urllib.parse import parse_qs

def _clean(v):
    return str(v or '').strip()

def _num(v, default=0):
    try:
        s=str(v or '').strip().replace('€','').replace(' ','')
        if s.count(',') and s.count('.'): s=s.replace('.','').replace(',','.')
        else: s=s.replace(',','.')
        return float(s)
    except Exception:
        return default

def _bool(v, default=True):
    s=_clean(v).lower()
    if not s:return default
    return s not in ('0','false','nao','não','no','inativo','inactiva','inactivo')

def _norm(s):
    s=_clean(s).lower()
    trans=str.maketrans({'á':'a','à':'a','ã':'a','â':'a','ä':'a','é':'e','ê':'e','è':'e','ë':'e','í':'i','ì':'i','ï':'i','ó':'o','ô':'o','õ':'o','ò':'o','ö':'o','ú':'u','ù':'u','ü':'u','ç':'c','ñ':'n'})
    return re.sub(r'[^a-z0-9]','',s.translate(trans))

ALIASES={
    'sku':{'sku','codigo','codigoartigo','ref','referencia','referenciaartigo','skureferencia','codigoreferencia','referencia sku'},
    'barcode':{'ean','ean13','ean8','barcode','codigodebarras','gtin'},
    'name':{'nome','name','produto','designacao','designacaoproduto','descricao curta','nomeproduto','designacao curta'},
    'brand':{'marca','brand'},
    'category':{'categoria','category'},
    'subcategory':{'subcategoria','subcategory','subfamilia','subfamilias'},
    'family':{'familia','family'},
    'type':{'tipo','type'},
    'price':{'preco','price','pvp','pvpciva','precovenda','precodevenda'},
    'oldPrice':{'precoantigo','oldprice','oldpvp'},
    'description':{'descricao','description','descricaolonga','descricaodetalhada'},
    'image':{'imagem','image','urlimagem','imagemurl','fotografia','foto'},
    'badge':{'badge','etiqueta'},
    'cost':{'custo','cost','precocusto'},
    'vatRate':{'iva','ivarate','taxaiva'},
    'active':{'ativo','active','estado'},
    'stockMin':{'stockmin','stockminimo','minstock','stockminimoartigo'},
    'stockInitial':{'stock','stockinicial','stockinicialfisico','quantidade','quantidadeinicial'}
}
_ALIAS_NORM={field:{_norm(x) for x in keys} for field,keys in ALIASES.items()}

def _match_field(header):
    n=_norm(header)
    if not n:return None
    for field,keys in _ALIAS_NORM.items():
        if n in keys:return field
    if n.startswith('sku') or n.endswith('sku'):return 'sku'
    if 'ean' in n or 'barcode' in n or 'codigodebarras' in n:return 'barcode'
    if 'descricao' in n and ('curta' in n or 'produto' in n):return 'name'
    if 'descricao' in n:return 'description'
    if 'familia' in n:return 'family'
    if 'subfamilia' in n or 'subcategoria' in n:return 'subcategory'
    if 'categoria' in n:return 'category'
    if 'marca' in n:return 'brand'
    if 'pvp' in n or 'preco' in n:return 'price'
    if 'custo' in n:return 'cost'
    if 'iva' in n:return 'vatRate'
    if 'stockmin' in n:return 'stockMin'
    if 'stockinicial' in n:return 'stockInitial'
    if n=='stock' or n.startswith('stock') and 'min' not in n:return 'stockInitial'
    return None

def _image_cell_value(cell):
    try:
        v=cell.value
        if isinstance(v,str) and v.strip():return v.strip()
        link=getattr(cell,'hyperlink',None)
        target=getattr(link,'target',None) if link else None
        if target:return str(target).strip()
    except Exception:pass
    return ''

def _row_payload(raw):
    normalized={}
    for k,v in raw.items():
        field=_match_field(k)
        if field and field not in normalized:normalized[field]=v
    out=dict(normalized)
    if 'name' not in out and 'description' in out:out['name']=out['description']
    for k in ('sku','name','brand','category','subcategory','family','type','barcode','description','image','badge'):
        out[k]=_clean(out.get(k))
    out['price']=_num(out.get('price'));out['oldPrice']=_num(out.get('oldPrice'));out['cost']=_num(out.get('cost'));out['vatRate']=_num(out.get('vatRate'),23);out['stockMin']=max(0,int(_num(out.get('stockMin'),0)));out['active']=_bool(out.get('active'),True)
    if 'stockInitial' in normalized:
        out['stockInitial']=max(0,int(_num(normalized.get('stockInitial'),0)));out['stockProvided']=True
    else:
        out['stockInitial']=0;out['stockProvided']=False
    return out

def _find_header(ws):
    best=None
    for row_number,row in enumerate(ws.iter_rows(min_row=1,max_row=min(ws.max_row,60),values_only=True),1):
        fields=[_match_field(v) for v in row if v not in (None,'')]
        if 'sku' in fields and ('name' in fields or 'description' in fields):
            score=3+int('brand' in fields)+int('category' in fields)+int('price' in fields)+int('stockInitial' in fields)+int('image' in fields)
            candidate=(score,row_number,row)
            if best is None or candidate[0]>best[0]:best=candidate
    return (best[1],best[2]) if best else None

def _extract_embedded_images(data,ws):
    result={}
    try:
        drawing_target=None
        for rel in getattr(ws,'_rels',[]) or []:
            if str(getattr(rel,'Type','')).endswith('/drawing'):
                drawing_target=str(getattr(rel,'Target','')).lstrip('/')
                break
        if not drawing_target:return result
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            if drawing_target not in zf.namelist():return result
            drawing_root=ET.fromstring(zf.read(drawing_target))
            rel_path=posixpath.join(posixpath.dirname(drawing_target),'_rels',posixpath.basename(drawing_target)+'.rels')
            if rel_path not in zf.namelist():return result
            rel_root=ET.fromstring(zf.read(rel_path))
            relmap={r.attrib.get('Id'):r.attrib.get('Target','') for r in rel_root}
            ns={'xdr':'http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing','a':'http://schemas.openxmlformats.org/drawingml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
            for anchor in drawing_root:
                frm=anchor.find('xdr:from',ns)
                if frm is None:continue
                row_el=frm.find('xdr:row',ns)
                pic=anchor.find('.//xdr:pic',ns)
                blip=pic.find('.//a:blip',ns) if pic is not None else None
                if row_el is None or blip is None:continue
                row=int(row_el.text)+1
                rid=blip.attrib.get('{%s}embed'%ns['r']);target=relmap.get(rid)
                if not target:continue
                media=posixpath.normpath(posixpath.join(posixpath.dirname(drawing_target),target))
                if media not in zf.namelist():continue
                raw=zf.read(media);ext=media.rsplit('.',1)[-1].lower();mime={'jpg':'image/jpeg','jpeg':'image/jpeg','gif':'image/gif','webp':'image/webp','bmp':'image/bmp'}.get(ext,'image/png')
                result[row]=f'data:{mime};base64,'+base64.b64encode(raw).decode('ascii')
    except Exception:
        return result
    return result

def _read_excel(data,filename=''):
    from openpyxl import load_workbook
    wb=load_workbook(io.BytesIO(data),read_only=False,data_only=True)
    candidates=[];preferred=('produtos','catalogo','catálogo','rida','composição skus','composicao skus')
    for ws in wb.worksheets:
        header=_find_header(ws)
        if not header:continue
        header_row,headers=header;images=_extract_embedded_images(data,ws);rows=[]
        image_header_col=next((i+1 for i,h in enumerate(headers) if _match_field(h)=='image'),None)
        for r in range(header_row+1,ws.max_row+1):
            vals=[ws.cell(r,c).value for c in range(1,ws.max_column+1)]
            if not any(v not in (None,'') for v in vals):continue
            raw=dict(zip(headers,vals));item=_row_payload(raw)
            if image_header_col:
                cell_img=_image_cell_value(ws.cell(r,image_header_col))
                if cell_img:item['image']=cell_img
            if not item.get('sku') and not item.get('name'):continue
            if r in images and not item.get('image'):item['image']=images[r]
            rows.append(item)
        if rows:
            title=ws.title.strip().lower();preference=1 if any(p in title for p in preferred) else 0;candidates.append((preference,len(rows),ws.title,rows))
    if not candidates:raise ValueError('Excel: não encontrei uma folha com cabeçalhos de produto contendo SKU e Descrição/Nome.')
    candidates.sort(key=lambda x:(x[0],x[1]),reverse=True);return candidates[0][3]

def _read_file(data,filename):
    if filename.lower().endswith(('.xlsx','.xlsm')):return _read_excel(data,filename)
    text=data.decode('utf-8-sig',errors='replace');sample=text[:4096]
    try:dialect=csv.Sniffer().sniff(sample,delimiters=',;\t')
    except Exception:dialect=csv.excel;dialect.delimiter=';'
    return [_row_payload(r) for r in csv.DictReader(io.StringIO(text),dialect=dialect)]

def _extract_multipart(handler):
    length=int(handler.headers.get('Content-Length','0') or 0);raw=handler.rfile.read(length);ctype=handler.headers.get('Content-Type','');m=re.search(r'boundary=(?:"([^"]+)"|([^;]+))',ctype)
    if not m:raise ValueError('Multipart inválido: boundary em falta')
    boundary=(m.group(1) or m.group(2)).encode()
    for part in raw.split(b'--'+boundary):
        if b'filename=' not in part:continue
        head,sep,body=part.partition(b'\r\n\r\n')
        if not sep:continue
        hm=re.search(br'filename="([^"]*)"',head);filename=(hm.group(1).decode('utf-8','replace') if hm else 'import.csv');return filename,body.rstrip(b'\r\n-')
    raise ValueError('Nenhum ficheiro encontrado')

def _preview(rows):
    def has_image(r):
        v=_clean(r.get('image','')).lower()
        return v.startswith('data:image/') or v.startswith('http://') or v.startswith('https://')
    return {'total':len(rows),'with_images':sum(1 for r in rows if has_image(r)),'with_stock':sum(1 for r in rows if r.get('stockProvided')),'excel_stock_total':sum(int(r.get('stockInitial',0) or 0) for r in rows if r.get('stockProvided')),'without_stock':sum(1 for r in rows if not r.get('stockProvided'))}

def _import_rows(rows):
    from v98_catalog_products_api import handle_post
    import psycopg,os
    if not os.environ.get('DATABASE_URL'):raise RuntimeError('DATABASE_URL não configurado')
    errors=[];created=updated=images=stock_added=0
    with psycopg.connect(os.environ['DATABASE_URL']) as conn:
        with conn.cursor() as cur:
            for line,row in enumerate(rows,2):
                cur.execute('SELECT stock FROM mm_product_stock WHERE sku=%s',(row['sku'],));stock_row=cur.fetchone();had_stock=stock_row is not None
                payload={k:v for k,v in row.items() if k not in ('stockInitial','stockProvided','_filename')};captured=[]
                handle_post('/api/catalog/products',payload,lambda status,payload:captured.append((status,payload)))
                status,result=captured[-1] if captured else (500,{'ok':False,'error':'Sem resposta'})
                if status>=300 or not result.get('ok'):
                    errors.append({'linha':line,'sku':row['sku'],'error':result.get('error','Erro desconhecido')});continue
                if _clean(row.get('image','')).lower().startswith(('data:image/','http://','https://')):images+=1
                if had_stock:updated+=1
                else:created+=1
                if row.get('stockProvided') and not had_stock:
                    initial=int(row.get('stockInitial',0) or 0)
                    cur.execute('UPDATE mm_product_stock SET stock=%s,updated_at=NOW() WHERE sku=%s',(initial,row['sku']))
                    if initial>0:
                        cur.execute("INSERT INTO mm_stock_movements(sku,movement_type,delta,resulting_stock,reason,notes) VALUES(%s,'entrada',%s,%s,%s,%s)",(row['sku'],initial,initial,'Importação inicial de catálogo','Stock inicial importado do Excel '+str(row.get('_filename',''))));stock_added+=initial
        conn.commit()
    return {'created':created,'updated':updated,'images':images,'stock_added':stock_added,'errors':errors}

def handle_upload(handler,send_json):
    try:
        filename,data=_extract_multipart(handler)
        if not filename.lower().endswith(('.csv','.xlsx','.xlsm')):raise ValueError('Formato não suportado. Use CSV ou Excel (.xlsx).')
        rows=_read_file(data,filename)
        if not rows:raise ValueError('O ficheiro não contém linhas de dados.')
        if len(rows)>5000:raise ValueError('Limite de 5000 linhas por importação.')
        bad=[i+2 for i,r in enumerate(rows) if not r.get('sku') or not r.get('name')]
        if bad:raise ValueError('SKU e Nome são obrigatórios. Linhas inválidas: '+', '.join(map(str,bad[:20]))+('…' if len(bad)>20 else ''))
        qs=parse_qs(handler.path.split('?',1)[1] if '?' in handler.path else '');mode=(qs.get('mode') or [''])[0]
        if mode=='preview':send_json(200,{'ok':True,'filename':filename,'preview':_preview(rows)});return True
        for r in rows:r['_filename']=filename
        result=_import_rows(rows);send_json(200,{'ok':not result['errors'],'filename':filename,'total':len(rows),'created':result['created'],'updated':result['updated'],'images':result['images'],'stockAdded':result['stock_added'],'failed':len(result['errors']),'errors':result['errors'][:50],'message':f"Importação concluída: {result['created']} novos, {result['updated']} atualizados, {result['images']} imagens e {result['stock_added']} unidades de stock aplicadas do Excel."});return True
    except ValueError as e:send_json(400,{'ok':False,'error':str(e)});return True
    except Exception as e:send_json(503,{'ok':False,'error':f'Importação: {e}'});return True
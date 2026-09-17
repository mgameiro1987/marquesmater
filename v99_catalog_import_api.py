import csv, io, json, re, base64
from urllib.parse import parse_qs


def _clean(v): return str(v or '').strip()
def _num(v, default=0):
    try:
        s=str(v or '').strip().replace('€','').replace(' ','')
        if s.count(',') and s.count('.'): s=s.replace('.','').replace(',','.')
        else: s=s.replace(',','.')
        return float(s)
    except Exception: return default

def _bool(v, default=True):
    s=_clean(v).lower()
    if not s:return default
    return s not in ('0','false','nao','não','no','inativo','inactiva','inactivo')

def _norm(s):
    return re.sub(r'[^a-z0-9]','',_clean(s).lower().replace('á','a').replace('à','a').replace('ã','a').replace('â','a').replace('é','e').replace('ê','e').replace('í','i').replace('ó','o').replace('ô','o').replace('õ','o').replace('ú','u').replace('ç','c'))

ALIASES={
 'sku':{'sku','codigo','codigoartigo','ref','referencia','referenciaartigo'},'barcode':{'ean','ean13','ean8','barcode','codigodebarras','gtin'},
 'name':{'nome','name','produto','designacao','designacaoproduto','descricao curta'},'brand':{'marca','brand'},'category':{'categoria','category'},
 'subcategory':{'subcategoria','subcategory','subfamilia','subfamilias'},'family':{'familia','family'},'type':{'tipo','type'},
 'price':{'preco','price','pvp','pvpciva','precovenda'},'oldPrice':{'precoantigo','oldprice','oldpvp'},
 'description':{'descricao','description','descricaolonga'},'image':{'imagem','image','urlimagem','imagemurl'},'badge':{'badge','etiqueta'},
 'cost':{'custo','cost','precocusto'},'vatRate':{'iva','ivarate','taxaiva'},'active':{'ativo','active','estado'},
 'stockMin':{'stockmin','stockminimo','minstock'},'stockInitial':{'stock','stockinicial','stockinicialfisico','quantidade','quantidadeinicial'}
}

def _row_payload(raw):
    normalized={_norm(k):v for k,v in raw.items() if k is not None};out={}
    for field,keys in ALIASES.items():
        for k in keys:
            if _norm(k) in normalized: out[field]=normalized[_norm(k)];break
    if 'name' not in out and 'description' in out: out['name']=out['description']
    for k in ('sku','name','brand','category','subcategory','family','type','barcode','description','image','badge'): out[k]=_clean(out.get(k))
    out['price']=_num(out.get('price'));out['oldPrice']=_num(out.get('oldPrice'));out['cost']=_num(out.get('cost'));out['vatRate']=_num(out.get('vatRate'),23);out['stockMin']=max(0,int(_num(out.get('stockMin'),0)));out['stockInitial']=max(0,int(_num(out.get('stockInitial'),0)));out['active']=_bool(out.get('active'),True)
    return out

def _find_header(ws):
    for row in ws.iter_rows(min_row=1,max_row=min(ws.max_row,30),values_only=True):
        vals=[_norm(v) for v in row if v not in (None,'')]
        if 'sku' in vals and ('descricao' in vals or 'produto' in vals or 'nome' in vals): return row
    return None

def _extract_embedded_images(ws):
    result={}
    for image in getattr(ws,'_images',[]) or []:
        try:
            row=image.anchor._from.row+1;col=image.anchor._from.col+1
            if col!=2: continue
            raw=image._data();ext=str(getattr(image,'format','png') or 'png').lower().replace('jpeg','jpg');mime='image/jpeg' if ext in ('jpg','jpeg') else 'image/png'
            result[row]=f'data:{mime};base64,'+base64.b64encode(raw).decode('ascii')
        except Exception: continue
    return result

def _read_excel(data):
    from openpyxl import load_workbook
    wb=load_workbook(io.BytesIO(data),read_only=False,data_only=True);ws=wb.active;headers=_find_header(ws)
    if not headers: raise ValueError('Excel: não encontrei uma linha de cabeçalhos com SKU e Descrição/Nome.')
    header_row=1
    for i,row in enumerate(ws.iter_rows(min_row=1,max_row=min(ws.max_row,30),values_only=True),1):
        if tuple(row)==tuple(headers): header_row=i;break
    images=_extract_embedded_images(ws);rows=[]
    for r in range(header_row+1,ws.max_row+1):
        vals=[ws.cell(r,c).value for c in range(1,ws.max_column+1)]
        if not any(v not in (None,'') for v in vals): continue
        item=_row_payload(dict(zip(headers,vals)))
        if not item.get('sku') and not item.get('name'): continue
        if r in images:item['image']=images[r]
        rows.append(item)
    return rows

def _read_file(data,filename):
    if filename.lower().endswith(('.xlsx','.xlsm')): return _read_excel(data)
    text=data.decode('utf-8-sig',errors='replace');sample=text[:4096]
    try:dialect=csv.Sniffer().sniff(sample,delimiters=',;\t')
    except Exception:dialect=csv.excel;dialect.delimiter=';'
    return [_row_payload(r) for r in csv.DictReader(io.StringIO(text),dialect=dialect)]

def _extract_multipart(handler):
    length=int(handler.headers.get('Content-Length','0') or 0);raw=handler.rfile.read(length);ctype=handler.headers.get('Content-Type','');m=re.search(r'boundary=(?:"([^"]+)"|([^;]+))',ctype)
    if not m: raise ValueError('Multipart inválido: boundary em falta')
    boundary=(m.group(1) or m.group(2)).encode()
    for part in raw.split(b'--'+boundary):
        if b'filename=' not in part: continue
        head,sep,body=part.partition(b'\r\n\r\n')
        if not sep: continue
        hm=re.search(br'filename="([^"]*)"',head);filename=(hm.group(1).decode('utf-8','replace') if hm else 'import.csv');return filename,body.rstrip(b'\r\n-')
    raise ValueError('Nenhum ficheiro encontrado')

def _preview(rows,default_stock):
    explicit=sum(int(r.get('stockInitial',0) or 0) for r in rows);fallback=sum(1 for r in rows if int(r.get('stockInitial',0) or 0)==0)*default_stock
    return {'total':len(rows),'with_images':sum(bool(r.get('image','').startswith('data:image/')) for r in rows),'with_stock':sum(1 for r in rows if int(r.get('stockInitial',0) or 0)>0),'new_stock_total':explicit+fallback,'default_stock':default_stock}

def _import_rows(rows,default_stock):
    from v98_catalog_products_api import handle_post
    import psycopg,os
    if not os.environ.get('DATABASE_URL'): raise RuntimeError('DATABASE_URL não configurado')
    errors=[];created=updated=images=stock_added=0
    with psycopg.connect(os.environ['DATABASE_URL']) as conn:
        with conn.cursor() as cur:
            for line,row in enumerate(rows,2):
                cur.execute('SELECT stock FROM mm_product_stock WHERE sku=%s',(row['sku'],));stock_row=cur.fetchone();had_stock=stock_row is not None
                payload={k:v for k,v in row.items() if k not in ('stockInitial','_filename')};captured=[]
                handle_post('/api/catalog/products',payload,lambda status,payload:captured.append((status,payload)))
                status,result=captured[-1] if captured else (500,{'ok':False,'error':'Sem resposta'})
                if status>=300 or not result.get('ok'):
                    errors.append({'linha':line,'sku':row['sku'],'error':result.get('error','Erro desconhecido')});continue
                if row.get('image','').startswith('data:image/'): images+=1
                if had_stock: updated+=1
                else: created+=1
                initial=int(row.get('stockInitial',0) or 0) or (default_stock if default_stock>0 else 0)
                if initial>0 and not had_stock:
                    cur.execute('UPDATE mm_product_stock SET stock=%s,updated_at=NOW() WHERE sku=%s',(initial,row['sku']))
                    cur.execute("INSERT INTO mm_stock_movements(sku,movement_type,delta,resulting_stock,reason,notes) VALUES(%s,'entrada',%s,%s,%s,%s)",(row['sku'],initial,initial,'Importação inicial de catálogo','Stock inicial importado do ficheiro '+str(row.get('_filename',''))));stock_added+=initial
        conn.commit()
    return {'created':created,'updated':updated,'images':images,'stock_added':stock_added,'errors':errors}

def handle_upload(handler,send_json):
    try:
        filename,data=_extract_multipart(handler)
        if not filename.lower().endswith(('.csv','.xlsx','.xlsm')): raise ValueError('Formato não suportado. Use CSV ou Excel (.xlsx).')
        rows=_read_file(data,filename)
        if not rows: raise ValueError('O ficheiro não contém linhas de dados.')
        if len(rows)>5000: raise ValueError('Limite de 5000 linhas por importação.')
        bad=[i+2 for i,r in enumerate(rows) if not r.get('sku') or not r.get('name')]
        if bad: raise ValueError('SKU e Nome são obrigatórios. Linhas inválidas: '+', '.join(map(str,bad[:20]))+('…' if len(bad)>20 else ''))
        qs=parse_qs(handler.path.split('?',1)[1] if '?' in handler.path else '');mode=(qs.get('mode') or [''])[0];default_stock=max(0,int(_num((qs.get('defaultStock') or ['0'])[0],0)))
        if mode=='preview':send_json(200,{'ok':True,'filename':filename,'preview':_preview(rows,default_stock)});return True
        for r in rows:r['_filename']=filename
        result=_import_rows(rows,default_stock)
        send_json(200,{'ok':not result['errors'],'filename':filename,'total':len(rows),'created':result['created'],'updated':result['updated'],'images':result['images'],'stockAdded':result['stock_added'],'failed':len(result['errors']),'errors':result['errors'][:50],'message':f"Importação concluída: {result['created']} novos, {result['updated']} atualizados, {result['images']} imagens e +{result['stock_added']} unidades de stock inicial."});return True
    except ValueError as e:send_json(400,{'ok':False,'error':str(e)});return True
    except Exception as e:send_json(503,{'ok':False,'error':f'Importação: {e}'});return True

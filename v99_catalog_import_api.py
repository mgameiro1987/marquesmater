import csv, io, json, re


def _clean(v):
    return str(v or '').strip()


def _num(v, default=0):
    try:
        s=str(v or '').strip().replace('€','').replace(' ','')
        if s.count(',') and s.count('.'):
            s=s.replace('.','').replace(',','.')
        else:
            s=s.replace(',','.')
        return float(s)
    except Exception:
        return default


def _bool(v, default=True):
    s=_clean(v).lower()
    if not s:return default
    return s not in ('0','false','nao','não','no','inativo','inactiva','inactivo')


def _norm(s):
    return re.sub(r'[^a-z0-9]','',_clean(s).lower().replace('á','a').replace('à','a').replace('ã','a').replace('â','a').replace('é','e').replace('ê','e').replace('í','i').replace('ó','o').replace('ô','o').replace('õ','o').replace('ú','u').replace('ç','c'))

ALIASES={
 'sku':{'sku','codigo','codigoartigo','ref','referencia','referenciaartigo'},
 'barcode':{'ean','ean13','ean8','barcode','codigodebarras','gtin'},
 'name':{'nome','name','produto','designacao','descricao curta','designacaoproduto'},
 'brand':{'marca','brand'}, 'category':{'categoria','category'},
 'subcategory':{'subcategoria','subcategory'}, 'family':{'familia','family'},
 'type':{'tipo','type'}, 'price':{'preco','price','pvp','pvpciva','precovenda'},
 'oldPrice':{'precoantigo','oldprice','oldpvp'}, 'description':{'descricao','description','descricaolonga'},
 'image':{'imagem','image','urlimagem','imagemurl'}, 'badge':{'badge','etiqueta'},
 'cost':{'custo','cost','precocusto'}, 'vatRate':{'iva','ivarate','taxaiva'},
 'active':{'ativo','active','estado'}, 'stockMin':{'stockmin','stockminimo','minstock'}
}


def _row_payload(raw):
    normalized={_norm(k):v for k,v in raw.items() if k is not None}
    out={}
    for field,keys in ALIASES.items():
        for k in keys:
            nk=_norm(k)
            if nk in normalized:
                out[field]=normalized[nk]
                break
    if 'name' not in out and 'description' in out: out['name']=out['description']
    out['sku']=_clean(out.get('sku'))
    out['name']=_clean(out.get('name'))
    out['brand']=_clean(out.get('brand'));out['category']=_clean(out.get('category'));out['subcategory']=_clean(out.get('subcategory'));out['family']=_clean(out.get('family'));out['type']=_clean(out.get('type'))
    out['barcode']=_clean(out.get('barcode'))
    out['price']=_num(out.get('price'));out['oldPrice']=_num(out.get('oldPrice'));out['cost']=_num(out.get('cost'));out['vatRate']=_num(out.get('vatRate'),23);out['stockMin']=max(0,int(_num(out.get('stockMin'),0)))
    out['active']=_bool(out.get('active'),True)
    out['description']=_clean(out.get('description'));out['image']=_clean(out.get('image'));out['badge']=_clean(out.get('badge'))
    return out


def _read_file(data, filename):
    lower=filename.lower()
    if lower.endswith('.xlsx') or lower.endswith('.xlsm'):
        from openpyxl import load_workbook
        wb=load_workbook(io.BytesIO(data),read_only=True,data_only=True)
        ws=wb.active; rows=ws.iter_rows(values_only=True)
        headers=next(rows,None)
        if not headers: return []
        return [dict(zip(headers,row)) for row in rows if any(v not in (None,'') for v in row)]
    text=data.decode('utf-8-sig',errors='replace')
    sample=text[:4096]
    try: dialect=csv.Sniffer().sniff(sample,delimiters=',;\t')
    except Exception: dialect=csv.excel; dialect.delimiter=';'
    return list(csv.DictReader(io.StringIO(text),dialect=dialect))


def _extract_multipart(handler):
    length=int(handler.headers.get('Content-Length','0') or 0)
    raw=handler.rfile.read(length)
    ctype=handler.headers.get('Content-Type','')
    m=re.search(r'boundary=(?:"([^"]+)"|([^;]+))',ctype)
    if not m: raise ValueError('Multipart inválido: boundary em falta')
    boundary=(m.group(1) or m.group(2)).encode()
    marker=b'--'+boundary
    for part in raw.split(marker):
        if b'filename=' not in part: continue
        head,sep,body=part.partition(b'\r\n\r\n')
        if not sep: continue
        hm=re.search(br'filename="([^"]*)"',head)
        filename=(hm.group(1).decode('utf-8','replace') if hm else 'import.csv')
        body=body.rstrip(b'\r\n-')
        return filename,body
    raise ValueError('Nenhum ficheiro encontrado')


def handle_upload(handler,send_json):
    try:
        filename,data=_extract_multipart(handler)
        if not filename.lower().endswith(('.csv','.xlsx','.xlsm')):
            raise ValueError('Formato não suportado. Use CSV ou Excel (.xlsx).')
        rows=[_row_payload(r) for r in _read_file(data,filename)]
        if not rows: raise ValueError('O ficheiro não contém linhas de dados.')
        if len(rows)>5000: raise ValueError('Limite de 5000 linhas por importação.')
        bad=[i+2 for i,r in enumerate(rows) if not r.get('sku') or not r.get('name')]
        if bad: raise ValueError('SKU e Nome são obrigatórios. Linhas inválidas: '+', '.join(map(str,bad[:20]))+('…' if len(bad)>20 else ''))
        from v98_catalog_products_api import handle_post
        results=[]; ok=0
        def capture(status,payload): results.append((status,payload))
        for i,row in enumerate(rows,2):
            results.clear();handle_post('/api/catalog/products',row,capture)
            status,payload=results[-1] if results else (500,{'ok':False,'error':'Sem resposta'})
            if status<300 and payload.get('ok'):
                ok+=1
            else:
                results.append((status,payload))
        errors=[{'linha':i+2,'error':(next((p.get('error') for s,p in []),None) or 'Erro')} for i in []]
        # Re-run is intentionally avoided: handle_post is the single source of truth and protects stock.
        send_json(200,{'ok':True,'filename':filename,'total':len(rows),'imported':ok,'failed':len(rows)-ok,'message':f'{ok} de {len(rows)} linhas processadas. Stock não é alterado pela importação.'})
        return True
    except ValueError as e:
        send_json(400,{'ok':False,'error':str(e)});return True
    except Exception as e:
        send_json(503,{'ok':False,'error':f'Importação: {e}'});return True

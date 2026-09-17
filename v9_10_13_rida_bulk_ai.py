import os, json, threading, time, urllib.request
import psycopg

JOB={"status":"idle","total":0,"done":0,"errors":0,"last":None,"started_at":None,"finished_at":None}

GARDEN={"RGT11280","RHT09025","RCS03V016","RCS06006","RBP01040","RBL06650","REP16245"}
CONSTRUCTION={"RCR11022","RGG11310","RJR12000","RHD01075","RCG07115","RCG07125","RCH072D6","RCC00190","RCC08150","RCJ08025","RCO11125","RCO13150","RCL1250H"}
ACCESSORIES={"RB2020","RB2040","RFC24","RDC30","BMCB75"}
GARDEN_KITS={"RGT11280-C12","RHT09025-C12","RCS03V016-C24","RCS06006-C12","RBP01040-C12","RBL06650-C22"}
CONSTRUCTION_KITS={"RHD01075-B22","RCG07115-B24","RCG07125-B24","RCH072D6-B24","RCC00190-C14","RCC08150-C14","RCJ08025-C22","RCO11125-C12","RCO13150-C12","RCL1250H-C12"}

def db():
    return psycopg.connect(os.environ["DATABASE_URL"])

def image_url(value):
    value=str(value or "").strip()
    if not value:return None
    if value.startswith("data:image/") or value.startswith("http://") or value.startswith("https://"):return value
    host=os.environ.get("PUBLIC_BASE_URL","https://marquesmater-7ap1.onrender.com").rstrip("/")
    return host+"/"+value.lstrip("/")

def generate(product):
    key=os.environ.get("OPENAI_API_KEY")
    if not key: raise RuntimeError("OPENAI_API_KEY não configurada")
    model=os.environ.get("OPENAI_MODEL","gpt-5.6-luna")
    attrs=product.get("attributes") or {}
    context={
      "sku":product.get("sku"),"ean":product.get("barcode"),"brand":product.get("brand"),
      "name":product.get("name"),"type":product.get("type"),
      "commercial_category":product.get("commercial_category"),
      "commercial_subcategory":product.get("commercial_subcategory"),
      "rida_category":product.get("rida_category"),
      "rida_subcategory":product.get("rida_subcategory"),
      "rida_family":product.get("rida_family"),
      "existing_description":product.get("description") or "",
      "source_attributes":attrs,
      "source_specs":product.get("specs") or {}
    }
    instructions=("És o assistente de conteúdos da MarquesMater. Escreve em português de Portugal e cria conteúdo profissional para uma loja online de ferramentas e máquinas RIDA. "
      "Analisa a imagem quando fornecida e cruza-a com SKU, nome e dados estruturados. "
      "NUNCA inventes números, tensões, potências, capacidades, rotações, pesos, dimensões, certificações, autonomia ou outras especificações técnicas. "
      "Só apresentes como confirmado o que estiver visível na imagem ou fornecido nos dados. Se não for possível confirmar uma especificação, deixa-a vazia. "
      "A descrição deve ser comercial mas factual. Características e aplicações devem ser objetivas. Especificações deve conter apenas dados técnicos confirmados.")
    schema={"type":"object","properties":{
      "description":{"type":"string"},
      "characteristics":{"type":"string"},
      "specifications":{"type":"array","items":{"type":"string"}},
      "applications":{"type":"string"}
    },"required":["description","characteristics","specifications","applications"],"additionalProperties":False}
    content=[{"type":"input_text","text":"Dados do produto:\n"+json.dumps(context,ensure_ascii=False)+"\n\nGera os quatro campos."}]
    img=image_url(product.get("image"))
    if img: content.append({"type":"input_image","image_url":img,"detail":"high"})
    payload={"model":model,"store":False,"instructions":instructions,"input":[{"role":"user","content":content}],
             "text":{"format":{"type":"json_schema","name":"marquesmater_rida_bulk_content","schema":schema,"strict":True}}}
    req=urllib.request.Request("https://api.openai.com/v1/responses",data=json.dumps(payload,ensure_ascii=False).encode(),
        headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=120) as response:
        data=json.loads(response.read().decode())
    raw=data.get("output_text") or ""
    if not raw:
        for item in data.get("output") or []:
            for part in item.get("content") or []:
                if part.get("type")=="output_text": raw=part.get("text") or ""; break
            if raw: break
    return json.loads(raw or "{}")

def mapping(sku):
    base=sku
    if base in GARDEN or base in GARDEN_KITS:
        commercial=(4,25,33,"Jardim & Agricultura","Serras de Poda","garden") if base in {"RBP01040","RBP01040-C12"} else (4,None,None,"Jardim & Agricultura",None,None)
        return commercial,(11,16602,16604,"RIDA","Máquinas a bateria","Jardim")
    if base in CONSTRUCTION or base in CONSTRUCTION_KITS:
        return (7,None,None,"Construção",None,None),(11,16602,16603,"RIDA","Máquinas a bateria","Construção")
    if base in ACCESSORIES:
        if base in {"RB2020","RB2040"}: commercial=(8,None,None,"Ferragens",None,None)
        elif base in {"RFC24","RDC30"}: commercial=(10,None,None,"Eletricidade",None,None)
        else: commercial=(8,None,None,"Ferragens",None,None)
        return commercial,(11,16602,16605,"RIDA","Máquinas a bateria","Acessórios")
    return None,None

def ensure_classification(cur,pid,ctype,m):
    if not m:return
    cat,sub,fam,*_=m
    cur.execute("""INSERT INTO mm_product_classifications(product_id,classification_type,category_id,subcategory_id,family_id)
                   VALUES(%s,%s,%s,%s,%s)
                   ON CONFLICT(product_id,classification_type) DO UPDATE SET category_id=EXCLUDED.category_id,subcategory_id=EXCLUDED.subcategory_id,family_id=EXCLUDED.family_id,updated_at=NOW()""",
                (pid,ctype,cat,sub,fam))

def worker():
    global JOB
    JOB.update(status="running",done=0,errors=0,last=None,started_at=time.time(),finished_at=None)
    try:
        with db() as c:
            with c.cursor() as cur:
                cur.execute("SELECT id,sku,brand,name,type,description,image,attributes,specs FROM catalog_products WHERE brand ILIKE 'RIDA' ORDER BY id")
                rows=cur.fetchall()
                JOB["total"]=len(rows)
                for row in rows:
                    pid,sku,brand,name,typ,desc,img,attrs,specs=row
                    try:
                        com,rida=mapping(str(sku))
                        product={"sku":sku,"brand":brand,"name":name,"type":typ,"description":desc,"image":img,"attributes":attrs or {},"specs":specs or {},
                                 "commercial_category":com[3] if com else None,"commercial_subcategory":com[4] if com else None,
                                 "rida_category":rida[3] if rida else None,"rida_subcategory":rida[4] if rida else None,"rida_family":rida[5] if rida else None}
                        result=generate(product)
                        newattrs=dict(attrs or {})
                        newattrs["characteristics"]=str(result.get("characteristics") or "").strip()
                        newattrs["applications"]=str(result.get("applications") or "").strip()
                        new_specs=[str(x).strip() for x in (result.get("specifications") or []) if str(x).strip()]
                        cur.execute("UPDATE catalog_products SET description=%s, specs=%s, attributes=%s, category=%s, subcategory=%s, category_id=%s, subcategory_id=%s, family_id=%s, updated_at=NOW() WHERE id=%s",
                            (str(result.get("description") or "").strip(),json.dumps(new_specs,ensure_ascii=False),json.dumps(newattrs,ensure_ascii=False),
                             com[3] if com else None,com[4] if com else None,com[0] if com else None,com[1] if com else None,com[2] if com else None,pid))
                        ensure_classification(cur,pid,"commercial",com)
                        ensure_classification(cur,pid,"rida",rida)
                        c.commit()
                        JOB["done"]+=1;JOB["last"]=sku
                    except Exception as e:
                        c.rollback();JOB["errors"]+=1;JOB["last"]=str(sku)+": "+str(e)[:300]
                JOB["status"]="done";JOB["finished_at"]=time.time()
    except Exception as e:
        JOB["status"]="error";JOB["last"]=str(e)[:500];JOB["finished_at"]=time.time()

def start():
    global JOB
    if JOB.get("status")=="running": return JOB
    t=threading.Thread(target=worker,daemon=True);t.start()
    return {"status":"started","total":JOB.get("total",0)}

def status():
    return {k:v for k,v in JOB.items() if k not in {"started_at","finished_at"}}

def handle_get(query,send_json):
    from urllib.parse import parse_qs
    q=parse_qs(query or "")
    token=(q.get("token") or [""])[0]
    if token != os.environ.get("RIDA_BULK_TOKEN"): send_json(403,{"ok":False,"error":"Acesso não autorizado"});return True
    if (q.get("run") or [""])[0]=="1":
        send_json(200,{"ok":True,"job":start()});return True
    send_json(200,{"ok":True,"job":status()});return True

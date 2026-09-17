import os, json, threading, time, urllib.request, urllib.error
import psycopg

JOB_KEY="rida-content-41-v3"
GARDEN={"RGT11280","RHT09025","RCS03V016","RCS06006","RBP01040","RBL06650","REP16245"}
CONSTRUCTION={"RCR11022","RGG11310","RJR12000","RHD01075","RCG07115","RCG07125","RCH072D6","RCC00190","RCC08150","RCJ08025","RCO11125","RCO13150","RCL1250H"}
ACCESSORIES={"RB2020","RB2040","RFC24","RDC30","BMCB75"}
GARDEN_KITS={"RGT11280-C12","RHT09025-C12","RCS03V016-C24","RCS06006-C12","RBP01040-C12","RBL06650-C22"}
CONSTRUCTION_KITS={"RHD01075-B22","RCG07115-B24","RCG07125-B24","RCH072D6-B24","RCC00190-C14","RCC08150-C14","RCJ08025-C22","RCO11125-C12","RCO13150-C12","RCL1250H-C12"}

def db(): return psycopg.connect(os.environ["DATABASE_URL"])

def init_job():
    with db() as c:
        with c.cursor() as x:
            x.execute("""CREATE TABLE IF NOT EXISTS mm_ai_bulk_runs(
              job_key TEXT PRIMARY KEY,status TEXT NOT NULL DEFAULT 'pending',total INTEGER NOT NULL DEFAULT 0,
              done INTEGER NOT NULL DEFAULT 0,errors INTEGER NOT NULL DEFAULT 0,last TEXT,
              started_at TIMESTAMPTZ,updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),finished_at TIMESTAMPTZ)""")
            c.commit()

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
    context={"sku":product.get("sku"),"ean":product.get("barcode"),"brand":product.get("brand"),"name":product.get("name"),
      "type":product.get("type"),"commercial_category":product.get("commercial_category"),
      "commercial_subcategory":product.get("commercial_subcategory"),"rida_category":product.get("rida_category"),
      "rida_subcategory":product.get("rida_subcategory"),"rida_family":product.get("rida_family"),
      "existing_description":product.get("description") or "","source_attributes":attrs,"source_specs":product.get("specs") or {}}
    instructions=("És o assistente de conteúdos da MarquesMater. Escreve em português de Portugal e cria conteúdo profissional para uma loja online de ferramentas e máquinas RIDA. "
      "Analisa a imagem quando fornecida e cruza-a com SKU, nome e dados estruturados. "
      "NUNCA inventes números, tensões, potências, capacidades, rotações, pesos, dimensões, certificações, autonomia ou outras especificações técnicas. "
      "Só apresentes como confirmado o que estiver visível na imagem ou fornecido nos dados. Se uma especificação técnica não puder ser confirmada, deixa-a vazia. "
      "A descrição deve ser comercial mas factual. Características e aplicações devem ser objetivas.")
    schema={"type":"object","properties":{"description":{"type":"string"},"characteristics":{"type":"string"},
      "specifications":{"type":"array","items":{"type":"string"}},"applications":{"type":"string"}},
      "required":["description","characteristics","specifications","applications"],"additionalProperties":False}
    content=[{"type":"input_text","text":"Dados do produto:\n"+json.dumps(context,ensure_ascii=False)+"\n\nGera os quatro campos."}]
    img=image_url(product.get("image"))
    if img: content.append({"type":"input_image","image_url":img,"detail":"high"})
    payload={"model":model,"store":False,"instructions":instructions,"input":[{"role":"user","content":content}],
      "text":{"format":{"type":"json_schema","name":"marquesmater_rida_bulk_content","schema":schema,"strict":True}}}
    req=urllib.request.Request("https://api.openai.com/v1/responses",data=json.dumps(payload,ensure_ascii=False).encode(),
      headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"},method="POST")
    data=None
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req,timeout=120) as response:
                data=json.loads(response.read().decode())
            break
        except urllib.error.HTTPError as e:
            if e.code!=429 or attempt>=5: raise
            retry=e.headers.get("Retry-After")
            try: wait=max(10,min(60,float(retry))) if retry else min(60,15*(attempt+1))
            except Exception: wait=min(60,15*(attempt+1))
            time.sleep(wait)
    raw=(data or {}).get("output_text") or ""
    if not raw:
        for item in data.get("output") or []:
            for part in item.get("content") or []:
                if part.get("type")=="output_text": raw=part.get("text") or ""; break
            if raw: break
    return json.loads(raw or "{}")

def mapping(sku):
    if sku in GARDEN or sku in GARDEN_KITS:
        # Só o produto de poda usa a subcategoria comercial já existente; os restantes ficam na categoria comercial.
        com=(4,25,33,"Jardim & Agricultura","Serras de Poda","garden") if sku in {"RBP01040","RBP01040-C12"} else (4,None,None,"Jardim & Agricultura","Jardim & Agricultura",None)
        return com,(11,16602,16604,"RIDA","Máquinas a bateria","Jardim")
    if sku in CONSTRUCTION or sku in CONSTRUCTION_KITS:
        return (7,None,None,"Construção","Construção",None),(11,16602,16603,"RIDA","Máquinas a bateria","Construção")
    if sku in ACCESSORIES:
        if sku in {"RB2020","RB2040"}: com=(8,None,None,"Ferragens","Acessórios",None)
        elif sku in {"RFC24","RDC30"}: com=(10,None,None,"Eletricidade","Acessórios",None)
        else: com=(8,None,None,"Ferragens","Acessórios",None)
        return com,(11,16602,16605,"RIDA","Máquinas a bateria","Acessórios")
    return None,None

def ensure_classification(cur,pid,ctype,m):
    if not m:return
    cat,sub,fam=m[:3]
    cur.execute("""INSERT INTO mm_product_classifications(product_id,classification_type,category_id,subcategory_id,family_id)
      VALUES(%s,%s,%s,%s,%s)
      ON CONFLICT(product_id,classification_type) DO UPDATE SET category_id=EXCLUDED.category_id,
      subcategory_id=EXCLUDED.subcategory_id,family_id=EXCLUDED.family_id,updated_at=NOW()""",(pid,ctype,cat,sub,fam))

def worker():
    try:
        with db() as c:
            with c.cursor() as cur:
                cur.execute("""SELECT id,sku,brand,name,type,description,image,attributes,specs,barcode FROM catalog_products
                  WHERE sku = ANY(%s)
                  AND (COALESCE(attributes->>'characteristics','')='' OR COALESCE(attributes->>'applications','')='' OR specs IS NULL OR specs='[]'::jsonb OR specs='{}'::jsonb)
                  ORDER BY id""", [list(GARDEN|CONSTRUCTION|ACCESSORIES|GARDEN_KITS|CONSTRUCTION_KITS)])
                rows=cur.fetchall()
                cur.execute("UPDATE mm_ai_bulk_runs SET total=%s,status='running',started_at=COALESCE(started_at,NOW()),updated_at=NOW() WHERE job_key=%s",(len(rows),JOB_KEY));c.commit()
                for row in rows:
                    pid,sku,brand,name,typ,desc,img,attrs,specs,barcode=row
                    try:
                        com,rida=mapping(str(sku))
                        product={"sku":sku,"brand":brand,"name":name,"type":typ,"description":desc,"image":img,"barcode":barcode,
                          "attributes":attrs or {},"specs":specs or {},"commercial_category":com[3] if com else None,
                          "commercial_subcategory":com[4] if com else None,"rida_category":rida[3] if rida else None,
                          "rida_subcategory":rida[4] if rida else None,"rida_family":rida[5] if rida else None}
                        result=generate(product)
                        newattrs=dict(attrs or {})
                        newattrs["characteristics"]=str(result.get("characteristics") or "").strip()
                        newattrs["applications"]=str(result.get("applications") or "").strip()
                        new_specs=[str(x).strip() for x in (result.get("specifications") or []) if str(x).strip()]
                        cur.execute("""UPDATE catalog_products SET description=%s,specs=%s,attributes=%s,
                          category=%s,subcategory=%s,category_id=%s,subcategory_id=%s,family_id=%s,updated_at=NOW() WHERE id=%s""",
                          (str(result.get("description") or "").strip(),json.dumps(new_specs,ensure_ascii=False),
                           json.dumps(newattrs,ensure_ascii=False),com[3] if com else None,com[4] if com else None,
                           com[0] if com else None,com[1] if com else None,com[2] if com else None,pid))
                        ensure_classification(cur,pid,"commercial",com);ensure_classification(cur,pid,"rida",rida)
                        cur.execute("UPDATE mm_ai_bulk_runs SET done=done+1,last=%s,updated_at=NOW() WHERE job_key=%s",(sku,JOB_KEY));c.commit()\n                        time.sleep(10)
                    except Exception as e:
                        c.rollback()
                        with c.cursor() as x:
                            x.execute("UPDATE mm_ai_bulk_runs SET errors=errors+1,last=%s,updated_at=NOW() WHERE job_key=%s",(str(sku)+": "+str(e)[:500],JOB_KEY));c.commit()
                with c.cursor() as x:
                    x.execute("UPDATE mm_ai_bulk_runs SET status='done',finished_at=NOW(),updated_at=NOW() WHERE job_key=%s",(JOB_KEY,));c.commit()
    except Exception as e:
        try:
            with db() as c:
                with c.cursor() as x:x.execute("UPDATE mm_ai_bulk_runs SET status='error',last=%s,updated_at=NOW() WHERE job_key=%s",(str(e)[:700],JOB_KEY));c.commit()
        except Exception: pass

def start_once():
    init_job()
    with db() as c:
        with c.cursor() as x:
            x.execute("SELECT status,updated_at FROM mm_ai_bulk_runs WHERE job_key=%s",(JOB_KEY,))
            row=x.fetchone()
            if row and row[0]=="done": return False
            if row and row[0]=="running": return False
            x.execute("INSERT INTO mm_ai_bulk_runs(job_key,status,started_at,updated_at) VALUES(%s,'running',NOW(),NOW()) ON CONFLICT(job_key) DO UPDATE SET status='running',started_at=NOW(),updated_at=NOW(),finished_at=NULL",(JOB_KEY,));c.commit()
    threading.Thread(target=worker,daemon=True).start()
    return True

def handle_get(query,send_json):
    from urllib.parse import parse_qs
    q=parse_qs(query or "")
    init_job()
    if (q.get("run") or ["0"])[0]=="1":
        started=start_once()
        send_json(200,{"ok":True,"started":started,"message":"Processamento IA RIDA iniciado ou já estava em execução."});return True
    with db() as c:
        with c.cursor() as x:
            x.execute("SELECT status,total,done,errors,last,started_at,finished_at FROM mm_ai_bulk_runs WHERE job_key=%s",(JOB_KEY,));r=x.fetchone()
    send_json(200,{"ok":True,"job":dict(zip(["status","total","done","errors","last","started_at","finished_at"],r or []))});return True

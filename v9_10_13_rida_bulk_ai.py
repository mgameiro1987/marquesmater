import os, json, threading, time, urllib.request, urllib.error
import psycopg

JOB_KEY="rida-content-41-v6"
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

def generate_batch(products):
    key=os.environ.get("OPENAI_API_KEY")
    if not key: raise RuntimeError("OPENAI_API_KEY não configurada")
    model=os.environ.get("OPENAI_MODEL","gpt-5.6-luna")
    contexts=[]
    for p in products:
        attrs=p.get("attributes") or {}
        contexts.append({"sku":p.get("sku"),"name":p.get("name"),"brand":p.get("brand"),"type":p.get("type"),
          "commercial_category":p.get("commercial_category"),"commercial_subcategory":p.get("commercial_subcategory"),
          "rida_category":p.get("rida_category"),"rida_subcategory":p.get("rida_subcategory"),"rida_family":p.get("rida_family"),
          "existing_description":p.get("description") or "","source_attributes":attrs,"source_specs":p.get("specs") or {}})
    instructions=("És o assistente de conteúdos da MarquesMater. Escreve em português de Portugal. "
      "Gera conteúdo profissional para os produtos RIDA abaixo. Usa apenas os dados fornecidos. "
      "NUNCA inventes números, tensões, potências, capacidades, rotações, pesos, dimensões, certificações, autonomia ou outras especificações técnicas. "
      "Se uma especificação não puder ser confirmada pelos dados fornecidos, deixa a lista de especificações vazia. "
      "A descrição deve ser comercial mas factual; características e aplicações devem ser objetivas. "
      "Devolve exatamente um resultado por SKU, mantendo o SKU original.")
    schema={"type":"object","properties":{"items":{"type":"array","items":{"type":"object","properties":{
      "sku":{"type":"string"},"description":{"type":"string"},"characteristics":{"type":"string"},
      "specifications":{"type":"array","items":{"type":"string"}},"applications":{"type":"string"}},
      "required":["sku","description","characteristics","specifications","applications"],"additionalProperties":False}}},
      "required":["items"],"additionalProperties":False}
    payload={"model":model,"store":False,"instructions":instructions,
      "input":[{"role":"user","content":[{"type":"input_text","text":"Dados dos produtos:\n"+json.dumps(contexts,ensure_ascii=False)+"\n\nGera os quatro campos para cada produto."}]}],
      "text":{"format":{"type":"json_schema","name":"marquesmater_rida_bulk_contents","schema":schema,"strict":True}}}
    req=urllib.request.Request("https://api.openai.com/v1/responses",data=json.dumps(payload,ensure_ascii=False).encode(),
      headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=180) as response: data=json.loads(response.read().decode())
    raw=data.get("output_text") or ""
    if not raw:
        for item in data.get("output") or []:
            for part in item.get("content") or []:
                if part.get("type")=="output_text": raw=part.get("text") or ""; break
            if raw: break
    return json.loads(raw or "{}").get("items") or []


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
                  WHERE sku = ANY(%s) ORDER BY id""", [list(GARDEN|CONSTRUCTION|ACCESSORIES|GARDEN_KITS|CONSTRUCTION_KITS)])
                rows=cur.fetchall()
                cur.execute("UPDATE mm_ai_bulk_runs SET total=%s,status='running',started_at=COALESCE(started_at,NOW()),updated_at=NOW() WHERE job_key=%s",(len(rows),JOB_KEY));c.commit()
                pending=[]
                for row in rows:
                    pid,sku,brand,name,typ,desc,img,attrs,specs,barcode=row
                    com,rida=mapping(str(sku))
                    attrs=attrs or {}; specs=specs or {}
                    cur.execute("""UPDATE catalog_products SET category=%s,subcategory=%s,category_id=%s,subcategory_id=%s,family_id=%s,updated_at=NOW() WHERE id=%s""",
                      (com[3] if com else None,com[4] if com else "Acessórios",com[0] if com else None,com[1] if com else None,com[2] if com else None,pid))
                    ensure_classification(cur,pid,"commercial",com);ensure_classification(cur,pid,"rida",rida)
                    needs_ai=(not str(attrs.get("characteristics") or "").strip() or not str(attrs.get("applications") or "").strip() or not isinstance(specs,list) or len(specs)==0)
                    if needs_ai:
                        pending.append({"id":pid,"sku":sku,"brand":brand,"name":name,"type":typ,"description":desc,
                          "attributes":attrs,"specs":specs,"commercial_category":com[3] if com else None,
                          "commercial_subcategory":com[4] if com else None,"rida_category":rida[3] if rida else None,
                          "rida_subcategory":rida[4] if rida else None,"rida_family":rida[5] if rida else None})
                c.commit()
                if pending:
                    results=generate_batch(pending)
                    bysku={str(x.get("sku")):x for x in results}
                    for p in pending:
                        x=bysku.get(str(p["sku"]))
                        if not x: 
                            cur.execute("UPDATE mm_ai_bulk_runs SET errors=errors+1,last=%s,updated_at=NOW() WHERE job_key=%s",("Sem resposta IA para "+str(p["sku"]),JOB_KEY));continue
                        attrs=dict(p["attributes"]);attrs["characteristics"]=str(x.get("characteristics") or "").strip();attrs["applications"]=str(x.get("applications") or "").strip()
                        specs=[str(v).strip() for v in (x.get("specifications") or []) if str(v).strip()]
                        cur.execute("UPDATE catalog_products SET description=%s,specs=%s,attributes=%s,updated_at=NOW() WHERE id=%s",
                          (str(x.get("description") or "").strip(),json.dumps(specs,ensure_ascii=False),json.dumps(attrs,ensure_ascii=False),p["id"]))
                        cur.execute("UPDATE mm_ai_bulk_runs SET done=done+1,last=%s,updated_at=NOW() WHERE job_key=%s",(p["sku"],JOB_KEY))
                        c.commit()
                cur.execute("UPDATE mm_ai_bulk_runs SET status='done',finished_at=NOW(),updated_at=NOW() WHERE job_key=%s",(JOB_KEY,));c.commit()
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

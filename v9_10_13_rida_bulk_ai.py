import os, json, threading, time, urllib.request, urllib.error
import psycopg

JOB_KEY="rida-content-41-v7"
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

def local_content(p):
    name=str(p.get("name") or "Produto RIDA").strip()
    sku=str(p.get("sku") or "").strip()
    cat=str(p.get("commercial_category") or "RIDA").strip()
    lname=name.lower()
    if "berbequim" in lname: use="perfuração e aparafusamento em trabalhos de construção, montagem e manutenção"
    elif "rebarbadora" in lname: use="corte, desbaste e acabamento em trabalhos de construção e oficina"
    elif "martelo perfurador" in lname: use="perfuração e trabalhos de construção"
    elif "serra circular" in lname: use="corte de materiais em trabalhos de construção e montagem"
    elif "tico-tico" in lname: use="corte e recorte de materiais em trabalhos de construção e bricolage"
    elif "serra sabre" in lname: use="corte e desmontagem em trabalhos de construção e manutenção"
    elif "lixadora" in lname: use="lixagem e preparação de superfícies em construção e bricolage"
    elif "pistola de silicone" in lname: use="aplicação de selantes e adesivos em trabalhos de montagem e acabamento"
    elif "luz de trabalho" in lname: use="iluminação de zonas de trabalho e manutenção"
    elif "aparador de relva" in lname: use="corte e acabamento de relvados e manutenção de espaços verdes"
    elif "corta-sebes" in lname: use="manutenção e corte de sebes e arbustos"
    elif "motosserra" in lname: use="corte e manutenção de madeira e vegetação em espaços exteriores"
    elif "tesoura de poda" in lname: use="poda e manutenção de árvores, arbustos e plantas"
    elif "soprador" in lname: use="remoção de folhas e resíduos em jardins e espaços exteriores"
    elif "vara extensível" in lname: use="trabalhos de jardinagem que exijam alcance adicional"
    elif "bateria" in lname: use="alimentação de equipamentos RIDA compatíveis"
    elif "carregador" in lname: use="carregamento de baterias RIDA compatíveis"
    elif "mala" in lname: use="transporte e acondicionamento de equipamento"
    elif "coluna" in lname: use="utilização portátil em espaços de trabalho e lazer"
    else: use="trabalhos gerais de manutenção"
    is_kit="kit " in lname
    desc=(f"{name} RIDA, uma solução destinada a {use}. "
          f"O artigo pertence à gama RIDA e está enquadrado na categoria comercial {cat}. "
          f"A configuração e os dados técnicos específicos devem ser confirmados na ficha do produto.")
    chars="\n".join([
      "• Marca: RIDA",
      f"• Designação: {name}",
      f"• Referência/SKU: {sku}",
      f"• Categoria comercial: {cat}",
      "• Plataforma de equipamento RIDA a bateria" if ("bateria" in lname or is_kit or cat in ("Construção","Jardim & Agricultura")) else "• Acessório para a gama RIDA"
    ])
    apps=f"• {use.capitalize()}\n• Utilização em contexto profissional ou de manutenção, de acordo com o tipo de produto\n• Consultar a ficha do artigo para confirmar a configuração e compatibilidade"
    return {"description":desc,"characteristics":chars,"specifications":[],"applications":apps}

def worker():
    try:
        with db() as c:
            with c.cursor() as cur:
                cur.execute("""SELECT id,sku,brand,name,type,description,image,attributes,specs,barcode FROM catalog_products
                  WHERE sku = ANY(%s) ORDER BY id""", [list(GARDEN|CONSTRUCTION|ACCESSORIES|GARDEN_KITS|CONSTRUCTION_KITS)])
                rows=cur.fetchall()
                cur.execute("UPDATE mm_ai_bulk_runs SET total=%s,status='running',started_at=COALESCE(started_at,NOW()),updated_at=NOW() WHERE job_key=%s",(len(rows),JOB_KEY));c.commit()
                for row in rows:
                    pid,sku,brand,name,typ,desc,img,attrs,specs,barcode=row
                    try:
                        com,rida=mapping(str(sku))
                        attrs=attrs or {};specs=specs or []
                        cur.execute("""UPDATE catalog_products SET category=%s,subcategory=%s,category_id=%s,subcategory_id=%s,family_id=%s,updated_at=NOW() WHERE id=%s""",
                          (com[3] if com else None,com[4] if com else "Acessórios",com[0] if com else None,com[1] if com else None,com[2] if com else None,pid))
                        ensure_classification(cur,pid,"commercial",com);ensure_classification(cur,pid,"rida",rida)
                        if not str(attrs.get("characteristics") or "").strip() or not str(attrs.get("applications") or "").strip() or not isinstance(specs,list) or len(specs)==0:
                            x=local_content({"sku":sku,"name":name,"commercial_category":com[3] if com else None})
                            attrs["characteristics"]=x["characteristics"];attrs["applications"]=x["applications"]
                            # Não inventar especificações técnicas: só gravamos lista vazia quando não há dados confirmados.
                            cur.execute("""UPDATE catalog_products SET description=%s,specs=%s,attributes=%s,updated_at=NOW() WHERE id=%s""",
                              (x["description"],json.dumps(x["specifications"],ensure_ascii=False),json.dumps(attrs,ensure_ascii=False),pid))
                        c.commit()
                        cur.execute("UPDATE mm_ai_bulk_runs SET done=done+1,last=%s,updated_at=NOW() WHERE job_key=%s",(sku,JOB_KEY));c.commit()
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

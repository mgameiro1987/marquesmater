# MarquesMater — enriquecimento RIDA a partir da estrutura/preços do Excel V37.
# Idempotente: atualiza apenas dados de catálogo; NÃO altera stock nem imagens.
import os, psycopg

CATEGORY_ID=10
SUBCATEGORY_ID=99
BRAND_ID=1
VAT=23
RIDA_PRODUCTS = [
  {"sku":"RHD01075-B22","name":"Kit Berbequim 75N","price":116.18,"cost":47.23,"family":"Construção","familyId":1,"type":"kit"},
  {"sku":"RCG07115-B24","name":"Kit Rebarbadora 115","price":159.78,"cost":64.95,"family":"Construção","familyId":1,"type":"kit"},
  {"sku":"RCG07125-B24","name":"Kit Rebarbadora 125","price":161.63,"cost":65.70,"family":"Construção","familyId":1,"type":"kit"},
  {"sku":"RCH072D6-B24","name":"Kit Martelo perfurador D6","price":229.92,"cost":93.46,"family":"Construção","familyId":1,"type":"kit"},
  {"sku":"RCC00190-C14","name":"Kit Serra circular 190","price":172.46,"cost":70.11,"family":"Construção","familyId":1,"type":"kit"},
  {"sku":"RCC08150-C14","name":"Kit Serra circular 150","price":132.68,"cost":53.93,"family":"Construção","familyId":1,"type":"kit"},
  {"sku":"RCJ08025-C22","name":"Kit Serra tico-tico 25","price":133.74,"cost":54.37,"family":"Construção","familyId":1,"type":"kit"},
  {"sku":"RCO11125-C12","name":"Kit Lixadora 125","price":85.83,"cost":34.89,"family":"Construção","familyId":1,"type":"kit"},
  {"sku":"RCO13150-C12","name":"Kit Lixadora 150","price":67.88,"cost":27.60,"family":"Construção","familyId":1,"type":"kit"},
  {"sku":"RCL1250H-C12","name":"Kit Luz de trabalho 1250H","price":75.67,"cost":30.76,"family":"Construção","familyId":1,"type":"kit"},
  {"sku":"RGT11280-C12","name":"Kit Aparador de relva 280","price":88.37,"cost":35.92,"family":"Jardim","familyId":2,"type":"kit"},
  {"sku":"RHT09025-C12","name":"Kit Corta-sebes 25","price":124.17,"cost":50.48,"family":"Jardim","familyId":2,"type":"kit"},
  {"sku":"RCS03V016-C24","name":"Kit Motosserra V016","price":237.98,"cost":96.74,"family":"Jardim","familyId":2,"type":"kit"},
  {"sku":"RCS06006-C12","name":"Kit Motosserra 06006","price":89.00,"cost":36.18,"family":"Jardim","familyId":2,"type":"kit"},
  {"sku":"RBP01040-C12","name":"Kit Tesoura de poda 40","price":125.26,"cost":50.92,"family":"Jardim","familyId":2,"type":"kit"},
  {"sku":"RBL06650-C22","name":"Kit Soprador 650","price":105.19,"cost":42.76,"family":"Jardim","familyId":2,"type":"kit"},
  {"sku":"RCR11022","name":"Serra sabre a bateria","price":89.90,"cost":21.07,"family":"Construção","familyId":1,"type":"máquina"},
  {"sku":"RGG11310","name":"Pistola de silicone a bateria","price":99.90,"cost":36.06,"family":"Construção","familyId":1,"type":"máquina"},
  {"sku":"RJR12000","name":"Coluna portátil a bateria","price":89.90,"cost":27.08,"family":"Construção","familyId":1,"type":"máquina"},
  {"sku":"REP16245","name":"Vara extensível","price":59.90,"cost":17.86,"family":"Construção","familyId":1,"type":"máquina"},
  {"sku":"RHD01075","name":"Berbequim a bateria","price":89.90,"cost":20.67,"family":"Construção","familyId":1,"type":"máquina"},
  {"sku":"RCG07115","name":"Rebarbadora a bateria","price":99.90,"cost":24.82,"family":"Construção","familyId":1,"type":"máquina"},
  {"sku":"RCG07125","name":"Rebarbadora a bateria","price":99.90,"cost":25.57,"family":"Construção","familyId":1,"type":"máquina"},
  {"sku":"RCH072D6","name":"Martelo perfurador a bateria","price":169.90,"cost":53.33,"family":"Construção","familyId":1,"type":"máquina"},
  {"sku":"RCC00190","name":"Serra circular a bateria","price":149.90,"cost":47.48,"family":"Construção","familyId":1,"type":"máquina"},
  {"sku":"RCC08150","name":"Serra circular a bateria","price":99.90,"cost":31.30,"family":"Construção","familyId":1,"type":"máquina"},
  {"sku":"RCJ08025","name":"Serra tico-tico a bateria","price":89.90,"cost":28.67,"family":"Construção","familyId":1,"type":"máquina"},
  {"sku":"RCO11125","name":"Lixadora a bateria","price":69.90,"cost":19.04,"family":"Construção","familyId":1,"type":"máquina"},
  {"sku":"RCO13150","name":"Lixadora a bateria","price":49.90,"cost":11.75,"family":"Construção","familyId":1,"type":"máquina"},
  {"sku":"RCL1250H","name":"Luz de trabalho a bateria","price":49.90,"cost":14.92,"family":"Construção","familyId":1,"type":"máquina"},
  {"sku":"RGT11280","name":"Aparador de relva a bateria","price":64.90,"cost":20.08,"family":"Jardim","familyId":2,"type":"máquina"},
  {"sku":"RHT09025","name":"Corta-sebes a bateria","price":99.90,"cost":34.63,"family":"Jardim","familyId":2,"type":"máquina"},
  {"sku":"RCS03V016","name":"Motosserra a bateria","price":149.90,"cost":50.51,"family":"Jardim","familyId":2,"type":"máquina"},
  {"sku":"RCS06006","name":"Motosserra a bateria","price":69.90,"cost":20.34,"family":"Jardim","familyId":2,"type":"máquina"},
  {"sku":"RBP01040","name":"Tesoura de poda a bateria","price":89.90,"cost":35.08,"family":"Jardim","familyId":2,"type":"máquina"},
  {"sku":"RBL06650","name":"Soprador a bateria","price":99.90,"cost":26.92,"family":"Jardim","familyId":2,"type":"máquina"},
  {"sku":"RB2020","name":"Bateria 2Ah","price":19.90,"cost":9.85,"family":"Acessórios","familyId":3,"type":"acessório"},
  {"sku":"RB2040","name":"Bateria 4Ah","price":34.90,"cost":16.64,"family":"Acessórios","familyId":3,"type":"acessório"},
  {"sku":"RFC24","name":"Carregador simples","price":21.90,"cost":5.99,"family":"Acessórios","familyId":3,"type":"acessório"},
  {"sku":"RDC30","name":"Carregador duplo","price":34.90,"cost":12.96,"family":"Acessórios","familyId":3,"type":"acessório"},
  {"sku":"BMCB75","name":"Mala BMC — Berbequim 75","price":9.90,"cost":0.87,"family":"Acessórios","familyId":3,"type":"acessório"}
]

def enrich_existing():
    url=os.environ.get("DATABASE_URL")
    if not url:
        return {"ok":False,"updated":0,"error":"DATABASE_URL não configurado"}
    updated=0
    with psycopg.connect(url) as conn, conn.cursor() as cur:
        for p in RIDA_PRODUCTS:
            cur.execute(
                "UPDATE catalog_products SET brand='RIDA', name=%s, category='RIDA', "
                "subcategory='Máquinas a bateria', type=%s, price=%s, category_id=%s, "
                "subcategory_id=%s, family_id=%s, brand_id=%s, "
                "attributes=jsonb_build_object('family',%s,'cost',%s,'vatRate',%s) "
                "|| COALESCE(attributes,'{}'::jsonb), updated_at=NOW() WHERE sku=%s",
                (p["name"],p["type"],p["price"],CATEGORY_ID,SUBCATEGORY_ID,p["familyId"],BRAND_ID,
                 p["family"],p["cost"],VAT,p["sku"])
            )
            updated += cur.rowcount
        conn.commit()
    return {"ok":True,"updated":updated,"total":len(RIDA_PRODUCTS)}

def enrich_row(row):
    sku=str(row.get("sku") or "").strip()
    p=next((x for x in RIDA_PRODUCTS if x["sku"]==sku),None)
    if not p:
        return row
    out=dict(row)
    out.update({
        "brand":"RIDA","name":p["name"],"category":"RIDA",
        "subcategory":"Máquinas a bateria","family":p["family"],"type":p["type"],
        "price":p["price"],"vatRate":VAT,"cost":p["cost"],
        "categoryId":CATEGORY_ID,"subcategoryId":SUBCATEGORY_ID,
        "familyId":p["familyId"],"brandId":BRAND_ID
    })
    return out

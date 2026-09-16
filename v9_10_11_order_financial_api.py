import os, json
import psycopg

def _db():
    url=os.environ.get('DATABASE_URL')
    if not url: raise RuntimeError('DATABASE_URL não configurado no Render')
    return psycopg.connect(url)

def _financial(data):
    data=data or {}; items=data.get('items') or []; item_subtotal=0.0
    for i in items:
        try: item_subtotal += max(0.0,float(str(i.get('price',0)).replace(',','.'))) * max(1,int(i.get('qty',i.get('quantity',1)) or 1))
        except Exception: pass
    item_subtotal=round(item_subtotal,2)
    m=data.get('marketing') or {}
    subtotal=round(float(m.get('subtotal',data.get('subtotal',item_subtotal)) or item_subtotal),2)
    if subtotal<=0: subtotal=item_subtotal
    coupon=m.get('coupon'); coupon_discount=round(float(m.get('couponDiscount',0) or 0),2)
    promotion_discount=round(float(m.get('promotionDiscount',0) or 0),2)
    discount=round(float(m.get('discount',coupon_discount+promotion_discount) or 0),2)
    delivery_cost=round(float(m.get('deliveryCost',data.get('deliveryCost',4.90 if data.get('delivery')=='Entrega em Portugal Continental' else 0)) or 0),2)
    calculated=round(max(0,subtotal-discount)+delivery_cost,2)
    stored=round(float(data.get('total') or 0),2)
    if stored==delivery_cost and subtotal>0: stored=calculated
    return {'subtotal':subtotal,'coupon':coupon,'couponDiscount':coupon_discount,'promotionDiscount':promotion_discount,'discount':discount,'promotions':m.get('promotions') or [],'deliveryCost':delivery_cost,'total':stored if stored>0 else calculated}

def handle_get(order_id,send_json):
    try: oid=int(order_id)
    except Exception: send_json(400,{'ok':False,'error':'Encomenda inválida'}); return True
    try:
        with _db() as conn, conn.cursor() as cur:
            cur.execute('SELECT data FROM orders WHERE id=%s',(oid,)); row=cur.fetchone()
            if not row: send_json(404,{'ok':False,'error':'Encomenda não encontrada'}); return True
            f=_financial(row[0] or {})
            send_json(200,{'ok':True,'financial':f}); return True
    except Exception as e:
        send_json(503,{'ok':False,'error':str(e)}); return True

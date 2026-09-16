import os, json
import psycopg

def _db():
    url=os.environ.get('DATABASE_URL')
    if not url: raise RuntimeError('DATABASE_URL não configurado no Render')
    return psycopg.connect(url)

def _financials(data):
    data = data or {}
    items = data.get('items') or []
    item_subtotal = 0.0
    for item in items:
        try:
            qty = max(1, int(item.get('qty', item.get('quantity', 1)) or 1))
            price = max(0.0, float(str(item.get('price', 0)).replace(',', '.')))
            item_subtotal += price * qty
        except Exception:
            pass
    item_subtotal = round(item_subtotal, 2)
    marketing = data.get('marketing') or {}
    subtotal = round(float(marketing.get('subtotal', data.get('subtotal', item_subtotal)) or item_subtotal), 2)
    if subtotal <= 0 and item_subtotal > 0:
        subtotal = item_subtotal
    coupon_discount = round(float(marketing.get('couponDiscount', 0) or 0), 2)
    promotion_discount = round(float(marketing.get('promotionDiscount', 0) or 0), 2)
    discount = round(float(marketing.get('discount', coupon_discount + promotion_discount) or 0), 2)
    delivery_cost = float(marketing.get('deliveryCost', data.get('deliveryCost', 4.90 if data.get('delivery') == 'Entrega em Portugal Continental' else 0)) or 0)
    delivery_cost = round(delivery_cost, 2)
    calculated = round(max(0.0, subtotal - discount) + delivery_cost, 2)
    stored_total = round(float(data.get('total') or 0), 2)
    # Corrige também encomendas antigas que tenham ficado apenas com os portes como total.
    if stored_total == delivery_cost and subtotal > 0:
        stored_total = calculated
    total = stored_total if stored_total > 0 else calculated
    return {
        'subtotal': subtotal,
        'coupon': marketing.get('coupon'),
        'couponDiscount': coupon_discount,
        'promotionDiscount': promotion_discount,
        'discount': discount,
        'promotions': marketing.get('promotions') or [],
        'deliveryCost': delivery_cost,
        'total': total
    }

def handle_get(email, send_json):
    email=str(email or '').strip().lower()
    if not email:
        send_json(400,{'ok':False,'error':'Email do cliente em falta'}); return True
    try:
        with _db() as conn, conn.cursor() as cur:
            cur.execute("""SELECT o.id,o.created_at,o.data,c.name,c.email,c.phone
                         FROM orders o
                         LEFT JOIN customers c ON c.id=o.customer_id
                         WHERE COALESCE(NULLIF(o.data->>'total','')::numeric,0)>0
                           AND (LOWER(COALESCE(c.email,''))=LOWER(%s)
                                OR LOWER(COALESCE(o.data->'customer'->>'email',''))=LOWER(%s))
                         ORDER BY o.created_at DESC,o.id DESC""",(email,email))
            out=[]
            for r in cur.fetchall():
                d=r[2] or {}; cust=d.get('customer') or {}; f=_financials(d)
                out.append({'id':r[0],'created_at':r[1],'order_number':d.get('number') or f'MM-{r[0]}','status':d.get('status') or 'Pendente','total':f['total'],'subtotal':f['subtotal'],'coupon':f['coupon'],'couponDiscount':f['couponDiscount'],'promotionDiscount':f['promotionDiscount'],'discount':f['discount'],'promotions':f['promotions'],'deliveryCost':f['deliveryCost'],'customer':cust,'customer_name':r[3] or cust.get('name',''),'customer_email':r[4] or cust.get('email',''),'customer_phone':r[5] or cust.get('phone',''),'delivery':d.get('delivery',''),'payment':d.get('payment',''),'items':d.get('items') or []})
            send_json(200,{'ok':True,'items':out,'count':len(out)}); return True
    except Exception as e:
        send_json(503,{'ok':False,'error':f'API V9.6: {e}'}); return True

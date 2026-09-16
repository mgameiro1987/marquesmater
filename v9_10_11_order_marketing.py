import json
import psycopg


def _db():
    import os
    url=os.environ.get('DATABASE_URL')
    if not url: raise RuntimeError('DATABASE_URL não configurado no Render')
    return psycopg.connect(url)


def create_order(body, send_json):
    from v9_10_11_marketing_api import calculate, ensure as ensure_marketing, consume_coupon
    items=body.get('items') or []
    if not isinstance(items,list) or not items: raise ValueError('A encomenda tem de conter pelo menos um artigo.')
    try: subtotal=round(float(body.get('subtotal') or 0),2)
    except Exception: raise ValueError('Subtotal inválido.')
    if subtotal<=0: raise ValueError('O subtotal tem de ser superior a 0 €.')
    delivery=str(body.get('delivery') or '')
    delivery_cost=4.90 if delivery=='Entrega em Portugal Continental' else 0.0
    with _db() as conn, conn.cursor() as cur:
        ensure_marketing()
        result=calculate(cur,body.get('couponCode'),subtotal,items)
        final_total=round(max(0.0,result['totalAfterDiscount'])+delivery_cost,2)
    if final_total<=0: raise ValueError('Uma encomenda não pode ter custo zero ou negativo.')
    clean_body=dict(body)
    clean_body['total']=final_total
    captured={}
    def capture(status,payload):
        captured['status']=status;captured['payload']=payload
        return send_json(status,payload)
    from v96_api import handle_post
    handled=handle_post('/api/orders',clean_body,capture)
    if not handled: raise RuntimeError('Não foi possível registar a encomenda.')
    if captured.get('status')==201 and captured.get('payload',{}).get('ok'):
        order=captured['payload'].get('order') or {}
        oid=order.get('id')
        if oid:
            with _db() as conn, conn.cursor() as cur:
                marketing={'coupon':result.get('coupon'),'couponDiscount':result.get('couponDiscount',0),'promotionDiscount':result.get('promotionDiscount',0),'discount':result.get('discount',0),'promotions':result.get('promotions',[]),'subtotal':result.get('subtotal',0)}
                cur.execute('SELECT data FROM orders WHERE id=%s FOR UPDATE',(int(oid),)); row=cur.fetchone()
                if row:
                    data=row[0] or {}; data['marketing']=marketing
                    cur.execute('UPDATE orders SET data=%s::jsonb WHERE id=%s',(json.dumps(data,ensure_ascii=False),int(oid)))
                if result.get('coupon'): consume_coupon(cur,result['coupon'])
                conn.commit()
    return True

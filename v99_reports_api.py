import os
import psycopg
from urllib.parse import parse_qs

def db():
    url=os.environ.get('DATABASE_URL')
    if not url: raise RuntimeError('DATABASE_URL não configurado no Render')
    return psycopg.connect(url)

def money(v):
    try: return round(float(v or 0),2)
    except Exception: return 0.0

def handle_get(path,query,send_json):
    if path!='/api/reports/sales': return False
    try:
        q=parse_qs(query or '')
        start=(q.get('start') or [''])[0].strip()
        end=(q.get('end') or [''])[0].strip()
        where="COALESCE(NULLIF(o.data->>'total','')::numeric,0)>0"
        args=[]
        if start:
            where += " AND o.created_at >= %s::date"
            args.append(start)
        if end:
            where += " AND o.created_at < (%s::date + INTERVAL '1 day')"
            args.append(end)
        with db() as conn,conn.cursor() as cur:
            cur.execute(f"SELECT o.id,o.created_at,o.data,c.name,c.email FROM orders o LEFT JOIN customers c ON c.id=o.customer_id WHERE {where} ORDER BY o.created_at DESC,o.id DESC",args)
            rows=cur.fetchall()
            total=0; count=0; cancelled=0; status_counts={}; products={}; categories={}; brands={}; customers={}
            for oid,created,data,cname,cemail in rows:
                d=data or {}; status=str(d.get('status') or 'Pendente'); value=money(d.get('total'))
                status_counts[status]=status_counts.get(status,0)+1
                if status.lower()=='cancelada': cancelled+=1
                else: total+=value
                count+=1
                email=(cemail or (d.get('customer') or {}).get('email') or '').lower()
                cname=cname or (d.get('customer') or {}).get('name') or 'Cliente'
                if status.lower()!='cancelada': customers[email or cname]=customers.get(email or cname,{'name':cname,'email':email,'orders':0,'spent':0});customers[email or cname]['orders']+=1;customers[email or cname]['spent']+=value
                for it in (d.get('items') or []):
                    sku=str(it.get('sku') or '').strip(); name=str(it.get('name') or it.get('productName') or sku or 'Artigo'); qty=int(it.get('qty',it.get('quantity',0)) or 0); price=money(it.get('price'))
                    key=sku or name
                    p=products.setdefault(key,{'sku':sku,'name':name,'qty':0,'sales':0});p['qty']+=qty;p['sales']+=price*qty
                    brand=str(it.get('brand') or '').strip() or 'Sem marca';brands.setdefault(brand,{'name':brand,'qty':0,'sales':0});brands[brand]['qty']+=qty;brands[brand]['sales']+=price*qty
                    cat=str(it.get('category') or '').strip() or 'Sem categoria';categories.setdefault(cat,{'name':cat,'qty':0,'sales':0});categories[cat]['qty']+=qty;categories[cat]['sales']+=price*qty
            active_count=count-cancelled
            avg=total/active_count if active_count else 0
            top_products=sorted(products.values(),key=lambda x:(x['sales'],x['qty']),reverse=True)[:10]
            top_customers=sorted(customers.values(),key=lambda x:x['spent'],reverse=True)[:10]
            top_categories=sorted(categories.values(),key=lambda x:x['sales'],reverse=True)[:10]
            top_brands=sorted(brands.values(),key=lambda x:x['sales'],reverse=True)[:10]
            for arr in (top_products,top_customers,top_categories,top_brands):
                for x in arr:
                    for k in ('sales','spent'): 
                        if k in x:x[k]=money(x[k])
            send_json(200,{'ok':True,'period':{'start':start,'end':end},'summary':{'orders':count,'activeOrders':active_count,'cancelledOrders':cancelled,'sales':money(total),'averageOrder':money(avg)},'status':status_counts,'topProducts':top_products,'topCustomers':top_customers,'topCategories':top_categories,'topBrands':top_brands})
            return True
    except Exception as e:
        send_json(503,{'ok':False,'error':f'API relatórios: {e}'});return True

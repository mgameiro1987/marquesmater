import json, os, time, threading
from urllib.parse import urlsplit, parse_qs
try:
    import psycopg
except Exception:
    psycopg=None

SCHEMA='''
CREATE TABLE IF NOT EXISTS chat_agents (id BIGSERIAL PRIMARY KEY,name TEXT NOT NULL,email TEXT NOT NULL UNIQUE,role TEXT NOT NULL DEFAULT 'atendimento',active BOOLEAN NOT NULL DEFAULT TRUE,created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),last_seen TIMESTAMPTZ);
CREATE TABLE IF NOT EXISTS chat_conversations (id BIGSERIAL PRIMARY KEY,visitor_id TEXT NOT NULL,customer_id BIGINT REFERENCES customers(id) ON DELETE SET NULL,name TEXT NOT NULL DEFAULT 'Visitante',email TEXT NOT NULL DEFAULT '',phone TEXT NOT NULL DEFAULT '',status TEXT NOT NULL DEFAULT 'new' CHECK(status IN ('new','active','waiting','resolved')),assigned_agent_id BIGINT REFERENCES chat_agents(id) ON DELETE SET NULL,subject TEXT NOT NULL DEFAULT '',page_url TEXT NOT NULL DEFAULT '',product_sku TEXT NOT NULL DEFAULT '',created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),last_message_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),unread_admin INTEGER NOT NULL DEFAULT 0,unread_customer INTEGER NOT NULL DEFAULT 0);
CREATE INDEX IF NOT EXISTS idx_chat_conv_updated ON chat_conversations(updated_at DESC);CREATE INDEX IF NOT EXISTS idx_chat_conv_visitor ON chat_conversations(visitor_id,updated_at DESC);
CREATE TABLE IF NOT EXISTS chat_messages (id BIGSERIAL PRIMARY KEY,conversation_id BIGINT NOT NULL REFERENCES chat_conversations(id) ON DELETE CASCADE,sender_type TEXT NOT NULL CHECK(sender_type IN ('customer','agent','system')),sender_id BIGINT REFERENCES chat_agents(id) ON DELETE SET NULL,sender_name TEXT NOT NULL DEFAULT '',body TEXT NOT NULL,attachment_url TEXT NOT NULL DEFAULT '',created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),read_at TIMESTAMPTZ);
CREATE INDEX IF NOT EXISTS idx_chat_msg_conv ON chat_messages(conversation_id,id);
CREATE TABLE IF NOT EXISTS chat_notes (id BIGSERIAL PRIMARY KEY,conversation_id BIGINT NOT NULL REFERENCES chat_conversations(id) ON DELETE CASCADE,agent_id BIGINT REFERENCES chat_agents(id) ON DELETE SET NULL,body TEXT NOT NULL,created_at TIMESTAMPTZ NOT NULL DEFAULT NOW());
'''

def conn(): return psycopg.connect(os.environ['DATABASE_URL']) if psycopg and os.environ.get('DATABASE_URL') else None

def init():
    c=conn()
    if not c:return
    try:
        with c:
            with c.cursor() as q:
                q.execute(SCHEMA)
                q.execute("INSERT INTO chat_agents(name,email,role) VALUES(%s,%s,%s) ON CONFLICT(email) DO NOTHING",('Mickael','admin@marquesmater.pt','Administrador'))
    finally:c.close()

def jload(h):
    try:
        n=int(h.headers.get('Content-Length','0'));return json.loads(h.rfile.read(n).decode() or '{}')
    except Exception:return {}

def out(h,status,payload):
    raw=json.dumps(payload,ensure_ascii=False,default=str).encode();h.send_response(status);h.send_header('Content-Type','application/json; charset=utf-8');h.send_header('Cache-Control','no-store');h.send_header('Content-Length',str(len(raw)));h.end_headers();h.wfile.write(raw)

def conv_row(r): return dict(zip(['id','visitor_id','customer_id','name','email','phone','status','assigned_agent_id','assigned_agent','subject','page_url','product_sku','created_at','updated_at','last_message_at','unread_admin','unread_customer'],r))

def messages(c,cid):
    with c.cursor() as q:
        q.execute("SELECT id,sender_type,sender_id,sender_name,body,attachment_url,created_at,read_at FROM chat_messages WHERE conversation_id=%s ORDER BY id",(cid,));return [dict(zip(['id','sender_type','sender_id','sender_name','body','attachment_url','created_at','read_at'],r)) for r in q.fetchall()]

def install(H):
    if getattr(H,'_mm_chat_installed',False):return
    H._mm_chat_installed=True
    try:init()
    except Exception as e:print('Chat schema error:',e)
    old_get,old_post=H.do_GET,H.do_POST
    def get(self):
        path=urlsplit(self.path).path;qs=parse_qs(urlsplit(self.path).query)
        if not path.startswith('/api/chat/'):return old_get(self)
        c=conn()
        if not c:return out(self,503,{'ok':False,'error':'Base de dados indisponível'})
        try:
            with c:
                with c.cursor() as q:
                    if path=='/api/chat/agents':
                        q.execute("SELECT id,name,email,role,active,last_seen FROM chat_agents WHERE active=TRUE ORDER BY id");return out(self,200,{'ok':True,'agents':[dict(zip(['id','name','email','role','active','last_seen'],r)) for r in q.fetchall()]})
                    if path=='/api/chat/conversations':
                        status=qs.get('status',[''])[0];sql="SELECT c.id,c.visitor_id,c.customer_id,c.name,c.email,c.phone,c.status,c.assigned_agent_id,a.name,c.subject,c.page_url,c.product_sku,c.created_at,c.updated_at,c.last_message_at,c.unread_admin,c.unread_customer FROM chat_conversations c LEFT JOIN chat_agents a ON a.id=c.assigned_agent_id";args=()
                        if status in ('new','active','waiting','resolved'):sql+=' WHERE c.status=%s';args=(status,)
                        q.execute(sql+' ORDER BY c.last_message_at DESC',args);rows=[conv_row(r) for r in q.fetchall()]
                        for x in rows:
                            q.execute("SELECT body,created_at,sender_type FROM chat_messages WHERE conversation_id=%s ORDER BY id DESC LIMIT 1",(x['id'],));m=q.fetchone();x['preview']=m[0] if m else '';x['last_message_type']=m[2] if m else None
                        return out(self,200,{'ok':True,'conversations':rows})
                    if path.startswith('/api/chat/conversations/'):
                        cid=int(path.rsplit('/',1)[1]);q.execute("SELECT c.id,c.visitor_id,c.customer_id,c.name,c.email,c.phone,c.status,c.assigned_agent_id,a.name,c.subject,c.page_url,c.product_sku,c.created_at,c.updated_at,c.last_message_at,c.unread_admin,c.unread_customer FROM chat_conversations c LEFT JOIN chat_agents a ON a.id=c.assigned_agent_id WHERE c.id=%s",(cid,));r=q.fetchone()
                        if not r:return out(self,404,{'ok':False,'error':'Conversa não encontrada'})
                        q.execute("UPDATE chat_conversations SET unread_admin=0 WHERE id=%s",(cid,));x=conv_row(r);x['messages']=messages(c,cid);q.execute("SELECT id,agent_id,body,created_at FROM chat_notes WHERE conversation_id=%s ORDER BY id DESC",(cid,));x['notes']=[dict(zip(['id','agent_id','body','created_at'],n)) for n in q.fetchall()];return out(self,200,{'ok':True,'conversation':x})
                    if path=='/api/chat/customer':
                        visitor=str(qs.get('visitor_id',[''])[0]);email=str(qs.get('email',[''])[0]).lower();q.execute("SELECT c.id,c.visitor_id,c.customer_id,c.name,c.email,c.phone,c.status,c.assigned_agent_id,a.name,c.subject,c.page_url,c.product_sku,c.created_at,c.updated_at,c.last_message_at,c.unread_admin,c.unread_customer FROM chat_conversations c LEFT JOIN chat_agents a ON a.id=c.assigned_agent_id WHERE (visitor_id=%s OR (%s<>'' AND email=%s)) AND status<>'resolved' ORDER BY last_message_at DESC LIMIT 1",(visitor,email,email));r=q.fetchone();return out(self,200,{'ok':True,'conversation':conv_row(r) if r else None,'messages':messages(c,r[0]) if r else []})
                    return out(self,404,{'ok':False,'error':'Endpoint não encontrado'})
        except Exception as e:c.rollback();print('Chat GET error:',e);return out(self,500,{'ok':False,'error':'Erro no chat'})
        finally:c.close()
    def post(self):
        path=urlsplit(self.path).path
        # Nunca ler o body de POSTs que pertencem a outros módulos.
        if not path.startswith('/api/chat/'):return old_post(self)
        data=jload(self)
        c=conn()
        if not c:return out(self,503,{'ok':False,'error':'Base de dados indisponível'})
        try:
            with c:
                with c.cursor() as q:
                    if path=='/api/chat/conversations':
                        visitor=str(data.get('visitor_id') or '').strip()
                        if not visitor:return out(self,400,{'ok':False,'error':'visitor_id obrigatório'})
                        name=str(data.get('name') or 'Visitante').strip()[:120];email=str(data.get('email') or '').strip().lower()[:180];phone=str(data.get('phone') or '').strip()[:50]
                        q.execute("SELECT id FROM chat_conversations WHERE visitor_id=%s AND status<>'resolved' ORDER BY last_message_at DESC LIMIT 1",(visitor,));r=q.fetchone()
                        if r:cid=r[0];q.execute("UPDATE chat_conversations SET name=%s,email=%s,phone=%s,page_url=%s,product_sku=%s,updated_at=NOW() WHERE id=%s",(name,email,phone,str(data.get('page_url') or '')[:500],str(data.get('product_sku') or '')[:100],cid))
                        else:q.execute("INSERT INTO chat_conversations(visitor_id,name,email,phone,page_url,product_sku) VALUES(%s,%s,%s,%s,%s,%s) RETURNING id",(visitor,name,email,phone,str(data.get('page_url') or '')[:500],str(data.get('product_sku') or '')[:100]));cid=q.fetchone()[0]
                        msg=str(data.get('message') or '').strip()
                        if msg:q.execute("INSERT INTO chat_messages(conversation_id,sender_type,sender_name,body) VALUES(%s,'customer',%s,%s)",(cid,name,msg));q.execute("UPDATE chat_conversations SET unread_admin=unread_admin+1,last_message_at=NOW(),updated_at=NOW() WHERE id=%s",(cid,))
                        return out(self,200,{'ok':True,'conversation_id':cid})
                    if path=='/api/chat/messages':
                        cid=int(data.get('conversation_id') or 0);body=str(data.get('body') or '').strip();typ=str(data.get('sender_type') or 'customer');
                        if not cid or not body or typ not in ('customer','agent'):return out(self,400,{'ok':False,'error':'Dados da mensagem inválidos'})
                        aid=int(data.get('agent_id') or 0) if typ=='agent' else None;name=str(data.get('sender_name') or ('Mickael' if typ=='agent' else 'Cliente'))[:120]
                        q.execute("SELECT id FROM chat_conversations WHERE id=%s",(cid,));
                        if not q.fetchone():return out(self,404,{'ok':False,'error':'Conversa não encontrada'})
                        q.execute("INSERT INTO chat_messages(conversation_id,sender_type,sender_id,sender_name,body) VALUES(%s,%s,%s,%s,%s) RETURNING id,created_at",(cid,typ,aid,name,body));mid,created=q.fetchone()
                        if typ=='agent':q.execute("UPDATE chat_conversations SET status='active',unread_customer=unread_customer+1,last_message_at=NOW(),updated_at=NOW() WHERE id=%s",(cid,))
                        else:q.execute("UPDATE chat_conversations SET unread_admin=unread_admin+1,last_message_at=NOW(),updated_at=NOW(),status=CASE WHEN status='waiting' THEN 'active' ELSE status END WHERE id=%s",(cid,))
                        return out(self,200,{'ok':True,'message':{'id':mid,'created_at':created}})
                    if path=='/api/chat/assign':
                        cid=int(data.get('conversation_id') or 0);aid=int(data.get('agent_id') or 0);q.execute("UPDATE chat_conversations SET assigned_agent_id=%s,status=CASE WHEN status='new' THEN 'active' ELSE status END,updated_at=NOW() WHERE id=%s RETURNING id",(aid or None,cid));r=q.fetchone();return out(self,200 if r else 404,{'ok':bool(r)})
                    if path=='/api/chat/status':
                        cid=int(data.get('conversation_id') or 0);status=str(data.get('status') or '')
                        if status not in ('new','active','waiting','resolved'):return out(self,400,{'ok':False})
                        q.execute("UPDATE chat_conversations SET status=%s,updated_at=NOW() WHERE id=%s RETURNING id",(status,cid));r=q.fetchone();return out(self,200 if r else 404,{'ok':bool(r)})
                    if path=='/api/chat/notes':
                        cid=int(data.get('conversation_id') or 0);body=str(data.get('body') or '').strip();aid=int(data.get('agent_id') or 0) or None
                        if not cid or not body:return out(self,400,{'ok':False})
                        q.execute("INSERT INTO chat_notes(conversation_id,agent_id,body) VALUES(%s,%s,%s) RETURNING id",(cid,aid,body));return out(self,200,{'ok':True})
                    return out(self,404,{'ok':False,'error':'Endpoint não encontrado'})
        except Exception as e:c.rollback();print('Chat POST error:',e);return out(self,500,{'ok':False,'error':'Erro no chat'})
        finally:c.close()
    H.do_GET=get;H.do_POST=post

def install_later():
    def loop():
        for _ in range(200):
            H=getattr(__import__('__main__'),'Handler',None)
            if H:install(H);return
            time.sleep(.05)
    threading.Thread(target=loop,daemon=True).start()
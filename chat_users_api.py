import json, os, time, threading
from urllib.parse import urlsplit
try:
    import psycopg
except Exception:
    psycopg=None

def conn(): return psycopg.connect(os.environ['DATABASE_URL']) if psycopg and os.environ.get('DATABASE_URL') else None

def out(h,status,payload):
    raw=json.dumps(payload,ensure_ascii=False,default=str).encode();h.send_response(status);h.send_header('Content-Type','application/json; charset=utf-8');h.send_header('Cache-Control','no-store');h.send_header('Content-Length',str(len(raw)));h.end_headers();h.wfile.write(raw)

def body(h):
    try:
        n=int(h.headers.get('Content-Length','0'));return json.loads(h.rfile.read(n).decode() or '{}')
    except Exception:return {}

def install(H):
    if getattr(H,'_mm_users_installed',False): return
    H._mm_users_installed=True
    old_get,old_post=H.do_GET,H.do_POST
    def get(self):
        path=urlsplit(self.path).path
        if path!='/api/admin/users': return old_get(self)
        c=conn()
        if not c:return out(self,503,{'ok':False,'error':'Base de dados indisponível'})
        try:
            with c:
                with c.cursor() as q:
                    q.execute("SELECT id,name,email,role,active,last_seen FROM chat_agents ORDER BY name")
                    users=[dict(zip(['id','name','email','role','active','last_seen'],r)) for r in q.fetchall()]
            return out(self,200,{'ok':True,'users':users})
        except Exception as e:
            return out(self,500,{'ok':False,'error':'Erro ao ler utilizadores'})
        finally:c.close()
    def post(self):
        path=urlsplit(self.path).path
        # Nunca ler o body de POSTs que pertencem a outros módulos.
        if path not in ('/api/admin/users','/api/admin/users/status','/api/admin/users/presence'): return old_post(self)
        data=body(self)
        c=conn()
        if not c:return out(self,503,{'ok':False,'error':'Base de dados indisponível'})
        try:
            with c:
                with c.cursor() as q:
                    if path=='/api/admin/users':
                        name=str(data.get('name') or '').strip()[:120];email=str(data.get('email') or '').strip().lower()[:180];role=str(data.get('role') or 'atendimento')
                        if not name or not email:return out(self,400,{'ok':False,'error':'Nome e email são obrigatórios'})
                        if role not in ('admin','gestor','atendimento','vendas'):role='atendimento'
                        active=bool(data.get('active',True))
                        if data.get('id'):
                            q.execute("UPDATE chat_agents SET name=%s,email=%s,role=%s,active=%s WHERE id=%s RETURNING id",(name,email,role,active,int(data['id'])))
                        else:
                            q.execute("INSERT INTO chat_agents(name,email,role,active) VALUES(%s,%s,%s,%s) ON CONFLICT(email) DO UPDATE SET name=EXCLUDED.name,role=EXCLUDED.role,active=EXCLUDED.active RETURNING id",(name,email,role,active))
                        return out(self,200,{'ok':True,'id':int(q.fetchone()[0])})
                    if path=='/api/admin/users/status':
                        q.execute('UPDATE chat_agents SET active=%s WHERE id=%s',(bool(data.get('active',True)),int(data.get('id'))));return out(self,200,{'ok':True})
                    q.execute('UPDATE chat_agents SET last_seen=CASE WHEN %s THEN NOW() ELSE last_seen END WHERE id=%s',(bool(data.get('online',False)),int(data.get('id'))));return out(self,200,{'ok':True})
        except Exception as e:
            c.rollback();return out(self,500,{'ok':False,'error':'Erro ao guardar utilizador'})
        finally:c.close()
    H.do_GET=get;H.do_POST=post

def install_later():
    def loop():
        for _ in range(200):
            H=getattr(__import__('__main__'),'Handler',None)
            if H:install(H);return
            time.sleep(.05)
    threading.Thread(target=loop,daemon=True).start()
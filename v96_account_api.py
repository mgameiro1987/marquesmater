import os, json, hashlib, secrets
import psycopg


def _db():
    url=os.environ.get('DATABASE_URL')
    if not url: raise RuntimeError('DATABASE_URL não configurado no Render')
    return psycopg.connect(url)


def _ensure():
    with _db() as conn, conn.cursor() as cur:
        cur.execute("""CREATE TABLE IF NOT EXISTS mm_customer_accounts (
            id BIGSERIAL PRIMARY KEY,
            customer_id BIGINT NOT NULL UNIQUE REFERENCES customers(id) ON DELETE CASCADE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            session_token_hash TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )""")
        cur.execute("CREATE INDEX IF NOT EXISTS mm_customer_accounts_token_idx ON mm_customer_accounts(session_token_hash)")
        conn.commit()


def _hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 210000).hex()
    return f'pbkdf2_sha256$210000${salt}${digest}'


def _verify(password, stored):
    try:
        alg, rounds, salt, digest = stored.split('$', 3)
        if alg != 'pbkdf2_sha256': return False
        check = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), int(rounds)).hex()
        return secrets.compare_digest(check, digest)
    except Exception:
        return False


def _customer(cur, cid):
    cur.execute("SELECT id,name,email,phone FROM customers WHERE id=%s", (cid,))
    r=cur.fetchone()
    return {'id':r[0],'name':r[1] or '','email':r[2] or '','phone':r[3] or ''} if r else None


def _response_account(cur, cid, token):
    c=_customer(cur,cid)
    return {'id':cid,'name':c['name'],'email':c['email'],'phone':c['phone'],'token':token}


def handle_post(path, body, send_json):
    if path not in ('/api/account/register','/api/account/login','/api/account/logout'):
        return False
    try:
        _ensure()
        if path=='/api/account/logout':
            token=str(body.get('token') or '').strip()
            if token:
                with _db() as conn, conn.cursor() as cur:
                    cur.execute('UPDATE mm_customer_accounts SET session_token_hash=NULL,updated_at=NOW() WHERE session_token_hash=%s',(hashlib.sha256(token.encode()).hexdigest(),))
                    conn.commit()
            send_json(200,{'ok':True}); return True
        email=str(body.get('email') or '').strip().lower()
        password=str(body.get('password') or '')
        if not email or '@' not in email: raise ValueError('Indica um email válido.')
        if len(password)<8: raise ValueError('A palavra-passe deve ter pelo menos 8 caracteres.')
        with _db() as conn, conn.cursor() as cur:
            if path=='/api/account/register':
                name=str(body.get('name') or '').strip()
                phone=str(body.get('phone') or '').strip()
                if not name: raise ValueError('Indica o nome completo.')
                cur.execute('SELECT id FROM mm_customer_accounts WHERE LOWER(email)=LOWER(%s)',(email,))
                if cur.fetchone(): raise ValueError('Já existe uma conta com este email. Entra na tua conta.')
                cur.execute('SELECT id FROM customers WHERE LOWER(email)=LOWER(%s) ORDER BY id LIMIT 1',(email,)); row=cur.fetchone()
                if row:
                    cid=int(row[0]); cur.execute('UPDATE customers SET name=%s,phone=%s,updated_at=NOW() WHERE id=%s',(name,phone,cid))
                else:
                    cur.execute('INSERT INTO customers(email,name,phone) VALUES(%s,%s,%s) RETURNING id',(email,name,phone)); cid=int(cur.fetchone()[0])
                token=secrets.token_urlsafe(32)
                cur.execute('INSERT INTO mm_customer_accounts(customer_id,email,password_hash,session_token_hash) VALUES(%s,%s,%s,%s)',(cid,email,_hash_password(password),hashlib.sha256(token.encode()).hexdigest()))
                conn.commit()
                send_json(201,{'ok':True,'account':_response_account(cur,cid,token)}); return True
            cur.execute('SELECT customer_id,password_hash FROM mm_customer_accounts WHERE LOWER(email)=LOWER(%s)',(email,)); row=cur.fetchone()
            if not row or not _verify(password,row[1]):
                send_json(401,{'ok':False,'error':'Email ou palavra-passe incorretos.'}); return True
            cid=int(row[0]); token=secrets.token_urlsafe(32)
            cur.execute('UPDATE mm_customer_accounts SET session_token_hash=%s,updated_at=NOW() WHERE customer_id=%s',(hashlib.sha256(token.encode()).hexdigest(),cid))
            conn.commit()
            send_json(200,{'ok':True,'account':_response_account(cur,cid,token)}); return True
    except ValueError as e:
        send_json(400,{'ok':False,'error':str(e)}); return True
    except psycopg.errors.UniqueViolation:
        send_json(409,{'ok':False,'error':'Já existe uma conta com este email.'}); return True
    except Exception as e:
        send_json(503,{'ok':False,'error':f'API de conta: {e}'}); return True


def handle_get(path, query, send_json):
    if path!='/api/account/me': return False
    try:
        _ensure(); params={}
        for part in (query or '').split('&'):
            if '=' in part:
                k,v=part.split('=',1); params[k]=v
        token=params.get('token','').strip()
        if not token:
            send_json(401,{'ok':False,'error':'Sessão não iniciada'}); return True
        th=hashlib.sha256(token.encode()).hexdigest()
        with _db() as conn, conn.cursor() as cur:
            cur.execute('SELECT customer_id FROM mm_customer_accounts WHERE session_token_hash=%s',(th,)); row=cur.fetchone()
            if not row:
                send_json(401,{'ok':False,'error':'Sessão expirada'}); return True
            c=_customer(cur,int(row[0]))
            send_json(200,{'ok':True,'account':c}); return True
    except Exception as e:
        send_json(503,{'ok':False,'error':f'API de conta: {e}'}); return True

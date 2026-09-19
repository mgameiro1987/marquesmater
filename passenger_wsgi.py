import os
import sys
import time
import socket
import subprocess
import threading
import http.client
from urllib.parse import urlsplit

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_PORT = 10000 + (os.getpid() % 1000)

_backend = None
_lock = threading.Lock()

def _start_backend():
    global _backend
    with _lock:
        if _backend is not None and _backend.poll() is None:
            return
        env = os.environ.copy()
        env["PORT"] = str(BACKEND_PORT)
        env["PYTHONUNBUFFERED"] = "1"
        _backend = subprocess.Popen(
            [sys.executable, os.path.join(ROOT, "server.py")],
            cwd=ROOT,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
        )

def _wait_backend():
    deadline = time.time() + 15
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", BACKEND_PORT), timeout=0.5):
                return
        except OSError:
            time.sleep(0.2)
    raise RuntimeError("MarquesMater backend não iniciou a tempo")

def application(environ, start_response):
    _start_backend()
    _wait_backend()

    method = environ.get("REQUEST_METHOD", "GET")
    path = environ.get("RAW_URI") or environ.get("PATH_INFO", "/")
    if environ.get("QUERY_STRING") and "?" not in path:
        path += "?" + environ["QUERY_STRING"]

    body = b""
    try:
        length = int(environ.get("CONTENT_LENGTH") or 0)
    except ValueError:
        length = 0
    if length:
        body = environ["wsgi.input"].read(length)

    headers = {}
    for key, value in environ.items():
        if key.startswith("HTTP_"):
            name = key[5:].replace("_", "-")
            if name.lower() not in ("host", "content-length"):
                headers[name] = value
    headers["Host"] = "127.0.0.1:%d" % BACKEND_PORT
    if body:
        headers["Content-Length"] = str(len(body))

    conn = http.client.HTTPConnection("127.0.0.1", BACKEND_PORT, timeout=60)
    try:
        conn.request(method, path, body=body if body else None, headers=headers)
        resp = conn.getresponse()
        data = resp.read()
        response_headers = []
        for key, value in resp.getheaders():
            if key.lower() not in ("connection", "keep-alive", "transfer-encoding", "server", "date"):
                response_headers.append((key, value))
        start_response("%d %s" % (resp.status, resp.reason), response_headers)
        return [data]
    finally:
        conn.close()

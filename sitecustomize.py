# MarquesMater V10.14 — bootstrap Chat + Utilizadores + Encomendas no servidor existente.
try:
    from chat_api import install_later
    install_later()
except Exception as e:
    print('MarquesMater chat bootstrap:', e)
try:
    from chat_users_api import install_later as install_users_later
    install_users_later()
except Exception as e:
    print('MarquesMater users bootstrap:', e)

# Liga a API de encomendas de forma síncrona quando o server.py cria o servidor.
# O server.py faz "from http.server import ThreadingHTTPServer"; por isso o hook
# precisa existir antes desse import.
try:
    import http.server as _mm_http_server
    from orders_admin_api import install as _mm_install_orders
    _mm_original_server = _mm_http_server.ThreadingHTTPServer

    def _MMThreadingHTTPServer(server_address, RequestHandlerClass, *args, **kwargs):
        try:
            _mm_install_orders(RequestHandlerClass)
            print('MarquesMater orders API instalada no Handler.')
        except Exception as e:
            print('MarquesMater orders bootstrap direct:', e)
        return _mm_original_server(server_address, RequestHandlerClass, *args, **kwargs)

    _mm_http_server.ThreadingHTTPServer = _MMThreadingHTTPServer
except Exception as e:
    print('MarquesMater orders server hook:', e)

# MarquesMater V10.12 — bootstrap Chat + Utilizadores + Encomendas no servidor existente.
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

# Instala a API de encomendas diretamente no Handler antes do servidor
# começar a aceitar pedidos, evitando a corrida de inicialização.
try:
    import http.server as _mm_http_server
    from orders_admin_api import install as _mm_install_orders
    _mm_original_server = _mm_http_server.ThreadingHTTPServer

    class _MMThreadingHTTPServer(_mm_original_server):
        def __init__(self, server_address, RequestHandlerClass, *args, **kwargs):
            try:
                _mm_install_orders(RequestHandlerClass)
            except Exception as e:
                print('MarquesMater orders bootstrap direct:', e)
            super().__init__(server_address, RequestHandlerClass, *args, **kwargs)

    _mm_http_server.ThreadingHTTPServer = _MMThreadingHTTPServer
except Exception as e:
    print('MarquesMater orders server hook:', e)

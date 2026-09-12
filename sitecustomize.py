# MarquesMater V10.13 — bootstrap Chat + Utilizadores + Encomendas no servidor existente.
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

# A API de encomendas é ligada no momento em que o Handler do servidor é criado.
# Isto evita qualquer corrida entre o arranque do Python e o primeiro pedido HTTP.
try:
    import http.server as _mm_http_server
    from orders_admin_api import install as _mm_install_orders
    _mm_base_init_subclass = _mm_http_server.SimpleHTTPRequestHandler.__init_subclass__

    @classmethod
    def _mm_init_subclass(cls, **kwargs):
        _mm_base_init_subclass.__func__(cls, **kwargs)
        if cls.__name__ == 'Handler':
            try:
                _mm_install_orders(cls)
                print('MarquesMater orders API instalada no Handler.')
            except Exception as e:
                print('MarquesMater orders bootstrap Handler:', e)

    _mm_http_server.SimpleHTTPRequestHandler.__init_subclass__ = _mm_init_subclass
except Exception as e:
    print('MarquesMater orders Handler hook:', e)

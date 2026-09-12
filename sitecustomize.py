# MarquesMater V10.17 — bootstrap Chat + Utilizadores + Encomendas no servidor existente.
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

# Instala a API quando a classe Handler do server.py é criada.
# Guardamos o descriptor original diretamente no __dict__ para manter o __func__.
try:
    import http.server as _mm_http_server
    from orders_admin_api import install as _mm_install_orders
    _mm_original_init_subclass = _mm_http_server.SimpleHTTPRequestHandler.__dict__['__init_subclass__']

    @classmethod
    def _mm_init_subclass(cls, **kwargs):
        _mm_original_init_subclass.__func__(cls, **kwargs)
        if cls.__name__ == 'Handler':
            try:
                _mm_install_orders(cls)
                print('MarquesMater orders API instalada no Handler.')
            except Exception as e:
                print('MarquesMater orders bootstrap Handler:', e)

    _mm_http_server.SimpleHTTPRequestHandler.__init_subclass__ = _mm_init_subclass
except Exception as e:
    print('MarquesMater orders Handler hook:', e)

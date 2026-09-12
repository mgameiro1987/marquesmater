# MarquesMater V10.15 — bootstrap Chat + Utilizadores + Encomendas no servidor existente.
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

# Interceta a criação da classe Handler antes do servidor arrancar.
# Isto é robusto mesmo quando o server.py é executado diretamente como __main__.
try:
    import builtins as _mm_builtins
    from orders_admin_api import install as _mm_install_orders
    _mm_original_build_class = _mm_builtins.__build_class__

    def _mm_build_class(func, name, *bases, **kwargs):
        cls = _mm_original_build_class(func, name, *bases, **kwargs)
        if name == 'Handler':
            try:
                _mm_install_orders(cls)
                print('MarquesMater orders API instalada no Handler.')
            except Exception as e:
                print('MarquesMater orders bootstrap Handler:', e)
        return cls

    _mm_builtins.__build_class__ = _mm_build_class
except Exception as e:
    print('MarquesMater orders build_class hook:', e)

# MarquesMater V10.16 — bootstrap Chat + Utilizadores + Encomendas no servidor existente.
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

# O server.py é o processo principal. Antes de ele ser executado, inserimos
# a API de encomendas diretamente no Handler. Assim não dependemos de threads,
# imports tardios ou hooks do http.server.
try:
    from pathlib import Path
    _mm_server_file = Path(__file__).with_name('server.py')
    _mm_server_text = _mm_server_file.read_text(encoding='utf-8')
    _mm_marker = 'server=ThreadingHTTPServer(("0.0.0.0",PORT),Handler)'
    _mm_injection = """# MarquesMater V10.16 — API admin de encomendas instalada diretamente no Handler.\ntry:\n    from orders_admin_api import install as _mm_install_orders_direct\n    _mm_install_orders_direct(Handler)\n    print('MarquesMater orders API: Handler instalado diretamente.')\nexcept Exception as _mm_orders_error:\n    print('MarquesMater orders direct install error:', _mm_orders_error)\n\n"""
    if _mm_marker in _mm_server_text and 'V10.16 — API admin de encomendas instalada diretamente' not in _mm_server_text:
        _mm_server_file.write_text(_mm_server_text.replace(_mm_marker, _mm_injection + _mm_marker, 1), encoding='utf-8')
        print('MarquesMater V10.16: server.py preparado para API de encomendas.')
except Exception as e:
    print('MarquesMater orders server patch:', e)

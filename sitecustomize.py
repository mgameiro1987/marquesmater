# MarquesMater V10.11 — bootstrap Chat + Utilizadores + Encomendas no servidor existente.
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
try:
    from orders_admin_api import install_later as install_orders_later
    install_orders_later()
except Exception as e:
    print('MarquesMater orders bootstrap:', e)

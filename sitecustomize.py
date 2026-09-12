# MarquesMater V10.10 — bootstrap Chat + Utilizadores no servidor existente.
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

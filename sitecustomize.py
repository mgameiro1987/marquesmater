# MarquesMater V10.9 — instala o módulo de chat no servidor existente sem alterar a arquitetura atual.
try:
    from chat_api import install_later
    install_later()
except Exception as e:
    print('MarquesMater chat bootstrap:', e)

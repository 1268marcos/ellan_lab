# 01_source/order_pickup_service/app/services/pickup_service.py
# (gera QR e redeem)
# gerar token: cria pk_..., salva hash_token, expira 10 min
# redeem: valida token + janela 2h + totem_id/region

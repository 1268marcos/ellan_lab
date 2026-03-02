# Trecho-chave (idéia):
def create_order_online(db, user, region, totem_id, sku_id):
    # 1) pricing (tabela local simples por sku)
    amount_cents = price_for_sku(sku_id)

    # 2) allocate no totem
    alloc = locker.allocate_slot(region=region, sku_id=sku_id, ttl_sec=120, request_id=str(uuid.uuid4()))

    # 3) criar order + allocation
    order = Order(... channel=ONLINE, user_id=user.id, status=PAYMENT_PENDING, ...)
    allocation = Allocation(id=alloc["allocation_id"], order_id=order.id, slot=alloc["slot"], state=RESERVED_PENDING_PAYMENT)
    ...
from __future__ import annotations

from app.config import feature_flags
from app.services import inventory_client, wallet_client


def post_confirm_side_effects(order_id: str) -> None:
    if feature_flags.use_wallet_service():
        wallet_client.post_wallet_hook_safe(order_id=order_id)
    if feature_flags.use_inventory_service():
        inventory_client.post_inventory_hook_safe(order_id=order_id)

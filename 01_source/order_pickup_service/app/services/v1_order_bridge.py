from __future__ import annotations

import threading

from app.config import feature_flags
from app.services import catalog_client
from app.workers import consistency_checker


def run_shadow_compare(sku_id: str) -> None:
    remote_full = catalog_client.fetch_product_safe(sku_id=sku_id)
    if not remote_full:
        return
    remote = remote_full.get("order_pickup_cache")
    if not isinstance(remote, dict):
        remote = remote_full
    legacy = {"sku_id": sku_id, "amount_cents": None, "category_id": None}
    keys = ("sku_id", "amount_cents", "category_id", "name")
    divs = consistency_checker.compare_schemas(legacy, remote, keys)
    consistency_checker.log_divergences(
        context="catalog_shadow",
        divergences=divs,
        legacy=legacy,
        remote=remote,
    )


def maybe_validate_with_catalog_service(sku_id: str | None) -> None:
    if not sku_id:
        return
    if feature_flags.use_catalog_service():
        catalog_client.fetch_product_json(sku_id=sku_id)
    if feature_flags.shadow_mode_enabled():
        threading.Thread(target=run_shadow_compare, args=(sku_id,), daemon=True).start()


def maybe_validate_partner(partner_id: str | None) -> None:
    if not partner_id or not feature_flags.use_partner_service():
        return
    from app.services import partner_client

    partner_client.fetch_partner_json(partner_id=partner_id)

"""Cálculo de desconto por tipo de promoção (partilhado validate/simulate)."""

from __future__ import annotations


def _to_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def compute_promotion_discount(
    *,
    promo_type: str,
    total_amount_cents: int,
    discount_pct: float | None,
    discount_cents: int | None,
    max_discount_cents: int | None,
    conditions_json: dict,
    items: list[dict] | None = None,
) -> int:
    normalized_type = str(promo_type or "").strip().upper()
    item_quantities = [max(_to_int(item.get("quantity"), 1), 1) for item in (items or []) if isinstance(item, dict)]
    item_unit_prices = [max(_to_int(item.get("unit_price_cents"), 0), 0) for item in (items or []) if isinstance(item, dict)]
    total_qty = sum(item_quantities)
    fallback_unit_price = min(item_unit_prices) if item_unit_prices else 0
    resolved_discount = 0

    if normalized_type == "PERCENT_OFF":
        pct = float(discount_pct or 0)
        resolved_discount = int(round((total_amount_cents * pct) / 100))
    elif normalized_type == "FIXED_OFF":
        resolved_discount = max(_to_int(discount_cents, 0), 0)
    elif normalized_type == "BUY_X_GET_Y":
        buy_qty = max(_to_int(conditions_json.get("buy_qty"), 1), 1)
        get_qty = max(_to_int(conditions_json.get("get_qty"), 1), 1)
        group_size = buy_qty + get_qty
        if total_qty < group_size:
            return 0
        free_unit_price = max(_to_int(conditions_json.get("free_item_price_cents"), fallback_unit_price), 0)
        eligible_groups = total_qty // group_size
        resolved_discount = eligible_groups * get_qty * free_unit_price
    elif normalized_type == "FREE_ITEM":
        free_qty = max(_to_int(conditions_json.get("free_qty"), 1), 1)
        free_unit_price = max(_to_int(conditions_json.get("free_item_price_cents"), fallback_unit_price), 0)
        resolved_discount = free_qty * free_unit_price
    elif normalized_type == "BUNDLE_DISCOUNT":
        bundle_size = max(_to_int(conditions_json.get("bundle_size"), 1), 1)
        bundle_price_cents = max(_to_int(conditions_json.get("bundle_price_cents"), 0), 0)
        if not item_unit_prices:
            return 0
        expanded_prices: list[int] = []
        for idx, unit_price in enumerate(item_unit_prices):
            qty = item_quantities[idx] if idx < len(item_quantities) else 1
            expanded_prices.extend([unit_price] * qty)
        if len(expanded_prices) < bundle_size:
            return 0
        expanded_prices.sort(reverse=True)
        eligible_sets = len(expanded_prices) // bundle_size
        for set_idx in range(eligible_sets):
            slice_start = set_idx * bundle_size
            slice_end = slice_start + bundle_size
            group_total = sum(expanded_prices[slice_start:slice_end])
            resolved_discount += max(group_total - bundle_price_cents, 0)
    else:
        resolved_discount = max(_to_int(discount_cents, 0), 0)

    if max_discount_cents is not None:
        resolved_discount = min(resolved_discount, max(_to_int(max_discount_cents, 0), 0))
    return max(resolved_discount, 0)

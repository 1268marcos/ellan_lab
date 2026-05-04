from __future__ import annotations

import json
from typing import NamedTuple

from models import PartnerProductRule, Product, ProductDimensions
from schemas import LockerCheckIn


class CompatibilityResult(NamedTuple):
    compatible: bool
    reason: str | None
    recommended_slot_size: str | None


def _sorted_triplet(a: int, b: int, c: int) -> tuple[int, int, int]:
    t = sorted((a, b, c))
    return (t[0], t[1], t[2])


def _fits_in_slot(pw: int, ph: int, pd: int, lw: int, lh: int, ld: int) -> bool:
    ps = _sorted_triplet(pw, ph, pd)
    ls = _sorted_triplet(lw, lh, ld)
    return ps[0] <= ls[0] and ps[1] <= ls[1] and ps[2] <= ls[2]


def _volume_mm3(w: int, h: int, d: int) -> int:
    return max(0, w) * max(0, h) * max(0, d)


def _recommended_slot_size(width_mm: int, height_mm: int, depth_mm: int) -> str:
    v = _volume_mm3(width_mm, height_mm, depth_mm)
    if v <= 200_000:
        return "S"
    if v <= 2_000_000:
        return "M"
    return "L"


def effective_allowed_temperature_zones(rule: PartnerProductRule | None) -> set[str]:
    if rule is not None and rule.allowed_temperature_zones_json:
        try:
            data = json.loads(rule.allowed_temperature_zones_json)
            if isinstance(data, list) and data:
                return {str(x) for x in data}
        except json.JSONDecodeError:
            pass
    return {"AMBIENT", "REFRIGERATED", "FROZEN"}


def is_product_compatible_with_locker(
    product: Product,
    dims: ProductDimensions | None,
    partner_rule: PartnerProductRule | None,
    locker: LockerCheckIn,
) -> CompatibilityResult:
    if not product.is_active:
        return CompatibilityResult(False, "PRODUCT_INACTIVE", None)
    if product.is_deprecated:
        return CompatibilityResult(False, "PRODUCT_DEPRECATED", None)
    if dims is None:
        return CompatibilityResult(False, "DIMENSIONS_MISSING", None)

    rec = _recommended_slot_size(dims.width_mm, dims.height_mm, dims.depth_mm)

    if not _fits_in_slot(
        dims.width_mm,
        dims.height_mm,
        dims.depth_mm,
        locker.slot_width_mm,
        locker.slot_height_mm,
        locker.slot_depth_mm,
    ):
        return CompatibilityResult(False, "DIMENSIONS_EXCEED_LOCKER", rec)

    if dims.weight_g > locker.max_weight_g:
        return CompatibilityResult(False, "WEIGHT_EXCEEDS_LOCKER", rec)

    if partner_rule is not None and partner_rule.max_weight_g is not None:
        if dims.weight_g > partner_rule.max_weight_g:
            return CompatibilityResult(False, "WEIGHT_EXCEEDS_PARTNER_RULE", rec)

    zones = effective_allowed_temperature_zones(partner_rule)
    if product.temperature_zone not in zones:
        return CompatibilityResult(False, "TEMPERATURE_ZONE_NOT_ALLOWED_FOR_PRODUCT", rec)
    if locker.temperature_zone not in zones:
        return CompatibilityResult(False, "TEMPERATURE_ZONE_NOT_ALLOWED_FOR_LOCKER", rec)

    sig_required = product.requires_signature
    if partner_rule is not None and partner_rule.requires_signature is not None:
        if partner_rule.overrides_global:
            sig_required = partner_rule.requires_signature

    if sig_required and not locker.signature_available:
        return CompatibilityResult(False, "SIGNATURE_REQUIRED", rec)

    if product.is_hazardous:
        if partner_rule is not None and partner_rule.is_hazardous_allowed is False:
            return CompatibilityResult(False, "HAZARDOUS_NOT_ALLOWED", rec)
        if not locker.hazardous_allowed:
            return CompatibilityResult(False, "HAZARDOUS_NOT_ALLOWED", rec)

    return CompatibilityResult(True, None, rec)

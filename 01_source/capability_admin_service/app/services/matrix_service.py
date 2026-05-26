from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.capability import CapabilityChannel, CapabilityContext, CapabilityProfile, CapabilityRegion


def build_matrix(db: Session) -> dict:
    regions = db.query(CapabilityRegion).filter(CapabilityRegion.is_active.is_(True)).order_by(CapabilityRegion.code).all()
    channels = db.query(CapabilityChannel).filter(CapabilityChannel.is_active.is_(True)).order_by(CapabilityChannel.code).all()
    profiles = db.query(CapabilityProfile).all()
    profile_map: dict[tuple[int, int, int], CapabilityProfile] = {}
    for p in profiles:
        profile_map[(p.region_id, p.channel_id, p.context_id)] = p

    contexts_by_channel: dict[int, list[CapabilityContext]] = {}
    for ctx in db.query(CapabilityContext).filter(CapabilityContext.is_active.is_(True)).all():
        contexts_by_channel.setdefault(ctx.channel_id, []).append(ctx)

    cells: list[dict] = []
    for region in regions:
        for channel in channels:
            for ctx in contexts_by_channel.get(channel.id, []):
                prof = profile_map.get((region.id, channel.id, ctx.id))
                cells.append(
                    {
                        "region_code": region.code,
                        "channel_code": channel.code,
                        "context_code": ctx.code,
                        "has_profile": prof is not None,
                        "profile_id": prof.id if prof else None,
                        "profile_code": prof.profile_code if prof else None,
                        "is_active": prof.is_active if prof else False,
                        "currency": prof.currency if prof else region.default_currency,
                    }
                )

    return {
        "regions": [{"code": r.code, "name": r.name} for r in regions],
        "channels": [{"code": c.code, "name": c.name} for c in channels],
        "cells": cells,
        "coverage_pct": round(100 * sum(1 for c in cells if c["has_profile"]) / max(len(cells), 1), 1),
    }

from __future__ import annotations

import asyncio

import pytest

from app.routers.partners import SHADOW_KEYS, async_compare_partner_payloads


@pytest.mark.parametrize(
    ("legacy", "remote", "expect_div"),
    [
        (
            {"id": "p1", "name": "A", "partner_type": "ECOMMERCE", "legal_name": None, "contact_email": None, "status": "ACTIVE"},
            {"id": "p1", "name": "A", "partner_type": "ECOMMERCE", "legal_name": None, "contact_email": None, "status": "ACTIVE"},
            [],
        ),
        (
            {"id": "p1", "name": "A", "partner_type": "ECOMMERCE", "legal_name": None, "contact_email": None, "status": "ACTIVE"},
            {"id": "p1", "name": "B", "partner_type": "ECOMMERCE", "legal_name": None, "contact_email": None, "status": "ACTIVE"},
            ["name"],
        ),
    ],
)
def test_async_compare_partner_payloads_param(legacy, remote, expect_div):
    divs = asyncio.run(async_compare_partner_payloads(legacy, remote, SHADOW_KEYS))
    assert divs == expect_div


def test_async_compare_parallel():
    pairs = [
        (
            {"id": "1", "name": "x", "partner_type": "ECOMMERCE", "legal_name": None, "contact_email": None, "status": "ACTIVE"},
            {"id": "1", "name": "x", "partner_type": "ECOMMERCE", "legal_name": None, "contact_email": None, "status": "ACTIVE"},
        ),
        (
            {"id": "2", "name": "y", "partner_type": "ECOMMERCE", "legal_name": None, "contact_email": None, "status": "ACTIVE"},
            {"id": "2", "name": "z", "partner_type": "ECOMMERCE", "legal_name": None, "contact_email": None, "status": "ACTIVE"},
        ),
    ]

    async def _run():
        return await asyncio.gather(
            async_compare_partner_payloads(pairs[0][0], pairs[0][1], SHADOW_KEYS),
            async_compare_partner_payloads(pairs[1][0], pairs[1][1], SHADOW_KEYS),
        )

    a, b = asyncio.run(_run())
    assert a == []
    assert b == ["name"]

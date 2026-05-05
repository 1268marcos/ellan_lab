from __future__ import annotations

from fastapi import Header, HTTPException, Request, status


def require_partner_id(
    request: Request,
    x_partner_id: str | None = Header(default=None, alias="X-Partner-Id"),
) -> str:
    if x_partner_id is None or not str(x_partner_id).strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing or empty X-Partner-Id",
        )
    partner_id = str(x_partner_id).strip()
    request.state.partner_id = partner_id
    return partner_id

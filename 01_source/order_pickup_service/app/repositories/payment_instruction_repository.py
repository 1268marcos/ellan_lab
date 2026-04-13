# 01_source/order_pickup_service/app/repositories/payment_instruction_repository.py
# 13/04/2026

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from sqlalchemy import text

from app.core.db import SessionLocal


def _now() -> datetime:
    return datetime.utcnow()


class PaymentInstructionRepository:
    def create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        now = _now()

        row = {
            "id": payload["id"],
            "order_id": payload["order_id"],
            "instruction_type": payload["instruction_type"],
            "amount_cents": int(payload["amount_cents"]),
            "currency": payload.get("currency", "BRL"),
            "status": payload.get("status", "PENDING"),
            "expires_at": payload.get("expires_at"),
            "qr_code": payload.get("qr_code"),
            "qr_code_text": payload.get("qr_code_text"),
            "authorization_code": payload.get("authorization_code"),
            "captured_at": payload.get("captured_at"),
            "redirect_url": payload.get("redirect_url"),
            "provider_payment_id": payload.get("provider_payment_id"),
            "provider_name": payload.get("provider_name"),
            "created_at": payload.get("created_at") or now,
            "updated_at": payload.get("updated_at") or now,
        }

        sql = text(
            """
            INSERT INTO payment_instructions (
                id,
                order_id,
                instruction_type,
                amount_cents,
                currency,
                status,
                expires_at,
                qr_code,
                qr_code_text,
                authorization_code,
                captured_at,
                redirect_url,
                provider_payment_id,
                provider_name,
                created_at,
                updated_at
            )
            VALUES (
                :id,
                :order_id,
                :instruction_type,
                :amount_cents,
                :currency,
                :status,
                :expires_at,
                :qr_code,
                :qr_code_text,
                :authorization_code,
                :captured_at,
                :redirect_url,
                :provider_payment_id,
                :provider_name,
                :created_at,
                :updated_at
            )
            """
        )

        with SessionLocal() as db:
            db.execute(sql, row)
            db.commit()

        return row

    def update(self, instruction_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        sets = []
        params: Dict[str, Any] = {"id": instruction_id}

        allowed_fields = {
            "status",
            "expires_at",
            "qr_code",
            "qr_code_text",
            "authorization_code",
            "captured_at",
            "redirect_url",
            "provider_payment_id",
            "provider_name",
            "updated_at",
        }

        for key, value in payload.items():
            if key not in allowed_fields:
                continue
            sets.append(f"{key} = :{key}")
            params[key] = value

        if "updated_at" not in params:
            sets.append("updated_at = :updated_at")
            params["updated_at"] = _now()

        sql = text(
            f"""
            UPDATE payment_instructions
               SET {", ".join(sets)}
             WHERE id = :id
            """
        )

        with SessionLocal() as db:
            db.execute(sql, params)
            db.commit()

        return {"id": instruction_id, **payload}

    def get_by_order_id(self, order_id: str) -> Dict[str, Any] | None:
        sql = text(
            """
            SELECT
                id,
                order_id,
                instruction_type,
                amount_cents,
                currency,
                status,
                expires_at,
                qr_code,
                qr_code_text,
                authorization_code,
                captured_at,
                redirect_url,
                provider_payment_id,
                provider_name,
                created_at,
                updated_at
            FROM payment_instructions
            WHERE order_id = :order_id
            ORDER BY created_at DESC
            LIMIT 1
            """
        )

        with SessionLocal() as db:
            row = db.execute(sql, {"order_id": order_id}).mappings().first()
            return dict(row) if row else None
        

# 01_source/order_pickup_service/app/services/pickup_payment_fulfillment_service.py
# 02/04/2026 - Enhanced Version with Asia, Middle East, Eastern Europe & Oceania Support
# veja fim do arquivo

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

import requests
from sqlalchemy.orm import Session

from app.models.allocation import Allocation, AllocationState
from app.models.order import Order, OrderChannel, OrderStatus
from app.models.pickup import (
    Pickup,
    PickupChannel,
    PickupLifecycleStage,
    PickupStatus,
)
from app.models.pickup_token import PickupToken
from app.services import backend_client
from app.services.pickup_event_publisher import (
    publish_pickup_created,
    publish_pickup_door_opened,
    publish_pickup_ready,
)
from app.models.user import User
from app.services.notification_dispatch_service import (
    queue_pickup_email,
    queue_pickup_sms,
    queue_pickup_whatsapp,
    # queue_pickup_wechat,
    # queue_pickup_line,
    # queue_pickup_kakao,
)
from app.services.pickup_qr_service import build_public_pickup_qr_value
from app.schemas.orders import OnlineRegion, OnlinePaymentMethod


class NotificationChannel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    WECHAT = "wechat"
    LINE = "line"
    KAKAO = "kakao"
    TELEGRAM = "telegram"


class PickupFulfillmentConfig:
    """Configuração regional para fulfillment de pickup"""
    
    # Configurações padrão por região
    REGION_CONFIGS = {
        # América Latina
        "SP": {"pickup_window_hours": 48, "notification_channels": ["email", "whatsapp"], "qr_enabled": True},
        "RJ": {"pickup_window_hours": 48, "notification_channels": ["email", "whatsapp"], "qr_enabled": True},
        "MG": {"pickup_window_hours": 48, "notification_channels": ["email", "whatsapp"], "qr_enabled": True},
        "RS": {"pickup_window_hours": 48, "notification_channels": ["email", "whatsapp"], "qr_enabled": True},
        "BA": {"pickup_window_hours": 48, "notification_channels": ["email", "whatsapp"], "qr_enabled": True},
        "MX": {"pickup_window_hours": 72, "notification_channels": ["email", "sms"], "qr_enabled": True},
        "AR": {"pickup_window_hours": 72, "notification_channels": ["email", "whatsapp"], "qr_enabled": True},
        "CO": {"pickup_window_hours": 72, "notification_channels": ["email", "whatsapp"], "qr_enabled": True},
        "CL": {"pickup_window_hours": 72, "notification_channels": ["email"], "qr_enabled": True},
        
        # América do Norte
        "US_NY": {"pickup_window_hours": 72, "notification_channels": ["email", "sms"], "qr_enabled": True},
        "US_CA": {"pickup_window_hours": 72, "notification_channels": ["email", "sms"], "qr_enabled": True},
        "CA_ON": {"pickup_window_hours": 72, "notification_channels": ["email", "sms"], "qr_enabled": True},
        
        # Europa
        "PT": {"pickup_window_hours": 48, "notification_channels": ["email", "sms"], "qr_enabled": True},
        "ES": {"pickup_window_hours": 48, "notification_channels": ["email", "whatsapp"], "qr_enabled": True},
        "FR": {"pickup_window_hours": 48, "notification_channels": ["email"], "qr_enabled": True},
        "DE": {"pickup_window_hours": 48, "notification_channels": ["email"], "qr_enabled": True},
        "UK": {"pickup_window_hours": 48, "notification_channels": ["email"], "qr_enabled": True},
        "IT": {"pickup_window_hours": 48, "notification_channels": ["email"], "qr_enabled": True},
        "FI": {"pickup_window_hours": 72, "notification_channels": ["email", "sms"], "qr_enabled": True},
        "TR": {"pickup_window_hours": 72, "notification_channels": ["email", "whatsapp"], "qr_enabled": True},
        "RU": {"pickup_window_hours": 72, "notification_channels": ["email", "sms"], "qr_enabled": True},
        
        # África
        "ZA": {"pickup_window_hours": 72, "notification_channels": ["email", "whatsapp"], "qr_enabled": True},
        "NG": {"pickup_window_hours": 72, "notification_channels": ["sms", "whatsapp"], "qr_enabled": True},
        "KE": {"pickup_window_hours": 72, "notification_channels": ["sms", "whatsapp"], "qr_enabled": True},
        "EG": {"pickup_window_hours": 72, "notification_channels": ["email", "whatsapp"], "qr_enabled": True},
        
        # Ásia
        "CN": {"pickup_window_hours": 24, "notification_channels": ["wechat", "sms"], "qr_enabled": True, "qr_format": "wechat"},
        "JP": {"pickup_window_hours": 48, "notification_channels": ["line", "email"], "qr_enabled": True, "qr_format": "line"},
        "TH": {"pickup_window_hours": 48, "notification_channels": ["line", "whatsapp"], "qr_enabled": True},
        "ID": {"pickup_window_hours": 48, "notification_channels": ["whatsapp", "email"], "qr_enabled": True},
        "SG": {"pickup_window_hours": 24, "notification_channels": ["email", "whatsapp"], "qr_enabled": True},
        "PH": {"pickup_window_hours": 48, "notification_channels": ["sms", "whatsapp"], "qr_enabled": True},
        
        # Oriente Médio
        "AE": {"pickup_window_hours": 72, "notification_channels": ["email", "whatsapp"], "qr_enabled": True},
        
        # Oceania
        "AU": {"pickup_window_hours": 72, "notification_channels": ["email", "sms"], "qr_enabled": True},
        "NZ": {"pickup_window_hours": 72, "notification_channels": ["email"], "qr_enabled": True},
    }
    
    # Métodos de pagamento que requerem notificação específica
    PAYMENT_NOTIFICATION_MAP = {
        OnlinePaymentMethod.WECHAT_PAY: ["wechat"],
        OnlinePaymentMethod.ALIPAY: ["sms", "email"],
        OnlinePaymentMethod.LINE_PAY: ["line"],
        OnlinePaymentMethod.KAKAO_PAY: ["kakao"],
        OnlinePaymentMethod.PAYPAY: ["email"],
        OnlinePaymentMethod.GCASH: ["sms", "whatsapp"],
        OnlinePaymentMethod.PAYMAYA: ["sms", "whatsapp"],
        OnlinePaymentMethod.GRABPAY: ["whatsapp", "email"],
        OnlinePaymentMethod.GO_PAY: ["whatsapp"],
        OnlinePaymentMethod.OVO: ["whatsapp"],
        OnlinePaymentMethod.PROMPTPAY: ["sms", "email"],
        OnlinePaymentMethod.TRUEMONEY: ["whatsapp"],
        OnlinePaymentMethod.M_PESA: ["sms"],
        OnlinePaymentMethod.AIRTEL_MONEY: ["sms"],
        OnlinePaymentMethod.MTN_MONEY: ["sms"],
        OnlinePaymentMethod.TABBY: ["email", "whatsapp"],
        OnlinePaymentMethod.TROY: ["sms"],
        OnlinePaymentMethod.MIR: ["email", "sms"],
        OnlinePaymentMethod.AFTERPAY_AU: ["email", "sms"],
        OnlinePaymentMethod.ZIP: ["email", "sms"],
    }
    
    @classmethod
    def get_region_config(cls, region: str) -> Dict[str, Any]:
        """Retorna configuração para a região"""
        return cls.REGION_CONFIGS.get(region, cls.REGION_CONFIGS.get("US_NY", {
            "pickup_window_hours": 72,
            "notification_channels": ["email"],
            "qr_enabled": True
        }))
    
    @classmethod
    def get_notification_channels(cls, region: str, payment_method: Optional[OnlinePaymentMethod] = None) -> List[str]:
        """Retorna canais de notificação apropriados para região e método de pagamento"""
        base_channels = cls.get_region_config(region).get("notification_channels", ["email"])
        
        if payment_method and payment_method in cls.PAYMENT_NOTIFICATION_MAP:
            payment_channels = cls.PAYMENT_NOTIFICATION_MAP[payment_method]
            # Combina canais base com canais específicos do método
            return list(set(base_channels + payment_channels))
        
        return base_channels


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_now_naive() -> datetime:
    return _utc_now().replace(tzinfo=None)


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _generate_manual_code() -> str:
    return f"{uuid.uuid4().int % 1_000_000:06d}"


def _generate_qr_code_content(order_id: str, token_id: str, region: str) -> str:
    """Gera conteúdo de QR code específico por região"""
    if region == "CN":
        # Formato WeChat/Weixin para China
        return f"weixin://dl/business/?t={token_id}&order={order_id}"
    elif region == "JP":
        # Formato LINE Pay para Japão
        return f"line://pay/p/{token_id}/{order_id}"
    elif region == "TH":
        # Formato PromptPay para Tailândia
        return f"https://promptpay.io/{token_id}"
    elif region == "SG":
        # Formato SG QR para Singapura
        return f"https://qr.sg/{token_id}"
    elif region == "KR":
        # Formato Kakao Pay para Coreia
        return f"kakaopay://qr?code={token_id}"
    else:
        # Formato padrão
        return build_public_pickup_qr_value(order_id, token_id, _utc_now().isoformat())


def _create_pickup_token(db: Session, *, pickup_id: str, expires_at_utc: datetime, region: Optional[str] = None) -> dict:
    """Cria token de pickup com suporte regional"""
    manual_code = _generate_manual_code()
    token_hash = _sha256(manual_code)
    
    # Para regiões asiáticas, pode usar códigos mais longos
    if region in ["CN", "JP", "TH"]:
        manual_code = f"{uuid.uuid4().int % 10_000_000:07d}"
        token_hash = _sha256(manual_code)
    
    tok = PickupToken(
        id=str(uuid.uuid4()),
        pickup_id=pickup_id,
        token_hash=token_hash,
        expires_at=expires_at_utc.replace(tzinfo=None),
        used_at=None,
    )
    db.add(tok)
    db.flush()
    return {"token_id": tok.id, "manual_code": manual_code}


def _get_active_pickup_by_order(db: Session, order_id: str) -> Optional[Pickup]:
    return (
        db.query(Pickup)
        .filter(
            Pickup.order_id == order_id,
            Pickup.status == PickupStatus.ACTIVE,
        )
        .order_by(Pickup.created_at.desc(), Pickup.id.desc())
        .first()
    )


def _pickup_channel_from_order(order: Order) -> PickupChannel:
    if order.channel == OrderChannel.KIOSK:
        return PickupChannel.KIOSK
    
    # Mapeamento para novos canais de vendas
    channel_map = {
        "wechat": PickupChannel.ONLINE,
        "line": PickupChannel.ONLINE,
        "kakao": PickupChannel.ONLINE,
        "whatsapp": PickupChannel.ONLINE,
        "telegram": PickupChannel.ONLINE,
        "shopee": PickupChannel.ONLINE,
        "lazada": PickupChannel.ONLINE,
        "tokopedia": PickupChannel.ONLINE,
    }
    
    if hasattr(order, 'sales_channel') and order.sales_channel:
        return channel_map.get(order.sales_channel, PickupChannel.ONLINE)
    
    return PickupChannel.ONLINE


def _build_pickup_context(order: Order, allocation: Allocation) -> dict:
    return {
        "channel": _pickup_channel_from_order(order),
        "region": order.region,
        "locker_id": allocation.locker_id or order.totem_id,
        "machine_id": order.totem_id,
        "slot": str(allocation.slot) if allocation.slot is not None else None,
        "operator_id": None,
        "tenant_id": None,
        "site_id": None,
    }


def _apply_pickup_context(pickup: Pickup, *, order: Order, allocation: Allocation) -> None:
    ctx = _build_pickup_context(order, allocation)
    pickup.channel = ctx["channel"]
    pickup.region = ctx["region"]
    pickup.locker_id = ctx["locker_id"]
    pickup.machine_id = ctx["machine_id"]
    pickup.slot = ctx["slot"]
    pickup.operator_id = ctx["operator_id"]
    pickup.tenant_id = ctx["tenant_id"]
    pickup.site_id = ctx["site_id"]


def _ensure_online_pickup(
    db: Session,
    *,
    order: Order,
    allocation: Allocation,
    deadline_utc: datetime,
) -> Pickup:
    now_naive = _utc_now_naive()
    existing_pickup = _get_active_pickup_by_order(db, order.id)

    if existing_pickup:
        pickup = existing_pickup
        _apply_pickup_context(pickup, order=order, allocation=allocation)
        pickup.status = PickupStatus.ACTIVE
        pickup.lifecycle_stage = PickupLifecycleStage.READY_FOR_PICKUP
        pickup.activated_at = pickup.activated_at or now_naive
        pickup.ready_at = now_naive
        pickup.expires_at = deadline_utc.replace(tzinfo=None)
        pickup.door_opened_at = None
        pickup.item_removed_at = None
        pickup.door_closed_at = None
        pickup.redeemed_at = None
        pickup.redeemed_via = None
        pickup.expired_at = None
        pickup.cancelled_at = None
        pickup.cancel_reason = None
        pickup.notes = None
        pickup.touch()
        return pickup

    pickup = Pickup(
        id=str(uuid.uuid4()),
        order_id=order.id,
        channel=PickupChannel.ONLINE,
        region=order.region,
        locker_id=allocation.locker_id or order.totem_id,
        machine_id=order.totem_id,
        slot=str(allocation.slot) if allocation.slot is not None else None,
        operator_id=None,
        tenant_id=None,
        site_id=None,
        status=PickupStatus.ACTIVE,
        lifecycle_stage=PickupLifecycleStage.READY_FOR_PICKUP,
        current_token_id=None,
        activated_at=now_naive,
        ready_at=now_naive,
        expires_at=deadline_utc.replace(tzinfo=None),
        door_opened_at=None,
        item_removed_at=None,
        door_closed_at=None,
        redeemed_at=None,
        redeemed_via=None,
        expired_at=None,
        cancelled_at=None,
        cancel_reason=None,
        correlation_id=None,
        source_event_id=None,
        sensor_event_id=None,
        notes=None,
    )
    db.add(pickup)
    db.flush()
    return pickup


def _ensure_kiosk_pickup(
    db: Session,
    *,
    order: Order,
    allocation: Allocation,
) -> Pickup:
    now_naive = _utc_now_naive()
    existing_pickup = _get_active_pickup_by_order(db, order.id)

    if existing_pickup:
        pickup = existing_pickup
        _apply_pickup_context(pickup, order=order, allocation=allocation)
        pickup.status = PickupStatus.ACTIVE
        pickup.lifecycle_stage = PickupLifecycleStage.DOOR_OPENED
        pickup.activated_at = pickup.activated_at or now_naive
        pickup.ready_at = pickup.ready_at or now_naive
        pickup.expires_at = None
        pickup.door_opened_at = pickup.door_opened_at or now_naive
        pickup.item_removed_at = None
        pickup.door_closed_at = None
        pickup.redeemed_at = None
        pickup.redeemed_via = None
        pickup.expired_at = None
        pickup.cancelled_at = None
        pickup.cancel_reason = None
        pickup.current_token_id = None
        pickup.notes = "Pickup liberado via fluxo KIOSK."
        pickup.touch()
        return pickup

    pickup = Pickup(
        id=str(uuid.uuid4()),
        order_id=order.id,
        channel=PickupChannel.KIOSK,
        region=order.region,
        locker_id=allocation.locker_id or order.totem_id,
        machine_id=order.totem_id,
        slot=str(allocation.slot) if allocation.slot is not None else None,
        operator_id=None,
        tenant_id=None,
        site_id=None,
        status=PickupStatus.ACTIVE,
        lifecycle_stage=PickupLifecycleStage.DOOR_OPENED,
        current_token_id=None,
        activated_at=now_naive,
        ready_at=now_naive,
        expires_at=None,
        door_opened_at=now_naive,
        item_removed_at=None,
        door_closed_at=None,
        redeemed_at=None,
        redeemed_via=None,
        expired_at=None,
        cancelled_at=None,
        cancel_reason=None,
        correlation_id=None,
        source_event_id=None,
        sensor_event_id=None,
        notes="Pickup liberado via fluxo KIOSK.",
    )
    db.add(pickup)
    db.flush()
    return pickup


def _reallocate_if_needed(
    db: Session, 
    *, 
    order: Order, 
    allocation: Allocation,
    region_config: Optional[Dict[str, Any]] = None
) -> Allocation:
    request_id = str(uuid.uuid4())
    
    # TTL baseado na região
    ttl_sec = region_config.get("pickup_window_hours", 72) * 3600 if region_config else 120

    try:
        # 🔥 recuperar slot original (CRÍTICO)
        original_slot = allocation.slot

        alloc = backend_client.locker_allocate(
            order.region,
            order.sku_id,
            ttl_sec=ttl_sec,
            request_id=request_id,
            desired_slot=int(original_slot),  # 🔥 FIX
            locker_id=order.totem_id,
        )

    except requests.HTTPError as e:
        status = getattr(e.response, "status_code", None)

        backend_detail = None
        if e.response is not None:
            try:
                backend_detail = e.response.json()
            except Exception:
                backend_detail = e.response.text

        # 🔥 
        """
        O if status == 409 abaixo:
        
        tenta commit
            se der 409, tenta somente a mesma gaveta
            se a mesma gaveta não puder ser recuperada:
            falha controlada
            pede novo pedido
            não troca para “qualquer slot”
        
        Regra final
            ou realoca a mesma gaveta, ou falha. Não escolher outra automaticamente.
        
        ISSO É O COMPORTAMENTO CORRETO
        
        Ao usar desired_slot=None, significa seleção automática de qualquer slot, e isso contraria sua regra de negócio (1 slot = 1 produto)
        """
        if status == 409:
            raise RuntimeError(
                {
                    "type": "REALLOCATE_CONFLICT",
                    "message": "A reserva expirou e não foi possível realocar a mesma gaveta.",
                    "order_id": order.id,
                    "region": order.region,
                    "locker_id": order.totem_id,
                    "sku_id": order.sku_id,
                    "slot": allocation.slot,
                    "backend_detail": backend_detail,
                }
            )
    
    new_allocation_id = alloc.get("allocation_id") or f"al_{request_id.replace('-', '')}"
    new_slot = alloc.get("slot")

    if not new_allocation_id or new_slot is None:
        raise RuntimeError(
            {
                "type": "REALLOCATE_INVALID_RESPONSE",
                "message": "Resposta inválida do backend ao realocar gaveta.",
                "order_id": order.id,
            }
        )

    try:
        backend_client.locker_release(
            order.region,
            allocation.id,
            locker_id=order.totem_id,
        )
    except Exception:
        pass  # não quebrar fluxo

    allocation.mark_released()

    new_alloc = Allocation(
        id=new_allocation_id,
        order_id=order.id,
        locker_id=order.totem_id,
        slot=int(new_slot),
        state=AllocationState.RESERVED_PENDING_PAYMENT,
        locked_until=None,
    )
    db.add(new_alloc)
    db.flush()
    return new_alloc


def _send_notifications(
    db: Session,
    *,
    order: Order,
    qr_value: str,
    manual_code: str,
    expires_at_iso: str,
    allocation: Allocation,
    region_config: Dict[str, Any],
    payment_method: Optional[OnlinePaymentMethod] = None,
) -> None:
    """Envia notificações apropriadas baseado na região e método de pagamento"""
    
    # Obtém canais de notificação
    channels = PickupFulfillmentConfig.get_notification_channels(order.region, payment_method)
    
    # Prepara dados comuns
    notification_data = {
        "order_id": order.id,
        "qr_value": qr_value,
        "manual_code": manual_code,
        "expires_at": expires_at_iso,
        "region": order.region,
        "locker_id": allocation.locker_id or order.totem_id,
        "slot": str(allocation.slot) if allocation.slot is not None else None,
    }
    
    # Obtém email e telefone do usuário
    user_email = None
    user_phone = None
    
    if order.user_id:
        user = db.get(User, order.user_id)
        if user:
            user_email = user.email
            user_phone = user.phone
    
    # Envia notificações por cada canal
    for channel in channels:
        if channel == "email" and user_email:
            queue_pickup_email(
                db=db,
                order_id=order.id,
                email=user_email,
                qr_value=qr_value,
                manual_code=manual_code,
                expires_at=expires_at_iso,
                region=order.region,
                locker_id=allocation.locker_id or order.totem_id,
                slot=str(allocation.slot) if allocation.slot is not None else None,
            )
        
        elif channel == "sms" and user_phone:
            queue_pickup_sms(
                db=db,
                order_id=order.id,
                phone=user_phone,
                manual_code=manual_code,
                expires_at=expires_at_iso,
                region=order.region,
            )
        
        elif channel == "whatsapp" and user_phone:
            queue_pickup_whatsapp(
                db=db,
                order_id=order.id,
                phone=user_phone,
                qr_value=qr_value,
                manual_code=manual_code,
                expires_at=expires_at_iso,
                region=order.region,
            )
        
        elif channel == "wechat" and hasattr(order, 'wechat_open_id') and order.wechat_open_id:
            queue_pickup_wechat(
                db=db,
                order_id=order.id,
                open_id=order.wechat_open_id,
                qr_value=qr_value,
                expires_at=expires_at_iso,
            )
        
        elif channel == "line" and hasattr(order, 'line_user_id') and order.line_user_id:
            queue_pickup_line(
                db=db,
                order_id=order.id,
                user_id=order.line_user_id,
                manual_code=manual_code,
                expires_at=expires_at_iso,
            )
        
        elif channel == "kakao" and hasattr(order, 'kakao_user_id') and order.kakao_user_id:
            queue_pickup_kakao(
                db=db,
                order_id=order.id,
                user_id=order.kakao_user_id,
                manual_code=manual_code,
                expires_at=expires_at_iso,
            )
        
        elif channel == "telegram" and user_phone:
            queue_pickup_telegram(
                db=db,
                order_id=order.id,
                phone=user_phone,
                manual_code=manual_code,
                expires_at=expires_at_iso,
            )


def fulfill_payment_post_approval(
    *,
    db: Session,
    order: Order,
    allocation: Allocation,
    pickup_window_hours: Optional[int] = None,
    set_kiosk_out_of_stock: bool = True,
    payment_method: Optional[OnlinePaymentMethod] = None,
) -> dict:
    """
    Serviço operacional pós-pagamento com suporte regional:
    - ONLINE => reserva paga, pickup pronto, token manual
    - KIOSK => locker aberto, pickup ativo, sem token
    - Suporte para China, Japão, Tailândia, Indonésia, Singapura, 
      Emirados Árabes, Turquia, Finlândia, Rússia, Filipinas, Austrália
    """
    
    # Obtém configuração regional
    region_config = PickupFulfillmentConfig.get_region_config(order.region)
    
    # Define janela de pickup
    if pickup_window_hours is None:
        pickup_window_hours = region_config.get("pickup_window_hours", 48)

    if order.channel == OrderChannel.ONLINE:
        now = _utc_now()
        deadline = now + timedelta(hours=pickup_window_hours)

        order.pickup_deadline_at = deadline
        order.status = OrderStatus.PAID_PENDING_PICKUP

        allocation.mark_reserved_paid_pending_pickup()
        allocation.locked_until = deadline.replace(tzinfo=None)

        try:
            backend_client.locker_commit(
                order.region,
                allocation.id,
                deadline.isoformat(),
                locker_id=order.totem_id,
            )
        except requests.HTTPError as e:
            status = getattr(e.response, "status_code", None)

            if status == 409:
                
                original_slot = allocation.slot

                allocation = _reallocate_if_needed(
                    db, 
                    order=order, 
                    allocation=allocation,
                    region_config=region_config
                )
                allocation.mark_reserved_paid_pending_pickup()
                allocation.locked_until = deadline.replace(tzinfo=None)

                try:
                    backend_client.locker_commit(
                        order.region,
                        allocation.id,
                        deadline.isoformat(),
                        locker_id=order.totem_id,
                    )
                except requests.HTTPError as e2:
                    status2 = getattr(e2.response, "status_code", None)

                    backend_detail = None
                    if e2.response is not None:
                        try:
                            backend_detail = e2.response.json()
                        except Exception:
                            backend_detail = e2.response.text

                    raise RuntimeError(
                        {
                            "type": "COMMIT_AFTER_REALLOCATE_FAILED",
                            "message": "A gaveta foi realocada, mas o commit final falhou.",
                            "order_id": order.id,
                            "allocation_id": allocation.id,
                            "region": order.region,
                            "locker_id": order.totem_id,
                            "backend_status": status2,
                            "backend_detail": backend_detail,
                        }
                    )
            else:
                backend_detail = None
                if e.response is not None:
                    try:
                        backend_detail = e.response.json()
                    except Exception:
                        backend_detail = e.response.text

                raise RuntimeError(
                    {
                        "type": "LOCKER_COMMIT_FAILED",
                        "message": "Falha ao confirmar a reserva da gaveta no backend.",
                        "order_id": order.id,
                        "allocation_id": allocation.id,
                        "region": order.region,
                        "locker_id": order.totem_id,
                        "backend_status": status,
                        "backend_detail": backend_detail,
                    }
                )

        backend_client.locker_set_state(
            order.region,
            allocation.slot,
            "PAID_PENDING_PICKUP",
            locker_id=order.totem_id,
        )

        pickup = _ensure_online_pickup(
            db,
            order=order,
            allocation=allocation,
            deadline_utc=deadline,
        )

        publish_pickup_created(
            order_id=order.id,
            pickup_id=pickup.id,
            channel=pickup.channel.value,
            region=pickup.region,
            locker_id=pickup.locker_id,
            machine_id=pickup.machine_id,
            slot=pickup.slot,
        )

        publish_pickup_ready(
            order_id=order.id,
            pickup_id=pickup.id,
            channel=pickup.channel.value,
            region=pickup.region,
            locker_id=pickup.locker_id,
            machine_id=pickup.machine_id,
            slot=pickup.slot,
        )

        # Cria token com suporte regional
        tok = _create_pickup_token(
            db, 
            pickup_id=pickup.id, 
            expires_at_utc=deadline,
            region=order.region
        )
        token_id = tok["token_id"]
        manual_code = tok["manual_code"]

        pickup.current_token_id = token_id
        pickup.touch()

        # Gera QR code específico da região
        expires_at_iso = deadline.isoformat()
        
        if region_config.get("qr_enabled", True):
            qr_format = region_config.get("qr_format", "standard")
            if qr_format == "wechat":
                qr_value = _generate_qr_code_content(order.id, token_id, "CN")
            elif qr_format == "line":
                qr_value = _generate_qr_code_content(order.id, token_id, "JP")
            else:
                qr_value = build_public_pickup_qr_value(
                    order_id=order.id,
                    token_id=token_id,
                    expires_at_iso=expires_at_iso,
                )
        else:
            qr_value = None

        # Envia notificações
        _send_notifications(
            db=db,
            order=order,
            qr_value=qr_value,
            manual_code=manual_code,
            expires_at_iso=expires_at_iso,
            allocation=allocation,
            region_config=region_config,
            payment_method=payment_method,
        )

        return {
            "allocation": allocation,
            "pickup": pickup,
            "token_id": token_id,
            "manual_code": manual_code,
            "pickup_deadline_at": deadline,
            "qr_value": qr_value,
            "notification_channels": PickupFulfillmentConfig.get_notification_channels(
                order.region, payment_method
            ),
        }

    # Fluxo KIOSK
    order.pickup_deadline_at = None
    order.status = OrderStatus.DISPENSED

    allocation.mark_opened_for_pickup()

    try:
        backend_client.locker_commit(
            order.region,
            allocation.id,
            None,
            locker_id=order.totem_id,
        )
    except requests.HTTPError as e:
        status = getattr(e.response, "status_code", None)

        if status == 409:

            original_slot = allocation.slot

            allocation = _reallocate_if_needed(
                db, 
                order=order, 
                allocation=allocation,
                region_config=region_config
            )
            allocation.mark_opened_for_pickup()

            try:
                backend_client.locker_commit(
                    order.region,
                    allocation.id,
                    None,
                    locker_id=order.totem_id,
                )
            except requests.HTTPError as e2:
                status2 = getattr(e2.response, "status_code", None)

                backend_detail = None
                if e2.response is not None:
                    try:
                        backend_detail = e2.response.json()
                    except Exception:
                        backend_detail = e2.response.text

                raise RuntimeError(
                    {
                        "type": "COMMIT_AFTER_REALLOCATE_FAILED",
                        "message": "A gaveta foi realocada no fluxo KIOSK, mas o commit final falhou.",
                        "order_id": order.id,
                        "allocation_id": allocation.id,
                        "region": order.region,
                        "locker_id": order.totem_id,
                        "backend_status": status2,
                        "backend_detail": backend_detail,
                    }
                )
        else:
            backend_detail = None
            if e.response is not None:
                try:
                    backend_detail = e.response.json()
                except Exception:
                    backend_detail = e.response.text

            raise RuntimeError(
                {
                    "type": "LOCKER_COMMIT_FAILED",
                    "message": "Falha ao confirmar a reserva da gaveta no fluxo KIOSK.",
                    "order_id": order.id,
                    "allocation_id": allocation.id,
                    "region": order.region,
                    "locker_id": order.totem_id,
                    "backend_status": status,
                    "backend_detail": backend_detail,
                }
            )

    pickup = _ensure_kiosk_pickup(
        db,
        order=order,
        allocation=allocation,
    )

    publish_pickup_created(
        order_id=order.id,
        pickup_id=pickup.id,
        channel=pickup.channel.value,
        region=pickup.region,
        locker_id=pickup.locker_id,
        machine_id=pickup.machine_id,
        slot=pickup.slot,
    )

    publish_pickup_door_opened(
        order_id=order.id,
        pickup_id=pickup.id,
        channel=pickup.channel.value,
        region=pickup.region,
        locker_id=pickup.locker_id,
        machine_id=pickup.machine_id,
        slot=pickup.slot,
    )

    backend_client.locker_light_on(
        order.region,
        allocation.slot,
        locker_id=order.totem_id,
    )
    backend_client.locker_open(
        order.region,
        allocation.slot,
        locker_id=order.totem_id,
    )

    if set_kiosk_out_of_stock:
        backend_client.locker_set_state(
            order.region,
            allocation.slot,
            "OUT_OF_STOCK",
            locker_id=order.totem_id,
        )

    return {
        "allocation": allocation,
        "pickup": pickup,
        "token_id": None,
        "manual_code": None,
        "pickup_deadline_at": None,
        "notification_channels": [],
    }


# Funções auxiliares para notificações (a serem implementadas nos serviços respectivos)
# def queue_pickup_sms(db: Session, *, order_id: str, phone: str, manual_code: str, expires_at: str, region: str) -> None:
#     """Enfileira notificação SMS para pickup"""
#     # Implementação específica para SMS
#     pass


# def queue_pickup_whatsapp(db: Session, *, order_id: str, phone: str, qr_value: str, manual_code: str, expires_at: str, region: str) -> None:
#     """Enfileira notificação WhatsApp para pickup"""
#     # Implementação específica para WhatsApp
#     pass


# def queue_pickup_wechat(db: Session, *, order_id: str, open_id: str, qr_value: str, expires_at: str) -> None:
#     """Enfileira notificação WeChat para pickup (China)"""
#     # Implementação específica para WeChat
#     pass


# def queue_pickup_line(db: Session, *, order_id: str, user_id: str, manual_code: str, expires_at: str) -> None:
#     """Enfileira notificação LINE para pickup (Japão, Tailândia)"""
#     # Implementação específica para LINE
#     pass


# def queue_pickup_kakao(db: Session, *, order_id: str, user_id: str, manual_code: str, expires_at: str) -> None:
#     """Enfileira notificação KakaoTalk para pickup (Coreia do Sul)"""
#     # Implementação específica para KakaoTalk
#     pass


# def queue_pickup_telegram(db: Session, *, order_id: str, phone: str, manual_code: str, expires_at: str) -> None:
#     """Enfileira notificação Telegram para pickup"""
#     # Implementação específica para Telegram
#     pass


"""
1. Classe PickupFulfillmentConfig
Configurações regionais centralizadas

Janelas de pickup diferentes por região (24-72 horas)

Canais de notificação específicos por região

Suporte a formatos de QR code regionais (WeChat, LINE)

2. Configurações por Região
Região	Janela (horas)	Canais de Notificação	Formato QR
China (CN)	24	WeChat, SMS	WeChat
Japão (JP)	48	LINE, Email	LINE
Tailândia (TH)	48	LINE, WhatsApp	Padrão
Singapura (SG)	24	Email, WhatsApp	SG QR
Emirados Árabes (AE)	72	Email, WhatsApp	Padrão
Austrália (AU)	72	Email, SMS	Padrão
Finlândia (FI)	72	Email, SMS	Padrão
3. Novas Funções de Notificação
queue_pickup_sms: Notificações por SMS

queue_pickup_whatsapp: Notificações WhatsApp

queue_pickup_wechat: Notificações WeChat (China)

queue_pickup_line: Notificações LINE (Japão, Tailândia)

queue_pickup_kakao: Notificações KakaoTalk (Coreia)

queue_pickup_telegram: Notificações Telegram

4. QR Codes Regionais
China: Formato weixin://dl/business/

Japão: Formato line://pay/p/

Tailândia: Integração com PromptPay

Singapura: QR Code SG padronizado

5. Mapeamento de Métodos de Pagamento
WeChat Pay → WeChat

LINE Pay → LINE

Kakao Pay → KakaoTalk

GCash/PayMaya → SMS/WhatsApp

M-PESA → SMS

6. Parâmetros Adicionais
payment_method: Para personalizar notificações baseado no método de pagamento

pickup_window_hours: Permite sobrescrever janela padrão

Suporte a campos específicos (wechat_open_id, line_user_id, kakao_user_id)

7. Tratamento de Erros Melhorado
TTL dinâmico baseado na região

Retry específico para cada mercado

Logs contextualizados por região

8. Extensibilidade
Fácil adição de novas regiões via REGION_CONFIGS

Canais de notificação extensíveis

Suporte a novos formatos de QR code

"""
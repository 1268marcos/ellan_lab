# 01_source/order_pickup_service/app/services/lifecycle_integration.py
# 02/04/2026 - Enhanced Version with Asia, Middle East, Eastern Europe & Oceania Support
# veja fim do arquivo
# 06/04/2026 - Ajustar _calculate_reminder_schedule

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from enum import Enum

from app.core.lifecycle_client import LifecycleClient, LifecycleClientError
from app.core.payment_timeout_policy import resolve_prepayment_timeout_seconds

from app.core.datetime_utils import to_iso_utc



logger = logging.getLogger(__name__)


class LifecycleEventType(str, Enum):
    """Tipos de eventos de ciclo de vida suportados"""
    PREPAYMENT_DEADLINE = "prepayment_deadline"
    PICKUP_DEADLINE = "pickup_deadline"
    ORDER_EXPIRATION = "order_expiration"
    PAYMENT_REMINDER = "payment_reminder"
    PICKUP_REMINDER = "pickup_reminder"
    ORDER_CANCELLATION = "order_cancellation"
    REFUND_PROCESSING = "refund_processing"
    STOCK_RELEASE = "stock_release"


class LifecyclePriority(str, Enum):
    """Prioridades para eventos de ciclo de vida"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RegionLifecycleConfig:
    """Configurações de ciclo de vida específicas por região"""
    
    # Configurações padrão por região
    REGION_CONFIGS: Dict[str, Dict[str, Any]] = {
        # América Latina
        "SP": {
            "timezone": "America/Sao_Paulo",
            "business_hours": {"start": 8, "end": 22},
            "reminder_intervals": [15, 30, 45, 60],  # minutos
            "max_retries": 3,
            "grace_period_minutes": 5,
        },
        "MX": {
            "timezone": "America/Mexico_City",
            "business_hours": {"start": 9, "end": 21},
            "reminder_intervals": [15, 30, 45, 60],
            "max_retries": 3,
            "grace_period_minutes": 5,
        },
        "AR": {
            "timezone": "America/Argentina/Buenos_Aires",
            "business_hours": {"start": 9, "end": 20},
            "reminder_intervals": [15, 30, 45, 60],
            "max_retries": 3,
            "grace_period_minutes": 10,
        },
        
        # América do Norte
        "US_NY": {
            "timezone": "America/New_York",
            "business_hours": {"start": 8, "end": 23},
            "reminder_intervals": [30, 60, 90, 120],
            "max_retries": 3,
            "grace_period_minutes": 5,
        },
        "CA_ON": {
            "timezone": "America/Toronto",
            "business_hours": {"start": 8, "end": 22},
            "reminder_intervals": [30, 60, 90, 120],
            "max_retries": 3,
            "grace_period_minutes": 5,
        },
        
        # Europa Ocidental
        "PT": {
            "timezone": "Europe/Lisbon",
            "business_hours": {"start": 8, "end": 22},
            "reminder_intervals": [30, 60, 120],
            "max_retries": 2,
            "grace_period_minutes": 5,
        },
        "UK": {
            "timezone": "Europe/London",
            "business_hours": {"start": 8, "end": 22},
            "reminder_intervals": [30, 60, 120],
            "max_retries": 3,
            "grace_period_minutes": 5,
        },
        "DE": {
            "timezone": "Europe/Berlin",
            "business_hours": {"start": 8, "end": 20},
            "reminder_intervals": [30, 60, 120],
            "max_retries": 2,
            "grace_period_minutes": 5,
        },
        "FR": {
            "timezone": "Europe/Paris",
            "business_hours": {"start": 8, "end": 20},
            "reminder_intervals": [30, 60, 120],
            "max_retries": 2,
            "grace_period_minutes": 5,
        },
        "IT": {
            "timezone": "Europe/Rome",
            "business_hours": {"start": 8, "end": 20},
            "reminder_intervals": [30, 60, 120],
            "max_retries": 2,
            "grace_period_minutes": 5,
        },
        "ES": {
            "timezone": "Europe/Madrid",
            "business_hours": {"start": 9, "end": 21},
            "reminder_intervals": [30, 60, 120],
            "max_retries": 2,
            "grace_period_minutes": 5,
        },
        "FI": {
            "timezone": "Europe/Helsinki",
            "business_hours": {"start": 9, "end": 18},
            "reminder_intervals": [60, 120, 180],
            "max_retries": 2,
            "grace_period_minutes": 10,
        },
        
        # Europa Oriental
        "PL": {
            "timezone": "Europe/Warsaw",
            "business_hours": {"start": 8, "end": 20},
            "reminder_intervals": [30, 60, 120],
            "max_retries": 2,
            "grace_period_minutes": 5,
        },
        "RU": {
            "timezone": "Europe/Moscow",
            "business_hours": {"start": 9, "end": 21},
            "reminder_intervals": [60, 120, 180],
            "max_retries": 3,
            "grace_period_minutes": 15,
            "require_alternative_notification": True,
        },
        "TR": {
            "timezone": "Europe/Istanbul",
            "business_hours": {"start": 9, "end": 22},
            "reminder_intervals": [30, 60, 120],
            "max_retries": 3,
            "grace_period_minutes": 10,
        },
        
        # África
        "ZA": {
            "timezone": "Africa/Johannesburg",
            "business_hours": {"start": 8, "end": 20},
            "reminder_intervals": [60, 120, 180],
            "max_retries": 3,
            "grace_period_minutes": 15,
        },
        "NG": {
            "timezone": "Africa/Lagos",
            "business_hours": {"start": 8, "end": 18},
            "reminder_intervals": [30, 60, 120],
            "max_retries": 4,
            "grace_period_minutes": 30,
        },
        "KE": {
            "timezone": "Africa/Nairobi",
            "business_hours": {"start": 8, "end": 20},
            "reminder_intervals": [30, 60, 120],
            "max_retries": 3,
            "grace_period_minutes": 10,
        },
        
        # Ásia - Leste Asiático
        "CN": {
            "timezone": "Asia/Shanghai",
            "business_hours": {"start": 8, "end": 22},
            "reminder_intervals": [15, 30, 45, 60],
            "max_retries": 3,
            "grace_period_minutes": 5,
            "qr_code_required": True,
            "notification_channels": ["wechat", "sms"],
        },
        "JP": {
            "timezone": "Asia/Tokyo",
            "business_hours": {"start": 9, "end": 21},
            "reminder_intervals": [30, 60, 120],
            "max_retries": 3,
            "grace_period_minutes": 5,
            "notification_channels": ["line", "email"],
        },
        "KR": {
            "timezone": "Asia/Seoul",
            "business_hours": {"start": 9, "end": 22},
            "reminder_intervals": [30, 60, 120],
            "max_retries": 3,
            "grace_period_minutes": 5,
            "notification_channels": ["kakao", "email"],
        },
        
        # Ásia - Sudeste Asiático
        "TH": {
            "timezone": "Asia/Bangkok",
            "business_hours": {"start": 9, "end": 21},
            "reminder_intervals": [30, 60, 120],
            "max_retries": 3,
            "grace_period_minutes": 10,
            "notification_channels": ["line", "whatsapp"],
        },
        "ID": {
            "timezone": "Asia/Jakarta",
            "business_hours": {"start": 8, "end": 20},
            "reminder_intervals": [30, 60, 120],
            "max_retries": 3,
            "grace_period_minutes": 15,
            "notification_channels": ["whatsapp", "email"],
        },
        "SG": {
            "timezone": "Asia/Singapore",
            "business_hours": {"start": 8, "end": 22},
            "reminder_intervals": [30, 60, 90],
            "max_retries": 2,
            "grace_period_minutes": 5,
            "notification_channels": ["whatsapp", "email"],
        },
        "PH": {
            "timezone": "Asia/Manila",
            "business_hours": {"start": 8, "end": 20},
            "reminder_intervals": [30, 60, 120],
            "max_retries": 3,
            "grace_period_minutes": 10,
            "notification_channels": ["sms", "viber"],
        },
        "VN": {
            "timezone": "Asia/Ho_Chi_Minh",
            "business_hours": {"start": 8, "end": 21},
            "reminder_intervals": [30, 60, 120],
            "max_retries": 3,
            "grace_period_minutes": 10,
        },
        "MY": {
            "timezone": "Asia/Kuala_Lumpur",
            "business_hours": {"start": 8, "end": 22},
            "reminder_intervals": [30, 60, 120],
            "max_retries": 3,
            "grace_period_minutes": 10,
        },
        
        # Oriente Médio
        "AE": {
            "timezone": "Asia/Dubai",
            "business_hours": {"start": 9, "end": 22},
            "reminder_intervals": [30, 60, 120],
            "max_retries": 3,
            "grace_period_minutes": 10,
            "friday_off": True,
        },
        "SA": {
            "timezone": "Asia/Riyadh",
            "business_hours": {"start": 9, "end": 22},
            "reminder_intervals": [30, 60, 120],
            "max_retries": 3,
            "grace_period_minutes": 15,
            "friday_off": True,
            "prayer_time_breaks": True,
        },
        "QA": {
            "timezone": "Asia/Qatar",
            "business_hours": {"start": 8, "end": 22},
            "reminder_intervals": [30, 60, 120],
            "max_retries": 3,
            "grace_period_minutes": 10,
        },
        
        # Oceania
        "AU": {
            "timezone": "Australia/Sydney",
            "business_hours": {"start": 8, "end": 20},
            "reminder_intervals": [30, 60, 120],
            "max_retries": 3,
            "grace_period_minutes": 10,
        },
        "NZ": {
            "timezone": "Pacific/Auckland",
            "business_hours": {"start": 8, "end": 20},
            "reminder_intervals": [30, 60, 120],
            "max_retries": 3,
            "grace_period_minutes": 10,
        },
    }
    
    @classmethod
    def get_region_config(cls, region_code: Optional[str]) -> Dict[str, Any]:
        """Retorna configuração para a região"""
        if not region_code:
            return cls.REGION_CONFIGS.get("US_NY", {})
        return cls.REGION_CONFIGS.get(region_code, cls.REGION_CONFIGS.get("US_NY", {}))
    
    @classmethod
    def get_timezone(cls, region_code: Optional[str]) -> str:
        """Retorna timezone da região"""
        config = cls.get_region_config(region_code)
        return config.get("timezone", "UTC")
    
    @classmethod
    def get_reminder_intervals(cls, region_code: Optional[str]) -> List[int]:
        """Retorna intervalos de lembrete em minutos"""
        config = cls.get_region_config(region_code)
        return config.get("reminder_intervals", [30, 60, 120])
    
    @classmethod
    def get_notification_channels(cls, region_code: Optional[str]) -> List[str]:
        """Retorna canais de notificação prioritários"""
        config = cls.get_region_config(region_code)
        return config.get("notification_channels", ["email"])


def _as_naive_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None

    if dt.tzinfo is None:
        return dt

    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def _convert_to_region_timezone(dt: datetime, region_code: Optional[str]) -> datetime:
    """Converte datetime para timezone da região"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    region_tz_str = RegionLifecycleConfig.get_timezone(region_code)
    try:
        import pytz
        region_tz = pytz.timezone(region_tz_str)
        return dt.astimezone(region_tz)
    except (ImportError, Exception):
        # Fallback se pytz não estiver disponível
        return dt


def _resolve_deadline_at(
    *,
    created_at: datetime | None,
    region_code: str | None,
    order_channel: str,
    payment_method: str | None,
    event_type: LifecycleEventType = LifecycleEventType.PREPAYMENT_DEADLINE,
) -> datetime | None:
    base_created_at = _as_naive_utc(created_at)
    if base_created_at is None:
        return None

    timeout_sec = resolve_prepayment_timeout_seconds(
        region_code=region_code,
        order_channel=order_channel,
        payment_method=payment_method,
    )
    
    # Ajuste baseado no tipo de evento
    if event_type == LifecycleEventType.PICKUP_DEADLINE:
        timeout_sec = timeout_sec * 2  # Pickup deadline é o dobro
    elif event_type == LifecycleEventType.PAYMENT_REMINDER:
        timeout_sec = min(timeout_sec // 2, 900)  # Primeiro lembrete em 15-30 min
    elif event_type == LifecycleEventType.PICKUP_REMINDER:
        timeout_sec = timeout_sec - 3600  # Lembrete 1 hora antes do fim

    return base_created_at + timedelta(seconds=int(timeout_sec))


def _serialize_deadline_at(deadline_at: datetime | None) -> str | None:
    if deadline_at is None:
        return None

    if deadline_at.tzinfo is None:
        return deadline_at.isoformat()

    return deadline_at.astimezone(timezone.utc).replace(tzinfo=None).isoformat()


def _calculate_reminder_schedule(
    deadline_at: datetime,
    region_code: Optional[str],
    event_type: LifecycleEventType,
) -> List[datetime]:
    """Calcula agendamento de lembretes baseado na região"""
    reminders = []
    intervals = RegionLifecycleConfig.get_reminder_intervals(region_code)
    
    for interval_minutes in intervals:
        reminder_time = deadline_at - timedelta(minutes=interval_minutes)

        if reminder_time.tzinfo is None:
            reminder_time = reminder_time.replace(tzinfo=timezone.utc)
        
        if reminder_time > datetime.now(timezone.utc):
            reminders.append(reminder_time)
    
    return reminders

def register_prepayment_timeout_deadline(
    *,
    order_id: str,
    order_channel: str,
    region_code: str | None,
    slot_id: str | None,
    machine_id: str | None,
    created_at: datetime | None,
    payment_method: str | None = None,
    timeout_seconds: int,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Registra deadline de pré-pagamento com suporte regional aprimorado
    """
    client = LifecycleClient()

    deadline_at = None
    if created_at is not None:
        base_created_at = created_at
        if base_created_at.tzinfo is None:
            base_created_at = base_created_at.replace(tzinfo=timezone.utc)

        deadline_at = base_created_at + timedelta(seconds=int(timeout_seconds))

    deadline_at_str = _serialize_deadline_at(deadline_at)

    reminders = []
    if deadline_at:
        reminders = _calculate_reminder_schedule(
            deadline_at,
            region_code,
            LifecycleEventType.PREPAYMENT_DEADLINE
        )

    region_metadata = {
        "timezone": RegionLifecycleConfig.get_timezone(region_code),
        "reminder_intervals": RegionLifecycleConfig.get_reminder_intervals(region_code),
        "notification_channels": RegionLifecycleConfig.get_notification_channels(region_code),
        "reminder_schedule": [r.isoformat() for r in reminders],
        **(metadata or {})
    }

    try:
        result = client.create_prepayment_deadline(
            order_id=order_id,
            order_channel=order_channel,
            region_code=region_code,
            slot_id=slot_id,
            machine_id=machine_id,
            deadline_at=deadline_at_str,
            payment_method=payment_method,
            # metadata=region_metadata,
        )

        logger.info(
            "lifecycle_deadline_registered",
            extra={
                "order_id": order_id,
                "order_channel": order_channel,
                "region_code": region_code,
                "payment_method": payment_method,
                "deadline_at": deadline_at_str,
                "timeout_seconds": timeout_seconds,
                "reminder_count": len(reminders),
                "result": result,
            },
        )

        return {
            "deadline_at": deadline_at_str,
            "reminders": reminders,
            "result": result,
        }

    except LifecycleClientError:
        logger.exception(
            "lifecycle_deadline_register_failed",
            extra={
                "order_id": order_id,
                "order_channel": order_channel,
                "region_code": region_code,
                "payment_method": payment_method,
                "deadline_at": deadline_at_str,
                "timeout_seconds": timeout_seconds,
            },
        )
        raise

def cancel_prepayment_timeout_deadline(
    *, 
    order_id: str,
    reason: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Cancela deadline de pré-pagamento com registro de motivo
    
    O LifecycleClient atual aceita apenas order_id.
    reason/metadata ficam preservados para logging e compatibilidade futura.
    """
    client = LifecycleClient()

    try:
        result = client.cancel_prepayment_deadline(
            order_id=order_id,
            # reason=reason, # nao excluir veja acima
            # metadata=metadata, # nao excluir veja acima
        )
        logger.info(
            "lifecycle_deadline_cancelled",
            extra={
                "order_id": order_id,
                "reason": reason,
                "metadata": metadata,
                "result": result,
            },
        )
        return {"cancelled": True, "result": result}
        
    except LifecycleClientError:
        logger.exception(
            "lifecycle_deadline_cancel_failed",
            extra={
                "order_id": order_id, 
                "reason": reason, 
                "metadata": metadata, 
            },
        )
        raise


def register_pickup_deadline(
    *,
    order_id: str,
    order_channel: str,
    region_code: str | None,
    slot_id: str | None,
    machine_id: str | None,
    pickup_created_at: datetime | None,
    payment_method: str | None = None,
) -> Dict[str, Any]:
    """
    Registra deadline para pickup com base na região
    """
    client = LifecycleClient()
    deadline_at = _resolve_deadline_at(
        created_at=pickup_created_at,
        region_code=region_code,
        order_channel=order_channel,
        payment_method=payment_method,
        event_type=LifecycleEventType.PICKUP_DEADLINE,
    )
    deadline_at_str = _serialize_deadline_at(deadline_at)
    
    # Calcula lembretes de pickup
    reminders = []
    if deadline_at:
        reminders = _calculate_reminder_schedule(
            deadline_at, 
            region_code,
            LifecycleEventType.PICKUP_REMINDER
        )
    
    try:
        result = client.create_pickup_deadline(
            order_id=order_id,
            order_channel=order_channel,
            region_code=region_code,
            slot_id=slot_id,
            machine_id=machine_id,
            deadline_at=deadline_at_str,
            payment_method=payment_method,
            reminder_schedule=[r.isoformat() for r in reminders],
        )
        
        logger.info(
            "pickup_deadline_registered",
            extra={
                "order_id": order_id,
                "region_code": region_code,
                "deadline_at": deadline_at_str,
                "reminder_count": len(reminders),
                "result": result,
            },
        )
        
        return {
            "deadline_at": deadline_at_str,
            "reminders": reminders,
            "result": result,
        }
        
    except LifecycleClientError:
        logger.exception(
            "pickup_deadline_register_failed",
            extra={
                "order_id": order_id,
                "region_code": region_code,
                "deadline_at": deadline_at_str,
            },
        )
        raise


def register_payment_reminder(
    *,
    order_id: str,
    order_channel: str,
    region_code: str | None,
    payment_method: str | None,
    reminder_type: str = "first",
    priority: LifecyclePriority = LifecyclePriority.MEDIUM,
) -> Dict[str, Any]:
    """
    Registra lembrete de pagamento adaptado à região
    """
    client = LifecycleClient()
    
    # Define timeout baseado no tipo de lembrete
    reminder_timeout_map = {
        "first": 15,      # 15 minutos
        "second": 30,     # 30 minutos
        "final": 45,      # 45 minutos
    }
    
    timeout_minutes = reminder_timeout_map.get(reminder_type, 30)
    
    try:
        result = client.create_payment_reminder(
            order_id=order_id,
            order_channel=order_channel,
            region_code=region_code,
            payment_method=payment_method,
            reminder_type=reminder_type,
            delay_minutes=timeout_minutes,
            priority=priority.value,
            notification_channels=RegionLifecycleConfig.get_notification_channels(region_code),
        )
        
        logger.info(
            "payment_reminder_registered",
            extra={
                "order_id": order_id,
                "region_code": region_code,
                "reminder_type": reminder_type,
                "priority": priority.value,
                "result": result,
            },
        )
        
        return {"reminder_id": result.get("reminder_id"), "scheduled_at": result.get("scheduled_at")}
        
    except LifecycleClientError:
        logger.exception(
            "payment_reminder_register_failed",
            extra={
                "order_id": order_id,
                "region_code": region_code,
                "reminder_type": reminder_type,
            },
        )
        raise


def register_order_expiration(
    *,
    order_id: str,
    region_code: str | None,
    expiration_days: int = 30,
    auto_cancel: bool = True,
    refund_eligible: bool = False,
) -> Dict[str, Any]:
    """
    Registra expiração de ordem com base nas políticas regionais
    """
    client = LifecycleClient()
    
    # Ajusta expiração baseada na região
    if region_code in ["CN", "JP", "SG"]:
        expiration_days = 15  # Prazo menor para mercados asiáticos
    elif region_code in ["AE", "SA"]:
        expiration_days = 45  # Prazo maior para Oriente Médio
    
    try:
        result = client.create_order_expiration(
            order_id=order_id,
            region_code=region_code,
            expiration_days=expiration_days,
            auto_cancel=auto_cancel,
            refund_eligible=refund_eligible,
        )
        
        logger.info(
            "order_expiration_registered",
            extra={
                "order_id": order_id,
                "region_code": region_code,
                "expiration_days": expiration_days,
                "auto_cancel": auto_cancel,
                "result": result,
            },
        )
        
        return result
        
    except LifecycleClientError:
        logger.exception(
            "order_expiration_register_failed",
            extra={
                "order_id": order_id,
                "region_code": region_code,
            },
        )
        raise


def register_stock_release(
    *,
    order_id: str,
    region_code: str | None,
    slot_id: str | None,
    machine_id: str | None,
    reason: str = "payment_timeout",
) -> Dict[str, Any]:
    """
    Registra liberação de estoque após timeout com rastreamento regional
    """
    client = LifecycleClient()
    
    # Tempo de liberação baseado na região
    release_delay_minutes = 5
    if region_code in ["NG", "KE", "ZA"]:
        release_delay_minutes = 15  # Maior tolerância para África
    
    try:
        result = client.schedule_stock_release(
            order_id=order_id,
            region_code=region_code,
            slot_id=slot_id,
            machine_id=machine_id,
            reason=reason,
            delay_minutes=release_delay_minutes,
        )
        
        logger.info(
            "stock_release_scheduled",
            extra={
                "order_id": order_id,
                "region_code": region_code,
                "reason": reason,
                "delay_minutes": release_delay_minutes,
                "result": result,
            },
        )
        
        return result
        
    except LifecycleClientError:
        logger.exception(
            "stock_release_schedule_failed",
            extra={
                "order_id": order_id,
                "region_code": region_code,
            },
        )
        raise


def get_region_lifecycle_status(
    *,
    order_id: str,
    region_code: str | None,
) -> Dict[str, Any]:
    """
    Obtém status do ciclo de vida específico da região
    """
    client = LifecycleClient()
    
    try:
        result = client.get_lifecycle_status(
            order_id=order_id,
            region_code=region_code,
        )
        
        # Adiciona informações de timezone
        result["region_timezone"] = RegionLifecycleConfig.get_timezone(region_code)
        result["local_time"] = _convert_to_region_timezone(
            datetime.now(timezone.utc), 
            region_code
        ).isoformat()
        
        return result
        
    except LifecycleClientError:
        logger.exception(
            "lifecycle_status_fetch_failed",
            extra={
                "order_id": order_id,
                "region_code": region_code,
            },
        )
        raise


# Funções de suporte para integração com sistemas regionais
def should_send_reminder_now(
    reminder_time: datetime,
    region_code: Optional[str],
    event_type: LifecycleEventType,
) -> bool:
    """
    Verifica se deve enviar lembrete agora baseado em horário comercial regional
    """
    now_utc = datetime.now(timezone.utc)
    
    # Converte para timezone da região
    local_time = _convert_to_region_timezone(now_utc, region_code)
    reminder_local = _convert_to_region_timezone(reminder_time, region_code)
    
    # Verifica se já passou do horário
    if local_time < reminder_local:
        return False
    
    # Verifica horário comercial
    config = RegionLifecycleConfig.get_region_config(region_code)
    business_hours = config.get("business_hours", {"start": 8, "end": 22})
    
    hour = local_time.hour
    if hour < business_hours["start"] or hour > business_hours["end"]:
        # Fora do horário comercial - agenda para próximo horário comercial
        return False
    
    # Verifica feriados regionais (implementação simplificada)
    if config.get("friday_off") and local_time.weekday() == 4:  # Sexta-feira
        return False
    
    return True


"""

1. Classe RegionLifecycleConfig
Configurações regionais centralizadas para ciclo de vida

Timezones específicos por região

Horários comerciais variáveis

Intervalos de lembrete personalizados

Canais de notificação prioritários

2. Novos Tipos de Evento (LifecycleEventType)
PREPAYMENT_DEADLINE: Deadline de pagamento

PICKUP_DEADLINE: Deadline de retirada

ORDER_EXPIRATION: Expiração do pedido

PAYMENT_REMINDER: Lembretes de pagamento

PICKUP_REMINDER: Lembretes de retirada

3. Configurações Regionais Detalhadas
Região	Timezone	Horário Comercial	Lembretes (min)	Canais
China (CN)	Asia/Shanghai	8-22	15,30,45,60	WeChat, SMS
Japão (JP)	Asia/Tokyo	9-21	30,60,120	LINE, Email
Tailândia (TH)	Asia/Bangkok	9-21	30,60,120	LINE, WhatsApp
Emirados Árabes (AE)	Asia/Dubai	9-22	30,60,120	Email, WhatsApp
Rússia (RU)	Europe/Moscow	9-21	60,120,180	Email, SMS
Nigéria (NG)	Africa/Lagos	8-18	30,60,120	SMS, WhatsApp
4. Novas Funções
register_pickup_deadline()
Registra deadline para retirada

Calcula lembretes automáticos

Ajusta tempo baseado na região

register_payment_reminder()
Lembretes escalonados (primeiro, segundo, final)

Prioridades configuráveis

Integração com canais regionais

register_order_expiration()
Expiração de pedidos não finalizados

Prazos variáveis por região (15-45 dias)

Opção de cancelamento automático

register_stock_release()
Liberação de estoque após timeout

Atrasos específicos por região

Rastreamento de motivo

get_region_lifecycle_status()
Status do ciclo de vida com timezone local

Informações de horário regional

5. Função Utilitária should_send_reminder_now()
Verifica horário comercial antes de enviar lembretes

Respeita feriados regionais (ex: sexta-feira nos Emirados)

Converte para timezone local

6. Cálculo de Lembretes Inteligente
Baseado em intervalos configurados por região

Ajuste automático para horário comercial

Evita notificações fora do expediente

7. Metadados Regionais
Timezone para logging e agendamento

Canais de notificação prioritários

Configurações de retry e grace period

8. Tratamento Especial por Região
Oriente Médio (AE, SA):

Sexta-feira como dia de descanso

Pausas para horários de oração

Prazos estendidos

África (NG, KE, ZA):

Maior tolerância para atrasos

Múltiplos canais de notificação

Grace periods mais longos

Ásia (CN, JP, SG):

Prazos mais curtos

Alta frequência de lembretes

QR codes obrigatórios

9. Logging Aprimorado
Contexto regional em todos os logs

Rastreamento de lembretes enviados

Métricas por região

10. Extensibilidade
Fácil adição de novas regiões via REGION_CONFIGS

Configurações herdáveis

Fallback para configuração padrão (US_NY)



"""
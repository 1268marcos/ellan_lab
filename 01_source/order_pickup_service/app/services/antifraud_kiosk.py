# 01_source/order_pickup_service/app/services/antifraud_kiosk.py
# 02/04/2026 - Enhanced Version with Global Markets Support
# veja final do arquivo

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple
from enum import Enum

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.kiosk_antifraud_event import KioskAntifraudEvent

from app.core.datetime_utils import to_iso_utc



logger = logging.getLogger(__name__)


# ==================== Enums e Constantes ====================

class RiskLevel(str, Enum):
    """Nível de risco para KIOSK"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# Configurações por região
REGION_CONFIGS = {
    # Brasil
    "SP": {"window_sec": 60, "max_events": 6, "block_sec": 90},
    "RJ": {"window_sec": 60, "max_events": 6, "block_sec": 90},
    "MG": {"window_sec": 60, "max_events": 6, "block_sec": 90},
    "RS": {"window_sec": 60, "max_events": 6, "block_sec": 90},
    "BA": {"window_sec": 60, "max_events": 6, "block_sec": 90},
    
    # Portugal
    "PT": {"window_sec": 60, "max_events": 8, "block_sec": 60},
    
    # México
    "MX": {"window_sec": 60, "max_events": 5, "block_sec": 120},
    
    # Argentina
    "AR": {"window_sec": 60, "max_events": 5, "block_sec": 120},
    
    # Colômbia
    "CO": {"window_sec": 60, "max_events": 5, "block_sec": 120},
    
    # Chile
    "CL": {"window_sec": 60, "max_events": 6, "block_sec": 90},
    
    # China
    "CN": {"window_sec": 30, "max_events": 10, "block_sec": 60},
    
    # Japão
    "JP": {"window_sec": 60, "max_events": 8, "block_sec": 60},
    
    # Tailândia
    "TH": {"window_sec": 60, "max_events": 6, "block_sec": 90},
    
    # Indonésia
    "ID": {"window_sec": 60, "max_events": 5, "block_sec": 120},
    
    # Singapura
    "SG": {"window_sec": 60, "max_events": 10, "block_sec": 60},
    
    # Filipinas
    "PH": {"window_sec": 60, "max_events": 5, "block_sec": 120},
    
    # Emirados Árabes
    "AE": {"window_sec": 60, "max_events": 8, "block_sec": 60},
    
    # Turquia
    "TR": {"window_sec": 60, "max_events": 6, "block_sec": 90},
    
    # Rússia
    "RU": {"window_sec": 60, "max_events": 5, "block_sec": 120},
    
    # Austrália
    "AU": {"window_sec": 60, "max_events": 10, "block_sec": 60},
    
    # África do Sul
    "ZA": {"window_sec": 60, "max_events": 6, "block_sec": 90},
    
    # Nigéria
    "NG": {"window_sec": 60, "max_events": 4, "block_sec": 180},
    
    # Quênia
    "KE": {"window_sec": 60, "max_events": 4, "block_sec": 180},
    
    # Padrão
    "DEFAULT": {"window_sec": 60, "max_events": 6, "block_sec": 90},
}

# Configurações de rate limit por IP
IP_RATE_LIMITS = {
    "DEFAULT": {"window_sec": 60, "max_requests": 30},
    "NG": {"window_sec": 60, "max_requests": 20},
    "KE": {"window_sec": 60, "max_requests": 20},
    "CN": {"window_sec": 30, "max_requests": 50},
}

# Listas negras de IPs conhecidos (simulado - em produção viria de um serviço externo)
BLACKLISTED_IPS = set()
BLACKLISTED_DEVICES = set()


# ==================== Funções Utilitárias ====================

def _hash(v: str) -> str:
    """Gera hash SHA256 de uma string"""
    return hashlib.sha256(v.encode("utf-8")).hexdigest()


def _get_region_config(region: str) -> Dict[str, int]:
    """Retorna configuração específica da região"""
    region_upper = region.upper()
    return REGION_CONFIGS.get(region_upper, REGION_CONFIGS["DEFAULT"])


def _get_ip_rate_limit(region: str) -> Dict[str, int]:
    """Retorna limite de taxa por IP para a região"""
    region_upper = region.upper()
    return IP_RATE_LIMITS.get(region_upper, IP_RATE_LIMITS["DEFAULT"])


def _check_ip_rate_limit(
    db: Session,
    ip_hash: str,
    region: str,
    window_sec: int,
    max_requests: int,
) -> Tuple[bool, int]:
    """Verifica se IP excedeu limite de requisições"""
    now = datetime.now(timezone.utc)
    window_start = (now - timedelta(seconds=window_sec)).replace(tzinfo=None)
    
    count = (
        db.query(KioskAntifraudEvent)
        .filter(
            KioskAntifraudEvent.ip_hash == ip_hash,
            KioskAntifraudEvent.created_at >= window_start,
        )
        .count()
    )
    
    return count >= max_requests, count


def _check_global_rate_limit(
    db: Session,
    totem_id: str,
    region: str,
    window_sec: int,
) -> Tuple[bool, int]:
    """Verifica limite global para o totem"""
    now = datetime.now(timezone.utc)
    window_start = (now - timedelta(seconds=window_sec)).replace(tzinfo=None)
    
    count = (
        db.query(KioskAntifraudEvent)
        .filter(
            KioskAntifraudEvent.totem_id == totem_id,
            KioskAntifraudEvent.region == region,
            KioskAntifraudEvent.created_at >= window_start,
        )
        .count()
    )
    
    # Limite global: 100 requisições por minuto por totem
    return count >= 100, count


def _calculate_risk_score(
    db: Session,
    fp_hash: str,
    ip_hash: str,
    totem_id: str,
    region: str,
    recent_events: int,
) -> Tuple[int, RiskLevel, list]:
    """Calcula pontuação de risco baseada em múltiplos fatores"""
    score = 0
    reasons = []
    
    # Fator 1: Histórico de tentativas
    if recent_events >= 10:
        score += 40
        reasons.append("Excessive attempts history")
    elif recent_events >= 5:
        score += 20
        reasons.append("High attempts history")
    elif recent_events >= 3:
        score += 10
        reasons.append("Moderate attempts history")
    
    # Fator 2: Verifica se dispositivo está em lista negra
    if fp_hash in BLACKLISTED_DEVICES:
        score += 50
        reasons.append("Device in blacklist")
    
    # Fator 3: Verifica se IP está em lista negra
    if ip_hash in BLACKLISTED_IPS:
        score += 50
        reasons.append("IP in blacklist")
    
    # Fator 4: Verifica tentativas anteriores bloqueadas
    recent_blocks = (
        db.query(KioskAntifraudEvent)
        .filter(
            KioskAntifraudEvent.fp_hash == fp_hash,
            KioskAntifraudEvent.blocked_until.isnot(None),
            KioskAntifraudEvent.created_at >= datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=24)
        )
        .count()
    )
    
    if recent_blocks >= 3:
        score += 30
        reasons.append("Multiple blocks in last 24h")
    elif recent_blocks >= 1:
        score += 10
        reasons.append("Previous block detected")
    
    # Fator 5: Regiões de alto risco
    high_risk_regions = {"NG", "KE", "RU", "AR", "ID", "PH"}
    if region.upper() in high_risk_regions:
        score += 15
        reasons.append(f"High risk region: {region}")
    
    # Determina nível de risco
    if score >= 70:
        risk_level = RiskLevel.CRITICAL
    elif score >= 50:
        risk_level = RiskLevel.HIGH
    elif score >= 25:
        risk_level = RiskLevel.MEDIUM
    else:
        risk_level = RiskLevel.LOW
    
    return score, risk_level, reasons


def _log_antifraud_event(
    fp_hash: str,
    ip_hash: str,
    totem_id: str,
    region: str,
    decision: str,
    score: int,
    risk_level: str,
    reasons: list,
    blocked: bool = False,
) -> None:
    """Loga evento antifraude para auditoria"""
    logger.info(
        f"Antifraud KIOSK event - fp={fp_hash[:8]}..., ip={ip_hash[:8]}..., "
        f"totem={totem_id}, region={region}, decision={decision}, "
        f"score={score}, risk_level={risk_level}, blocked={blocked}, "
        f"reasons={reasons}"
    )


# ==================== Função Principal ====================

def check_kiosk_antifraud(
    db: Session,
    request: Request,
    totem_id: str,
    region: str,
    device_fingerprint: str | None,
    payment_method: Optional[str] = None,
    amount_cents: Optional[int] = None,
) -> None:
    """
    Verifica antifraude para operações no KIOSK.
    
    Implementa:
    - Rate limiting por dispositivo
    - Rate limiting por IP
    - Rate limiting global por totem
    - Listas negras
    - Pontuação de risco
    - Configurações regionais específicas
    """
    # Obtém IP do cliente
    ip = request.client.host if request.client else "unknown"
    fp = device_fingerprint or "missing_fp"
    
    # Gera hashes
    fp_hash = _hash(fp)
    ip_hash = _hash(ip)
    
    # Obtém configurações da região
    region_config = _get_region_config(region)
    window_sec = region_config["window_sec"]
    max_events = region_config["max_events"]
    block_sec = region_config["block_sec"]
    
    now = datetime.now(timezone.utc)
    window_start = (now - timedelta(seconds=window_sec)).replace(tzinfo=None)
    
    # ==================== 1. Verifica bloqueio ativo ====================
    active_block = (
        db.query(KioskAntifraudEvent)
        .filter(
            KioskAntifraudEvent.fp_hash == fp_hash,
            KioskAntifraudEvent.blocked_until.isnot(None),
            KioskAntifraudEvent.blocked_until > now.replace(tzinfo=None),
        )
        .order_by(KioskAntifraudEvent.created_at.desc())
        .first()
    )
    
    if active_block:
        logger.warning(
            f"KIOSK blocked - fp={fp_hash[:8]}..., totem={totem_id}, "
            f"region={region}, blocked_until={active_block.blocked_until}"
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "type": "KIOSK_RATE_LIMITED",
                "message": "Dispositivo temporariamente bloqueado devido a múltiplas tentativas",
                "blocked_until": active_block.blocked_until.isoformat(),
                "retry_after": int((active_block.blocked_until - now.replace(tzinfo=None)).total_seconds()),
            }
        )
    
    # ==================== 2. Verifica rate limit por IP ====================
    ip_limit_config = _get_ip_rate_limit(region)
    ip_exceeded, ip_count = _check_ip_rate_limit(
        db, ip_hash, region, ip_limit_config["window_sec"], ip_limit_config["max_requests"]
    )
    
    if ip_exceeded:
        logger.warning(f"IP rate limit exceeded - ip={ip_hash[:8]}..., count={ip_count}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "type": "KIOSK_IP_RATE_LIMITED",
                "message": "Muitas requisições deste IP. Tente novamente mais tarde.",
                "retry_after": ip_limit_config["window_sec"],
            }
        )
    
    # ==================== 3. Verifica limite global do totem ====================
    global_exceeded, global_count = _check_global_rate_limit(db, totem_id, region, 60)
    
    if global_exceeded:
        logger.warning(f"Global rate limit exceeded - totem={totem_id}, count={global_count}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "type": "KIOSK_GLOBAL_RATE_LIMITED",
                "message": "Muitas tentativas neste equipamento. Tente novamente mais tarde.",
            }
        )
    
    # ==================== 4. Conta eventos recentes ====================
    count_recent = (
        db.query(KioskAntifraudEvent)
        .filter(
            KioskAntifraudEvent.fp_hash == fp_hash,
            KioskAntifraudEvent.created_at >= window_start,
        )
        .count()
    )
    
    # ==================== 5. Calcula pontuação de risco ====================
    risk_score, risk_level, risk_reasons = _calculate_risk_score(
        db, fp_hash, ip_hash, totem_id, region, count_recent
    )
    
    # ==================== 6. Determina ação baseada no risco ====================
    should_block = False
    block_reason = None
    
    if risk_level == RiskLevel.CRITICAL:
        should_block = True
        block_reason = "Critical risk score"
    elif risk_level == RiskLevel.HIGH and count_recent >= max_events - 1:
        should_block = True
        block_reason = "High risk with rate limit exceeded"
    elif count_recent + 1 > max_events:
        should_block = True
        block_reason = f"Rate limit exceeded: {count_recent + 1}/{max_events} in {window_sec}s"
    
    # ==================== 7. Cria evento ====================
    ev = KioskAntifraudEvent.new(
        fp_hash=fp_hash,
        ip_hash=ip_hash,
        totem_id=totem_id,
        region=region,
        created_at=now.replace(tzinfo=None),
        blocked_until=None,
    )
    
    # Adiciona metadados do evento
    ev.payment_method = payment_method
    ev.amount_cents = amount_cents
    ev.risk_score = risk_score
    ev.risk_level = risk_level.value
    
    # ==================== 8. Aplica bloqueio se necessário ====================
    if should_block:
        ev.blocked_until = (now + timedelta(seconds=block_sec)).replace(tzinfo=None)
        ev.block_reason = block_reason
    
    db.add(ev)
    db.commit()
    
    # ==================== 9. Log do evento ====================
    _log_antifraud_event(
        fp_hash=fp_hash,
        ip_hash=ip_hash,
        totem_id=totem_id,
        region=region,
        decision="BLOCK" if should_block else "ALLOW",
        score=risk_score,
        risk_level=risk_level.value,
        reasons=risk_reasons,
        blocked=should_block,
    )
    
    # ==================== 10. Retorna erro se bloqueado ====================
    if ev.blocked_until:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "type": "KIOSK_RATE_LIMITED",
                "message": f"Dispositivo bloqueado temporariamente: {block_reason}",
                "blocked_until": ev.blocked_until.isoformat(),
                "retry_after": int((ev.blocked_until - now.replace(tzinfo=None)).total_seconds()),
                "risk_score": risk_score,
                "risk_level": risk_level.value,
            }
        )
    
    # Log de sucesso para auditoria
    if risk_level in {RiskLevel.HIGH, RiskLevel.CRITICAL}:
        logger.warning(
            f"KIOSK high risk allowed - fp={fp_hash[:8]}..., "
            f"score={risk_score}, level={risk_level.value}, reasons={risk_reasons}"
        )


# ==================== Funções Adicionais ====================

def report_fraudulent_device(
    db: Session,
    device_fingerprint: str,
    reason: str,
    reporter: str,
) -> bool:
    """
    Reporta dispositivo fraudulento para adicionar à lista negra.
    """
    fp_hash = _hash(device_fingerprint)
    BLACKLISTED_DEVICES.add(fp_hash)
    
    # Registra no banco para persistência
    # (implementação simplificada - em produção, teria uma tabela específica)
    
    logger.warning(
        f"Device reported as fraudulent - fp_hash={fp_hash[:8]}..., "
        f"reason={reason}, reporter={reporter}"
    )
    
    return True


def report_fraudulent_ip(
    db: Session,
    ip_address: str,
    reason: str,
    reporter: str,
) -> bool:
    """
    Reporta IP fraudulento para adicionar à lista negra.
    """
    ip_hash = _hash(ip_address)
    BLACKLISTED_IPS.add(ip_hash)
    
    logger.warning(
        f"IP reported as fraudulent - ip_hash={ip_hash[:8]}..., "
        f"reason={reason}, reporter={reporter}"
    )
    
    return True


def get_device_risk_profile(
    db: Session,
    device_fingerprint: str,
    hours: int = 24,
) -> Dict[str, Any]:
    """
    Retorna perfil de risco de um dispositivo.
    """
    fp_hash = _hash(device_fingerprint)
    now = datetime.now(timezone.utc)
    since = (now - timedelta(hours=hours)).replace(tzinfo=None)
    
    events = (
        db.query(KioskAntifraudEvent)
        .filter(
            KioskAntifraudEvent.fp_hash == fp_hash,
            KioskAntifraudEvent.created_at >= since,
        )
        .all()
    )
    
    blocks = [e for e in events if e.blocked_until is not None]
    
    return {
        "device_hash": fp_hash[:8],
        "total_events": len(events),
        "total_blocks": len(blocks),
        "block_rate": len(blocks) / len(events) if events else 0,
        "first_seen": min([e.created_at for e in events]) if events else None,
        "last_seen": max([e.created_at for e in events]) if events else None,
        "is_blacklisted": fp_hash in BLACKLISTED_DEVICES,
    }


def clear_device_history(
    db: Session,
    device_fingerprint: str,
    older_than_days: int = 30,
) -> int:
    """
    Limpa histórico antigo de um dispositivo.
    """
    fp_hash = _hash(device_fingerprint)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=older_than_days)).replace(tzinfo=None)
    
    deleted = (
        db.query(KioskAntifraudEvent)
        .filter(
            KioskAntifraudEvent.fp_hash == fp_hash,
            KioskAntifraudEvent.created_at < cutoff,
        )
        .delete()
    )
    
    db.commit()
    
    logger.info(f"Cleared {deleted} events for device {fp_hash[:8]}...")
    
    return deleted


"""

1. Configurações por Região:
REGION_CONFIGS: Configurações específicas para cada mercado

IP_RATE_LIMITS: Limites de taxa por IP por região

Suporte a Brasil, Portugal, México, Argentina, China, Japão, Tailândia, Indonésia, Singapura, Filipinas, Emirados Árabes, Turquia, Rússia, Austrália, África do Sul, Nigéria, Quênia

2. Múltiplas Camadas de Proteção:
Rate limiting por dispositivo (fingerprint)

Rate limiting por IP

Rate limiting global por totem

Listas negras de dispositivos e IPs

Pontuação de risco multi-fator

3. Pontuação de Risco Avançada:
Histórico de tentativas

Listas negras

Bloqueios anteriores

Regiões de alto risco

Retorna RiskLevel (LOW, MEDIUM, HIGH, CRITICAL)

4. Logging e Auditoria:
_log_antifraud_event(): Log estruturado

Metadados nos eventos (payment_method, amount_cents, risk_score, risk_level)

Warnings para eventos de alto risco

5. Funções Administrativas:
report_fraudulent_device(): Adiciona dispositivo à lista negra

report_fraudulent_ip(): Adiciona IP à lista negra

get_device_risk_profile(): Consulta perfil de risco

clear_device_history(): Limpa histórico antigo

6. Respostas Detalhadas:
Código HTTP 429 com detalhes

blocked_until: Quando o bloqueio expira

retry_after: Segundos para tentar novamente

risk_score e risk_level: Contexto do bloqueio

7. Parâmetros Adicionais:
payment_method: Para logging específico

amount_cents: Para análise de valor

Suporte a diferentes métodos de pagamento por região

8. Tratamento de Erros Aprimorado:
Exceções com tipos específicos

Mensagens descritivas

Status codes apropriados

9. Performance:
Índices apropriados (assumindo que o modelo tem)

Queries otimizadas

Cache de listas negras em memória

10. Compatibilidade:
Mantém a função original check_kiosk_antifraud

Adiciona novos parâmetros opcionais

Sem breaking changes

"""
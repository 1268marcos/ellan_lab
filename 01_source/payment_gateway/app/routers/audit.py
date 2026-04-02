# 01_source/payment_gateway/app/routers/audit.py

from __future__ import annotations

import time
from typing import Optional

from fastapi import APIRouter, Query

# from app.core.config import SQLITE_PATH
from app.core.config import settings
# SQLITE_PATH = settings.SQLITE_PATH

from app.services.sqlite_service import SQLiteService
from app.services.risk_events_service import RiskEventsService

router = APIRouter()


@router.get("/audit/events")
def audit_events(
    since_hours: int = Query(24, ge=0, le=720, description="Janela de busca em horas"),
    decision: Optional[str] = Query(None, description="ALLOW|CHALLENGE|BLOCK"),
    region: Optional[str] = Query(None, description="SP|PT"),
    # porta: Optional[int] = Query(None, ge=1, le=24, description="Número da gaveta"),
    porta: Optional[int] = Query(
        None, 
        ge=1, 
        description="Número da gaveta/slot (validado dinamicamente no backend)"
    ),
    request_id: Optional[str] = Query(None, description="ID da requisição para buscar evento específico"),
    policy_id: Optional[str] = Query(None, description="Filtrar por política de risco"),
    event_type: Optional[str] = Query(None, description="Tipo de evento (ex: PAYMENT, WITHDRAWAL)"),
    locker_id: Optional[str] = Query(None, description="ID do locker"),
    limit: int = Query(100, ge=1, le=500, description="Número máximo de registros"),
    offset: int = Query(0, ge=0, description="Deslocamento para paginação"),
    include_signals: bool = Query(False, description="Incluir dados de sinais (IP/device hash)"),
    compact: bool = Query(False, description="Versão compacta (sem reasons brutos)"),
    sort_by: str = Query("created_at", description="Campo para ordenação"),
    sort_order: str = Query("DESC", description="ASC ou DESC"),
):
    """
    01_source/payment_gateway/app/routers/audity.py

    Endpoint de auditoria para consultar eventos de risco com filtros avançados.

    Retorna eventos de risco com paginação, filtros por data, decisão, região, etc.
    """
    sqlite = SQLiteService(settings.SQLITE_PATH)
    sqlite.migrate()
    svc = RiskEventsService(sqlite)

    # Calcular timestamps baseado em since_hours
    now = int(time.time())
    start_epoch = now - (since_hours * 3600)  # Converter horas para segundos
    end_epoch = now

    # Se request_id for fornecido, ignorar outros filtros e buscar específico
    if request_id:
        # Usar list_events com filtro especial OU implementar método get_by_request_id
        # Por simplicidade, vamos adaptar para usar o método existente
        return get_event_by_request_id(svc, request_id)

    # Chamar o método list_events com os parâmetros corretos
    data = svc.list_events(
        start_epoch=start_epoch,
        end_epoch=end_epoch,
        decision=decision,
        region=region,
        porta=porta,
        policy_id=policy_id,
        event_type=event_type,
        locker_id=locker_id,
        limit=limit,
        offset=offset,
        include_signals=include_signals,
        compact=compact,
        sort_by=sort_by,
        sort_order=sort_order
    )

    return {
        "service": "payment_gateway",
        "endpoint": "/audit/events",
        "timestamp": time.time(),
        "type": "RISK_EVENTS",
        "query_params": {
            "since_hours": since_hours,
            "window_start": start_epoch,
            "window_end": end_epoch,
            "filters_applied": data["metadata"]["filters_applied"]
        },
        **data,
    }


@router.get("/audit/events/{event_id}")
def audit_event_detail(event_id: int):
    """
    01_source/payment_gateway/app/routers/audity.py

    Busca um evento específico pelo ID.
    """
    sqlite = SQLiteService(settings.SQLITE_PATH)
    sqlite.migrate()
    svc = RiskEventsService(sqlite)
    
    # Método auxiliar para buscar por ID
    event = get_event_by_id(svc, event_id)
    
    if not event:
        return {
            "service": "payment_gateway",
            "endpoint": f"/audit/events/{event_id}",
            "timestamp": time.time(),
            "error": "Event not found",
            "status_code": 404
        }
    
    return {
        "service": "payment_gateway",
        "endpoint": f"/audit/events/{event_id}",
        "timestamp": time.time(),
        "type": "RISK_EVENT_DETAIL",
        "event": event
    }


@router.get("/audit/forensics")
def audit_forensics(
    start_hours_ago: int = Query(24, ge=1, le=168, description="Início da janela (horas atrás)"),
    end_hours_ago: int = Query(0, ge=0, le=168, description="Fim da janela (horas atrás, 0 = agora)"),
):
    """
    01_source/payment_gateway/app/routers/audity.py

    Endpoint forense com estatísticas agregadas e amostras de eventos.
    """
    sqlite = SQLiteService(settings.SQLITE_PATH)
    sqlite.migrate()
    svc = RiskEventsService(sqlite)
    
    now = int(time.time())
    start_epoch = now - (start_hours_ago * 3600)
    end_epoch = now - (end_hours_ago * 3600)
    
    # Garantir ordem cronológica correta
    if start_epoch > end_epoch:
        start_epoch, end_epoch = end_epoch, start_epoch
    
    forensics_data = svc.forensics_between(start_epoch, end_epoch)
    
    return {
        "service": "payment_gateway",
        "endpoint": "/audit/forensics",
        "timestamp": time.time(),
        "type": "RISK_FORENSICS",
        **forensics_data
    }


@router.get("/audit/self_check")
def audit_self_check(hours: int = Query(24, ge=1, le=168)):
    """
    01_source/payment_gateway/app/routers/audity.py

    Auto-diagnóstico do sistema de risco.
    Retorna severidade baseada em métricas de bloqueios.
    """
    sqlite = SQLiteService(settings.SQLITE_PATH)
    sqlite.migrate()
    svc = RiskEventsService(sqlite)

    # Usar list_events para obter estatísticas
    now = int(time.time())
    start_epoch = now - (hours * 3600)
    
    events_data = svc.list_events(
        start_epoch=start_epoch,
        end_epoch=now,
        limit=10000,  # Limite alto para estatísticas
        compact=True
    )
    
    # Calcular estatísticas manualmente a partir dos eventos
    stats = {
        "total_events": events_data["metadata"]["total"],
        "by_decision": events_data["stats"].get("decisions", {}),
        "by_region": events_data["stats"].get("regions", {}),
        "time_window_hours": hours,
        "start_epoch": start_epoch,
        "end_epoch": now
    }

    # severity simples v1
    decisions = stats["by_decision"]
    blocks = decisions.get("BLOCK", 0)
    challenges = decisions.get("CHALLENGE", 0)

    if blocks >= 10:
        severity = "HIGH"
        severity_code = "GATEWAY_RISK_BLOCK_SPIKE"
        summary = f"🚨 Alerta: {blocks} bloqueios nas últimas {hours}h (acima do limite de 10)"
    elif blocks >= 3 or challenges >= 20:
        severity = "MEDIUM"
        severity_code = "GATEWAY_RISK_ELEVATED"
        summary = f"⚠️ Atenção: {blocks} bloqueios, {challenges} desafios nas últimas {hours}h"
    else:
        severity = "INFO"
        severity_code = "GATEWAY_RISK_OK"
        summary = f"✅ OK: {blocks} bloqueios nas últimas {hours}h (dentro do esperado)"

    return {
        "service": "payment_gateway",
        "endpoint": "/audit/self_check",
        "timestamp": time.time(),
        "severity": severity,
        "severity_code": severity_code,
        "summary": summary,
        "stats": stats,
        "recommendations": get_recommendations(severity, stats)
    }


# === Funções auxiliares ===

def get_event_by_id(svc: RiskEventsService, event_id: int) -> Optional[dict]:
    """
    01_source/payment_gateway/app/routers/audity.py

    Busca um evento específico pelo ID.
    """
    # Implementação simplificada - idealmente teria um método específico
    # no RiskEventsService para buscar por ID
    try:
        # Assumindo que o SQLiteService tem um método para isso
        with svc.sqlite.session() as conn:
            row = conn.execute(
                """
                SELECT
                    id, request_id, event_type, decision, score,
                    policy_id, region, locker_id, porta, created_at,
                    reasons_json, signals_json, audit_event_id
                FROM risk_events
                WHERE id = ?
                """,
                (event_id,)
            ).fetchone()
        
        if not row:
            return None
            
        reasons, _ = svc._parse_reasons(row["reasons_json"])
        
        event = {
            "id": row["id"],
            "request_id": row["request_id"],
            "event_type": row["event_type"],
            "decision": (row["decision"] or "").upper(),
            "score": int(row["score"]) if row["score"] else 0,
            "policy_id": row["policy_id"],
            "region": row["region"],
            "locker_id": row["locker_id"],
            "porta": int(row["porta"]) if row["porta"] else None,
            "created_at": int(row["created_at"]),
            "audit_event_id": row["audit_event_id"],
            "reasons": reasons
        }
        
        # Incluir signals se existirem
        if row["signals_json"]:
            try:
                event["signals"] = json.loads(row["signals_json"])
            except:
                event["signals"] = {}
                
        return event
        
    except Exception as e:
        print(f"Erro ao buscar evento {event_id}: {e}")
        return None


def get_event_by_request_id(svc: RiskEventsService, request_id: str) -> dict:
    """
    01_source/payment_gateway/app/routers/audity.py

    Busca um evento específico pelo request_id.
    """
    # Implementação simplificada
    with svc.sqlite.session() as conn:
        rows = conn.execute(
            """
            SELECT
                id, request_id, event_type, decision, score,
                policy_id, region, locker_id, porta, created_at,
                reasons_json, signals_json, audit_event_id
            FROM risk_events
            WHERE request_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (request_id,)
        ).fetchall()
    
    if not rows:
        return {
            "service": "payment_gateway",
            "endpoint": f"/audit/events?request_id={request_id}",
            "timestamp": time.time(),
            "type": "RISK_EVENTS",
            "error": "Event not found",
            "request_id": request_id,
            "events": []
        }
    
    events = []
    for r in rows:
        reasons, _ = svc._parse_reasons(r["reasons_json"])
        events.append({
            "id": r["id"],
            "request_id": r["request_id"],
            "event_type": r["event_type"],
            "decision": (r["decision"] or "").upper(),
            "score": int(r["score"]) if r["score"] else 0,
            "policy_id": r["policy_id"],
            "region": r["region"],
            "locker_id": r["locker_id"],
            "porta": int(r["porta"]) if r["porta"] else None,
            "created_at": int(r["created_at"]),
            "reasons": reasons
        })
    
    return {
        "service": "payment_gateway",
        "endpoint": f"/audit/events?request_id={request_id}",
        "timestamp": time.time(),
        "type": "RISK_EVENTS",
        "request_id": request_id,
        "events": events
    }


def get_recommendations(severity: str, stats: dict) -> list:
    """
    01_source/payment_gateway/app/routers/audity.py

    Gera recomendações baseadas na severidade e estatísticas.
    """
    recommendations = []
    
    if severity == "HIGH":
        recommendations = [
            "🔍 Investigar pico de bloqueios - possível ataque ou falha de configuração",
            "📊 Verificar políticas de risco recentemente alteradas",
            "🛡️ Considerar rate limiting temporário",
            "📈 Analisar padrões nos IPs/regiões dos bloqueios"
        ]
    elif severity == "MEDIUM":
        recommendations = [
            "👀 Monitorar tendência nas próximas horas",
            "⚙️ Revisar thresholds das políticas de risco",
            "📋 Verificar se há padrão nos desafios (CHALLENGE)"
        ]
    else:
        recommendations = [
            "✅ Sistema operando normalmente",
            "📊 Continue monitorando métricas",
            "🔄 Próxima verificação em 24h"
        ]
    
    return recommendations


# Import necessário para a função get_event_by_id
import json
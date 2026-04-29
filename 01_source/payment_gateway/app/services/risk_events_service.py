# 01_source/payment_gateway/app/services/risk_events_service.py

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple, Union

from app.services.sqlite_service import SQLiteService


class RiskEventsService:
    def __init__(self, sqlite: SQLiteService):
        self.sqlite = sqlite

    def list_events(
        self,
        limit: int = 100,
        offset: int = 0,
        start_epoch: Optional[int] = None,
        end_epoch: Optional[int] = None,
        decision: Optional[str] = None,
        region: Optional[str] = None,
        policy_id: Optional[str] = None,
        event_type: Optional[str] = None,
        locker_id: Optional[str] = None,
        porta: Optional[int] = None,
        sort_by: str = "created_at",
        sort_order: str = "DESC",
        include_signals: bool = False,
        compact: bool = False
    ) -> Dict[str, Any]:
        """
        Lista eventos de risco com filtros e paginação.
        
        Args:
            limit: Número máximo de registros
            offset: Deslocamento para paginação
            start_epoch: Timestamp inicial (filtro created_at >=)
            end_epoch: Timestamp final (filtro created_at <=)
            decision: Filtrar por decisão (ALLOW, BLOCK, CHALLENGE)
            region: Filtrar por região
            policy_id: Filtrar por policy_id
            event_type: Filtrar por tipo de evento
            locker_id: Filtrar por locker_id
            porta: Filtrar por número da porta
            sort_by: Campo para ordenação
            sort_order: Direção da ordenação (ASC ou DESC)
            include_signals: Incluir signals_json na resposta
            compact: Retornar versão compacta (sem dados sensíveis)
            
        Returns:
            Dicionário com metadados e lista de eventos
        """
        
        # Construir query base
        query = """
            SELECT
                id,
                request_id,
                event_type,
                decision,
                score,
                policy_id,
                region,
                locker_id,
                porta,
                created_at,
                reasons_json,
                audit_event_id
        """
        
        # Incluir signals se solicitado
        if include_signals:
            query += ", signals_json"
            
        query += """
            FROM risk_events
            WHERE 1=1
        """
        
        params: List[Any] = []
        
        # Aplicar filtros
        if start_epoch is not None:
            query += " AND created_at >= ?"
            params.append(start_epoch)
            
        if end_epoch is not None:
            query += " AND created_at <= ?"
            params.append(end_epoch)
            
        if decision:
            query += " AND UPPER(decision) = UPPER(?)"
            params.append(decision)
            
        if region:
            query += " AND region = ?"
            params.append(region)
            
        if policy_id:
            query += " AND policy_id = ?"
            params.append(policy_id)
            
        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)
            
        if locker_id:
            query += " AND locker_id = ?"
            params.append(locker_id)
            
        if porta is not None:
            query += " AND porta = ?"
            params.append(porta)
            
        # Ordenação
        valid_sort_fields = {"created_at", "id", "score", "region", "decision"}
        normalized_sort_by = sort_by if sort_by in valid_sort_fields else "created_at"
        normalized_sort_order = "ASC" if sort_order.upper() == "ASC" else "DESC"
        order_clause_map = {
            ("created_at", "ASC"): " ORDER BY created_at ASC",
            ("created_at", "DESC"): " ORDER BY created_at DESC",
            ("id", "ASC"): " ORDER BY id ASC",
            ("id", "DESC"): " ORDER BY id DESC",
            ("score", "ASC"): " ORDER BY score ASC",
            ("score", "DESC"): " ORDER BY score DESC",
            ("region", "ASC"): " ORDER BY region ASC",
            ("region", "DESC"): " ORDER BY region DESC",
            ("decision", "ASC"): " ORDER BY decision ASC",
            ("decision", "DESC"): " ORDER BY decision DESC",
        }
        query += order_clause_map[(normalized_sort_by, normalized_sort_order)]
        
        # Paginação
        query += " LIMIT ? OFFSET ?"
        params.append(limit)
        params.append(offset)
        
        # Query para contar total (sem paginação)
        count_query = """
            SELECT COUNT(*) as total
            FROM risk_events
            WHERE 1=1
        """
        count_params: List[Any] = []
        
        # Replicar filtros para count
        if start_epoch is not None:
            count_query += " AND created_at >= ?"
            count_params.append(start_epoch)
        if end_epoch is not None:
            count_query += " AND created_at <= ?"
            count_params.append(end_epoch)
        if decision:
            count_query += " AND UPPER(decision) = UPPER(?)"
            count_params.append(decision)
        if region:
            count_query += " AND region = ?"
            count_params.append(region)
        if policy_id:
            count_query += " AND policy_id = ?"
            count_params.append(policy_id)
        if event_type:
            count_query += " AND event_type = ?"
            count_params.append(event_type)
        if locker_id:
            count_query += " AND locker_id = ?"
            count_params.append(locker_id)
        if porta is not None:
            count_query += " AND porta = ?"
            count_params.append(porta)
            
        # Executar queries
        with self.sqlite.session() as conn:
            # Buscar total
            total_row = conn.execute(count_query, count_params).fetchone()
            total = total_row["total"] if total_row else 0
            
            # Buscar eventos
            rows = conn.execute(query, params).fetchall()
            
        # Processar resultados
        events = []
        for r in rows:
            event = {
                "id": r["id"],
                "request_id": r["request_id"],
                "event_type": r["event_type"],
                "decision": (r["decision"] or "").upper(),
                "score": int(r["score"]) if r["score"] is not None else 0,
                "policy_id": r["policy_id"],
                "region": r["region"],
                "locker_id": r["locker_id"],
                "porta": int(r["porta"]) if r["porta"] is not None else None,
                "created_at": int(r["created_at"]) if r["created_at"] else None,
                "audit_event_id": r["audit_event_id"],
            }
            
            # Processar reasons
            reasons, parse_ok = self._parse_reasons(r["reasons_json"])
            event["reasons"] = reasons
            event["reasons_parse_ok"] = parse_ok
            
            # Incluir reason_codes se compact=True
            if compact:
                reason_codes = [item.get("code") or "UNKNOWN" for item in reasons[:10]]
                event["reason_codes"] = reason_codes
                # Remover dados brutos se compact
                del event["reasons"]
                if "signals_json" in event:
                    del event["signals_json"]
            
            # Incluir signals se solicitado
            if include_signals and "signals_json" in r.keys():
                try:
                    event["signals"] = json.loads(r["signals_json"] or "{}")
                except Exception:
                    event["signals"] = {}
                    event["signals_parse_ok"] = False
                else:
                    event["signals_parse_ok"] = True
                    
            events.append(event)
            
        # Estatísticas agregadas
        stats = self._get_aggregated_stats(events) if events else {}
        
        return {
            "metadata": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "returned": len(events),
                "has_more": (offset + len(events)) < total,
                "filters_applied": {
                    "start_epoch": start_epoch,
                    "end_epoch": end_epoch,
                    "decision": decision,
                    "region": region,
                    "policy_id": policy_id,
                    "event_type": event_type,
                    "locker_id": locker_id,
                    "porta": porta,
                }
            },
            "stats": stats,
            "events": events
        }

    def list_between(self, start_epoch: int, end_epoch: int) -> List[Dict[str, Any]]:
        """Método existente - mantido para compatibilidade"""
        with self.sqlite.session() as conn:
            rows = conn.execute(
                """
                SELECT
                  id,
                  request_id,
                  event_type,
                  decision,
                  score,
                  policy_id,
                  region,
                  locker_id,
                  porta,
                  created_at,
                  reasons_json,
                  signals_json,
                  audit_event_id
                FROM risk_events
                WHERE created_at BETWEEN ? AND ?
                ORDER BY created_at ASC
                """,
                (start_epoch, end_epoch),
            ).fetchall()

        out: List[Dict[str, Any]] = []
        for r in rows:
            out.append(
                {
                    "id": r["id"],
                    "request_id": r["request_id"],
                    "event_type": r["event_type"],
                    "decision": (r["decision"] or "").upper(),
                    "score": int(r["score"]),
                    "policy_id": r["policy_id"],
                    "region": r["region"],
                    "locker_id": r["locker_id"],
                    "porta": int(r["porta"]),
                    "created_at": int(r["created_at"]),
                    "reasons_json": r["reasons_json"],
                    "signals_json": r["signals_json"],
                    "audit_event_id": r["audit_event_id"],
                }
            )
        return out

    def _parse_reasons(self, reasons_raw: Optional[str]) -> Tuple[List[Dict[str, Any]], bool]:
        """
        Retorna (reasons_list, ok_parse).
        """
        try:
            obj = json.loads(reasons_raw or "[]")
            if isinstance(obj, list):
                reasons = [x for x in obj if isinstance(x, dict)]
                return reasons, True
            return [], False
        except Exception:
            return [], False

    def _get_aggregated_stats(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calcula estatísticas agregadas dos eventos
        """
        if not events:
            return {}
            
        decisions = {}
        policies = {}
        regions = {}
        scores = []
        total_score = 0
        
        for ev in events:
            # Contar decisões
            dec = ev.get("decision", "UNKNOWN")
            decisions[dec] = decisions.get(dec, 0) + 1
            
            # Contar políticas
            pid = ev.get("policy_id", "UNKNOWN")
            policies[pid] = policies.get(pid, 0) + 1
            
            # Contar regiões
            reg = ev.get("region", "UNKNOWN")
            regions[reg] = regions.get(reg, 0) + 1
            
            # Acumular scores
            score = ev.get("score", 0)
            scores.append(score)
            total_score += score
            
        return {
            "total_events": len(events),
            "decisions": decisions,
            "policies": policies,
            "regions": regions,
            "score_avg": total_score / len(events) if events else 0,
            "score_min": min(scores) if scores else 0,
            "score_max": max(scores) if scores else 0,
        }

    def _compact_event(self, ev: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evento enxuto para snapshot forense (sem vazar ip_hash/device_hash).
        Signals e reasons vão compactados.
        """
        reasons, ok = self._parse_reasons(ev.get("reasons_json") or "[]")
        reason_codes = []
        for r in reasons[:10]:
            reason_codes.append(r.get("code") or "UNKNOWN")

        return {
            "id": ev["id"],
            "request_id": ev["request_id"],
            "event_type": ev.get("event_type"),
            "decision": ev["decision"],
            "score": ev["score"],
            "policy_id": ev["policy_id"],
            "region": ev["region"],
            "locker_id": ev["locker_id"],
            "porta": ev["porta"],
            "created_at": ev["created_at"],
            "audit_event_id": ev.get("audit_event_id"),
            "reason_codes": reason_codes,
            "reasons_parse_ok": ok,
        }

    def forensics_between(self, start_epoch: int, end_epoch: int) -> Dict[str, Any]:
        """
        Retorna:
          - stats (decisions + top reasons)
          - policy_ids_used (com contagem)
          - integrity (parse errors)
          - events_sample (amostra por decisão)
        """
        events = self.list_between(start_epoch, end_epoch)

        # Decisions
        decisions_count = {"ALLOW": 0, "CHALLENGE": 0, "BLOCK": 0, "UNKNOWN": 0}

        # Policies
        policy_counts: Dict[str, int] = {}

        # Reasons (todas)
        reason_counts: Dict[str, int] = {}

        # Integrity
        reasons_parse_ok = 0
        reasons_parse_fail = 0

        # Samples buckets
        by_decision: Dict[str, List[Dict[str, Any]]] = {"ALLOW": [], "CHALLENGE": [], "BLOCK": [], "UNKNOWN": []}

        for ev in events:
            d = (ev.get("decision") or "UNKNOWN").upper()
            if d not in decisions_count:
                d = "UNKNOWN"
            decisions_count[d] += 1

            # policy count
            pid = ev.get("policy_id") or "UNKNOWN_POLICY"
            policy_counts[pid] = policy_counts.get(pid, 0) + 1

            # reasons
            reasons, ok = self._parse_reasons(ev.get("reasons_json") or "[]")
            if ok:
                reasons_parse_ok += 1
            else:
                reasons_parse_fail += 1

            for item in reasons:
                code = item.get("code") or "UNKNOWN"
                reason_counts[code] = reason_counts.get(code, 0) + 1

            # sample bucket (compact)
            by_decision[d].append(self._compact_event(ev))

        # top reasons
        top_reasons = [
            {"code": code, "count": count}
            for code, count in sorted(reason_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]

        # policy ids used
        policy_ids_used = [
            {"policy_id": pid, "count": c}
            for pid, c in sorted(policy_counts.items(), key=lambda x: x[1], reverse=True)
        ]

        total_events = len(events)
        integrity = {
            "total_events": total_events,
            "reasons_json_parse": {
                "ok": int(reasons_parse_ok),
                "fail": int(reasons_parse_fail),
                "fail_rate": (float(reasons_parse_fail) / float(total_events)) if total_events else 0.0,
            },
        }

        # sample: pega 3 de cada decisão (prioriza começo e fim do dia)
        def pick_samples(items: List[Dict[str, Any]], n: int = 3) -> List[Dict[str, Any]]:
            if len(items) <= n:
                return items
            # 2 do fim + 1 do começo (bom pra ver mudança ao longo do dia)
            return [items[0], items[-2], items[-1]]

        events_sample = {
            "ALLOW": pick_samples(by_decision["ALLOW"], 3),
            "CHALLENGE": pick_samples(by_decision["CHALLENGE"], 3),
            "BLOCK": pick_samples(by_decision["BLOCK"], 3),
            "UNKNOWN": pick_samples(by_decision["UNKNOWN"], 3),
        }

        return {
            "window": {"start_epoch": int(start_epoch), "end_epoch": int(end_epoch), "inclusive": True},
            "stats": {
                "decisions": {
                    "ALLOW": int(decisions_count["ALLOW"]),
                    "CHALLENGE": int(decisions_count["CHALLENGE"]),
                    "BLOCK": int(decisions_count["BLOCK"]),
                    "UNKNOWN": int(decisions_count["UNKNOWN"]),
                },
                "top_reasons": top_reasons,
            },
            "policy_ids_used": policy_ids_used,
            "integrity": integrity,
            "events_sample": events_sample,
        }
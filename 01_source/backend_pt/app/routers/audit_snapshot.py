import os
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Query, Request, Header, HTTPException

from app.core.antifraud_snapshot import create_daily_snapshot
from app.core.antifraud_snapshot_verify import verify_snapshot_file

router = APIRouter(prefix="/audit", tags=["audit"])

INTERNAL_TOKEN = os.getenv("INTERNAL_TOKEN")  # opcional (recomendado)


def _require_internal_token(x_internal_token: str | None):
    if INTERNAL_TOKEN and x_internal_token != INTERNAL_TOKEN:
        raise HTTPException(
            status_code=401,
            detail={"type": "UNAUTHORIZED", "message": "invalid internal token", "retryable": False},
        )


def _resolve_machine_id(machine_id_qs: str | None) -> str:
    if machine_id_qs:
        return machine_id_qs
    env_mid = os.getenv("MACHINE_ID")
    if env_mid:
        return env_mid
    return "CACIFO-XX-001"


def _utc_date_str(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d")


@router.api_route("/snapshot", methods=["GET", "POST"])
def snapshot(
    request: Request,
    machine_id: str | None = Query(default=None),
    x_internal_token: str | None = Header(default=None),
):
    _require_internal_token(x_internal_token)
    mid = _resolve_machine_id(machine_id)

    try:
        result = create_daily_snapshot(machine_id=mid)
        return {
            "ok": True,
            "machine_id": mid,
            "endpoint": str(request.url.path),
            "result": result,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "type": "SNAPSHOT_CREATE_FAILED",
                "message": str(e),
                "retryable": True,
                "machine_id": mid,
                "endpoint": str(request.url.path),
            },
        )


@router.api_route("/snapshot/verify_file", methods=["GET", "POST"])
def snapshot_verify_file(
    request: Request,
    date_utc: str = Query(..., description="Formato YYYY-MM-DD (UTC)"),
    machine_id: str | None = Query(default=None),
    x_internal_token: str | None = Header(default=None),
):
    _require_internal_token(x_internal_token)
    mid = _resolve_machine_id(machine_id)

    try:
        result = verify_snapshot_file(machine_id=mid, date_utc=date_utc)
        return {
            "ok": True,
            "machine_id": mid,
            "date_utc": date_utc,
            "endpoint": str(request.url.path),
            "result": result,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "type": "SNAPSHOT_VERIFY_FAILED",
                "message": str(e),
                "retryable": True,
                "machine_id": mid,
                "date_utc": date_utc,
                "endpoint": str(request.url.path),
            },
        )


@router.get("/snapshot/verify_latest")
def snapshot_verify_latest(
    request: Request,
    days: int = Query(default=7, ge=1, le=60, description="Quantos dias para trás (UTC) verificar"),
    machine_id: str | None = Query(default=None),
    x_internal_token: str | None = Header(default=None),
):
    _require_internal_token(x_internal_token)
    mid = _resolve_machine_id(machine_id)

    def _classify_events_db_check(edb: dict | None) -> dict:
        """
        Retorna uma classificação amigável do drift.
        Espera que verify_snapshot_file retorne:
          events_db_check = {
            ok: bool,
            snapshot_last_hash: ...,
            events_db_last_hash_as_of_date: ...,
            tampered_or_drift: bool
          }
        """
        if not edb:
            return {"status": "UNKNOWN", "detail": "events_db_check missing"}

        s_hash = edb.get("snapshot_last_hash")
        d_hash = edb.get("events_db_last_hash_as_of_date")
        ok = bool(edb.get("ok"))

        if s_hash is None and d_hash is None:
            return {"status": "NO_EVENTS_DAY_OK", "ok": True, "message": "No events for this day (snapshot and DB agree)"}

        if s_hash is None and d_hash is not None:
            return {"status": "SNAPSHOT_HAS_NO_EVENTS_BUT_DB_HAS", "ok": False, "message": "Snapshot says no events, but DB has events for that day"}

        if s_hash is not None and d_hash is None:
            return {"status": "SNAPSHOT_HAS_EVENTS_BUT_DB_HAS_NONE", "ok": False, "message": "Snapshot has events hash, but DB has no events for that day"}

        # ambos não-nulos
        if ok:
            return {"status": "OK_MATCH", "ok": True, "message": "Snapshot last_hash matches DB last_hash for that day"}

        return {"status": "DRIFT_REAL", "ok": False, "message": "Snapshot last_hash differs from DB last_hash for that day"}

    try:
        today_utc = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        checks = []
        failed = []

        for i in range(0, days):
            d = today_utc - timedelta(days=i)
            date_utc = _utc_date_str(d)

            r = verify_snapshot_file(
                machine_id=mid,
                date_utc=date_utc,
                verify_previous=True,
                verify_against_events_db=True,  # agora é “as-of date”
            )

            reason = r.get("reason")
            tampered = bool(r.get("tampered"))

            prev_chk = r.get("previous_snapshot_check") or {}
            prev_ok = prev_chk.get("ok", True)
            prev_status = "OK" if prev_ok else "BROKEN_CHAIN"

            edb = r.get("events_db_check")
            drift = _classify_events_db_check(edb)

            # Status amigável geral do dia
            if reason == "file_not_found":
                status = "MISSING_SNAPSHOT"
            elif reason == "invalid_json":
                status = "INVALID_JSON"
            elif tampered:
                status = "TAMPERED"
            elif not prev_ok:
                status = "BROKEN_CHAIN"
            elif not drift.get("ok", True):
                status = drift["status"]  # DRIFT_REAL ou casos especiais
            else:
                status = "OK"

            item = {
                "date_utc": date_utc,
                "status": status,
                "ok": bool(r.get("ok")),
                "reason": reason,
                "path": r.get("path"),

                # integridade do arquivo
                "tampered": tampered,
                "snapshot_hash_file": r.get("snapshot_hash_file"),
                "snapshot_hash_expected": r.get("snapshot_hash_expected"),

                # cadeia diária
                "previous_snapshot_status": prev_status,
                "previous_snapshot_check": prev_chk,

                # drift amigável
                "events_db_drift": drift,
                "events_db_check": edb,
            }

            checks.append(item)
            if status != "OK":
                failed.append(item)

        # cronológico (mais antigo -> mais novo)
        checks_sorted = list(reversed(checks))
        failed_sorted = list(reversed(failed))

        # contagem por status
        by_status = {}
        for it in checks_sorted:
            by_status[it["status"]] = by_status.get(it["status"], 0) + 1

        return {
            "ok": True,
            "machine_id": mid,
            "endpoint": str(request.url.path),
            "days": days,
            "summary": {
                "total": len(checks_sorted),
                "failed": len(failed_sorted),
                "passed": len(checks_sorted) - len(failed_sorted),
                "by_status": by_status,
            },
            "failed": failed_sorted,
            "checks": checks_sorted,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "type": "VERIFY_LATEST_FAILED",
                "message": str(e),
                "retryable": True,
                "machine_id": mid,
                "days": days,
                "endpoint": str(request.url.path),
            },
        )


@router.get("/snapshot/create_latest")
def snapshot_create_latest(
    request: Request,
    days: int = Query(default=7, ge=1, le=60, description="Quantos dias para trás (UTC) criar/garantir snapshot"),
    machine_id: str | None = Query(default=None),
    x_internal_token: str | None = Header(default=None),
):
    """
    Bootstrap + auto-heal:
    1) Cria snapshots faltantes nos últimos N dias (inclui hoje), em ordem cronológica.
    2) Verifica a janela e detecta BROKEN_CHAIN.
    3) Se houver BROKEN_CHAIN, recria TODOS os snapshots da janela (overwrite) em ordem cronológica.
    4) Verifica novamente e retorna relatório rico.
    """
    _require_internal_token(x_internal_token)
    mid = _resolve_machine_id(machine_id)

    def _dates_window(days_: int) -> list[str]:
        today_utc = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        dates = []
        for i in range(0, days_):
            d = today_utc - timedelta(days=i)
            dates.append(_utc_date_str(d))
        # cronológico (mais antigo -> mais novo)
        return list(sorted(dates))

    def _run_verify_for_dates(dates: list[str]) -> dict:
        """
        Verifica cada dia com verify_snapshot_file e classifica status básico, incluindo BROKEN_CHAIN.
        """
        checks = []
        broken_chain_dates = []

        for date_utc in dates:
            r = verify_snapshot_file(
                machine_id=mid,
                date_utc=date_utc,
                verify_previous=True,
                verify_against_events_db=True,
            )

            reason = r.get("reason")
            tampered = bool(r.get("tampered"))

            prev_chk = r.get("previous_snapshot_check") or {}
            prev_ok = prev_chk.get("ok", True)

            edb = r.get("events_db_check") or {}
            drift_ok = bool(edb.get("ok", True))  # pode ser True mesmo com last_hash=None

            if reason == "file_not_found":
                status = "MISSING_SNAPSHOT"
            elif reason == "invalid_json":
                status = "INVALID_JSON"
            elif tampered:
                status = "TAMPERED"
            elif prev_ok is False:
                status = "BROKEN_CHAIN"
            elif drift_ok is False:
                status = "DRIFT_REAL"
            else:
                status = "OK"

            if status == "BROKEN_CHAIN":
                broken_chain_dates.append(date_utc)

            checks.append({
                "date_utc": date_utc,
                "status": status,
                "ok": bool(r.get("ok")),
                "reason": reason,
                "path": r.get("path"),
                "tampered": tampered,
                "previous_snapshot_check": prev_chk,
                "events_db_check": edb,
            })

        by_status = {}
        for it in checks:
            by_status[it["status"]] = by_status.get(it["status"], 0) + 1

        failed = [c for c in checks if c["status"] != "OK"]

        return {
            "summary": {
                "total": len(checks),
                "failed": len(failed),
                "passed": len(checks) - len(failed),
                "by_status": by_status,
            },
            "broken_chain_dates": broken_chain_dates,
            "failed": failed,
            "checks": checks,
        }

    def _create_snapshots(dates: list[str], *, overwrite: bool) -> tuple[list[dict], list[dict]]:
        """
        Cria snapshots para as datas fornecidas.
        - overwrite=True: recria sempre (overwrite do arquivo)
        - overwrite=False: cria apenas se faltar (file_not_found)
        Retorna (created, failed)
        """
        created = []
        failed = []

        for date_utc in dates:
            if not overwrite:
                probe = verify_snapshot_file(
                    machine_id=mid,
                    date_utc=date_utc,
                    verify_previous=False,
                    verify_against_events_db=False,
                )
                if probe.get("reason") != "file_not_found":
                    # já existe
                    continue

            try:
                cr = create_daily_snapshot(machine_id=mid, date_utc=date_utc)
                created.append({
                    "date_utc": cr.get("date_utc"),
                    "backup_path": cr.get("backup_path"),
                    "snapshot_hash": cr.get("snapshot_hash"),
                    "previous_snapshot_hash": cr.get("previous_snapshot_hash"),
                    "overwritten": overwrite,
                })
            except Exception as e:
                failed.append({
                    "date_utc": date_utc,
                    "error": str(e),
                    "overwritten": overwrite,
                })

        return created, failed

    try:
        dates = _dates_window(days)

        # 1) Criar apenas faltantes (ordem cronológica)
        created_1, failed_1 = _create_snapshots(dates, overwrite=False)

        # 2) Verificar
        verify_1 = _run_verify_for_dates(dates)
        broken = verify_1["broken_chain_dates"]

        heal_attempted = False
        healed = False
        created_2 = []
        failed_2 = []
        verify_2 = None

        # 3) Auto-heal se houver BROKEN_CHAIN
        if broken:
            heal_attempted = True

            # recria a janela inteira, mais antigo -> mais novo (overwrite)
            created_2, failed_2 = _create_snapshots(dates, overwrite=True)

            # verifica de novo
            verify_2 = _run_verify_for_dates(dates)

            healed = (len(verify_2["broken_chain_dates"]) == 0)

        return {
            "ok": True,
            "machine_id": mid,
            "endpoint": str(request.url.path),
            "days": days,
            "window": {"from": dates[0], "to": dates[-1], "dates": dates},

            "create_pass_1": {
                "mode": "missing_only",
                "created": created_1,
                "failed": failed_1,
            },

            "verify_after_pass_1": verify_1,

            "auto_heal": {
                "heal_attempted": heal_attempted,
                "broken_chain_detected": broken,
                "heal_pass_2": {
                    "mode": "overwrite_all" if heal_attempted else None,
                    "created": created_2,
                    "failed": failed_2,
                } if heal_attempted else None,
                "verify_after_pass_2": verify_2,
                "healed": healed if heal_attempted else None,
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "type": "CREATE_LATEST_FAILED",
                "message": str(e),
                "retryable": True,
                "machine_id": mid,
                "days": days,
                "endpoint": str(request.url.path),
            },
        )
    _require_internal_token(x_internal_token)
    mid = _resolve_machine_id(machine_id)

    try:
        today_utc = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

        # 1) Descobre faltantes
        missing = []
        existing = []
        for i in range(0, days):
            d = today_utc - timedelta(days=i)
            date_utc = _utc_date_str(d)
            r = verify_snapshot_file(
                machine_id=mid,
                date_utc=date_utc,
                verify_previous=False,
                verify_against_events_db=False,
            )
            if r.get("reason") == "file_not_found":
                missing.append({"date_utc": date_utc, "path": r.get("path")})
            else:
                existing.append({"date_utc": date_utc, "ok": bool(r.get("ok")), "path": r.get("path")})

        created = []
        create_failed = []

        # 2) Cria todos os faltantes (retroativo)
        # IMPORTANTE: criar em ordem cronológica (mais antigo -> mais novo) para encadeamento previous_snapshot_hash funcionar
        missing_sorted = sorted(missing, key=lambda x: x["date_utc"])
        for m in missing_sorted:
            date_utc = m["date_utc"]
            try:
                cr = create_daily_snapshot(machine_id=mid, date_utc=date_utc)
                created.append({
                    "date_utc": cr.get("date_utc"),
                    "backup_path": cr.get("backup_path"),
                    "snapshot_hash": cr.get("snapshot_hash"),
                    "previous_snapshot_hash": cr.get("previous_snapshot_hash"),
                })
            except Exception as e:
                create_failed.append({"date_utc": date_utc, "error": str(e)})

        # 3) Verifica depois de criar
        verify = snapshot_verify_latest(
            request=request,
            days=days,
            machine_id=mid,
            x_internal_token=x_internal_token,
        )

        return {
            "ok": True,
            "machine_id": mid,
            "endpoint": str(request.url.path),
            "days": days,
            "existing": list(reversed(existing)),
            "missing_before": list(reversed(missing)),
            "created": created,
            "create_failed": create_failed,
            "verify_after": verify,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "type": "CREATE_LATEST_FAILED",
                "message": str(e),
                "retryable": True,
                "machine_id": mid,
                "days": days,
                "endpoint": str(request.url.path),
            },
        )
    """
    Bootstrap: tenta garantir snapshots dos últimos N dias.

    IMPORTANTE:
    - create_daily_snapshot() hoje só cria snapshot para a data UTC atual.
    - Então este endpoint:
      - cria o snapshot de HOJE se estiver faltando
      - para dias anteriores, apenas reporta como "cannot_create_past_date_without_feature"
      - em seguida roda verify_latest e retorna um relatório combinado
    """
    _require_internal_token(x_internal_token)
    mid = _resolve_machine_id(machine_id)

    try:
        today_utc = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_str = _utc_date_str(today_utc)

        # 1) Descobre quais faltam (verificando existence via verify_snapshot_file)
        missing = []
        existing = []
        for i in range(0, days):
            d = today_utc - timedelta(days=i)
            date_utc = _utc_date_str(d)
            r = verify_snapshot_file(machine_id=mid, date_utc=date_utc, verify_previous=False, verify_against_events_db=False)

            if r.get("reason") == "file_not_found":
                missing.append({"date_utc": date_utc, "path": r.get("path")})
            else:
                existing.append({"date_utc": date_utc, "ok": bool(r.get("ok")), "path": r.get("path")})

        created = []
        create_failed = []
        skipped = []

        # 2) Criar o de hoje se estiver faltando
        missing_dates = {m["date_utc"] for m in missing}
        if today_str in missing_dates:
            try:
                cr = create_daily_snapshot(machine_id=mid)
                created.append({"date_utc": cr.get("date_utc"), "backup_path": cr.get("backup_path"), "snapshot_hash": cr.get("snapshot_hash")})
            except Exception as e:
                create_failed.append({"date_utc": today_str, "error": str(e)})
        else:
            skipped.append({"date_utc": today_str, "reason": "already_exists"})

        # 3) Para dias anteriores: não dá para criar sem suporte a date_utc no core
        for m in missing:
            if m["date_utc"] == today_str:
                continue
            skipped.append({
                "date_utc": m["date_utc"],
                "reason": "cannot_create_past_date_without_feature",
                "hint": "Add optional date_utc support to create_daily_snapshot(machine_id, date_utc=...)",
            })

        # 4) Rodar verify_latest após tentativa de criação
        verify = snapshot_verify_latest(
            request=request,
            days=days,
            machine_id=mid,
            x_internal_token=x_internal_token,
        )

        return {
            "ok": True,
            "machine_id": mid,
            "endpoint": str(request.url.path),
            "days": days,
            "existing": list(reversed(existing)),
            "missing_before": list(reversed(missing)),
            "created": created,
            "create_failed": create_failed,
            "skipped": list(reversed(skipped)),
            "verify_after": verify,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "type": "CREATE_LATEST_FAILED",
                "message": str(e),
                "retryable": True,
                "machine_id": mid,
                "days": days,
                "endpoint": str(request.url.path),
            },
        )
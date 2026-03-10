#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# ELLAN LAB - bootstrap estrutural seguro
# recursos:
#   --dry-run         : simula sem gravar
#   --base-dir=PATH   : diretório base (default: 01_source)
#   --log-dir=PATH    : onde salvar logs/relatórios (default: ./migration_logs)
#
# exemplos:
#   bash bootstrap_safe.sh --dry-run
#   bash bootstrap_safe.sh
#   bash bootstrap_safe.sh --base-dir=01_source --log-dir=./migration_logs
# ============================================================

DRY_RUN=0
BASE_DIR="01_source"
LOG_DIR="./migration_logs"

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --base-dir=*) BASE_DIR="${arg#*=}" ;;
    --log-dir=*) LOG_DIR="${arg#*=}" ;;
    *)
      echo "Argumento desconhecido: $arg"
      exit 1
      ;;
  esac
done

TS="$(date +%Y%m%d_%H%M%S)"
RUN_DIR="${LOG_DIR}/run_${TS}"
LOG_FILE="${RUN_DIR}/bootstrap.log"
REPORT_FILE="${RUN_DIR}/report.txt"
TREE_BEFORE="${RUN_DIR}/tree_before.txt"
TREE_AFTER="${RUN_DIR}/tree_after.txt"
TREE_DIFF="${RUN_DIR}/tree_diff.patch"
CREATED_FILELIST="${RUN_DIR}/created_files.txt"
SKIPPED_FILELIST="${RUN_DIR}/skipped_files.txt"
BACKUP_FILELIST="${RUN_DIR}/backups.txt"

mkdir -p "$RUN_DIR"
: > "$LOG_FILE"
: > "$REPORT_FILE"
: > "$CREATED_FILELIST"
: > "$SKIPPED_FILELIST"
: > "$BACKUP_FILELIST"

log() {
  echo "$1" | tee -a "$LOG_FILE"
}

report() {
  echo "$1" >> "$REPORT_FILE"
}

record_created() {
  echo "$1" >> "$CREATED_FILELIST"
}

record_skipped() {
  echo "$1" >> "$SKIPPED_FILELIST"
}

record_backup() {
  echo "$1" >> "$BACKUP_FILELIST"
}

run_cmd() {
  if [ "$DRY_RUN" -eq 1 ]; then
    log "[DRY-RUN] $*"
  else
    log "[EXEC] $*"
    eval "$@"
  fi
}

snapshot_tree() {
  local out="$1"
  if [ -d "$BASE_DIR" ]; then
    find "$BASE_DIR" | sort > "$out"
  else
    : > "$out"
  fi
}

safe_mkdir() {
  local d="$1"
  if [ -d "$d" ]; then
    log "  [SKIP] diretório já existe: $d"
    record_skipped "$d"
  else
    run_cmd "mkdir -p \"$d\""
    record_created "$d/"
  fi
}

safe_touch() {
  local f="$1"
  if [ -f "$f" ]; then
    log "  [SKIP] arquivo já existe: $f"
    record_skipped "$f"
  else
    if [ "$DRY_RUN" -eq 1 ]; then
      log "  [DRY-RUN] touch \"$f\""
    else
      touch "$f"
      log "  [NEW] $f"
    fi
    record_created "$f"
  fi
}

safe_write() {
  local f="$1"
  local tmp
  tmp="$(mktemp)"

  cat > "$tmp"

  if [ -f "$f" ]; then
    log "  [SKIP] arquivo já existe: $f"
    record_skipped "$f"
    rm -f "$tmp"
  else
    if [ "$DRY_RUN" -eq 1 ]; then
      log "  [DRY-RUN] criar arquivo \"$f\""
      rm -f "$tmp"
    else
      mkdir -p "$(dirname "$f")"
      mv "$tmp" "$f"
      log "  [NEW] $f"
    fi
    record_created "$f"
  fi
}

backup_dir_if_exists() {
  local d="$1"
  if [ -d "$d" ]; then
    local target="${d}.bak.${TS}"
    if [ "$DRY_RUN" -eq 1 ]; then
      log "  [DRY-RUN] backup \"$d\" -> \"$target\""
    else
      cp -r "$d" "$target"
      log "  [BACKUP] $d -> $target"
    fi
    record_backup "$target"
  else
    log "  [INFO] sem backup, diretório não existe: $d"
  fi
}

ensure_package_inits() {
  local root="$1"
  if [ ! -d "$root" ]; then
    return
  fi

  while IFS= read -r d; do
    safe_touch "$d/__init__.py"
  done < <(find "$root" -type d | sort)
}

generate_diff_report() {
  snapshot_tree "$TREE_AFTER"
  if command -v diff >/dev/null 2>&1; then
    diff -u "$TREE_BEFORE" "$TREE_AFTER" > "$TREE_DIFF" || true
  else
    : > "$TREE_DIFF"
  fi
}

write_summary_report() {
  {
    echo "ELLAN LAB - RELATÓRIO DE BOOTSTRAP"
    echo "Timestamp: $TS"
    echo "Base dir: $BASE_DIR"
    echo "Dry run: $DRY_RUN"
    echo
    echo "Arquivos/diretórios criados:"
    sort -u "$CREATED_FILELIST" || true
    echo
    echo "Itens ignorados por já existirem:"
    sort -u "$SKIPPED_FILELIST" || true
    echo
    echo "Backups:"
    sort -u "$BACKUP_FILELIST" || true
    echo
    echo "Arquivos de apoio:"
    echo "  - Log: $LOG_FILE"
    echo "  - Tree before: $TREE_BEFORE"
    echo "  - Tree after: $TREE_AFTER"
    echo "  - Tree diff: $TREE_DIFF"
  } >> "$REPORT_FILE"
}

# ------------------------------------------------------------
# início
# ------------------------------------------------------------

log "==> bootstrap estrutural seguro"
log "==> BASE_DIR=$BASE_DIR"
log "==> LOG_DIR=$RUN_DIR"
log "==> DRY_RUN=$DRY_RUN"

if [ ! -d "$BASE_DIR" ]; then
  log "ERRO: diretório base não encontrado: $BASE_DIR"
  exit 1
fi

snapshot_tree "$TREE_BEFORE"

log "==> fase 0: backups preventivos"
backup_dir_if_exists "$BASE_DIR/payment_gateway"
backup_dir_if_exists "$BASE_DIR/simulator"
backup_dir_if_exists "$BASE_DIR/order_pickup_service"

log "==> fase 1: shared_kernel"
safe_mkdir "$BASE_DIR/shared_kernel/audit"
safe_mkdir "$BASE_DIR/shared_kernel/security"
safe_mkdir "$BASE_DIR/shared_kernel/idempotency"
safe_mkdir "$BASE_DIR/shared_kernel/observability"
safe_mkdir "$BASE_DIR/shared_kernel/auth"
safe_mkdir "$BASE_DIR/shared_kernel/compliance"
ensure_package_inits "$BASE_DIR/shared_kernel"

safe_write "$BASE_DIR/shared_kernel/README.md" <<'EOF'
# shared_kernel

Biblioteca interna compartilhada para segurança, auditoria, idempotência e observabilidade.
EOF

safe_write "$BASE_DIR/shared_kernel/observability/correlation_id.py" <<'EOF'
from contextvars import ContextVar
from uuid import uuid4

_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")


def set_correlation_id(value: str | None = None) -> str:
    cid = value or str(uuid4())
    _correlation_id.set(cid)
    return cid


def get_correlation_id() -> str:
    return _correlation_id.get() or ""


def clear_correlation_id() -> None:
    _correlation_id.set("")
EOF

safe_write "$BASE_DIR/shared_kernel/observability/request_id.py" <<'EOF'
from contextvars import ContextVar
from uuid import uuid4

_request_id: ContextVar[str] = ContextVar("request_id", default="")


def set_request_id(value: str | None = None) -> str:
    rid = value or str(uuid4())
    _request_id.set(rid)
    return rid


def get_request_id() -> str:
    return _request_id.get() or ""


def clear_request_id() -> None:
    _request_id.set("")
EOF

safe_write "$BASE_DIR/shared_kernel/security/secret_redaction.py" <<'EOF'
SENSITIVE_KEYS = {
    "authorization",
    "token",
    "access_token",
    "refresh_token",
    "secret",
    "api_key",
    "signature",
    "webhook_signature",
}


def redact_dict(data: dict) -> dict:
    sanitized = {}
    for key, value in data.items():
        if key.lower() in SENSITIVE_KEYS:
            sanitized[key] = "***REDACTED***"
        elif isinstance(value, dict):
            sanitized[key] = redact_dict(value)
        else:
            sanitized[key] = value
    return sanitized
EOF

safe_write "$BASE_DIR/shared_kernel/security/webhook_signatures.py" <<'EOF'
import hashlib
import hmac


def verify_hmac_sha256(payload: bytes, secret: str, received_signature: str) -> bool:
    digest = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(digest, received_signature)
EOF

safe_write "$BASE_DIR/shared_kernel/idempotency/keys.py" <<'EOF'
import hashlib


def build_idempotency_fingerprint(*parts: str) -> str:
    normalized = "|".join((p or "").strip() for p in parts)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
EOF

safe_write "$BASE_DIR/shared_kernel/idempotency/store.py" <<'EOF'
from dataclasses import dataclass
from typing import Any


@dataclass
class IdempotencyRecord:
    key: str
    fingerprint: str
    response: Any | None = None
    status: str = "PENDING"


class InMemoryIdempotencyStore:
    def __init__(self) -> None:
        self._records: dict[str, IdempotencyRecord] = {}

    def get(self, key: str) -> IdempotencyRecord | None:
        return self._records.get(key)

    def save(self, record: IdempotencyRecord) -> None:
        self._records[record.key] = record
EOF

safe_write "$BASE_DIR/shared_kernel/audit/audit_context.py" <<'EOF'
from dataclasses import dataclass
from datetime import datetime, timezone

from shared_kernel.observability.correlation_id import get_correlation_id
from shared_kernel.observability.request_id import get_request_id


@dataclass
class AuditContext:
    actor: str
    action: str
    resource: str
    correlation_id: str
    request_id: str
    timestamp: str
    tenant_id: str | None = None
    network_id: str | None = None
    locker_id: str | None = None

    @classmethod
    def now(
        cls,
        actor: str,
        action: str,
        resource: str,
        tenant_id: str | None = None,
        network_id: str | None = None,
        locker_id: str | None = None,
    ) -> "AuditContext":
        return cls(
            actor=actor,
            action=action,
            resource=resource,
            correlation_id=get_correlation_id(),
            request_id=get_request_id(),
            timestamp=datetime.now(timezone.utc).isoformat(),
            tenant_id=tenant_id,
            network_id=network_id,
            locker_id=locker_id,
        )
EOF

safe_write "$BASE_DIR/shared_kernel/audit/audit_chain.py" <<'EOF'
import hashlib


def chain_hash(previous_hash: str, payload: str) -> str:
    raw = f"{previous_hash}|{payload}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
EOF

log "==> fase 2: platform_core"
safe_mkdir "$BASE_DIR/platform_core/app/core"
safe_mkdir "$BASE_DIR/platform_core/app/api/routers"
safe_mkdir "$BASE_DIR/platform_core/app/api/schemas"
safe_mkdir "$BASE_DIR/platform_core/app/domain/tenants"
safe_mkdir "$BASE_DIR/platform_core/app/domain/licensing"
safe_mkdir "$BASE_DIR/platform_core/app/domain/iam"
safe_mkdir "$BASE_DIR/platform_core/app/domain/partners"
safe_mkdir "$BASE_DIR/platform_core/app/infrastructure/db"
safe_mkdir "$BASE_DIR/platform_core/app/audit"
safe_mkdir "$BASE_DIR/platform_core/app/observability"
ensure_package_inits "$BASE_DIR/platform_core"

safe_write "$BASE_DIR/platform_core/README.md" <<'EOF'
# platform_core

Núcleo da plataforma SaaS de lockers.
EOF

safe_write "$BASE_DIR/platform_core/app/core/config.py" <<'EOF'
from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "platform_core"
    app_env: str = "dev"
    default_region: str = "SP"


settings = Settings()
EOF

safe_write "$BASE_DIR/platform_core/app/core/logging.py" <<'EOF'
import logging


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
EOF

safe_write "$BASE_DIR/platform_core/app/core/middleware.py" <<'EOF'
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from shared_kernel.observability.correlation_id import set_correlation_id
from shared_kernel.observability.request_id import set_request_id


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        set_request_id(request.headers.get("X-Request-Id"))
        set_correlation_id(request.headers.get("X-Correlation-Id"))
        response = await call_next(request)
        return response
EOF

safe_write "$BASE_DIR/platform_core/app/domain/tenants/models.py" <<'EOF'
from dataclasses import dataclass


@dataclass
class Tenant:
    tenant_id: str
    legal_name: str
    slug: str
    status: str = "ACTIVE"
EOF

safe_write "$BASE_DIR/platform_core/app/api/schemas/tenant.py" <<'EOF'
from pydantic import BaseModel, Field


class TenantCreateRequest(BaseModel):
    tenant_id: str = Field(..., min_length=1)
    legal_name: str = Field(..., min_length=1)
    slug: str = Field(..., min_length=1)
EOF

safe_write "$BASE_DIR/platform_core/app/api/routers/health.py" <<'EOF'
from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def healthcheck() -> dict:
    return {"status": "ok", "service": "platform_core"}
EOF

safe_write "$BASE_DIR/platform_core/app/api/routers/tenants.py" <<'EOF'
from fastapi import APIRouter

from app.api.schemas.tenant import TenantCreateRequest
from app.domain.tenants.models import Tenant

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.post("")
def create_tenant(payload: TenantCreateRequest) -> dict:
    tenant = Tenant(
        tenant_id=payload.tenant_id,
        legal_name=payload.legal_name,
        slug=payload.slug,
    )
    return {
        "tenant_id": tenant.tenant_id,
        "legal_name": tenant.legal_name,
        "slug": tenant.slug,
        "status": tenant.status,
    }
EOF

safe_write "$BASE_DIR/platform_core/app/main.py" <<'EOF'
from fastapi import FastAPI

from app.api.routers.health import router as health_router
from app.api.routers.tenants import router as tenants_router
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware

configure_logging()

app = FastAPI(title="platform_core")
app.add_middleware(RequestContextMiddleware)
app.include_router(health_router)
app.include_router(tenants_router)
EOF

log "==> fase 3: locker_operations"
safe_mkdir "$BASE_DIR/locker_operations/app/core"
safe_mkdir "$BASE_DIR/locker_operations/app/api/routers"
safe_mkdir "$BASE_DIR/locker_operations/app/api/schemas"
safe_mkdir "$BASE_DIR/locker_operations/app/domain/lockers"
safe_mkdir "$BASE_DIR/locker_operations/app/domain/slots"
safe_mkdir "$BASE_DIR/locker_operations/app/domain/allocations"
safe_mkdir "$BASE_DIR/locker_operations/app/domain/network"
safe_mkdir "$BASE_DIR/locker_operations/app/domain/telemetry"
safe_mkdir "$BASE_DIR/locker_operations/app/domain/incidents"
safe_mkdir "$BASE_DIR/locker_operations/app/infrastructure/db"
safe_mkdir "$BASE_DIR/locker_operations/app/audit"
safe_mkdir "$BASE_DIR/locker_operations/app/observability"
ensure_package_inits "$BASE_DIR/locker_operations"

safe_write "$BASE_DIR/locker_operations/README.md" <<'EOF'
# locker_operations

Domínio operacional da rede física de lockers.
EOF

safe_write "$BASE_DIR/locker_operations/app/core/config.py" <<'EOF'
from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "locker_operations"
    app_env: str = "dev"


settings = Settings()
EOF

safe_write "$BASE_DIR/locker_operations/app/core/logging.py" <<'EOF'
import logging


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
EOF

safe_write "$BASE_DIR/locker_operations/app/core/middleware.py" <<'EOF'
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from shared_kernel.observability.correlation_id import set_correlation_id
from shared_kernel.observability.request_id import set_request_id


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        set_request_id(request.headers.get("X-Request-Id"))
        set_correlation_id(request.headers.get("X-Correlation-Id"))
        response = await call_next(request)
        return response
EOF

safe_write "$BASE_DIR/locker_operations/app/domain/lockers/models.py" <<'EOF'
from dataclasses import dataclass


@dataclass
class Locker:
    locker_id: str
    tenant_id: str | None
    network_id: str
    site_id: str
    code: str
    status: str = "ACTIVE"
EOF

safe_write "$BASE_DIR/locker_operations/app/api/schemas/locker.py" <<'EOF'
from pydantic import BaseModel, Field


class LockerCreateRequest(BaseModel):
    locker_id: str = Field(..., min_length=1)
    network_id: str = Field(..., min_length=1)
    site_id: str = Field(..., min_length=1)
    code: str = Field(..., min_length=1)
    tenant_id: str | None = None
EOF

safe_write "$BASE_DIR/locker_operations/app/api/routers/health.py" <<'EOF'
from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def healthcheck() -> dict:
    return {"status": "ok", "service": "locker_operations"}
EOF

safe_write "$BASE_DIR/locker_operations/app/api/routers/lockers.py" <<'EOF'
from fastapi import APIRouter

from app.api.schemas.locker import LockerCreateRequest
from app.domain.lockers.models import Locker

router = APIRouter(prefix="/lockers", tags=["lockers"])


@router.post("")
def create_locker(payload: LockerCreateRequest) -> dict:
    locker = Locker(
        locker_id=payload.locker_id,
        tenant_id=payload.tenant_id,
        network_id=payload.network_id,
        site_id=payload.site_id,
        code=payload.code,
    )
    return {
        "locker_id": locker.locker_id,
        "tenant_id": locker.tenant_id,
        "network_id": locker.network_id,
        "site_id": locker.site_id,
        "code": locker.code,
        "status": locker.status,
    }
EOF

safe_write "$BASE_DIR/locker_operations/app/main.py" <<'EOF'
from fastapi import FastAPI

from app.api.routers.health import router as health_router
from app.api.routers.lockers import router as lockers_router
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware

configure_logging()

app = FastAPI(title="locker_operations")
app.add_middleware(RequestContextMiddleware)
app.include_router(health_router)
app.include_router(lockers_router)
EOF

log "==> fase 4: expansão conservadora payment_gateway"
safe_mkdir "$BASE_DIR/payment_gateway/app/core"
safe_mkdir "$BASE_DIR/payment_gateway/app/api/routers"
safe_mkdir "$BASE_DIR/payment_gateway/app/api/schemas"
safe_mkdir "$BASE_DIR/payment_gateway/app/domain/entities"
safe_mkdir "$BASE_DIR/payment_gateway/app/domain/services"
safe_mkdir "$BASE_DIR/payment_gateway/app/integrations/payments/base"
safe_mkdir "$BASE_DIR/payment_gateway/app/integrations/payments/stripe"
safe_mkdir "$BASE_DIR/payment_gateway/app/integrations/payments/mercadopago"
safe_mkdir "$BASE_DIR/payment_gateway/app/infrastructure/db"
safe_mkdir "$BASE_DIR/payment_gateway/app/infrastructure/secrets"
safe_mkdir "$BASE_DIR/payment_gateway/app/audit"
safe_mkdir "$BASE_DIR/payment_gateway/app/observability"
ensure_package_inits "$BASE_DIR/payment_gateway"

safe_write "$BASE_DIR/payment_gateway/app/integrations/payments/base/exceptions.py" <<'EOF'
class PaymentProviderError(Exception):
    pass


class PaymentAuthenticationError(PaymentProviderError):
    pass


class PaymentValidationError(PaymentProviderError):
    pass


class PaymentWebhookVerificationError(PaymentProviderError):
    pass
EOF

safe_write "$BASE_DIR/payment_gateway/app/integrations/payments/base/contracts.py" <<'EOF'
from dataclasses import dataclass
from typing import Protocol


@dataclass
class CreatePaymentCommand:
    order_id: str
    amount: float
    currency: str
    country: str
    customer_reference: str | None = None


@dataclass
class PaymentResult:
    provider: str
    provider_payment_id: str
    status: str
    raw_status: str
    redirect_url: str | None = None
    qr_code: str | None = None


class PaymentProvider(Protocol):
    provider_name: str

    def create_payment(self, command: CreatePaymentCommand) -> PaymentResult:
        ...

    def get_payment_status(self, provider_payment_id: str) -> PaymentResult:
        ...
EOF

safe_write "$BASE_DIR/payment_gateway/app/integrations/payments/base/webhook_verifier.py" <<'EOF'
from shared_kernel.security.webhook_signatures import verify_hmac_sha256
from app.integrations.payments.base.exceptions import PaymentWebhookVerificationError


def verify_webhook_or_raise(payload: bytes, secret: str, received_signature: str) -> None:
    valid = verify_hmac_sha256(payload, secret, received_signature)
    if not valid:
        raise PaymentWebhookVerificationError("Invalid webhook signature")
EOF

safe_write "$BASE_DIR/payment_gateway/app/integrations/payments/stripe/client.py" <<'EOF'
from app.integrations.payments.base.contracts import CreatePaymentCommand, PaymentResult


class StripeClient:
    provider_name = "stripe"

    def __init__(self, secret_key: str, account_region: str) -> None:
        self.secret_key = secret_key
        self.account_region = account_region

    def create_payment(self, command: CreatePaymentCommand) -> PaymentResult:
        return PaymentResult(
            provider=self.provider_name,
            provider_payment_id=f"stripe_{command.order_id}",
            status="PENDING",
            raw_status="stub_created",
        )
EOF

safe_write "$BASE_DIR/payment_gateway/app/integrations/payments/stripe/sp.py" <<'EOF'
from app.integrations.payments.stripe.client import StripeClient


def build_provider(secret_key: str) -> StripeClient:
    return StripeClient(secret_key=secret_key, account_region="SP")
EOF

safe_write "$BASE_DIR/payment_gateway/app/integrations/payments/stripe/pt.py" <<'EOF'
from app.integrations.payments.stripe.client import StripeClient


def build_provider(secret_key: str) -> StripeClient:
    return StripeClient(secret_key=secret_key, account_region="PT")
EOF

safe_write "$BASE_DIR/payment_gateway/app/integrations/payments/mercadopago/client.py" <<'EOF'
from app.integrations.payments.base.contracts import CreatePaymentCommand, PaymentResult


class MercadoPagoClient:
    provider_name = "mercadopago"

    def __init__(self, access_token: str) -> None:
        self.access_token = access_token

    def create_payment(self, command: CreatePaymentCommand) -> PaymentResult:
        return PaymentResult(
            provider=self.provider_name,
            provider_payment_id=f"mp_{command.order_id}",
            status="PENDING",
            raw_status="stub_created",
        )
EOF

safe_write "$BASE_DIR/payment_gateway/app/integrations/payments/mercadopago/sp.py" <<'EOF'
from app.integrations.payments.mercadopago.client import MercadoPagoClient


def build_provider(access_token: str) -> MercadoPagoClient:
    return MercadoPagoClient(access_token=access_token)
EOF

log "==> fase 5: logistics_service"
safe_mkdir "$BASE_DIR/logistics_service/app/core"
safe_mkdir "$BASE_DIR/logistics_service/app/api/routers"
safe_mkdir "$BASE_DIR/logistics_service/app/api/schemas"
safe_mkdir "$BASE_DIR/logistics_service/app/integrations/carriers/base"
safe_mkdir "$BASE_DIR/logistics_service/app/integrations/carriers/jadlog"
safe_mkdir "$BASE_DIR/logistics_service/app/integrations/carriers/fedex"
safe_mkdir "$BASE_DIR/logistics_service/app/integrations/carriers/dhl"
safe_mkdir "$BASE_DIR/logistics_service/app/audit"
safe_mkdir "$BASE_DIR/logistics_service/app/observability"
ensure_package_inits "$BASE_DIR/logistics_service"

safe_write "$BASE_DIR/logistics_service/README.md" <<'EOF'
# logistics_service

Serviço responsável por integrações com transportadoras.
EOF

safe_write "$BASE_DIR/logistics_service/app/integrations/carriers/base/contracts.py" <<'EOF'
from dataclasses import dataclass
from typing import Protocol


@dataclass
class CreateShipmentCommand:
    shipment_id: str
    country: str
    recipient_name: str
    address_line: str
    postal_code: str
    city: str


@dataclass
class ShipmentResult:
    provider: str
    provider_shipment_id: str
    status: str
    tracking_code: str | None = None


class CarrierProvider(Protocol):
    provider_name: str

    def create_shipment(self, command: CreateShipmentCommand) -> ShipmentResult:
        ...
EOF

safe_write "$BASE_DIR/logistics_service/app/integrations/carriers/jadlog/sp.py" <<'EOF'
from app.integrations.carriers.base.contracts import CreateShipmentCommand, ShipmentResult


class JadlogSPClient:
    provider_name = "jadlog"

    def create_shipment(self, command: CreateShipmentCommand) -> ShipmentResult:
        return ShipmentResult(
            provider=self.provider_name,
            provider_shipment_id=f"jadlog_{command.shipment_id}",
            status="CREATED",
            tracking_code=f"JAD-{command.shipment_id}",
        )
EOF

safe_write "$BASE_DIR/logistics_service/app/integrations/carriers/fedex/sp.py" <<'EOF'
from app.integrations.carriers.base.contracts import CreateShipmentCommand, ShipmentResult


class FedexSPClient:
    provider_name = "fedex"

    def create_shipment(self, command: CreateShipmentCommand) -> ShipmentResult:
        return ShipmentResult(
            provider=self.provider_name,
            provider_shipment_id=f"fedex_{command.shipment_id}",
            status="CREATED",
            tracking_code=f"FDX-{command.shipment_id}",
        )
EOF

safe_write "$BASE_DIR/logistics_service/app/integrations/carriers/dhl/pt.py" <<'EOF'
from app.integrations.carriers.base.contracts import CreateShipmentCommand, ShipmentResult


class DHLPTClient:
    provider_name = "dhl"

    def create_shipment(self, command: CreateShipmentCommand) -> ShipmentResult:
        return ShipmentResult(
            provider=self.provider_name,
            provider_shipment_id=f"dhl_{command.shipment_id}",
            status="CREATED",
            tracking_code=f"DHL-{command.shipment_id}",
        )
EOF

log "==> fase 6: commerce_hub"
safe_mkdir "$BASE_DIR/commerce_hub/app/core"
safe_mkdir "$BASE_DIR/commerce_hub/app/api/routers"
safe_mkdir "$BASE_DIR/commerce_hub/app/api/schemas"
safe_mkdir "$BASE_DIR/commerce_hub/app/integrations/channels/base"
safe_mkdir "$BASE_DIR/commerce_hub/app/integrations/channels/mercadolivre"
safe_mkdir "$BASE_DIR/commerce_hub/app/integrations/channels/magalu"
safe_mkdir "$BASE_DIR/commerce_hub/app/integrations/channels/ifood"
safe_mkdir "$BASE_DIR/commerce_hub/app/integrations/channels/amazon"
safe_mkdir "$BASE_DIR/commerce_hub/app/integrations/channels/ctt"
safe_mkdir "$BASE_DIR/commerce_hub/app/integrations/channels/worten"
safe_mkdir "$BASE_DIR/commerce_hub/app/audit"
safe_mkdir "$BASE_DIR/commerce_hub/app/observability"
ensure_package_inits "$BASE_DIR/commerce_hub"

safe_write "$BASE_DIR/commerce_hub/README.md" <<'EOF'
# commerce_hub

Serviço responsável por integrações com marketplaces e canais.
EOF

safe_write "$BASE_DIR/commerce_hub/app/integrations/channels/base/contracts.py" <<'EOF'
from dataclasses import dataclass
from typing import Protocol


@dataclass
class ImportOrdersCommand:
    account_id: str
    country: str


@dataclass
class ChannelOrderResult:
    provider: str
    external_order_id: str
    status: str
    raw_status: str


class ChannelProvider(Protocol):
    provider_name: str

    def import_orders(self, command: ImportOrdersCommand) -> list[ChannelOrderResult]:
        ...
EOF

safe_write "$BASE_DIR/commerce_hub/app/integrations/channels/mercadolivre/sp.py" <<'EOF'
from app.integrations.channels.base.contracts import ImportOrdersCommand, ChannelOrderResult


class MercadoLivreSPClient:
    provider_name = "mercadolivre"

    def import_orders(self, command: ImportOrdersCommand) -> list[ChannelOrderResult]:
        return [
            ChannelOrderResult(
                provider=self.provider_name,
                external_order_id="ml_stub_001",
                status="NEW",
                raw_status="stub_new",
            )
        ]
EOF

safe_write "$BASE_DIR/commerce_hub/app/integrations/channels/magalu/sp.py" <<'EOF'
from app.integrations.channels.base.contracts import ImportOrdersCommand, ChannelOrderResult


class MagaluSPClient:
    provider_name = "magalu"

    def import_orders(self, command: ImportOrdersCommand) -> list[ChannelOrderResult]:
        return []
EOF

safe_write "$BASE_DIR/commerce_hub/app/integrations/channels/ifood/sp.py" <<'EOF'
from app.integrations.channels.base.contracts import ImportOrdersCommand, ChannelOrderResult


class IFoodSPClient:
    provider_name = "ifood"

    def import_orders(self, command: ImportOrdersCommand) -> list[ChannelOrderResult]:
        return []
EOF

safe_write "$BASE_DIR/commerce_hub/app/integrations/channels/amazon/sp.py" <<'EOF'
from app.integrations.channels.base.contracts import ImportOrdersCommand, ChannelOrderResult


class AmazonSPClient:
    provider_name = "amazon"

    def import_orders(self, command: ImportOrdersCommand) -> list[ChannelOrderResult]:
        return []
EOF

safe_write "$BASE_DIR/commerce_hub/app/integrations/channels/amazon/pt.py" <<'EOF'
from app.integrations.channels.base.contracts import ImportOrdersCommand, ChannelOrderResult


class AmazonPTClient:
    provider_name = "amazon"

    def import_orders(self, command: ImportOrdersCommand) -> list[ChannelOrderResult]:
        return []
EOF

safe_write "$BASE_DIR/commerce_hub/app/integrations/channels/ctt/pt.py" <<'EOF'
from app.integrations.channels.base.contracts import ImportOrdersCommand, ChannelOrderResult


class CTTPTClient:
    provider_name = "ctt"

    def import_orders(self, command: ImportOrdersCommand) -> list[ChannelOrderResult]:
        return []
EOF

safe_write "$BASE_DIR/commerce_hub/app/integrations/channels/worten/pt.py" <<'EOF'
from app.integrations.channels.base.contracts import ImportOrdersCommand, ChannelOrderResult


class WortenPTClient:
    provider_name = "worten"

    def import_orders(self, command: ImportOrdersCommand) -> list[ChannelOrderResult]:
        return []
EOF

log "==> fase 7: simulator"
safe_mkdir "$BASE_DIR/simulator/payment_providers"
safe_mkdir "$BASE_DIR/simulator/carriers"
safe_mkdir "$BASE_DIR/simulator/channels"
ensure_package_inits "$BASE_DIR/simulator"

safe_write "$BASE_DIR/simulator/README.md" <<'EOF'
# simulator

Ambiente de simulação e fixtures.
EOF

safe_write "$BASE_DIR/simulator/payment_providers/webhook_fixtures.py" <<'EOF'
STRIPE_WEBHOOK_SAMPLE = {"type": "payment_intent.succeeded"}
MERCADOPAGO_WEBHOOK_SAMPLE = {"action": "payment.updated"}
EOF

safe_write "$BASE_DIR/simulator/carriers/tracking_fixtures.py" <<'EOF'
TRACKING_SAMPLE = {
    "tracking_code": "SIM-TRACK-001",
    "status": "IN_TRANSIT",
}
EOF

safe_write "$BASE_DIR/simulator/channels/order_fixtures.py" <<'EOF'
CHANNEL_ORDER_SAMPLE = {
    "external_order_id": "ORDER-STUB-001",
    "status": "NEW",
}
EOF

generate_diff_report
write_summary_report

log "==> concluído"
log "Relatório: $REPORT_FILE"
log "Diff da árvore: $TREE_DIFF"
log "Log: $LOG_FILE"

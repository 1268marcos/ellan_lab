# 01_source/backend/billing_fiscal_service/app/core/config.py
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
def analyze_fiscal_router_config():
    """
    Analisa a configuração atual do Billing Fiscal Service e retorna:
    - environment: Ambiente (app_env)
    - providers_real: Se os providers reais estão habilitados (BR/PT) e se há URLs configuradas
    - active_stubs: Lista de stubs ativos roteados
    - contingency_supported: Modos de contingência suportados
    - release_gate: risk_flags de acordo com a configuração atual
    - recommendation: Sugestão quanto ao uso de providers reais
    """
    import json

    # 1. Providers reais habilitados e URLs base
    providers_real = {
        "FISCAL_REAL_PROVIDER_BR_ENABLED": getattr(settings, "fiscal_real_provider_br_enabled", False),
        "FISCAL_REAL_PROVIDER_PT_ENABLED": getattr(settings, "fiscal_real_provider_pt_enabled", False),
        "BR_BASE_URL_CONFIGURED": (
            hasattr(settings, "sefaz_br_base_url")
            and isinstance(settings.sefaz_br_base_url, str)
            and len(settings.sefaz_br_base_url.strip()) > 0
        ) if hasattr(settings, "sefaz_br_base_url") else False,
        "PT_BASE_URL_CONFIGURED": (
            hasattr(settings, "at_pt_base_url")
            and isinstance(settings.at_pt_base_url, str)
            and len(settings.at_pt_base_url.strip()) > 0
        ) if hasattr(settings, "at_pt_base_url") else False,
    }

    # 2. Stubs ativos (sempre presentes, exceto se provider real estiver habilitado)
    active_stubs = []
    if not providers_real["FISCAL_REAL_PROVIDER_BR_ENABLED"]:
        active_stubs.append("sefaz_sp_service")
    if not providers_real["FISCAL_REAL_PROVIDER_PT_ENABLED"]:
        active_stubs.append("at_pt_service")
    active_stubs.append("aeat_es_service")  # ES não tem provider real implementado

    # 3. Modos de contingência suportados pelo router
    contingency_supported = {
        "OFFLINE_SAT": True,
        "CONTINGENCY_SVRS": True,
        "route_issue_invoice_handles": True,
    }

    # 4. Release Gate (risk_flags)
    def build_fiscal_release_gate_payload():
        risk_flags = []
        if not providers_real["FISCAL_REAL_PROVIDER_BR_ENABLED"]:
            risk_flags.append("BR_STUB")
        if not providers_real["FISCAL_REAL_PROVIDER_PT_ENABLED"]:
            risk_flags.append("PT_STUB")
        # Contingência é fallback, não flag
        return risk_flags

    release_gate = {
        "risk_flags": build_fiscal_release_gate_payload()
    }

    # 5. Recomendação
    has_real = providers_real["FISCAL_REAL_PROVIDER_BR_ENABLED"] or providers_real["FISCAL_REAL_PROVIDER_PT_ENABLED"]
    recommendation = (
        "Habilitar provider real para produção" if not has_real else
        "Providers reais ativos, ok para produção"
    )

    result = {
        "environment": getattr(settings, "app_env", "dev"),
        "providers_real": providers_real,
        "active_stubs": active_stubs,
        "contingency_supported": contingency_supported,
        "release_gate": release_gate,
        "recommendation": recommendation,
    }

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    service_name: str = Field(default="billing_fiscal_service", alias="SERVICE_NAME")
    app_env: str = Field(default="dev", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8020, alias="PORT")
    internal_token: str = Field(default="dev-internal-token", alias="INTERNAL_TOKEN")

    postgres_host: str = Field(default="postgres_central", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="locker_central", alias="POSTGRES_DB")
    postgres_user: str = Field(default="admin", alias="POSTGRES_USER")
    postgres_password: str = Field(default="admin123", alias="POSTGRES_PASSWORD")

    order_pickup_service_url: str = Field(
        default="http://order_pickup_service:8003",
        alias="ORDER_PICKUP_SERVICE_URL",
    )
    order_pickup_timeout_sec: int = Field(default=5, alias="ORDER_PICKUP_TIMEOUT_SEC")

    invoice_issue_poll_sec: int = Field(default=5, alias="INVOICE_ISSUE_POLL_SEC")
    invoice_issue_batch_size: int = Field(default=50, alias="INVOICE_ISSUE_BATCH_SIZE")
    invoice_issue_max_retries: int = Field(default=5, alias="INVOICE_ISSUE_MAX_RETRIES")
    invoice_issue_base_backoff_sec: int = Field(default=15, alias="INVOICE_ISSUE_BASE_BACKOFF_SEC")
    invoice_issue_processing_timeout_sec: int = Field(
        default=180,
        alias="INVOICE_ISSUE_PROCESSING_TIMEOUT_SEC",
    )
    invoice_issue_worker_id: str = Field(default="billing_fiscal_issue_worker", alias="INVOICE_ISSUE_WORKER_ID")

    # F-3 — E-mail fiscal (SMTP opcional + fila invoice_email_outbox)
    invoice_smtp_enabled: bool = Field(default=False, alias="INVOICE_SMTP_ENABLED")
    smtp_host: str | None = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: str | None = Field(default=None, alias="SMTP_USER")
    smtp_password: str | None = Field(default=None, alias="SMTP_PASSWORD")
    smtp_from: str | None = Field(default=None, alias="SMTP_FROM")
    smtp_use_tls: bool = Field(default=True, alias="SMTP_USE_TLS")
    smtp_use_ssl: bool = Field(default=False, alias="SMTP_USE_SSL")
    invoice_email_max_retries: int = Field(default=5, alias="INVOICE_EMAIL_MAX_RETRIES")
    invoice_email_lock_sec: int = Field(default=120, alias="INVOICE_EMAIL_LOCK_SEC")

    # F-3 — adapters de provider real (primeiro slice: estrutura + feature flags)
    fiscal_real_provider_br_enabled: bool = Field(default=False, alias="FISCAL_REAL_PROVIDER_BR_ENABLED")
    fiscal_real_provider_pt_enabled: bool = Field(default=False, alias="FISCAL_REAL_PROVIDER_PT_ENABLED")
    fiscal_real_provider_timeout_sec: int = Field(default=8, alias="FISCAL_REAL_PROVIDER_TIMEOUT_SEC")
    fiscal_real_provider_retries: int = Field(default=2, alias="FISCAL_REAL_PROVIDER_RETRIES")
    fiscal_real_provider_base_url_br: str | None = Field(default=None, alias="FISCAL_REAL_PROVIDER_BASE_URL_BR")
    fiscal_real_provider_base_url_pt: str | None = Field(default=None, alias="FISCAL_REAL_PROVIDER_BASE_URL_PT")
    fiscal_real_provider_api_key_br: str | None = Field(default=None, alias="FISCAL_REAL_PROVIDER_API_KEY_BR")
    fiscal_real_provider_api_key_pt: str | None = Field(default=None, alias="FISCAL_REAL_PROVIDER_API_KEY_PT")
    fiscal_a1_dry_run_enabled: bool = Field(default=False, alias="FISCAL_A1_DRY_RUN_ENABLED")
    fiscal_a1_dry_run_cert_ref: str | None = Field(default=None, alias="FISCAL_A1_DRY_RUN_CERT_REF")
    fiscal_a1_dry_run_hmac_secret: str | None = Field(default=None, alias="FISCAL_A1_DRY_RUN_HMAC_SECRET")

    fiscal_require_complete_consumer_for_real_issue: bool = Field(
        default=True,
        alias="FISCAL_REQUIRE_COMPLETE_CONSUMER_FOR_REAL_ISSUE",
    )

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
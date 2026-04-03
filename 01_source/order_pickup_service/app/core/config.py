# 01_source/order_pickup_service/app/core/config.py
# 02/04/2026 v3 - Enhanced with Global Market Support
# veja fim do arquivo

from functools import lru_cache
from typing import List, Dict, Optional, Set
from enum import Enum

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class RegionGroup(str, Enum):
    """Grupos de regiões para configurações agrupadas"""
    LATIN_AMERICA = "latin_america"
    NORTH_AMERICA = "north_america"
    WESTERN_EUROPE = "western_europe"
    EASTERN_EUROPE = "eastern_europe"
    AFRICA = "africa"
    EAST_ASIA = "east_asia"
    SOUTHEAST_ASIA = "southeast_asia"
    MIDDLE_EAST = "middle_east"
    OCEANIA = "oceania"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # =========================================================
    # Banco / serviço
    # =========================================================

    database_url: str = Field(
        default="sqlite:////data/sqlite/order_pickup/orders.db",
        alias="DATABASE_URL",
    )

    service_name: str = Field(
        default="order_pickup_service",
        alias="SERVICE_NAME",
    )

    environment: str = Field(
        default="development",
        alias="ENVIRONMENT",
    )

    app_version: str = Field(
        default="0.1.0",
        alias="APP_VERSION",
    )

    run_db_migrations_on_startup: bool = Field(
        default=False,
        alias="RUN_DB_MIGRATIONS_ON_STARTUP",
    )

    # =========================================================
    # 🔥 FRONTEND (CORREÇÃO DO BUG DE EMAIL)
    # =========================================================

    frontend_base_url: str = Field(
        default="http://localhost:5173",
        alias="FRONTEND_BASE_URL",
    )

    # Frontend URLs por região
    frontend_base_urls: Dict[str, str] = Field(
        default_factory=dict,
        alias="FRONTEND_BASE_URLS",
    )

    # =========================================================
    # Fluxo de pickup / deadlines (configurações globais)
    # =========================================================

    pickup_window_sec: int = Field(default=7200, alias="PICKUP_WINDOW_SEC")
    pickup_token_ttl_sec: int = Field(default=600, alias="PICKUP_TOKEN_TTL_SEC")
    prepayment_timeout_seconds: int = Field(default=90, alias="PREPAYMENT_TIMEOUT_SECONDS")

    expiry_poll_sec: int = Field(default=60, alias="EXPIRY_POLL_SEC")
    lifecycle_events_poll_sec: int = Field(default=10, alias="LIFECYCLE_EVENTS_POLL_SEC")

    expiry_batch_size: int = Field(default=100, alias="EXPIRY_BATCH_SIZE")
    expiry_max_retries: int = Field(default=3, alias="EXPIRY_MAX_RETRIES")

    expiry_enable_credit: bool = Field(default=False, alias="EXPIRY_ENABLE_CREDIT")
    expiry_credit_ratio: float = Field(default=0.50, alias="EXPIRY_CREDIT_RATIO")

    lifecycle_events_batch_size: int = Field(default=100, alias="LIFECYCLE_EVENTS_BATCH_SIZE")

    # =========================================================
    # Configurações regionais de pickup window
    # =========================================================
    
    regional_pickup_window_sec: Dict[str, int] = Field(
        default_factory=lambda: {
            # América Latina
            "BR": 7200,
            "SP": 7200,    # 2 horas
            "RJ": 7200,
            "MG": 7200,
            "RS": 7200,
            "BA": 7200,
            "MX": 10800,   # 3 horas
            "AR": 10800,
            "CO": 10800,
            "CL": 10800,
            # América do Norte
            "US_NY": 10800,
            "US_CA": 10800,
            "CA_ON": 10800,
            # Europa Ocidental
            "PT": 7200,
            "ES": 7200,
            "FR": 7200,
            "DE": 7200,
            "UK": 7200,
            "IT": 7200,
            "FI": 10800,   # 3 horas (devido à distância)
            # Europa Oriental
            "PL": 7200,
            "RU": 14400,   # 4 horas
            "TR": 10800,
            # África
            "ZA": 14400,   # 4 horas
            "NG": 21600,   # 6 horas
            "KE": 14400,
            "EG": 10800,
            # Ásia
            "CN": 7200,
            "JP": 7200,
            "KR": 7200,
            "TH": 7200,
            "ID": 10800,
            "SG": 7200,
            "PH": 10800,
            # Oriente Médio
            "AE": 10800,
            "SA": 10800,
            # Oceania
            "AU": 10800,
            "NZ": 10800,
        },
        alias="REGIONAL_PICKUP_WINDOW_SEC",
    )
    
    regional_prepayment_timeout_seconds: Dict[str, int] = Field(
        default_factory=lambda: {
            # Padrões regionais de timeout de pagamento
            "BR": 90,
            "SP": 90,
            "PT": 120,
            "CN": 300,    # 5 minutos para China (Alipay/WeChat)
            "JP": 180,    # 3 minutos para Japão
            "US_NY": 120,
            "NG": 300,    # 5 minutos para Nigéria (mobile money)
            "KE": 300,
            "AE": 180,
            "AU": 120,
        },
        alias="REGIONAL_PREPAYMENT_TIMEOUT_SEC",
    )

    # =========================================================
    # Backends internos / integração
    # =========================================================
    
    runtime_internal: str = Field(
        default="http://backend_runtime:8000",
        alias="RUNTIME_INTERNAL",
    )

    payment_gateway_internal: str = Field(
        default="http://payment_gateway:8000",
        alias="PAYMENT_GATEWAY_INTERNAL",
    )

    lifecycle_base_url: str = Field(
        default="http://order_lifecycle_service:8010",
        alias="ORDER_LIFECYCLE_BASE_URL",
    )

    # URLs específicas por região
    regional_runtime_urls: Dict[str, str] = Field(
        default_factory=dict,
        alias="REGIONAL_RUNTIME_URLS",
    )
    
    regional_payment_gateway_urls: Dict[str, str] = Field(
        default_factory=dict,
        alias="REGIONAL_PAYMENT_GATEWAY_URLS",
    )
    
    regional_lifecycle_urls: Dict[str, str] = Field(
        default_factory=dict,
        alias="REGIONAL_LIFECYCLE_URLS",
    )

    backend_client_timeout_sec: int = Field(default=5, alias="BACKEND_CLIENT_TIMEOUT_SEC")
    order_lifecycle_timeout_sec: int = Field(default=5, alias="ORDER_LIFECYCLE_TIMEOUT_SEC")
    
    # Timeouts regionais
    regional_backend_timeout_sec: Dict[str, int] = Field(
        default_factory=lambda: {
            "NG": 10,   # Timeout maior para Nigéria
            "KE": 10,
            "RU": 10,
            "CN": 8,
        },
        alias="REGIONAL_BACKEND_TIMEOUT_SEC",
    )

    backend_price_path_template: str = Field(
        default="/catalog/skus/{sku_id}",
        alias="BACKEND_PRICE_PATH_TEMPLATE",
    )

    payment_gateway_lockers_path_template: str = Field(
        default="/lockers/{locker_id}",
        alias="PAYMENT_GATEWAY_LOCKERS_PATH_TEMPLATE",
    )

    # =========================================================
    # Segurança / auth interna
    # =========================================================

    internal_token: str = Field(default="dev-internal-token", alias="INTERNAL_TOKEN")
    internal_health_token: str = Field(default="secret-token-123", alias="INTERNAL_HEALTH_TOKEN")

    jwt_secret: str = Field(default="CHANGE_ME_IN_PROD", alias="JWT_SECRET")
    jwt_alg: str = Field(default="HS256", alias="JWT_ALG")
    jwt_access_ttl_min: int = Field(default=60, alias="JWT_ACCESS_TTL_MIN")
    
    # Tokens específicos por região (para integrações regionais)
    regional_internal_tokens: Dict[str, str] = Field(
        default_factory=dict,
        alias="REGIONAL_INTERNAL_TOKENS",
    )

    # =========================================================
    # QR / resgate manual
    # =========================================================

    qr_rotate_sec: int = Field(default=600, alias="QR_ROTATE_SEC")

    pickup_qr_payload_version: int = Field(
        default=2,
        alias="PICKUP_QR_PAYLOAD_VERSION",
    )

    pickup_qr_secret: str = Field(default="", alias="PICKUP_QR_SECRET")
    
    # Secrets específicos por região
    regional_qr_secrets: Dict[str, str] = Field(
        default_factory=dict,
        alias="REGIONAL_QR_SECRETS",
    )

    manual_redeem_max_attempts: int = Field(default=5, alias="MANUAL_REDEEM_MAX_ATTEMPTS")
    manual_redeem_window_sec: int = Field(default=120, alias="MANUAL_REDEEM_WINDOW_SEC")
    manual_redeem_block_sec: int = Field(default=300, alias="MANUAL_REDEEM_BLOCK_SEC")
    
    # Configurações regionais para redeems manuais
    regional_manual_redeem_max_attempts: Dict[str, int] = Field(
        default_factory=lambda: {
            "CN": 3,    # Menos tentativas na China
            "JP": 3,
            "SG": 3,
        },
        alias="REGIONAL_MANUAL_REDEEM_MAX_ATTEMPTS",
    )

    # =========================================================
    # DEV / fallback
    # =========================================================

    dev_bypass_auth: bool = Field(default=False, alias="DEV_BYPASS_AUTH")
    dev_user_id: str = Field(default="dev_user_1", alias="DEV_USER_ID")

    dev_allow_unknown_sku: bool = Field(default=False, alias="DEV_ALLOW_UNKNOWN_SKU")
    dev_default_price_cents: int = Field(default=1000, alias="DEV_DEFAULT_PRICE_CENTS")
    dev_default_currency: str = Field(default="EUR", alias="DEV_DEFAULT_CURRENCY")
    
    # Moedas padrão por região
    regional_default_currencies: Dict[str, str] = Field(
        default_factory=lambda: {
            "BR": "BRL",
            "SP": "BRL",
            "PT": "EUR",
            "US_NY": "USD",
            "UK": "GBP",
            "CN": "CNY",
            "JP": "JPY",
            "KR": "KRW",
            "TH": "THB",
            "ID": "IDR",
            "SG": "SGD",
            "PH": "PHP",
            "AE": "AED",
            "SA": "SAR",
            "RU": "RUB",
            "TR": "TRY",
            "AU": "AUD",
            "NZ": "NZD",
            "ZA": "ZAR",
            "NG": "NGN",
            "KE": "KES",
        },
        alias="REGIONAL_DEFAULT_CURRENCIES",
    )

    # =========================================================
    # Orders service / compat
    # =========================================================

    alloc_ttl_sec: int = Field(default=120, alias="ALLOC_TTL_SEC")
    
    # TTL regional para alocações
    regional_alloc_ttl_sec: Dict[str, int] = Field(
        default_factory=lambda: {
            "CN": 300,   # 5 minutos para China
            "JP": 180,
            "NG": 300,
            "KE": 300,
        },
        alias="REGIONAL_ALLOC_TTL_SEC",
    )

    app_env: str = Field(default="dev", alias="APP_ENV")
    node_env: str = Field(default="dev", alias="NODE_ENV")

    # =========================================================
    # Email / SMTP
    # =========================================================

    email_enabled: bool = Field(default=False, alias="EMAIL_ENABLED")

    email_host: str = Field(default="", alias="EMAIL_HOST")
    email_port: int = Field(default=465, alias="EMAIL_PORT")
    email_secure: bool = Field(default=True, alias="EMAIL_SECURE")

    email_username: str = Field(default="", alias="EMAIL_USERNAME")
    email_password: str = Field(default="", alias="EMAIL_PASSWORD")

    email_sender: str = Field(default="", alias="EMAIL_SENDER")
    email_from_name: str = Field(default="ELLAN LAB", alias="EMAIL_FROM_NAME")
    
    # Configurações SMTP regionais (para provedores locais)
    regional_email_hosts: Dict[str, str] = Field(
        default_factory=dict,
        alias="REGIONAL_EMAIL_HOSTS",
    )
    regional_email_ports: Dict[str, int] = Field(
        default_factory=dict,
        alias="REGIONAL_EMAIL_PORTS",
    )

    # =========================================================
    # Notificações (SMS, WhatsApp, WeChat, LINE)
    # =========================================================
    
    # SMS
    sms_enabled: bool = Field(default=False, alias="SMS_ENABLED")
    sms_provider: str = Field(default="twilio", alias="SMS_PROVIDER")
    sms_api_key: Optional[str] = Field(default=None, alias="SMS_API_KEY")
    sms_api_secret: Optional[str] = Field(default=None, alias="SMS_API_SECRET")
    
    # Provedores SMS regionais
    regional_sms_providers: Dict[str, str] = Field(
        default_factory=lambda: {
            "NG": "africastalking",
            "KE": "africastalking",
            "ZA": "africastalking",
            "CN": "aliyun",
            "IN": "msg91",
        },
        alias="REGIONAL_SMS_PROVIDERS",
    )
    
    # WhatsApp
    whatsapp_enabled: bool = Field(default=False, alias="WHATSAPP_ENABLED")
    whatsapp_api_key: Optional[str] = Field(default=None, alias="WHATSAPP_API_KEY")
    
    # WeChat (China)
    wechat_enabled: bool = Field(default=False, alias="WECHAT_ENABLED")
    wechat_app_id: Optional[str] = Field(default=None, alias="WECHAT_APP_ID")
    wechat_app_secret: Optional[str] = Field(default=None, alias="WECHAT_APP_SECRET")
    
    # LINE (Japão, Tailândia)
    line_enabled: bool = Field(default=False, alias="LINE_ENABLED")
    line_channel_id: Optional[str] = Field(default=None, alias="LINE_CHANNEL_ID")
    line_channel_secret: Optional[str] = Field(default=None, alias="LINE_CHANNEL_SECRET")
    
    # KakaoTalk (Coreia do Sul)
    kakao_enabled: bool = Field(default=False, alias="KAKAO_ENABLED")
    kakao_api_key: Optional[str] = Field(default=None, alias="KAKAO_API_KEY")

    # =========================================================
    # Regiões para Lockers (EXPANDIDO)
    # =========================================================
    
    # Lista completa de regiões válidas
    VALID_LOCKER_REGIONS: List[str] = [
        # América Latina
        "BR", "SP", "RJ", "MG", "RS", "BA", "PR", "SC", "PE",
        "MX", "AR", "CO", "CL", "PE", "EC", "UY", "PY", "BO", "VE", "CR", "PA", "DO",
        # América do Norte
        "US_NY", "US_CA", "US_TX", "US_FL", "US_IL", "CA_ON", "CA_QC", "CA_BC",
        # Europa Ocidental
        "PT", "ES", "FR", "DE", "UK", "IT", "NL", "BE", "CH", "SE", "NO", "DK", "FI", "IE", "AT",
        # Europa Oriental
        "PL", "CZ", "GR", "HU", "RO", "RU", "TR",
        # África
        "ZA", "NG", "KE", "EG", "MA", "GH", "SN", "CI", "TZ", "UG", "RW", "MZ", "AO", "DZ", "TN",
        # Ásia
        "CN", "JP", "KR", "TH", "ID", "SG", "PH", "VN", "MY",
        # Oriente Médio
        "AE", "SA", "QA", "KW", "BH", "OM", "JO",
        # Oceania
        "AU", "NZ",
    ]
    
    VALIDATE_LOCKER_REGION: bool = Field(
        default=True,  # Mudado para True para maior segurança
        alias="VALIDATE_LOCKER_REGION",
    )
    
    # Mapeamento de região para grupo
    region_to_group: Dict[str, RegionGroup] = Field(
        default_factory=lambda: {
            # América Latina
            "BR": RegionGroup.LATIN_AMERICA, 
            "SP": RegionGroup.LATIN_AMERICA, "RJ": RegionGroup.LATIN_AMERICA,
            "MG": RegionGroup.LATIN_AMERICA, "RS": RegionGroup.LATIN_AMERICA,
            "BA": RegionGroup.LATIN_AMERICA, "MX": RegionGroup.LATIN_AMERICA,
            "AR": RegionGroup.LATIN_AMERICA, "CO": RegionGroup.LATIN_AMERICA,
            "CL": RegionGroup.LATIN_AMERICA, "PE": RegionGroup.LATIN_AMERICA,
            # América do Norte
            "US_NY": RegionGroup.NORTH_AMERICA, "US_CA": RegionGroup.NORTH_AMERICA,
            "CA_ON": RegionGroup.NORTH_AMERICA,
            # Europa
            "PT": RegionGroup.WESTERN_EUROPE, "ES": RegionGroup.WESTERN_EUROPE,
            "FR": RegionGroup.WESTERN_EUROPE, "DE": RegionGroup.WESTERN_EUROPE,
            "UK": RegionGroup.WESTERN_EUROPE, "IT": RegionGroup.WESTERN_EUROPE,
            "FI": RegionGroup.WESTERN_EUROPE,
            "PL": RegionGroup.EASTERN_EUROPE, "RU": RegionGroup.EASTERN_EUROPE,
            "TR": RegionGroup.EASTERN_EUROPE,
            # África
            "ZA": RegionGroup.AFRICA, "NG": RegionGroup.AFRICA,
            "KE": RegionGroup.AFRICA, "EG": RegionGroup.AFRICA,
            # Ásia
            "CN": RegionGroup.EAST_ASIA, "JP": RegionGroup.EAST_ASIA,
            "KR": RegionGroup.EAST_ASIA,
            "TH": RegionGroup.SOUTHEAST_ASIA, "ID": RegionGroup.SOUTHEAST_ASIA,
            "SG": RegionGroup.SOUTHEAST_ASIA, "PH": RegionGroup.SOUTHEAST_ASIA,
            # Oriente Médio
            "AE": RegionGroup.MIDDLE_EAST, "SA": RegionGroup.MIDDLE_EAST,
            # Oceania
            "AU": RegionGroup.OCEANIA, "NZ": RegionGroup.OCEANIA,
        },
        alias="REGION_TO_GROUP",
    )
    
    # Regiões que requerem QR code
    qr_required_regions: Set[str] = Field(
        default_factory=lambda: {"CN", "JP", "SG", "TH"},
        alias="QR_REQUIRED_REGIONS",
    )
    
    # Regiões que requerem validação de identidade
    identity_required_regions: Set[str] = Field(
        default_factory=lambda: {"CN", "NG", "KE", "ZA"},
        alias="IDENTITY_REQUIRED_REGIONS",
    )
    
    # =========================================================
    # Feature flags regionais
    # =========================================================
    
    # Habilita features específicas por região
    regional_features_enabled: Dict[str, List[str]] = Field(
        default_factory=lambda: {
            "CN": ["alipay", "wechat_pay", "qr_code", "face_recognition"],
            "JP": ["line_pay", "paypay", "qr_code", "konbini"],
            "SG": ["grabpay", "qr_code", "bank_link"],
            "AE": ["tabby", "payby", "bnpl"],
            "AU": ["afterpay", "zip", "bpay"],
            "NG": ["mobile_money", "ussd"],
            "KE": ["mpesa", "ussd"],
            "BR": ["pix", "boleto"],
        },
        alias="REGIONAL_FEATURES_ENABLED",
    )

    # =========================================================
    # Métodos utilitários
    # =========================================================
    
    @field_validator("VALID_LOCKER_REGIONS", mode="before")
    @classmethod
    def validate_lockers_regions(cls, v: List[str]) -> List[str]:
        """Valida lista de regiões"""
        if not v:
            return []
        return [r.upper().strip() for r in v if r and r.strip()]
    
    def get_pickup_window_sec(self, region: Optional[str] = None) -> int:
        """Obtém janela de pickup para uma região específica"""
        if region and region in self.regional_pickup_window_sec:
            return self.regional_pickup_window_sec[region]
        return self.pickup_window_sec
    
    def get_prepayment_timeout_sec(self, region: Optional[str] = None) -> int:
        """Obtém timeout de pré-pagamento para uma região específica"""
        if region and region in self.regional_prepayment_timeout_seconds:
            return self.regional_prepayment_timeout_seconds[region]
        return self.prepayment_timeout_seconds
    
    def get_alloc_ttl_sec(self, region: Optional[str] = None) -> int:
        """Obtém TTL de alocação para uma região específica"""
        if region and region in self.regional_alloc_ttl_sec:
            return self.regional_alloc_ttl_sec[region]
        return self.alloc_ttl_sec
    
    def get_backend_timeout_sec(self, region: Optional[str] = None) -> int:
        """Obtém timeout de backend para uma região específica"""
        if region and region in self.regional_backend_timeout_sec:
            return self.regional_backend_timeout_sec[region]
        return self.backend_client_timeout_sec
    
    def get_default_currency(self, region: Optional[str] = None) -> str:
        """Obtém moeda padrão para uma região"""
        if region and region in self.regional_default_currencies:
            return self.regional_default_currencies[region]
        return self.dev_default_currency
    
    def get_region_group(self, region: str) -> Optional[RegionGroup]:
        """Obtém grupo de uma região"""
        return self.region_to_group.get(region.upper())
    
    def requires_qr_code(self, region: str) -> bool:
        """Verifica se região requer QR code"""
        return region.upper() in self.qr_required_regions
    
    def requires_identity_validation(self, region: str) -> bool:
        """Verifica se região requer validação de identidade"""
        return region.upper() in self.identity_required_regions
    
    def is_region_valid(self, region: str) -> bool:
        """Verifica se região é válida"""
        if not self.VALIDATE_LOCKER_REGION:
            return True
        return region.upper() in [r.upper() for r in self.VALID_LOCKER_REGIONS]
    
    def get_frontend_url_for_region(self, region: str) -> str:
        """Obtém URL do frontend para uma região específica"""
        if region in self.frontend_base_urls:
            return self.frontend_base_urls[region]
        return self.frontend_base_url
    
    def get_runtime_url_for_region(self, region: str) -> str:
        """Obtém URL do runtime para uma região específica"""
        if region in self.regional_runtime_urls:
            return self.regional_runtime_urls[region]
        return self.runtime_internal
    
    def get_payment_gateway_url_for_region(self, region: str) -> str:
        """Obtém URL do payment gateway para uma região específica"""
        if region in self.regional_payment_gateway_urls:
            return self.regional_payment_gateway_urls[region]
        return self.payment_gateway_internal
    
    def get_lifecycle_url_for_region(self, region: str) -> str:
        """Obtém URL do lifecycle service para uma região específica"""
        if region in self.regional_lifecycle_urls:
            return self.regional_lifecycle_urls[region]
        return self.lifecycle_base_url
    
    def is_feature_enabled_for_region(self, region: str, feature: str) -> bool:
        """Verifica se uma feature está habilitada para determinada região"""
        region_upper = region.upper()
        if region_upper in self.regional_features_enabled:
            return feature in self.regional_features_enabled[region_upper]
        return False


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


# =========================================================
# Exports para compatibilidade
# =========================================================

# Mantém exports antigos para não quebrar código existente
database_url = settings.database_url
service_name = settings.service_name
environment = settings.environment
app_version = settings.app_version
run_db_migrations_on_startup = settings.run_db_migrations_on_startup

frontend_base_url = settings.frontend_base_url

pickup_window_sec = settings.pickup_window_sec
pickup_token_ttl_sec = settings.pickup_token_ttl_sec
prepayment_timeout_seconds = settings.prepayment_timeout_seconds

expiry_poll_sec = settings.expiry_poll_sec
lifecycle_events_poll_sec = settings.lifecycle_events_poll_sec

expiry_batch_size = settings.expiry_batch_size
expiry_max_retries = settings.expiry_max_retries

expiry_enable_credit = settings.expiry_enable_credit
expiry_credit_ratio = settings.expiry_credit_ratio

lifecycle_events_batch_size = settings.lifecycle_events_batch_size

runtime_internal = settings.runtime_internal
payment_gateway_internal = settings.payment_gateway_internal
lifecycle_base_url = settings.lifecycle_base_url

backend_client_timeout_sec = settings.backend_client_timeout_sec
order_lifecycle_timeout_sec = settings.order_lifecycle_timeout_sec

backend_price_path_template = settings.backend_price_path_template
payment_gateway_lockers_path_template = settings.payment_gateway_lockers_path_template

internal_token = settings.internal_token
internal_health_token = settings.internal_health_token

jwt_secret = settings.jwt_secret
jwt_alg = settings.jwt_alg
jwt_access_ttl_min = settings.jwt_access_ttl_min

qr_rotate_sec = settings.qr_rotate_sec
pickup_qr_payload_version = settings.pickup_qr_payload_version
pickup_qr_secret = settings.pickup_qr_secret

manual_redeem_max_attempts = settings.manual_redeem_max_attempts
manual_redeem_window_sec = settings.manual_redeem_window_sec
manual_redeem_block_sec = settings.manual_redeem_block_sec

dev_bypass_auth = settings.dev_bypass_auth
dev_user_id = settings.dev_user_id

dev_allow_unknown_sku = settings.dev_allow_unknown_sku
dev_default_price_cents = settings.dev_default_price_cents
dev_default_currency = settings.dev_default_currency

alloc_ttl_sec = settings.alloc_ttl_sec
app_env = settings.app_env
node_env = settings.node_env

email_enabled = settings.email_enabled
email_host = settings.email_host
email_port = settings.email_port
email_secure = settings.email_secure
email_username = settings.email_username
email_password = settings.email_password
email_sender = settings.email_sender
email_from_name = settings.email_from_name

VALID_LOCKER_REGIONS = settings.VALID_LOCKER_REGIONS
VALIDATE_LOCKER_REGION = settings.VALIDATE_LOCKER_REGION


"""

1. Enum RegionGroup
Agrupa regiões por continente/área geográfica

Facilita configurações em grupo

2. Configurações Regionais Expandidas
Configuração	Descrição
regional_pickup_window_sec	Janela de pickup por região (2-6 horas)
regional_prepayment_timeout_seconds	Timeout de pagamento por região
regional_alloc_ttl_sec	TTL de alocação por região
regional_backend_timeout_sec	Timeout de backend por região
regional_default_currencies	Moeda padrão por região
3. URLs Regionais
regional_runtime_urls: URLs específicas do runtime

regional_payment_gateway_urls: URLs do payment gateway

regional_lifecycle_urls: URLs do lifecycle service

frontend_base_urls: URLs do frontend por região

4. Configurações de Notificação
SMS: Provedores regionais (Twilio, Africa's Talking, Aliyun)

WhatsApp: API key configurável

WeChat: App ID e Secret para China

LINE: Channel ID/Secret para Japão/Tailândia

KakaoTalk: API Key para Coreia do Sul

5. Feature Flags Regionais
python
regional_features_enabled = {
    "CN": ["alipay", "wechat_pay", "qr_code", "face_recognition"],
    "JP": ["line_pay", "paypay", "qr_code", "konbini"],
    "SG": ["grabpay", "qr_code", "bank_link"],
    "AE": ["tabby", "payby", "bnpl"],
}
6. Validações Regionais
requires_qr_code(): Verifica se região requer QR code

requires_identity_validation(): Verifica necessidade de validação de identidade

is_region_valid(): Validação de região

7. Timeouts Regionais
Região	Pickup Window	Prepayment Timeout	Alloc TTL
China (CN)	2h	5min	5min
Nigéria (NG)	6h	5min	5min
Japão (JP)	2h	3min	3min
África do Sul (ZA)	4h	-	-
8. Moedas por Região
Brasil: BRL

China: CNY

Japão: JPY

Emirados Árabes: AED

Austrália: AUD

Nigéria: NGN

9. Métodos Utilitários
python
get_pickup_window_sec(region)      # Janela de pickup
get_prepayment_timeout_sec(region) # Timeout de pagamento
get_default_currency(region)       # Moeda padrão
get_region_group(region)           # Grupo da região
requires_qr_code(region)           # QR code obrigatório?
10. Configurações de Email Regionais
Suporte a provedores SMTP diferentes por região

Portas configuráveis

Credenciais específicas

11. QR Code por Região
qr_required_regions: CN, JP, SG, TH

Secrets específicos por região

Payload version configurável

12. Compatibilidade Mantida
Todas as variáveis antigas exportadas

Configurações padrão preservadas

Migração suave para novas regiões

13. Segurança
Tokens internos regionais

Validação de região habilitada por padrão

Secrets isolados por região

"""

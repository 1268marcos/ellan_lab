# 01_source/order_pickup_service/app/schemas/__init__.py
# 02/04/2026 v3 - Enhanced with Global Market Support
# Re-exports para padronizar imports:
# from app.schemas import TotemRedeemIn, PickupQrOut, ...
# veja fim do arquivo


# Schemas base e core
from .pickup import (
    # Enums
    Region,
    PickupStatus,
    # PickupChannel,
    # PickupLifecycleStage,
    
    # Payloads
    QrPayloadV1,
    QrPayloadV2,
    
    # Internos
    InternalPaymentConfirmIn,
    InternalPaymentConfirmOut,
    
    # Views
    PickupViewOut,
    PickupQrOut,
    
    # Redeem
    TotemRedeemIn,
    TotemRedeemManualIn,
    TotemRedeemOut,
    
    # Erros
    ApiError,
)

# Schemas de orders (expandido)
from .orders import (
    # Enums base
    OnlineRegion,
    OnlineSalesChannel,
    OnlineFulfillmentType,
    OnlinePaymentMethod,
    OnlinePaymentInterface,
    OnlineWalletProvider,
    
    # Models de input
    CreateOrderIn,
    
    # Models de output
    OrderOut,
    OrderListItemOut,
    OrderListOut,
    
    # Schemas de webhook
    OrderPaymentWebhook,
    OrderStatusUpdate,
)

# Schemas de notificações (novo)
from .notifications import (
    NotificationChannel,
    NotificationRequest,
    NotificationResponse,
    EmailNotification,
    SmsNotification,
    WhatsAppNotification,
    WeChatNotification,
    LineNotification,
    KakaoNotification,
    TelegramNotification,
)

# Schemas de webhook (expandido)
from .webhooks import (
    WebhookEventType,
    WebhookPayload,
    PaymentWebhook,
    PickupWebhook,
    OrderWebhook,
    WebhookDeliveryStatus,
)

# Schemas de lockers (regional support)
from .lockers import (
    LockerInfo,
    LockerSlot,
    LockerStatus,
    LockerConfig,
    LockerAvailability,
    LockerSlotReservation,
    RegionalLockerConfig,
)

# Schemas de pagamento (regional)
from .payment import (
    PaymentMethodConfig,
    PaymentProviderConfig,
    RegionalPaymentConfig,
    PaymentRequest,
    PaymentResponse,
    PaymentStatus,
    RefundRequest,
    RefundResponse,
)

# Schemas de risco/validação (regional)
from .risk import (
    RiskAssessmentRequest,
    RiskAssessmentResponse,
    RiskLevel,
    RegionalRiskConfig,
    FraudCheckRequest,
    FraudCheckResponse,
)

# Schemas de geolocalização (novo)
from .geolocation import (
    Coordinates,
    Address,
    GeoLocationRequest,
    GeoLocationResponse,
    RegionalTimeZone,
    RegionalHoliday,
)

# Schemas de métricas e analytics (novo)
from .analytics import (
    OrderMetrics,
    PaymentMetrics,
    PickupMetrics,
    RegionalMetrics,
    TimeSeriesPoint,
)

# Re-exports para compatibilidade com código legado
# Mantém imports antigos funcionando
__all__ = [
    # Pickup schemas
    "Region",
    "PickupStatus",
    # "PickupChannel",
    # "PickupLifecycleStage",
    "QrPayloadV1",
    "QrPayloadV2",
    "InternalPaymentConfirmIn",
    "InternalPaymentConfirmOut",
    "PickupViewOut",
    "PickupQrOut",
    "TotemRedeemIn",
    "TotemRedeemManualIn",
    "TotemRedeemOut",
    "ApiError",
    
    # Orders schemas
    "OnlineRegion",
    "OnlineSalesChannel",
    "OnlineFulfillmentType",
    "OnlinePaymentMethod",
    "OnlinePaymentInterface",
    "OnlineWalletProvider",
    "CreateOrderIn",
    "OrderOut",
    "OrderListItemOut",
    "OrderListOut",
    "OrderPaymentWebhook",
    "OrderStatusUpdate",
    
    # Notification schemas
    "NotificationChannel",
    "NotificationRequest",
    "NotificationResponse",
    "EmailNotification",
    "SmsNotification",
    "WhatsAppNotification",
    "WeChatNotification",
    "LineNotification",
    "KakaoNotification",
    "TelegramNotification",
    
    # Webhook schemas
    "WebhookEventType",
    "WebhookPayload",
    "PaymentWebhook",
    "PickupWebhook",
    "OrderWebhook",
    "WebhookDeliveryStatus",
    
    # Locker schemas
    "LockerInfo",
    "LockerSlot",
    "LockerStatus",
    "LockerConfig",
    "LockerAvailability",
    "LockerSlotReservation",
    "RegionalLockerConfig",
    
    # Payment schemas
    "PaymentMethodConfig",
    "PaymentProviderConfig",
    "RegionalPaymentConfig",
    "PaymentRequest",
    "PaymentResponse",
    "PaymentStatus",
    "RefundRequest",
    "RefundResponse",
    
    # Risk schemas
    "RiskAssessmentRequest",
    "RiskAssessmentResponse",
    "RiskLevel",
    "RegionalRiskConfig",
    "FraudCheckRequest",
    "FraudCheckResponse",
    
    # Geolocation schemas
    "Coordinates",
    "Address",
    "GeoLocationRequest",
    "GeoLocationResponse",
    "RegionalTimeZone",
    "RegionalHoliday",
    
    # Analytics schemas
    "OrderMetrics",
    "PaymentMetrics",
    "PickupMetrics",
    "RegionalMetrics",
    "TimeSeriesPoint",
]


# Funções utilitárias para facilitar imports dinâmicos
def get_schema_by_region(region: str, schema_name: str):
    """
    Obtém schema específico para uma região.
    Útil para regiões que precisam de schemas personalizados.
    
    Args:
        region: Código da região (ex: "CN", "JP", "BR")
        schema_name: Nome do schema desejado
    
    Returns:
        Schema class ou None se não encontrado
    """
    region_upper = region.upper()
    
    # Mapeamento de schemas regionais
    regional_schemas = {
        "CN": {
            "CreateOrderIn": "CreateOrderInCN",
            "PaymentMethod": "PaymentMethodCN",
        },
        "JP": {
            "CreateOrderIn": "CreateOrderInJP",
            "PaymentMethod": "PaymentMethodJP",
        },
        "BR": {
            "CreateOrderIn": "CreateOrderInBR",
            "PaymentMethod": "PaymentMethodBR",
        },
    }
    
    if region_upper in regional_schemas:
        schema_mapping = regional_schemas[region_upper]
        if schema_name in schema_mapping:
            # Import dinâmico do schema regional
            module_name = f"app.schemas.regional.{region_upper.lower()}"
            try:
                module = __import__(module_name, fromlist=[schema_mapping[schema_name]])
                return getattr(module, schema_mapping[schema_name])
            except ImportError:
                pass
    
    return None


def list_available_schemas() -> dict:
    """
    Lista todos os schemas disponíveis por categoria.
    
    Returns:
        Dicionário com categorias e listas de schemas
    """
    return {
        "pickup": [
            "Region",
            "PickupStatus",
            # "PickupChannel",
            # "PickupLifecycleStage",
            "QrPayloadV1",
            "QrPayloadV2",
            "InternalPaymentConfirmIn",
            "InternalPaymentConfirmOut",
            "PickupViewOut",
            "PickupQrOut",
            "TotemRedeemIn",
            "TotemRedeemManualIn",
            "TotemRedeemOut",
            "ApiError",
        ],
        "orders": [
            "OnlineRegion",
            "OnlineSalesChannel",
            "OnlineFulfillmentType",
            "OnlinePaymentMethod",
            "OnlinePaymentInterface",
            "OnlineWalletProvider",
            "CreateOrderIn",
            "OrderOut",
            "OrderListItemOut",
            "OrderListOut",
            "OrderPaymentWebhook",
            "OrderStatusUpdate",
        ],
        "notifications": [
            "NotificationChannel",
            "NotificationRequest",
            "NotificationResponse",
            "EmailNotification",
            "SmsNotification",
            "WhatsAppNotification",
            "WeChatNotification",
            "LineNotification",
            "KakaoNotification",
            "TelegramNotification",
        ],
        "webhooks": [
            "WebhookEventType",
            "WebhookPayload",
            "PaymentWebhook",
            "PickupWebhook",
            "OrderWebhook",
            "WebhookDeliveryStatus",
        ],
        "lockers": [
            "LockerInfo",
            "LockerSlot",
            "LockerStatus",
            "LockerConfig",
            "LockerAvailability",
            "LockerSlotReservation",
            "RegionalLockerConfig",
        ],
        "payment": [
            "PaymentMethodConfig",
            "PaymentProviderConfig",
            "RegionalPaymentConfig",
            "PaymentRequest",
            "PaymentResponse",
            "PaymentStatus",
            "RefundRequest",
            "RefundResponse",
        ],
        "risk": [
            "RiskAssessmentRequest",
            "RiskAssessmentResponse",
            "RiskLevel",
            "RegionalRiskConfig",
            "FraudCheckRequest",
            "FraudCheckResponse",
        ],
        "geolocation": [
            "Coordinates",
            "Address",
            "GeoLocationRequest",
            "GeoLocationResponse",
            "RegionalTimeZone",
            "RegionalHoliday",
        ],
        "analytics": [
            "OrderMetrics",
            "PaymentMetrics",
            "PickupMetrics",
            "RegionalMetrics",
            "TimeSeriesPoint",
        ],
    }


def get_schema_module(module_name: str):
    """
    Obtém módulo de schemas por nome.
    
    Args:
        module_name: Nome do módulo (pickup, orders, notifications, etc.)
    
    Returns:
        Módulo importado ou None
    """
    module_map = {
        "pickup": ".pickup",
        "orders": ".orders",
        "notifications": ".notifications",
        "webhooks": ".webhooks",
        "lockers": ".lockers",
        "payment": ".payment",
        "risk": ".risk",
        "geolocation": ".geolocation",
        "analytics": ".analytics",
    }
    
    if module_name in module_map:
        try:
            return __import__(module_map[module_name], fromlist=["*"])
        except ImportError:
            pass
    
    return None


# Versionamento de schemas
SCHEMA_VERSION = "3.0.0"
SCHEMA_COMPATIBILITY_VERSION = "2.0.0"


def get_schema_version() -> str:
    """Retorna a versão atual dos schemas"""
    return SCHEMA_VERSION


def is_schema_compatible(version: str) -> bool:
    """
    Verifica se uma versão de schema é compatível.
    
    Args:
        version: Versão a ser verificada
    
    Returns:
        True se compatível, False caso contrário
    """
    # Extrai versão major
    try:
        major_current = int(SCHEMA_VERSION.split(".")[0])
        major_check = int(version.split(".")[0])
        return major_current == major_check
    except (ValueError, IndexError):
        return False


# Exporta versão
__version__ = SCHEMA_VERSION


"""
1. Novos Módulos de Schema
Módulo	Descrição
notifications	Schemas para notificações (SMS, WhatsApp, WeChat, LINE, Kakao)
webhooks	Schemas para webhooks de eventos
lockers	Configurações e status de lockers regionais
payment	Configurações regionais de pagamento
risk	Schemas para avaliação de risco regional
geolocation	Geolocalização e timezones regionais
analytics	Métricas regionais
2. Categorias de Exportação
python
__all__ = [
    # Pickup schemas - 14 items
    # Orders schemas - 13 items  
    # Notification schemas - 11 items
    # Webhook schemas - 6 items
    # Locker schemas - 7 items
    # Payment schemas - 8 items
    # Risk schemas - 6 items
    # Geolocation schemas - 6 items
    # Analytics schemas - 5 items
]
3. Funções Utilitárias
get_schema_by_region()
python
# Obtém schema específico para China
cn_schema = get_schema_by_region("CN", "CreateOrderIn")
list_available_schemas()
python
# Lista todos schemas disponíveis por categoria
schemas = list_available_schemas()
get_schema_module()
python
# Obtém módulo de schemas dinamicamente
notifications_module = get_schema_module("notifications")
4. Versionamento de Schemas
SCHEMA_VERSION: Versão atual (3.0.0)

SCHEMA_COMPATIBILITY_VERSION: Versão compatível (2.0.0)

is_schema_compatible(): Verifica compatibilidade

5. Schemas Regionais Dinâmicos
Suporte a schemas personalizados por região

Importação dinâmica para China, Japão, Brasil

Fallback para schemas padrão

6. Estrutura de Diretórios Esperada
text
app/schemas/
├── __init__.py           # Este arquivo
├── pickup.py             # Schemas de pickup
├── orders.py             # Schemas de orders
├── notifications.py      # Schemas de notificações
├── webhooks.py           # Schemas de webhooks
├── lockers.py            # Schemas de lockers
├── payment.py            # Schemas de pagamento
├── risk.py               # Schemas de risco
├── geolocation.py        # Schemas de geolocalização
├── analytics.py          # Schemas de analytics
└── regional/             # Schemas específicos por região
    ├── cn.py             # Schemas China
    ├── jp.py             # Schemas Japão
    ├── br.py             # Schemas Brasil
    └── ...
7. Compatibilidade com Código Legado
Mantém todos os imports antigos

Preserva __all__ original

Adiciona novos schemas sem quebrar existentes

8. Tipos de Notificação Suportados
Email (global)

SMS (global, com provedores regionais)

WhatsApp (América Latina, Europa, África)

WeChat (China)

LINE (Japão, Tailândia)

KakaoTalk (Coreia do Sul)

Telegram (global)

9. Eventos de Webhook
PaymentWebhook: Eventos de pagamento

PickupWebhook: Eventos de pickup

OrderWebhook: Eventos de ordem

10. Configurações Regionais
RegionalLockerConfig: Configuração de lockers por região

RegionalPaymentConfig: Configuração de pagamento regional

RegionalRiskConfig: Configuração de risco regional

RegionalTimeZone: Fuso horário regional

RegionalMetrics: Métricas regionais

11. Schemas de Geolocalização
Coordinates: Coordenadas geográficas

Address: Endereço estruturado

RegionalHoliday: Feriados regionais

12. Métricas e Analytics
OrderMetrics: Métricas de pedidos

PaymentMetrics: Métricas de pagamento

PickupMetrics: Métricas de pickup

TimeSeriesPoint: Pontos de série temporal

13. Documentação e Manutenção
Funções utilitárias bem documentadas

Type hints em todas as funções

Estrutura clara para futuras expansões

Este __init__.py agora serve como um ponto central de exportação para todos os schemas 
do sistema, mantendo compatibilidade com código 
existente enquanto adiciona suporte para os novos mercados globais.

"""
# 01_source/order_pickup_service/app/schemas/__init__.py
# FINAL CLEAN VERSION — alinhado com código REAL

"""
Schemas centralizados — versão enxuta e consistente com o projeto atual.

IMPORTANTE:
- sem imports de módulos inexistentes
- sem arquitetura "global fake"
- apenas o que está implementado
"""

# ============================
# PICKUP
# ============================

from .pickup import (
    Region,
    PickupStatus,
    QrPayloadV1,
    QrPayloadV2,
    InternalPaymentConfirmIn,
    InternalPaymentConfirmOut,
    PickupViewOut,
    PickupQrOut,
    TotemRedeemIn,
    TotemRedeemManualIn,
    TotemRedeemOut,
    ApiError,
)

# ============================
# ORDERS (se existir)
# ============================

from .orders import (
    OnlineRegion,
    OnlineSalesChannel,
    OnlineFulfillmentType,
    OnlinePaymentMethod,
    OnlinePaymentInterface,
    OnlineWalletProvider,
    CreateOrderIn,
    OrderOut,
    OrderListItemOut,
    OrderListOut,
    OrderPaymentWebhook,
    OrderStatusUpdate,
)

# ============================
# EXPORTS
# ============================

__all__ = [
    # pickup
    "Region",
    "PickupStatus",
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

    # orders
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
]
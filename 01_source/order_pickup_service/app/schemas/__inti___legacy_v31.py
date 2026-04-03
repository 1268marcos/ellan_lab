# 01_source/order_pickup_service/app/schemas/__init__.py
# Re-exports para padronizar imports:
# from app.schemas import TotemRedeemIn, PickupQrOut, ...

from .pickup import (
    Region,
    PickupStatus,
    QrPayloadV1,
    InternalPaymentConfirmIn,
    InternalPaymentConfirmOut,
    PickupViewOut,
    PickupQrOut,
    TotemRedeemIn,
    TotemRedeemManualIn,
    TotemRedeemOut,
    ApiError,
)
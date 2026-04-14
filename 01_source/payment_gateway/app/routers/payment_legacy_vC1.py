# 01_source/payment_gateway/app/routers/payment.py

from fastapi import APIRouter, HTTPException, Header, Depends, status
from typing import Optional
from datetime import datetime
from app.schemas.payment import CancelPaymentRequest
from app.services.risk_events_service import RiskEventsService
from app.integrations.payments.mercadopago.sp import build_provider as build_mercadopago
from app.integrations.payments.stripe.pt import build_provider as build_stripe_pt
from app.integrations.payments.stripe.sp import build_provider as build_stripe_sp
from app.integrations.payments.base.contracts import CancelPaymentCommand
from app.core.event_log import GatewayEventLogger
from app.core.config import settings

router = APIRouter(tags=["Payment"])


def get_logger():
    """Lazy initialization of logger to avoid startup errors"""
    try:
        log_dir = getattr(settings, 'GATEWAY_LOG_DIR', '/logs')
        log_hash_salt = getattr(settings, 'LOG_HASH_SALT', None)
        
        if not log_hash_salt:
            print("Warning: LOG_HASH_SALT not configured, logger disabled")
            return None
        
        return GatewayEventLogger(
            gateway_id=getattr(settings, 'GATEWAY_ID', 'payment_gateway'),
            log_dir=log_dir,
            log_hash_salt=log_hash_salt
        )
    except Exception as e:
        print(f"Warning: Failed to initialize logger: {str(e)}")
        return None

# GERANDO ERRO POR ISSO COMENTADA
# CORREÇÃO 1: Adicionado response_model=None
# CORREÇÃO 2: Dependência injetada corretamente com Depends()
# @router.post(
#     "/gateway/pagamento/{order_id}/cancel",
#     status_code=status.HTTP_200_OK,
#     summary="Cancelar pagamento",
#     response_model=None,  # <--- CRUCIAL: Desabilita a geração automática do modelo de resposta
# )
# async def cancel_payment(
#     order_id: str,
#     body: CancelPaymentRequest,
#     idempotency_key: str = Header(..., alias="Idempotency-Key"),
#     risk_events_service: RiskEventsService = Depends(),  # <--- CORRETO: Sem argumento
# ):
#     # 1. Buscar evento do pagamento original
#     event = await risk_events_service.get_event_by_order_id(order_id)
# 
#     if not event:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"Payment not found for order_id: {order_id}"
#         )
# 
#     # 2. Validar se pode ser cancelado
#     if event.decision not in ("APPROVED",):
#         raise HTTPException(
#             status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
#             detail=f"Payment cannot be cancelled in current status: {event.decision}"
#         )
# 
#     # 3. Selecionar provider
#     try:
#         if event.provider == "mercadopago":
#             provider = build_mercadopago(access_token=settings.MERCADOPAGO_ACCESS_TOKEN)
#         elif event.provider == "stripe" and event.region == "PT":
#             provider = build_stripe_pt(secret_key=settings.STRIPE_SECRET_KEY_PT)
#         elif event.provider == "stripe" and event.region == "SP":
#             provider = build_stripe_sp(secret_key=settings.STRIPE_SECRET_KEY_SP)
#         else:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail=f"Unsupported provider/region: {event.provider}/{event.region}"
#             )
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to initialize payment provider: {str(e)}"
#         )
# 
#    # 4. Executar cancelamento
#     cancel_command = CancelPaymentCommand(
#         provider_payment_id=event.provider_payment_id,
#         reason=body.reason,
#         amount=body.amount
#     )
#     
#     refund_result = await provider.cancel_payment(cancel_command)
# 
#     if not refund_result.success:
#         raise HTTPException(
#             status_code=status.HTTP_502_BAD_GATEWAY,
#             detail=f"Provider refund failed: {refund_result.error}"
#         )
# 
#     # 5. Registrar no log
#     logger = get_logger()
#     if logger:
#         try:
#             logger.append_event(
#                 event={
#                     "event_type": "GATEWAY_PAYMENT_CANCELLED",
#                     "request_id": order_id,
#                     "region": getattr(event, 'region', None),
#                     "payload": {
#                         "order_id": order_id,
#                         "provider": event.provider,
#                         "provider_payment_id": event.provider_payment_id,
#                         "provider_refund_id": refund_result.refund_id,
#                         "reason": body.reason,
#                         "requested_by": body.requested_by,
#                         "amount": body.amount,
#                         "idempotency_key": idempotency_key,
#                     },
#                 }
#             )
#         except Exception as e:
#             print(f"Warning: Failed to log cancellation event: {str(e)}")
# 
#     return {
#         "order_id": order_id,
#         "cancelled": True,
#         "provider": event.provider,
#         "provider_refund_id": refund_result.refund_id,
#         "refund_status": refund_result.status,
#         "processed_at": refund_result.processed_at or datetime.utcnow(),
#         "reason": body.reason,
#         "requested_by": body.requested_by
#     }
# 01_source/payment_gateway/app/routers/payment.py
from fastapi import APIRouter, Header, Request

from app.models.payment_model import PaymentRequest
from app.models.gateway_response_model import GatewayPaymentResponse
from app.services.payment_service import process_payment

router = APIRouter(tags=["payment"])


@router.post("/gateway/pagamento", response_model=GatewayPaymentResponse)
async def pagamento(
    data: PaymentRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    device_fp: str = Header(..., alias="X-Device-Fingerprint"),
    request_id: str | None = Header(default=None, alias="X-Request-ID"),
):
    """
    Endpoint principal de criação/processamento de pagamento.

    Headers obrigatórios:
    - Idempotency-Key
    - X-Device-Fingerprint

    Header opcional:
    - X-Request-ID
    """
    return process_payment(
        data=data,
        request=request,
        idempotency_key=idempotency_key,
        device_fp=device_fp,
        request_id=request_id,
    )
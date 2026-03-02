from fastapi import APIRouter, Header, Request
from app.models.payment_model import PaymentRequest
from app.models.gateway_response_model import GatewayPaymentResponse
from app.services.payment_service import process_payment

router = APIRouter()

# uso do async - router async (evita gargalo futuro)

@router.post("/gateway/pagamento", response_model=GatewayPaymentResponse)
async def pagamento(
    data: PaymentRequest,
    request: Request,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    device_fp: str = Header(..., alias="X-Device-Fingerprint"),
    request_id: str | None = Header(None, alias="X-Request-ID"),
):
    return process_payment(data, request, idempotency_key, device_fp, request_id)
# HANDOFF — ELLAN Lab Locker

Este documento é o “ponto de retomada” rápido do projeto.  
Objetivo: permitir continuar o trabalho em outro chat/PC sem reabrir toda a história.

---

## 1) Arquitetura (Docker Compose)

Serviços principais e portas (fachada -> interno):

- **payment_gateway**: `8000 -> 8000`
- **backend_sp**: `8201 -> 8000`
- **backend_pt**: `8202 -> 8000`
- **order_pickup_service**: `8003 -> 8003`
- **mqtt_broker**: `1884 -> 1883`
- **redis_central**: `6382 -> 6379`
- **postgres_central**: `5435 -> 5432`

Convenção: **PORT interno = 8000** sempre que possível; portas externas são somente “fachada”.

Rede: `locker_network` (bridge).

---

## 2) Endpoints — Backends SP/PT (Locker)

Base:
- SP: `http://localhost:8201`
- PT: `http://localhost:8202`

Endpoints necessários (mínimo):
- `POST /locker/allocate` → retorna `allocation_id` e `slot`
- `POST /locker/allocations/{allocation_id}/commit`
- `POST /locker/allocations/{allocation_id}/release`
- `GET /locker/slots`
- `POST /locker/slots/{slot}/open`
- `POST /locker/slots/{slot}/light/on`
- `POST /locker/slots/{slot}/set-state`

Estados principais no backend (door_state):
- `AVAILABLE`
- `RESERVED`
- `PAID_PENDING_PICKUP`
- `PICKED_UP`
- `OUT_OF_STOCK`

---

## 3) Frontend (Vite) — Proxy para evitar CORS

Usar proxy do Vite para evitar CORS e não hardcode de portas no React:

- Gateway: `/api/gw/*` → `http://localhost:8000/*`
- Backend SP: `/api/sp/*` → `http://localhost:8201/*`
- Backend PT: `/api/pt/*` → `http://localhost:8202/*`

O frontend deve chamar sempre `fetch("/api/...")` e nunca `http://localhost:820X` diretamente.

---

## 4) Fluxo ONLINE (Order + Pickup)

### 4.1 Criar pedido (ONLINE)
- Cria Order + Allocation (reserva curta pode expirar; no payment-confirm há fallback com realocação)

### 4.2 Confirmar pagamento (INTERNAL)
Endpoint:
- `POST /internal/orders/{order_id}/payment-confirm` (header `X-Internal-Token`)

Efeitos ONLINE:
- `Order: PAYMENT_PENDING -> PAID_PENDING_PICKUP`
- `pickup_deadline_at = now + 2h`
- tenta `locker_commit(allocation_id, locked_until=deadline)`
  - se **409**, realoca e comita de novo
- `locker_set_state(slot, PAID_PENDING_PICKUP)`
- cria `PickupToken` (ponteiro) + `manual_code` (6 dígitos)

Efeitos KIOSK:
- fluxo simples abre porta; também blindado contra **409** com realocação no commit

---

## 5) QR Rotativo (Opção A — ponteiro)

QR contém apenas:
```json
{ "v": 1, "pickup_id": "order_id", "token_id": "...", "ctr": 0, "exp": 1234567890, "sig": "..." }
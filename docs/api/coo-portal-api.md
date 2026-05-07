# API do portal COO (`/api/v1/coo`)

Serviço: **`order_pickup_service`** (FastAPI). Todas as rotas listadas exigem autenticação via **`require_coo_access`**.

## Autenticação

| Método | Cabeçalho |
|--------|-----------|
| API key | `X-API-Key: <raw_key>` |
| Sessão | `Authorization: Bearer <token>` (token pode ser reutilizado como key em alguns fluxos) |

**Perfis aceites:** utilizador com role **`coo`**, **`ceo`** ou **`ops`** (sessão); ou parceiro cuja API key resolva para perfil operacional (ver `app/routers/coo/deps.py`).

### Erro 403 (sem acesso)

**Request**

```http
GET /api/v1/coo/meta HTTP/1.1
Host: localhost:8002
```

**Response** `403 application/json`

```json
{
  "detail": {
    "type": "COO_ACCESS_REQUIRED",
    "message": "Acesso restrito: role coo, ceo ou ops; ou parceiro operacional (API key)."
  }
}
```

---

## Convenções

- **Base URL:** `{origin}/api/v1/coo` (ex.: `http://localhost:8002/api/v1/coo`).
- **Content-Type:** `application/json` nos POST.
- **OpenAPI:** com a app completa levantada, consultar `/docs` ou `/openapi.json` e filtrar por tag **COO Portal** / **COO Portal 5180**.

---

## GET `/meta`

Metadados do portal (router `portal.py`).

**Request**

```http
GET /api/v1/coo/meta HTTP/1.1
Host: localhost:8002
X-API-Key: <sua-chave>
```

**Response** `200`

```json
{
  "portal": "coo",
  "title": "COO Portal",
  "api_version": "1",
  "as_of": "2026-05-07T12:00:00+00:00"
}
```

---

## GET `/dashboard/consolidated`

| Query | Tipo | Default |
|-------|------|---------|
| `days` | int | `7` (limitado pelo serviço a um intervalo seguro) |

**Response** `200` — `DashboardSummary`

```json
{
  "horizon_days": 7,
  "as_of": "2026-05-07T12:00:00+00:00",
  "orders_in_window": 120,
  "active_allocations": 15,
  "pending_pickup_allocations": 8,
  "error_allocations": 1,
  "lockers_total": 40,
  "lockers_active": 38,
  "pickups_created_in_window": 45,
  "pickups_redeemed_in_window": 40,
  "pickup_completion_rate_pct": 88.89,
  "avg_pickup_cycle_min": 18.5
}
```

---

## GET `/health/pickups`

| Query | Tipo | Descrição |
|-------|------|-----------|
| `region` | string opcional | Filtro de região (ex.: `SP`) |

**Response** `200` — `OperationsHealth`

```json
{
  "region": "SP",
  "pending_pickup": 4,
  "opened_for_pickup": 2,
  "errors": 0,
  "health_score": 98.5,
  "as_of": "2026-05-07T12:00:00+00:00"
}
```

---

## GET `/deadlines/urgent`

| Query | Tipo | Default |
|-------|------|---------|
| `limit` | int | `50` |

**Response** `200` — lista de objetos (pedidos com deadline próximo e/ou pickups com `expires_at`).

```json
[
  {
    "order_id": "ord_123",
    "pickup_deadline_at": "2026-05-07T14:30:00+00:00",
    "status": "PAID_PENDING_PICKUP",
    "source": "order_deadline"
  },
  {
    "pickup_id": "pk_456",
    "order_id": "ord_789",
    "locker_id": "LK-SP-001",
    "pickup_deadline_at": "2026-05-07T14:00:00+00:00",
    "time_remaining_min": 45,
    "status": "ACTIVE",
    "source": "pickup_expires_at"
  }
]
```

---

## GET `/logistics/manifests/active`

| Query | Tipo | Descrição |
|-------|------|-----------|
| `depot_id` | string opcional | Filtra por `locker_id` |

**Response** `200` — `LogisticsManifest[]`

```json
[
  {
    "id": "mf_001",
    "logistics_partner_id": "lp_01",
    "locker_id": "LK-SP-001",
    "status": "IN_TRANSIT",
    "manifest_date": "2026-05-07",
    "expected_parcel_count": 20,
    "actual_parcel_count": 12,
    "carrier_route_code": "RTE-88"
  }
]
```

---

## GET `/logistics/routing/realtime`

| Query | Tipo |
|-------|------|
| `region` | string opcional |

**Response** `200` — `LogisticsRoutingRow[]`

```json
[
  {
    "region": "SP",
    "locker_id": "LK-SP-001",
    "active_manifests": 2,
    "in_transit": 1
  }
]
```

---

## GET `/logistics/inventory/by-depot`

| Query | Tipo |
|-------|------|
| `depot_id` | string opcional (locker) |

**Response** `200` — `DepotInventoryRow[]`

```json
[
  {
    "locker_id": "LK-SP-001",
    "region": "SP",
    "total_slots": 24,
    "reserved_hint": 6
  }
]
```

---

## GET `/suppliers/sla`

| Query | Tipo | Default |
|-------|------|---------|
| `period` | `week` \| `month` \| `quarter` | `month` |

**Response** `200` — `SLAViolations`

```json
{
  "period": "month",
  "as_of": "2026-05-07T12:00:00+00:00",
  "suppliers": [
    {
      "supplier_id": "lp_01",
      "supplier_label": "lp_01",
      "on_time_pct": 95.0,
      "breach_count": 1
    }
  ]
}
```

---

## GET `/suppliers/penalties`

| Query | Tipo |
|-------|------|
| `supplier_id` | string opcional |
| `start_date` | ISO datetime opcional |
| `end_date` | ISO datetime opcional |

**Response** `200` — lista (pode ser vazia; stub até persistência dedicada)

```json
[]
```

---

## GET `/suppliers/compliance`

| Query | Tipo | Default |
|-------|------|---------|
| `period` | string | `month` |

**Response** `200` — lista de `ComplianceReportRow`

```json
[
  {
    "supplier_id": "lp_01",
    "compliance_score": 92.5,
    "audit_notes": null
  }
]
```

---

## GET `/kpis/network/uptime`

| Query | Tipo | Default |
|-------|------|---------|
| `days` | int | `30` |

**Response** `200` — `OperationalKPIs` (campos `historical` / `breakdown` opcionais)

```json
{
  "metric_key": "network_uptime_pct",
  "value": 97.5,
  "unit": "percent",
  "window_days": 30,
  "as_of": "2026-05-07T12:00:00+00:00",
  "historical": [
    { "date": "2026-05-01", "uptime": 97.35 }
  ],
  "breakdown": null
}
```

---

## GET `/kpis/mttr`

| Query | Tipo |
|-------|------|
| `incident_type` | string opcional (filtra amostras por substring no nome da ação auditada) |

**Response** `200` — `OperationalKPIs`

```json
{
  "metric_key": "mttr_hours_sampled",
  "value": 0.42,
  "unit": "hours",
  "window_days": 30,
  "as_of": "2026-05-07T12:00:00+00:00",
  "historical": null,
  "breakdown": [
    { "action": "pickup.retry", "mttr_hours": 0.35, "samples": 12 }
  ]
}
```

---

## GET `/kpis/fleet/efficiency`

| Query | Tipo | Default |
|-------|------|---------|
| `days` | int | `30` |

**Response** `200` — `OperationalKPIs`

```json
{
  "metric_key": "fleet_efficiency_deliveries_per_vehicle_day",
  "value": 1.25,
  "unit": "count",
  "window_days": 30,
  "as_of": "2026-05-07T12:00:00+00:00",
  "historical": null,
  "breakdown": [
    {
      "vehicle": "LK-SP-001",
      "deliveries_per_day": 1.1,
      "total_deliveries": 33
    }
  ]
}
```

---

## GET `/approvals/pending`

| Query | Tipo |
|-------|------|
| `approval_type` | string opcional |

**Response** `200` — lista de envelopes com `items` (estrutura estável para o frontend)

```json
[
  {
    "approval_type": "ANY",
    "pending_count": 2,
    "items": [
      {
        "id": "APP-001",
        "approval_type": "sla_adjustment",
        "requester": "Região Sul",
        "created_at": "2026-05-07T12:00:00+00:00",
        "details": { "region": "sul", "new_sla_minutes": 45 }
      }
    ],
    "note": "…"
  }
]
```

---

## POST `/approvals/sla/adjust`

**Request** `application/json` — `ApprovalRequest`

```json
{
  "approval_type": "sla_adjustment",
  "subject": "Ajuste Sul",
  "payload": { "region": "sul", "minutes": 45 }
}
```

**Response** `200` — `ApprovalAck`

```json
{
  "status": "QUEUED",
  "approval_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Ajuste de SLA enfileirado (stub COO)."
}
```

---

## POST `/approvals/expansion`

**Request**

```json
{
  "approval_type": "expansion",
  "subject": "Norte Shopping",
  "payload": { "lockers_requested": 5 }
}
```

**Response** `200`

```json
{
  "status": "QUEUED",
  "approval_id": "660e8400-e29b-41d4-a716-446655440001",
  "message": "Expansion request enfileirado (stub COO)."
}
```

---

## GET `/widgets/summary`

**Response** `200` — `CooWidgetsSummary`

```json
{
  "sla_violated_24h": 3,
  "avg_pickup_time_min": 12.4,
  "deliveries_today": 58,
  "lockers_offline": 2,
  "cost_per_delivery": 4.12
}
```

---

## Referências

| Recurso | Path no repo |
|---------|----------------|
| Rotas 5180 | `01_source/order_pickup_service/app/routers/coo/portal_5180.py` |
| Meta | `01_source/order_pickup_service/app/routers/coo/portal.py` |
| Schemas | `01_source/order_pickup_service/app/schemas/coo/portal_5180.py` |
| Auth | `01_source/order_pickup_service/app/routers/coo/deps.py` |
| Runbook operacional | [../runbooks/coo-portal-5180.md](../runbooks/coo-portal-5180.md) |

Os exemplos JSON são ilustrativos; valores reais dependem da base de dados e da janela temporal.

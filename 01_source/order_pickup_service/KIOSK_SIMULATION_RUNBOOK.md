# KIOSK_SIMULATION_RUNBOOK.md

Data de referência: 10/03/2026  
Projeto: ELLAN Lab Locker  
Fase: FASE 3 — V — Ambiente KIOSK de simulação

---

# 1. Objetivo

Este runbook define como subir, testar e validar o fluxo KIOSK de simulação no projeto ELLAN Lab Locker, sem depender do frontend online e sem depender do hardware físico real.

O objetivo desta fase é permitir um fluxo completo e repetível de:

- criar pedido KIOSK
- aprovar pagamento KIOSK
- confirmar alocação
- acender luz da gaveta
- abrir a gaveta
- observar o comportamento do simulador
- validar os estados internos do pedido e da allocation

---

# 2. Escopo desta fase

## Incluído
- fluxo KIOSK separado do dashboard online
- `order_pickup_service` como domínio do pedido KIOSK
- `backend_sp` e `backend_pt` como backends regionais do locker
- `simulator` como simulador de hardware MQTT de 24 portas
- frontend com rotas separadas para KIOSK:
  - `/sp/kiosk`
  - `/pt/kiosk`

## Não incluído nesta fase
- catálogo com fonte única
- crédito 50%
- confirmação física real de retirada por sensor
- fechamento automático em `PICKED_UP`
- PI-CI como etapa obrigatória do fluxo
- inventário persistido no `simulator`

---

# 3. Arquitetura operacional desta fase

## Fluxo oficial
1. frontend KIOSK cria pedido em `order_pickup_service`
2. `order_pickup_service` aloca slot via backend regional
3. frontend KIOSK aprova pagamento
4. `order_pickup_service` faz commit da allocation
5. `order_pickup_service` chama:
   - light on
   - open
   - set-state `OUT_OF_STOCK`
6. backend regional publica comandos MQTT
7. `simulator` consome os comandos e simula a gaveta

## Separação de responsabilidade
- `order_pickup_service` → regra de negócio KIOSK
- `backend_sp` / `backend_pt` → fachada regional do locker
- `simulator` → simulação física da gaveta
- `frontend` → tela operacional de teste

---

# 4. Estado funcional esperado

## ONLINE
Fluxo online permanece separado e estável.

## KIOSK
Fluxo KIOSK desta fase usa a seguinte semântica:

### Pedido
- criação: `PAYMENT_PENDING`
- pagamento aprovado: `DISPENSED`

### Allocation
- criação: `RESERVED_PENDING_PAYMENT`
- após pagamento/apertura: `OPENED_FOR_PICKUP`

### Pickup
- não é criado no fluxo KIOSK desta fase

## Observação importante
Nesta fase o KIOSK **não** marca `PICKED_UP` automaticamente.  
Esse fechamento fica para fase posterior, quando existir confirmação explícita de retirada.

---

# 5. Arquivos principais da fase

## Backend de domínio KIOSK
- `01_source/order_pickup_service/app/routers/kiosk.py`
- `01_source/order_pickup_service/app/schemas/kiosk.py`
- `01_source/order_pickup_service/app/routers/internal.py`
- `01_source/order_pickup_service/app/models/order.py`
- `01_source/order_pickup_service/app/models/allocation.py`

## Cliente de integração regional
- `01_source/order_pickup_service/app/services/backend_client.py`
- `01_source/order_pickup_service/app/services/locker_client.py`

## Backend regional
- `01_source/backend_sp/app/routers/hardware.py`
- `01_source/backend_pt/app/routers/hardware.py`

## Simulador
- `01_source/simulator/app/main.py`
- `01_source/simulator/README.md`

## Frontend
- `01_source/frontend/src/App.jsx`
- `01_source/frontend/src/pages/RegionPage.jsx`

---

# 6. Pré-requisitos

Antes de testar:

- Docker Compose funcional
- `mqtt` ativo
- `backend_sp` ativo
- `backend_pt` ativo
- `order_pickup_service` ativo
- `frontend` ativo
- `simulator` ativo para a região testada

## Variáveis importantes
### `order_pickup_service`
- `BACKEND_SP_INTERNAL`
- `BACKEND_PT_INTERNAL`

### `simulator`
- `MQTT_HOST`
- `MQTT_PORT`
- `REGION`
- `LOCKER_ID`
- `FAILURE_RATE`
- `PAYMENT_TRIGGERS_OPEN=false`
- `DEBUG_LOGS=true`

---

# 7. Procedimento de subida

## 7.1 Subir a stack
Usar o procedimento normal do projeto:

```bash
docker compose up -d --build
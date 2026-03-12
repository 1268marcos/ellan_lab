📘 ELLAN — Arquitetura do Lifecycle de Pedidos

Objetivo

    Este documento descreve a arquitetura de lifecycle de pedidos da plataforma ELLAN Lab Locker, incluindo:
        - criação de pedidos
        - deadlines operacionais
        - timeout pré-pagamento
        - eventos de domínio
        - fatos analíticos
        - consumo de eventos pelos serviços operacionais

    A arquitetura foi projetada para suportar:
        - múltiplos canais (ONLINE, KIOSK)
        - múltiplas regiões (SP, PT)
        - lockers físicos
        - analytics operacionais
        - desacoplamento entre serviços

1. Visão Geral da Arquitetura
                ┌───────────────────────────┐
                │        Frontend           │
                │  (Dashboard / Kiosk UI)   │
                └─────────────┬─────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │   order_pickup_service  │
                 │                         │
                 │ cria pedidos            │
                 │ reserva slots           │
                 │ confirma pagamento      │
                 │ consome eventos         │
                 └─────────────┬───────────┘
                               │
                               │ cria deadline
                               ▼
               ┌────────────────────────────────┐
               │      order_lifecycle_service   │
               │                                │
               │ lifecycle_deadlines            │
               │ domain_events                  │
               │ analytics_facts                │
               └──────────────┬─────────────────┘
                              │
                              │ worker
                              ▼
               ┌────────────────────────────────┐
               │    order_lifecycle_worker      │
               │                                │
               │ executa deadlines              │
               │ gera eventos de domínio        │
               │ gera fatos analíticos          │
               └──────────────┬─────────────────┘
                              │
                              ▼
              ┌─────────────────────────────────┐
              │      order_pickup_service       │
              │                                 │
              │ consome order.prepayment_timeout│
              │                                 │
              │ expira pedido                   │
              │ libera allocation               │
              │ libera slot no locker           │
              └─────────────────────────────────┘

2. Serviços do Sistema

    order_pickup_service

        Responsável por:
            - criação de pedidos
            - fluxo ONLINE
            - fluxo KIOSK
            - reserva de slots
            - confirmação de pagamento
            - pickup
            - consumo de eventos de lifecycle

        Estados do Pedido
        PAYMENT_PENDING
        PAID_PENDING_PICKUP
        DISPENSED
        PICKED_UP
        EXPIRED

    order_lifecycle_service

        Serviço dedicado ao lifecycle operacional de pedidos.

        Responsável por:
        - deadlines
        - timeouts
        - eventos de domínio
        - fatos analíticos

        Tabelas principais
            lifecycle_deadlines
            domain_events
            analytics_facts

    order_lifecycle_worker

        Worker responsável por:
            - detectar deadlines vencidos
            - executar compensações
            - gerar eventos
            - gerar fatos analíticos

3. Fluxo de Timeout Pré-Pagamento
    
    Cenário

    Cliente cria pedido mas não paga dentro do prazo.

    Passo 1 — criação do pedido

        POST /orders

        Estado:

        order.status = PAYMENT_PENDING
        allocation.state = RESERVED_PENDING_PAYMENT
   
    Passo 2 — criação do deadline

        order_pickup_service cria deadline:

        POST /internal/deadlines

        Registro criado:

        deadline_type = PREPAYMENT_TIMEOUT
        status = PENDING
        due_at = created_at + timeout

    Passo 3 — worker detecta deadline

        Worker executa:

        claim_due_deadlines()

        Transição:

        PENDING → EXECUTING

    Passo 4 — execução do deadline

        deadline_engine.execute_prepayment_timeout

        Transição:

        EXECUTING → EXECUTED

    Passo 5 — criação do evento de domínio

        Evento gerado:

        order.prepayment_timed_out

        Tabela:

        domain_events

    Passo 6 — criação do fato analítico

        Tabela:

        analytics_facts

        Fact gerado:

        order_abandoned_before_payment

    Passo 7 — consumo do evento

        order_pickup_service consome o evento.

        Ações executadas:

        order.status → EXPIRED
        allocation.state → RELEASED
        locker_release()
        locker_set_state(slot, AVAILABLE)

4. Eventos de Domínio

    Eventos registrados em:

    domain_events

    Estrutura
        event_key
        aggregate_type
        aggregate_id
        event_name
        payload
        occurred_at

    Exemplo
        event_name = order.prepayment_timed_out
        aggregate_id = order_id

5. Fatos Analíticos

    Registrados em:

    analytics_facts

    Permitem construir dashboards e relatórios.

    Exemplo
        fact_name = order_abandoned_before_payment

    Payload inclui:
        order_id
        order_channel
        region
        slot
        reason
        deadline_type

6. Benefícios da Arquitetura

    Desacoplamento

        order_pickup_service não precisa gerenciar timers.

    Escalabilidade

        Deadlines são executados por worker dedicado.

    Observabilidade

    Eventos e fatos analíticos permitem medir:

        abandono de carrinho
        conversão de pagamento
        tempo médio de pickup
        utilização dos lockers
        Idempotência

    Chaves utilizadas:

        deadline_key
        event_key
        fact_key

    Garantem que operações não sejam duplicadas.

7. Próximas Evoluções

    Timeout pós-pagamento

        Mover expiração de pickup para lifecycle.

    Novo deadline:

        POSTPAYMENT_EXPIRY
   
    Projeções operacionais

        Criar tabelas derivadas para dashboards:

            orders_abandoned_today
            orders_paid_today
            locker_utilization

    Event Bus

        No futuro eventos podem ser publicados em:

            Kafka
            RabbitMQ
            Redis Streams
    
    Observabilidade

        Adicionar:

            Prometheus metrics
            Grafana dashboards
            Tracing distribuído

8. Estrutura de Diretórios
    backend/
    ├─ order_pickup_service
    │   ├─ routers
    │   ├─ services
    │   ├─ jobs
    │   └─ models
    │
    ├─ order_lifecycle_service
    │   ├─ models
    │   ├─ services
    │   └─ routers
    │
    └─ order_lifecycle_worker
        └─ workers

9. Resumo

    A plataforma ELLAN agora possui uma arquitetura baseada em:

        deadlines
        domain events
        analytics facts
        workers dedicados

    Esse modelo permite evoluir o sistema para:

        múltiplas regiões

        múltiplos operadores de locker

        analytics avançado

        SaaS de lockers

    sem acoplamento entre os serviços operacionais.

10. <EOF>
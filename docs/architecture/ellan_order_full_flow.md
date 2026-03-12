📘 ELLAN — Fluxo Completo de um Pedido (do clique até abrir a gaveta)

Objetivo

    Este documento mostra, ponta a ponta, o fluxo operacional de um pedido na plataforma ELLAN:

        criação do pedido

        reserva da gaveta

        pagamento

        lifecycle

        timeout

        retirada

        abertura da gaveta

    Ele cobre os dois canais:

        ONLINE

        KIOSK

    e as regiões:

        SP

        PT

1. Visão geral

    Cliente / Operador
        ↓
    Frontend / Kiosk UI
        ↓
    order_pickup_service
        ↓
    backend regional (SP/PT)
        ↓
    locker físico / simulador

    Com os serviços auxiliares:

        payment_gateway
        order_lifecycle_service
        order_lifecycle_worker
        analytics_facts
        domain_events

2. Fluxo ONLINE — do clique ao pickup

    Diagrama macro

        [Cliente Web]
            ↓
        [Frontend]
            ↓ cria pedido
        [order_pickup_service]
            ↓ reserva slot
        [backend_sp/backend_pt]
            ↓
        [allocation criada]
            ↓ registra deadline
        [order_lifecycle_service]
            ↓
        [cliente paga]
            ↓
        [payment_gateway]
            ↓ confirma internamente
        [order_pickup_service]
            ↓ cancela deadline
        [order_lifecycle_service]
            ↓ cria pickup/token/QR
        [Cliente vai ao locker]
            ↓
        [pickup flow]
            ↓
        [backend regional]
            ↓
        [gaveta abre]

    Etapa 1 — cliente escolhe produto

        Origem:

            Frontend ONLINE

        A UI envia algo como:

            POST /orders

        com:

            região

            sku

            slot desejado opcional

            valor opcional ou preço vindo do catálogo

    Etapa 2 — criação do pedido

        Responsável:

            order_pickup_service/app/routers/orders.py

        Ações:

            valida payload

            resolve preço

            chama backend regional para reservar slot

            cria Order

            cria Allocation

            faz commit local

            registra deadline de pré-pagamento no lifecycle

        Estado após essa etapa:

            Order.status = PAYMENT_PENDING
            Allocation.state = RESERVED_PENDING_PAYMENT
            LifecycleDeadline.status = PENDING

    Etapa 3 — reserva física/lógica da gaveta

        Responsável:

            backend_sp / backend_pt

        Operação:

            locker_allocate()

            Retorno esperado:

            allocation_id

            slot

            ttl_sec

    Etapa 4 — deadline de pré-pagamento

        Responsável:

            order_lifecycle_service

        Endpoint:

            POST /internal/deadlines

        Cria:

            deadline_type = PREPAYMENT_TIMEOUT
            deadline_key = prepayment_timeout:<order_id>
            status = PENDING

    Etapa 5A — cliente paga dentro do prazo

        Responsáveis:

            payment_gateway
            order_pickup_service/internal.py
            order_lifecycle_service

        Fluxo:

            [payment_gateway]
                ↓
            POST /internal/orders/{order_id}/payment-confirm
                ↓
            [order_pickup_service]
                    ├─ muda pedido para PAID_PENDING_PICKUP
                    ├─ faz locker_commit
                    ├─ muda slot para PAID_PENDING_PICKUP
                    ├─ cria Pickup
                    ├─ cria PickupToken
                    └─ cancela deadline no lifecycle

        Estado final desta etapa:

            Order.status = PAID_PENDING_PICKUP
            Allocation.state = RESERVED_PAID_PENDING_PICKUP
            LifecycleDeadline.status = CANCELLED
            Pickup.status = ACTIVE

    Etapa 5B — cliente NÃO paga dentro do prazo

        Responsáveis:

            order_lifecycle_worker
            order_lifecycle_service
            order_pickup_service consumer

        Fluxo:

            [worker]
                ↓ detecta deadline vencido
            PENDING → EXECUTING
                ↓
            [deadline_engine]
                    ├─ EXECUTING → EXECUTED
                    ├─ cria domain_event
                    └─ cria analytics_fact
                ↓
            [order_pickup_service lifecycle consumer]
                    ├─ lê order.prepayment_timed_out
                    ├─ expira pedido
                    ├─ libera allocation
                    ├─ chama locker_release
                    ├─ volta slot para AVAILABLE
                    └─ dá ack no evento

        Estado final desta etapa:

            Order.status = EXPIRED
            Allocation.state = RELEASED
            LifecycleDeadline.status = EXECUTED
            DomainEvent.status = PUBLISHED
            AnalyticsFact criado
            Slot = AVAILABLE

    Etapa 6 — pickup do pedido ONLINE

        Se o cliente pagou:

            Responsável:

                order_pickup_service/app/routers/pickup.py

            Fluxo lógico:

                Cliente apresenta QR / token
                    ↓
                pickup validation
                    ↓
                valida order + pickup + token
                    ↓
                backend regional abre a gaveta
                    ↓
                pedido vira PICKED_UP

    Etapa 7 — abertura da gaveta ONLINE

        Responsáveis:

            order_pickup_service
            backend regional
            locker físico / simulador

        Comandos típicos:

            locker_light_on()
            locker_open()

3. Fluxo KIOSK — do clique até abrir a gaveta

    Diagrama macro

        [Operador / Cliente no Totem]
            ↓
        [Kiosk UI]
            ↓
        [order_pickup_service /kiosk/orders]
            ↓
        [backend regional allocate]
            ↓
        [deadline pré-pagamento]
            ↓
        [pagamento no kiosk]
            ↓
        [order_pickup_service /kiosk/orders/{id}/payment-approved]
            ↓
        [locker_commit]
        [light_on]
        [open]
        [set_state OUT_OF_STOCK]
            ↓
        [gaveta abre imediatamente]

    Etapa 1 — criação do pedido KIOSK

        Responsável:

            order_pickup_service/app/routers/kiosk.py

        Ações:

            antifraude kiosk

            consulta preço

            reserva slot

            cria pedido KIOSK

            cria allocation

            registra deadline pré-pagamento

        Estado:

            Order.status = PAYMENT_PENDING
            Allocation.state = RESERVED_PENDING_PAYMENT
            LifecycleDeadline.status = PENDING

    Etapa 2A — pagamento aprovado dentro do prazo

        Responsável:

            kiosk_payment_approved()

        Fluxo:

            [pagamento aprovado]
                ↓
            locker_commit
                ↓
            locker_light_on
                ↓
            locker_open
                ↓
            locker_set_state(OUT_OF_STOCK)
                ↓
            cancela deadline no lifecycle

        Estado final:

            Order.status = DISPENSED
            Allocation.state = OPENED_FOR_PICKUP
            LifecycleDeadline.status = CANCELLED

        No KIOSK, a gaveta abre no fluxo de pagamento aprovado, sem criar pickup separado como no ONLINE.

    Etapa 2B — pagamento NÃO aprovado dentro do prazo

        Mesmo raciocínio do ONLINE:

            deadline vence
                ↓
            worker executa
                ↓
            gera order.prepayment_timed_out
                ↓
            consumer expira pedido e libera allocation

        Estado final:

            Order.status = EXPIRED
            Allocation.state = RELEASED
            Slot = AVAILABLE

4. Fluxo de timeout — diagrama isolado

    [Order criada]
        ↓
    [LifecycleDeadline = PENDING]
        ↓ (tempo passa)
    [Worker encontra deadline]
        ↓
    [Deadline = EXECUTING]
        ↓
    [deadline_engine.execute_prepayment_timeout]
            ├─ Deadline = EXECUTED
            ├─ DomainEvent = order.prepayment_timed_out
            └─ AnalyticsFact = order_abandoned_before_payment
        ↓
    [order_pickup_service consumer]
            ├─ Order = EXPIRED
            ├─ Allocation = RELEASED
            ├─ locker_release()
            ├─ locker_set_state(AVAILABLE)
            └─ ack_event()

5. Fluxo de pagamento — diagrama isolado
    
    [Pedido PAYMENT_PENDING]
        ↓
    [payment_gateway ou payment-approved kiosk]
        ↓
    [order_pickup_service internal flow]
        ├─ atualiza pedido
        ├─ commit local
        └─ cancela deadline
                ↓
        [order_lifecycle_service]
        [LifecycleDeadline = CANCELLED]

6. Fluxo de retirada ONLINE — diagrama isolado

    [Pedido PAID_PENDING_PICKUP]
        ↓
    [Pickup ACTIVE]
        ↓
    [Token / QR gerado]
        ↓
    [cliente chega ao locker]
        ↓
    [validação do token]
        ↓
    [backend regional abre gaveta]
        ↓
    [Pedido PICKED_UP]

7. Estados por entidade

    Order

        PAYMENT_PENDING
            ↓ paga
        PAID_PENDING_PICKUP
            ↓ retira
        PICKED_UP

        ou

        PAYMENT_PENDING
            ↓ não paga
        EXPIRED

        ou no KIOSK:

        PAYMENT_PENDING
            ↓ pagamento aprovado
        DISPENSED

    Allocation

        RESERVED_PENDING_PAYMENT
            ↓ paga online
        RESERVED_PAID_PENDING_PICKUP
            ↓ retirada / fluxo posterior
        ...

        ou

        RESERVED_PENDING_PAYMENT
            ↓ timeout pré-pagamento
        RELEASED

        ou KIOSK pago:

        RESERVED_PENDING_PAYMENT
            ↓ payment-approved
        OPENED_FOR_PICKUP
        LifecycleDeadline
        PENDING
            ↓ worker pega
        EXECUTING
            ↓ sucesso
        EXECUTED

        ou

        PENDING
            ↓ pagamento antes do prazo
        CANCELLED

8. Onde cada parte do fluxo mora no código

    ONLINE create
        order_pickup_service/app/routers/orders.py

    KIOSK create + payment approved
        order_pickup_service/app/routers/kiosk.py
    
    payment confirm interno
        order_pickup_service/app/routers/internal.py
    
    lifecycle create/cancel deadlines
        backend/order_lifecycle_service/app/routers/internal.py
    
    worker de timeout
        backend/order_lifecycle_service/app/workers/prepayment_timeout_worker.py
    
    engine de timeout
        backend/order_lifecycle_service/app/services/deadline_engine.py
    
    consumer do evento no pickup service
        order_pickup_service/app/jobs/lifecycle_events_consumer.py
    
    backend físico/regional
        backend_sp/*
        backend_pt/*

9. O que é diferente entre ONLINE e KIOSK

    ONLINE

        pagamento pode ocorrer antes de ir ao locker

        gera Pickup

        gera token/QR

        pode entrar em PAID_PENDING_PICKUP

    KIOSK

        pagamento está acoplado ao totem

        aprovação já leva à abertura imediata

        tende a usar DISPENSED

        normalmente não depende do mesmo fluxo de pickup token

10. Leitura operacional em 1 frase

    ONLINE: cria → reserva → paga → pickup → abre
    KIOSK: cria → reserva → paga → abre
    TIMEOUT: cria → não paga → vence → expira → libera

11. Resumo executivo

    A plataforma ELLAN já possui um fluxo completo e desacoplado:

        order_pickup_service é dono do pedido

        order_lifecycle_service é dono do tempo

        backend_sp/backend_pt são donos da gaveta física

        payment_gateway é dono do pagamento

        frontend é dono da interação visual

    Isso permite crescer a plataforma com segurança, observabilidade e analytics.

12. <EOF>

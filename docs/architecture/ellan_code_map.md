📘 MAPA VISUAL DO CÓDIGO — ELLAN

1. Visão geral

    ELLAN
    │
    ├── frontend
    │   ├── telas operacionais
    │   ├── dashboard
    │   └── kiosk ui
    │
    ├── payment_gateway
    │   ├── recebe pedido de pagamento
    │   ├── antifraude
    │   ├── idempotência
    │   └── confirma pagamento
    │
    ├── backend_sp / backend_pt
    │   ├── controle regional de lockers
    │   ├── allocate / commit / release
    │   ├── open / led / state
    │   └── catálogo/preço regional
    │
    ├── order_pickup_service
    │   ├── cria pedido ONLINE/KIOSK
    │   ├── reserva slot
    │   ├── confirma pagamento
    │   ├── pickup / qr / token
    │   └── consome eventos de lifecycle
    │
    ├── order_lifecycle_service
    │   ├── deadlines
    │   ├── domain events
    │   ├── analytics facts
    │   └── contratos internos de lifecycle
    │
    └── order_lifecycle_worker
        └── executa timeout e gera eventos/facts

2. Mapa mental por serviço

    A. order_pickup_service
        Função

        É o dono do pedido.

        Pergunta prática

        “Quero mexer em pedido, pagamento, pickup, QR, KIOSK ou ONLINE. Onde vou?”
        Resposta: aqui.

        Estrutura mental
        order_pickup_service/
        └── app/
            ├── core/
            ├── models/
            ├── routers/
            ├── schemas/
            ├── services/
            ├── jobs/
            └── main.py
        Arquivos mais importantes
        app/main.py

        Ponto de entrada do serviço.

        Responsável por:

        subir FastAPI

        registrar routers

        iniciar loops/jobs

        startup/shutdown

        Mexa aqui quando:

        adicionar novo loop

        adicionar novo router

        ajustar startup

        app/core/config.py

        Config central do serviço.

        Responsável por:

        DATABASE_URL

        INTERNAL_TOKEN

        ORDER_LIFECYCLE_BASE_URL

        timeouts

        Mexa aqui quando:

        adicionar variável de ambiente

        mudar endpoint interno

        alterar timeout global

        app/core/db.py

        Infraestrutura de banco do serviço.

        Responsável por:

        engine SQLAlchemy

        sessão

        init_db()

        Mexa aqui quando:

        adicionar model novo

        revisar criação de tabelas

        trocar estratégia de banco

        app/core/internal_auth.py

        Proteção interna por token.

        Mexa aqui quando:

        mudar autenticação entre serviços

        reforçar segurança interna

        app/core/lifecycle_client.py

        Cliente HTTP para falar com order_lifecycle_service.

        Responsável por:

        criar deadline

        cancelar deadline

        Mexa aqui quando:

        mudar contrato /internal/deadlines

        mudar headers internos

        mudar serialização do payload

        app/core/lifecycle_events_client.py

        Cliente HTTP para ler eventos do lifecycle.

        Responsável por:

        listar eventos pendentes

        dar ack em evento

        Mexa aqui quando:

        mudar /internal/events/pending

        mudar /internal/events/ack

        Routers críticos
        app/routers/orders.py

        Fluxo ONLINE.

        Responsável por:

        criar pedido online

        reservar slot

        registrar deadline pré-pagamento

        Mexa aqui quando:

        mudar criação de pedido online

        adicionar idempotência de create

        mudar comportamento da reserva

        app/routers/kiosk.py

        Fluxo KIOSK.

        Responsável por:

        criar pedido kiosk

        reservar slot

        aprovar pagamento kiosk

        cancelar deadline após pagamento

        Mexa aqui quando:

        ajustar UX operacional do kiosk

        mudar pagamento kiosk

        mudar abertura imediata da gaveta

        app/routers/internal.py

        Contratos internos do serviço.

        Responsável por:

        payment-confirm

        release

        status interno

        operações protegidas

        Mexa aqui quando:

        outro serviço precisa acionar order_pickup_service

        timeout precisa liberar pedido

        operação interna mudar

        app/routers/pickup.py

        Fluxo de retirada.

        Responsável por:

        QR

        token

        validação de pickup

        confirmação final

        Mexa aqui quando:

        mudar regra de retirada

        girar QR

        validar abertura/fechamento

        Models críticos
        app/models/order.py

        Centro do domínio de pedidos.

        Estados típicos:

        PAYMENT_PENDING
        PAID_PENDING_PICKUP
        DISPENSED
        PICKED_UP
        EXPIRED

        Mexa aqui quando:

        adicionar novo estado

        revisar status lifecycle

        mudar semântica do pedido

        app/models/allocation.py

        Relação do pedido com a gaveta.

        Mexa aqui quando:

        mudar semântica de reserva

        distinguir pré-pagamento / pós-pagamento

        revisar RELEASED, EXPIRED, etc.

        app/models/pickup.py

        Retirada física/lógica.

        app/models/pickup_token.py

        Token manual/QR de retirada.

        Services críticos
        app/services/backend_client.py

        Cliente dos backends regionais.

        Responsável por:

        locker_allocate

        locker_commit

        locker_release

        locker_open

        locker_light_on

        locker_set_state

        Mexa aqui quando:

        mudar contrato com backend_sp / backend_pt

        criar nova ação física

        mudar endpoint regional

        app/services/lifecycle_integration.py

        Façade simples para integração com lifecycle.

        Responsável por:

        registrar timeout

        cancelar timeout

        Jobs
        app/jobs/expiry.py

        Expiração pós-pagamento atual.

        Responsável por:

        expirar PAID_PENDING_PICKUP

        liberar allocation

        marcar slot

        opcionalmente crédito

        Observação:
        esse job tende, no futuro, a migrar para o lifecycle.

        app/jobs/lifecycle_events_consumer.py

        Consumer do timeout pré-pagamento.

        Responsável por:

        ler order.prepayment_timed_out

        expirar pedido PAYMENT_PENDING

        liberar slot

        dar ack

        Esse arquivo é hoje um dos mais importantes da arquitetura nova.

    B. order_lifecycle_service
   
        Função

        É o dono dos deadlines e eventos de lifecycle.

        Pergunta prática

        “Quero mexer em timeout, evento de domínio ou analytics de abandono. Onde vou?”
        Resposta: aqui.

        Estrutura mental
        order_lifecycle_service/
        └── app/
            ├── core/
            ├── models/
            ├── routers/
            ├── schemas/
            ├── services/
            ├── workers/
            └── main.py
        Arquivos mais importantes
        app/models/lifecycle.py

        Coração do lifecycle.

        Tabelas principais:

        lifecycle_deadlines

        domain_events

        analytics_facts

        Mexa aqui quando:

        adicionar deadline novo

        adicionar tipo de evento

        revisar índices

        ampliar analytics

        app/routers/internal.py

        Contrato interno do lifecycle.

        Responsável por:

        criar deadline

        cancelar deadline

        listar eventos pendentes

        ack de evento

        Mexa aqui quando:

        outro serviço precisar integração nova

        mudar contrato de consumo

        app/schemas/internal.py

        Schemas dos contratos internos.

        Mexa aqui quando:

        mudar payload de deadline

        mudar payload de pending events

        mudar ack

        app/services/deadline_engine.py

        Motor de execução do deadline.

        Responsável por:

        execute_prepayment_timeout

        gerar DomainEvent

        gerar AnalyticsFact

        Mexa aqui quando:

        criar POSTPAYMENT_EXPIRY

        criar compensação operacional

        gerar novos facts

        app/services/event_publisher.py

        Hoje atua como marcador/publicador lógico.

        Responsável por:

        publicar/marcar eventos pendentes

        Mexa aqui quando:

        trocar PUBLISHED

        ligar event bus real

        integrar Kafka/RabbitMQ/Redis Streams

        app/workers/prepayment_timeout_worker.py

        Worker do timeout.

        Responsável por:

        buscar deadlines vencidos

        marcar EXECUTING

        executar engine

        commit final

        Arquivos mais sensíveis a bug:
        esse aqui e deadline_engine.py

    C. backend_sp e backend_pt
    
        Função

        São os donos do estado físico/regional do locker.

        Pergunta prática

        “Quero mexer em gaveta, disponibilidade, abertura, commit, release.”
        Resposta: aqui.

        O que normalmente existe

        routers de locker

        catálogo/preço

        integração com hardware/simulador

        estado de slots

        Operações críticas

        allocate

        commit

        release

        open

        light on

        set state

    D. payment_gateway
 
        Função

        É o dono do fluxo de pagamento e antifraude.

        Pergunta prática

        “Quero mexer no pagamento, confirmação, antifraude, idempotência.”
        Resposta: aqui.

        Responsabilidades

        receber requisição de pagamento

        validar dispositivo/contexto

        simular ou integrar provedor

        chamar payment-confirm interno

    E. frontend
        
        Função

        É a camada de interface.

        Áreas visuais típicas

        dashboard operacional

        pedido online

        ambiente kiosk

        painel de pickup

        lista de pedidos

        Pergunta prática

    “Quero mudar botão, UX, fluxo visual ou polling.”
    Resposta: aqui.

3. Mapa por tipo de mudança

    Se você quiser mudar...
    criação de pedido ONLINE

    Vá para:

    order_pickup_service/app/routers/orders.py
    order_pickup_service/app/schemas/orders.py
    order_pickup_service/app/models/order.py
    criação de pedido KIOSK

    Vá para:

    order_pickup_service/app/routers/kiosk.py
    order_pickup_service/app/schemas/kiosk.py
    order_pickup_service/app/models/order.py
    confirmação de pagamento

    Vá para:

    order_pickup_service/app/routers/internal.py
    payment_gateway/...
    timeout pré-pagamento

    Vá para:

    order_lifecycle_service/app/workers/prepayment_timeout_worker.py
    order_lifecycle_service/app/services/deadline_engine.py
    order_pickup_service/app/jobs/lifecycle_events_consumer.py
    expiração pós-pagamento

    Vá para:

    order_pickup_service/app/jobs/expiry.py
    order_pickup_service/app/models/pickup.py
    order_pickup_service/app/models/allocation.py
    QR / token / retirada

    Vá para:

    order_pickup_service/app/routers/pickup.py
    order_pickup_service/app/models/pickup.py
    order_pickup_service/app/models/pickup_token.py
    slot / estado de locker

    Vá para:

    order_pickup_service/app/services/backend_client.py
    backend_sp/...
    backend_pt/...
    analytics / abandono

    Vá para:

    order_lifecycle_service/app/models/lifecycle.py
    order_lifecycle_service/app/services/deadline_engine.py
    integração entre serviços

    Vá para:

    order_pickup_service/app/core/lifecycle_client.py
    order_pickup_service/app/core/lifecycle_events_client.py
    order_lifecycle_service/app/routers/internal.py
    variáveis de ambiente

    Vá para:

    order_pickup_service/app/core/config.py
    order_lifecycle_service/app/core/config.py
    docker-compose.yml
    loops/jobs

    Vá para:

    order_pickup_service/app/main.py
    order_pickup_service/app/jobs/expiry.py
    order_pickup_service/app/jobs/lifecycle_events_consumer.py
    order_lifecycle_service/app/workers/prepayment_timeout_worker.py
    banco / models

    Vá para:

    order_pickup_service/app/core/db.py
    order_pickup_service/app/models/*
    order_lifecycle_service/app/models/*
    alembic/

4. Mapa visual de criticidade

    Arquivos mais críticos do projeto hoje

    Nível 1 — muito críticos
        order_pickup_service/app/routers/internal.py
        order_pickup_service/app/routers/orders.py
        order_pickup_service/app/routers/kiosk.py
        order_pickup_service/app/jobs/lifecycle_events_consumer.py
        order_lifecycle_service/app/workers/prepayment_timeout_worker.py
        order_lifecycle_service/app/services/deadline_engine.py
        order_lifecycle_service/app/models/lifecycle.py

    Nível 2 — críticos
        order_pickup_service/app/services/backend_client.py
        order_pickup_service/app/core/config.py
        order_pickup_service/app/core/db.py
        order_lifecycle_service/app/routers/internal.py
        order_lifecycle_service/app/schemas/internal.py
        order_lifecycle_service/app/core/config.py

    Nível 3 — apoio/infra
        order_pickup_service/app/main.py
        order_lifecycle_service/app/main.py
        docker-compose.yml
        requirements.txt

5. Regra prática para não se perder

    Quando quiser fazer uma mudança, pense assim:

    “É pedido?”

        order_pickup_service

    “É deadline / timeout / abandono?”

        order_lifecycle_service

    “É gaveta física?”

        backend_sp / backend_pt

    “É pagamento?”

        payment_gateway

    “É tela?”

        frontend

6. Fluxo mental ideal de navegação

    quero mudar um comportamento
            ↓
    identifico o domínio
            ↓
    escolho o serviço dono
            ↓
    abro router
            ↓
    abro schema
            ↓
    abro model
            ↓
    abro service/job relacionado

    Exemplo:

        “timeout pré-pagamento não funcionou”
                ↓
        domínio = lifecycle
                ↓
        worker
                ↓
        deadline_engine
                ↓
        consumer no order_pickup_service

7. Próximo nível de organização recomendado

    Vale criar futuramente:

        docs/code-map/
        ├── order_pickup_service.md
        ├── order_lifecycle_service.md
        ├── payment_gateway.md
        ├── backend_regional.md
        └── frontend.md

    Cada um com:

        arquivos principais

        fluxo

        dependências

        pontos perigosos

8. Resumo final

    O projeto ELLAN hoje pode ser entendido assim:

        Frontend mostra
        Gateway cobra
        Order Pickup cria e opera pedido
        Lifecycle controla tempo e eventos
        Backend regional controla gaveta
        IoT executa no locker
        Analytics mede tudo

9. <EOF>

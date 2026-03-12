📘 ELLAN — Mapa de intervenção rápida

    Formato

        “se acontecer X, olhe primeiro em Y”

1. Pedido não é criado

    Sintoma

        POST /orders falha

        POST /kiosk/orders falha

        erro 400/409/502 na criação

    Olhe primeiro em:

        order_pickup_service/app/routers/orders.py
        order_pickup_service/app/routers/kiosk.py
        order_pickup_service/app/schemas/orders.py
        order_pickup_service/app/schemas/kiosk.py
        order_pickup_service/app/services/backend_client.py

    Verifique:

        payload recebido

        desired_slot

        amount_cents

        sku_id

        resposta de locker_allocate

2. Pedido cria, mas slot vem diferente do solicitado

    Sintoma

        enviou desired_slot=3

        voltou slot=16

    Olhe primeiro em:

        order_pickup_service/app/routers/orders.py
        order_pickup_service/app/routers/kiosk.py
        order_pickup_service/app/schemas/orders.py
        backend_sp/app/routers/locker.py
        backend_pt/app/routers/locker.py

    Verifique:

        se desired_slot está chegando no schema

        se está sendo passado para backend_client.locker_allocate

        se o backend regional respeita desired_slot

3. Valor do pedido sai errado

    Sintoma

        enviou amount_cents=1000

        sistema gravou outro valor

    Olhe primeiro em:

        order_pickup_service/app/routers/orders.py
        order_pickup_service/app/schemas/orders.py
        order_pickup_service/app/models/order.py
        backend_sp/app/routers/catalog*.py
        backend_pt/app/routers/catalog*.py

    Verifique:

        se amount_cents do payload está sendo aceito

        fallback de pricing

        se preço do backend está sobrescrevendo o valor

4. Deadline não é criado
    Sintoma

        pedido criado

        mas não aparece em lifecycle_deadlines

    Olhe primeiro em:

        order_pickup_service/app/services/lifecycle_integration.py
        order_pickup_service/app/core/lifecycle_client.py
        order_pickup_service/app/routers/orders.py
        order_pickup_service/app/routers/kiosk.py
        backend/order_lifecycle_service/app/routers/internal.py

    Verifique:

        ORDER_LIFECYCLE_BASE_URL

        INTERNAL_TOKEN

        register_prepayment_timeout_deadline(...)

        logs do order_lifecycle_service

5. Deadline fica PENDING para sempre

    Sintoma

        aparece na tabela

        não muda de status

    Olhe primeiro em:
        backend/order_lifecycle_service/app/workers/prepayment_timeout_worker.py
        backend/order_lifecycle_service/app/core/config.py
        02_docker/docker-compose.yml

    Verifique:

        worker subiu?

        PREPAYMENT_TIMEOUT_SECONDS

        WORKER_POLL_INTERVAL_SECONDS

        logs do order_lifecycle_worker

6. Deadline fica preso em EXECUTING

    Sintoma

        passou do prazo

        não virou EXECUTED

        não gerou evento

    Olhe primeiro em:

        backend/order_lifecycle_service/app/workers/prepayment_timeout_worker.py
        backend/order_lifecycle_service/app/services/deadline_engine.py
        backend/order_lifecycle_service/app/services/event_publisher.py

    Verifique:

        uso de objeto ORM fora da sessão

        commits do worker

        exceptions no log

        DetachedInstanceError

7. Evento de domínio não aparece

    Sintoma

        deadline executou

        mas domain_events está vazio

    Olhe primeiro em:

        backend/order_lifecycle_service/app/services/deadline_engine.py
        backend/order_lifecycle_service/app/models/lifecycle.py

    Verifique:

        DomainEvent(...)

        db.add(event)

        commit da transação

        unicidade de event_key

8. Analytics fact não aparece

    Sintoma

        timeout executou

        evento talvez exista

        mas analytics_facts está vazio

    Olhe primeiro em:

        backend/order_lifecycle_service/app/services/deadline_engine.py
        backend/order_lifecycle_service/app/models/lifecycle.py

    Verifique:

        AnalyticsFact(...)

        fact_key

        payload

        commit da transação

9. Evento existe, mas order_pickup_service não reage

    Sintoma

        domain_events existe

        pedido continua PAYMENT_PENDING

    Olhe primeiro em:

        order_pickup_service/app/jobs/lifecycle_events_consumer.py
        order_pickup_service/app/core/lifecycle_events_client.py
        order_pickup_service/app/main.py
        backend/order_lifecycle_service/app/routers/internal.py

    Verifique:

        lifecycle_events_loop() subiu?

        GET /internal/events/pending

        ack_event

        logs do consumer

10. Consumer não consegue conectar no lifecycle

    Sintoma

        Connection refused

        falha ao listar eventos

    Olhe primeiro em:

        02_docker/docker-compose.yml
        order_pickup_service/app/core/config.py
        backend/order_lifecycle_service/app/main.py
    
    Verifique:

        ORDER_LIFECYCLE_BASE_URL

        depends_on

        healthcheck

        se order_lifecycle_service está Up

11. Pedido não expira após evento de timeout

    Sintoma

        evento foi gerado

        mas pedido continua PAYMENT_PENDING

    Olhe primeiro em:

        order_pickup_service/app/jobs/lifecycle_events_consumer.py
        order_pickup_service/app/models/order.py
        order_pickup_service/app/models/allocation.py

    Verifique:

        condição if order.status != PAYMENT_PENDING

        update de order.status = EXPIRED

        allocation.state = RELEASED

        db.commit()

12. Slot não volta para disponível após timeout pré-pagamento

    Sintoma

        pedido expirou

        mas locker continua reservado/ocupado

    Olhe primeiro em:

        order_pickup_service/app/jobs/lifecycle_events_consumer.py
        order_pickup_service/app/services/backend_client.py
        backend_sp/app/routers/locker.py
        backend_pt/app/routers/locker.py

    Verifique:

        locker_release(...)

        locker_set_state(..., "AVAILABLE")

        resposta do backend regional

13. Pagamento é confirmado, mas deadline não cancela

    Sintoma

        pedido foi pago

        lifecycle_deadlines continua PENDING

    Olhe primeiro em:
        order_pickup_service/app/routers/internal.py
        order_pickup_service/app/routers/kiosk.py
        order_pickup_service/app/services/lifecycle_integration.py
        order_pickup_service/app/core/lifecycle_client.py
        backend/order_lifecycle_service/app/routers/internal.py
    
    Verifique:

        cancel_prepayment_timeout_deadline(...)

        deadline_key

        INTERNAL_TOKEN

        resposta do lifecycle

14. Pagamento confirmado duas vezes

    Sintoma

        retry de gateway

        repetição de chamada

        medo de duplicar operação

    Olhe primeiro em:

        order_pickup_service/app/routers/internal.py
        order_pickup_service/app/routers/kiosk.py
        order_pickup_service/app/models/order.py

    Verifique:

        idempotência por status

        retorno quando já está:

        PAID_PENDING_PICKUP

        DISPENSED

        PICKED_UP

15. Pickup QR/token não funciona

    Sintoma

        QR inválido

        token não bate

        pickup negado

    Olhe primeiro em:

        order_pickup_service/app/routers/pickup.py
        order_pickup_service/app/models/pickup.py
        order_pickup_service/app/models/pickup_token.py
        order_pickup_service/app/schemas/internal.py

    Verifique:

        expiração do token

        hash do token

        Pickup.status

        PickupToken.used_at

16. Expiração pós-pagamento não roda

    Sintoma

        pedido PAID_PENDING_PICKUP

        passou do prazo

        continua pendurado

    Olhe primeiro em:
        order_pickup_service/app/jobs/expiry.py
        order_pickup_service/app/main.py
        order_pickup_service/app/models/order.py

    Verifique:

        expiry_loop() subiu

        pickup_deadline_at

        OrderStatus.PAID_PENDING_PICKUP

        commit do job

17. Slot fica OUT_OF_STOCK quando deveria estar AVAILABLE

    Sintoma

        slot não volta a vender

        dashboard mostra bloqueado

    Olhe primeiro em:

        order_pickup_service/app/jobs/expiry.py
        order_pickup_service/app/jobs/lifecycle_events_consumer.py
        backend_sp/app/routers/locker.py
        backend_pt/app/routers/locker.py

    Regra mental

        pré-pagamento expirado → AVAILABLE

        pós-pagamento expirado / produto não retirado → normalmente OUT_OF_STOCK ou fluxo definido por reposição

18. Container sobe, mas código não parece atualizado

    Sintoma

        corrigiu arquivo

        erro continua igual

    Olhe primeiro em:

        Dockerfile
        02_docker/docker-compose.yml

    Faça:

        docker compose build --no-cache NOME_DO_SERVICO
        docker compose up -d NOME_DO_SERVICO

    Regra mental

        Se mudou Python e o comportamento não mudou, quase sempre faltou rebuild.

19. Serviço quebra no startup por import

    Sintoma

        ModuleNotFoundError

        ImportError

        app nem sobe

    Olhe primeiro em:

        app/main.py
        app/core/config.py
        requirements.txt
        __init__.py

    Verifique:

        arquivo existe fisicamente?

        pasta tem __init__.py?

        dependência está no requirements.txt?

        container foi rebuildado?

20. Banco não cria tabela/model

    Sintoma

        erro de tabela ausente

        model existe, tabela não

    Olhe primeiro em:

        order_pickup_service/app/core/db.py
        backend/order_lifecycle_service/alembic/
        backend/order_lifecycle_service/app/models/

    Verifique:

        model foi importado no init_db()

        migration foi aplicada

        banco certo está sendo usado

21. Mapa relâmpago por domínio
    
    Se o problema for...
    
        pedido

            order_pickup_service/app/routers/
            order_pickup_service/app/models/order.py
        
        timeout

            order_lifecycle_service/app/workers/
            order_lifecycle_service/app/services/deadline_engine.py
            order_pickup_service/app/jobs/lifecycle_events_consumer.py
        
        locker físico

            order_pickup_service/app/services/backend_client.py
            backend_sp/
            backend_pt/
        
        pagamento

            payment_gateway/
            order_pickup_service/app/routers/internal.py
            order_pickup_service/app/routers/kiosk.py
        
        pickup

            order_pickup_service/app/routers/pickup.py
            order_pickup_service/app/models/pickup.py
            order_pickup_service/app/models/pickup_token.py
        
        infraestrutura

            02_docker/docker-compose.yml
            app/core/config.py
            requirements.txt

22. Regra de intervenção em 4 passos

    Quando algo quebrar, siga sempre esta ordem:

        1. identificar o sintoma exato
        2. localizar o serviço dono
        3. abrir primeiro router/job
        4. depois abrir model/service/config

    Exemplo:

        “deadline não executa”
        → serviço dono: order_lifecycle_service
        → abrir worker
        → abrir deadline_engine
        → abrir logs

23. Regra de ouro

    Se o erro envolver:

        HTTP entre serviços

        olhe:

            config.py
            client.py
            docker-compose.yml
            internal_auth.py
    
    estado inconsistente

        olhe:

            router
            model
            job/worker

    comportamento físico da gaveta

        olhe:

            backend_client.py
            backend regional
            simulador / mqtt

24. <EOF>

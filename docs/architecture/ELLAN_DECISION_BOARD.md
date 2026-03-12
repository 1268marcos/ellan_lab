📘 ELLAN — Quadro de Decisão Operacional

1. Regra nº1 — Identifique o domínio primeiro

    PEDIDO / KIOSK / ONLINE           → order_pickup_service
    TIMEOUT / DEADLINE / ABANDONO     → order_lifecycle_service
    GAVETA / SLOT / HARDWARE          → backend_sp / backend_pt
    PAGAMENTO                         → payment_gateway
    TELA / UX                         → frontend
    INFRA / PORTA / REDE              → docker-compose

2. Fluxo mental padrão de debugging

    Sempre siga esta ordem:

        1 identificar sintoma
        2 identificar serviço dono
        3 abrir router/job
        4 abrir model
        5 abrir service
        6 verificar config/env

    Nunca comece pelo banco ou pelo docker.

3. Se acontecer X → olhe primeiro em Y
    
    Pedido não cria

        order_pickup_service/app/routers/orders.py
        order_pickup_service/app/schemas/orders.py
        order_pickup_service/app/services/backend_client.py
    
    Slot errado ou não respeita desired_slot
    
        order_pickup_service/app/routers/orders.py
        backend_sp/app/routers/locker.py
        backend_pt/app/routers/locker.py
    
    Deadline não aparece
    
        order_pickup_service/app/services/lifecycle_integration.py
        order_pickup_service/app/core/lifecycle_client.py
        order_lifecycle_service/app/routers/internal.py
    
    Deadline nunca executa
    
        order_lifecycle_service/app/workers/prepayment_timeout_worker.py
        order_lifecycle_service/app/core/config.py
        docker-compose.yml
    
    Deadline fica EXECUTING
    
        order_lifecycle_service/app/workers/prepayment_timeout_worker.py
        order_lifecycle_service/app/services/deadline_engine.py
    
    Evento de domínio não aparece
    
        order_lifecycle_service/app/services/deadline_engine.py
        order_lifecycle_service/app/models/lifecycle.py
    
    Evento existe mas pedido não expira
    
        order_pickup_service/app/jobs/lifecycle_events_consumer.py
        order_pickup_service/app/core/lifecycle_events_client.py
    
    Pedido expira mas slot não libera
    
        order_pickup_service/app/jobs/lifecycle_events_consumer.py
        order_pickup_service/app/services/backend_client.py
        backend_sp/backend_pt
    
    Pagamento confirmado mas deadline continua ativo
    
        order_pickup_service/app/routers/internal.py
        order_pickup_service/app/services/lifecycle_integration.py
    
    Pickup / QR não funciona
    
        order_pickup_service/app/routers/pickup.py
        order_pickup_service/app/models/pickup.py
        order_pickup_service/app/models/pickup_token.py
    
    Expiração pós-pagamento não roda
    
        order_pickup_service/app/jobs/expiry.py
        order_pickup_service/app/main.py

4. Arquivos mais críticos do sistema

    Se algo estranho acontecer, olhe primeiro nestes:

        order_pickup_service/app/routers/orders.py
        order_pickup_service/app/routers/kiosk.py
        order_pickup_service/app/routers/internal.py

        order_pickup_service/app/jobs/lifecycle_events_consumer.py
        order_pickup_service/app/jobs/expiry.py

        order_lifecycle_service/app/workers/prepayment_timeout_worker.py
        order_lifecycle_service/app/services/deadline_engine.py
        order_lifecycle_service/app/models/lifecycle.py

        02_docker/docker-compose.yml

5. Se o erro for de comunicação entre serviços

    Verifique sempre:

        config.py
        internal_token
        service_url
        docker network

    Arquivos:

        order_pickup_service/app/core/config.py
        order_pickup_service/app/core/internal_auth.py
        order_lifecycle_service/app/core/config.py
        docker-compose.yml

6. Regra de ouro para Docker

    Se o comportamento não mudou após alterar código:

        docker compose build --no-cache SERVICO
        docker compose up -d SERVICO

7. Regra de ouro para estados inconsistentes

    Verifique nesta ordem:

        router
        ↓
        model
        ↓
        job/worker
        ↓
        service
        ↓
        config

    Nunca comece pelo banco.

8. Estados principais do sistema
    
    Pedido
    
        PAYMENT_PENDING
        PAID_PENDING_PICKUP
        DISPENSED
        PICKED_UP
        EXPIRED
    
    Allocation
    
        RESERVED_PENDING_PAYMENT
        RESERVED_PAID_PENDING_PICKUP
        RELEASED
        EXPIRED
    
    Deadlines
    
        PENDING
        EXECUTING
        EXECUTED
        FAILED
        CANCELLED

9. Arquitetura mental da plataforma

    Frontend mostra
    Gateway cobra
    Order Pickup cria pedido
    Lifecycle controla tempo
    Backend regional controla gaveta
    IoT executa hardware
    Analytics mede tudo

10. Diagnóstico relâmpago
    
    Se problema envolve
     
        Sintoma	    Serviço

        pedido	    order_pickup_service
        timeout	    order_lifecycle_service
        gaveta	    backend_sp/backend_pt
        pagamento	payment_gateway
        interface	frontend
        infra	    docker

11. Regra final

    Antes de alterar qualquer coisa pergunte:

    QUAL SERVIÇO É DONO DISSO?

    Isso resolve 80% dos bugs mais rápido.

12. <EOF>

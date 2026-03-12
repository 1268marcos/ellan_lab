Árvore de pastas comentada — ELLAN

Visão geral

    ELLAN/
    │
    ├── 01_source/                         # Código-fonte principal da plataforma
    ├── 02_docker/                         # Orquestração local com Docker Compose
    ├── 03_data/                           # Volumes persistentes locais
    ├── 04_logs/                           # Logs persistidos
    ├── 05_backups/                        # Backups operacionais
    └── docs/                              # Documentação técnica e arquitetural

1. 01_source/

    01_source/
    │
    ├── frontend/                          # Interface web/dashboard/kiosk
    ├── payment_gateway/                   # Gateway de pagamento + antifraude
    ├── backend_sp/                        # Backend regional de lockers - São Paulo
    ├── backend_pt/                        # Backend regional de lockers - Portugal
    ├── order_pickup_service/              # Dono do pedido e do fluxo de pickup
    ├── backend/
    │   └── order_lifecycle_service/       # Dono de deadlines, eventos e analytics
    └── simulator/                         # Simulador de lockers/IoT para ambiente de lab

2. frontend/

    frontend/
    │
    ├── src/
    │   ├── pages/                         # Páginas principais (dashboard, kiosk, etc.)
    │   ├── components/                    # Componentes reutilizáveis
    │   ├── services/                      # Chamadas HTTP para APIs
    │   ├── hooks/                         # Hooks React customizados
    │   ├── utils/                         # Helpers de UI
    │   └── assets/                        # Ícones, imagens, recursos estáticos
    │
    ├── public/                            # Arquivos públicos do frontend
    ├── package.json                       # Dependências e scripts
    └── vite.config.* / similar            # Configuração do bundler
    
    Quando mexer aqui

        mudar tela

        ajustar UX

        alterar polling

        criar página kiosk

        melhorar dashboard operacional

3. payment_gateway/
    
    payment_gateway/
    │
    ├── app/
    │   ├── main.py                        # Ponto de entrada da API do gateway
    │   ├── routers/                       # Endpoints do gateway
    │   ├── services/                      # Regras de pagamento / integrações
    │   ├── core/                          # Config, segurança, db local, antifraude
    │   ├── models/                        # Models do gateway
    │   └── schemas/                       # Contratos de request/response
    │
    ├── requirements.txt                   # Dependências Python
    ├── Dockerfile                         # Imagem do serviço
    └── ...                                # Arquivos auxiliares
    
    Papel

        receber requisição de pagamento

        validar contexto

        antifraude

        idempotência

        chamar confirmação interna no order_pickup_service

    Arquivos críticos

        app/main.py

        app/services/payment_service.py ou equivalente

        app/core/* de antifraude/config

4. backend_sp/ e backend_pt/

    Esses dois têm papel semelhante.
    A diferença principal é a região.

    backend_sp/
    backend_pt/
    │
    ├── app/
    │   ├── main.py                        # API regional do locker
    │   ├── routers/                       # Endpoints de locker, catálogo, auditoria
    │   ├── services/                      # Lógica operacional do locker
    │   ├── core/                          # Config, DB, auth interna, logging
    │   ├── models/                        # Models regionais
    │   └── schemas/                       # Schemas regionais
    │
    ├── requirements.txt
    ├── Dockerfile
    └── ...
    
    Papel

        allocate

        commit

        release

        open

        light on

        set state

        catálogo e preço por região

    Quando mexer aqui

        gaveta

        disponibilidade

        regras regionais

        integração física/IoT

        endpoints de operação do locker

    Arquivos normalmente mais críticos

        app/routers/locker.py

        app/services/*locker*

        app/models/*slot*, allocation, catalog

5. order_pickup_service/

    Esse é um dos núcleos principais do sistema.

    order_pickup_service/
    │
    ├── app/
    │   ├── main.py                        # Sobe API + loops/jobs
    │   │
    │   ├── core/
    │   │   ├── config.py                  # Variáveis de ambiente do serviço
    │   │   ├── db.py                      # Engine, sessão, init_db
    │   │   ├── internal_auth.py           # X-Internal-Token
    │   │   ├── lifecycle_client.py        # Cliente para criar/cancelar deadlines
    │   │   └── lifecycle_events_client.py # Cliente para listar/ack eventos do lifecycle
    │   │
    │   ├── models/
    │   │   ├── order.py                   # Modelo central do pedido
    │   │   ├── allocation.py              # Relação do pedido com a gaveta
    │   │   ├── pickup.py                  # Fluxo de retirada
    │   │   ├── pickup_token.py            # Token/QR/manual code
    │   │   ├── credit.py                  # Crédito opcional
    │   │   ├── user.py                    # Usuário
    │   │   ├── login_otp.py               # OTP/autenticação, se aplicável
    │   │   └── kiosk_antifraud_event.py   # Eventos de antifraude kiosk
    │   │
    │   ├── routers/
    │   │   ├── orders.py                  # Fluxo ONLINE
    │   │   ├── kiosk.py                   # Fluxo KIOSK
    │   │   ├── pickup.py                  # QR, retirada, validação
    │   │   └── internal.py                # Contratos internos protegidos
    │   │
    │   ├── schemas/
    │   │   ├── orders.py                  # Contratos do pedido ONLINE
    │   │   ├── kiosk.py                   # Contratos do KIOSK
    │   │   ├── internal.py                # Contratos internos
    │   │   └── ...                        # Outros schemas
    │   │
    │   ├── services/
    │   │   ├── backend_client.py          # Fala com backend_sp/backend_pt
    │   │   ├── lifecycle_integration.py   # Façade da integração com lifecycle
    │   │   ├── antifraud_kiosk.py         # Antifraude kiosk
    │   │   ├── orders_service.py          # Regras de pedido, se houver
    │   │   └── ...                        # Demais serviços
    │   │
    │   ├── jobs/
    │   │   ├── expiry.py                  # Expiração pós-pagamento atual
    │   │   └── lifecycle_events_consumer.py # Consome order.prepayment_timed_out
    │   │
    │   └── health/
    │       ├── health.py                  # Health público
    │       └── internal.py                # Health interno
    │
    ├── requirements.txt
    ├── Dockerfile
    └── ...
    
    Papel

        criar pedido

        reservar slot

        confirmar pagamento

        gerar pickup

        processar KIOSK e ONLINE

        consumir eventos de lifecycle

    Subpastas mais importantes

        routers/

            Onde você mexe quando quer mudar comportamento HTTP.

        models/

            Onde você mexe quando quer mudar estado/estrutura do domínio.

        jobs/

            Onde ficam os loops assíncronos/rotinas operacionais.

        core/

            Infraestrutura do serviço.

    Arquivos mais críticos

        app/routers/orders.py
        app/routers/kiosk.py
        app/routers/internal.py
        app/jobs/lifecycle_events_consumer.py
        app/jobs/expiry.py
        app/services/backend_client.py
        app/models/order.py
        app/models/allocation.py

6. backend/order_lifecycle_service/

    Esse é o novo núcleo do lifecycle.

    backend/order_lifecycle_service/
    │
    ├── app/
    │   ├── main.py                        # API do lifecycle
    │   │
    │   ├── core/
    │   │   ├── config.py                  # Config do lifecycle
    │   │   ├── db.py                      # Conexão com Postgres central
    │   │   ├── logging.py                 # Logging estruturado
    │   │   └── internal_auth.py           # Token interno
    │   │
    │   ├── models/
    │   │   ├── base.py                    # Base declarativa
    │   │   └── lifecycle.py               # deadlines, events, analytics
    │   │
    │   ├── routers/
    │   │   ├── health.py                  # Health do serviço
    │   │   └── internal.py                # criar/cancelar deadline, pending events, ack
    │   │
    │   ├── schemas/
    │   │   ├── health.py
    │   │   └── internal.py                # contratos internos do lifecycle
    │   │
    │   ├── services/
    │   │   ├── deadline_engine.py         # executa timeout e gera efeitos
    │   │   └── event_publisher.py         # marca/publica eventos
    │   │
    │   └── workers/
    │       └── prepayment_timeout_worker.py # worker de timeout pré-pagamento
    │
    ├── alembic/                           # Migrations do lifecycle
    │   ├── env.py
    │   ├── script.py.mako
    │   └── versions/
    │       └── 0001_init_order_lifecycle.py
    │
    ├── alembic.ini
    ├── requirements.txt
    ├── Dockerfile
    └── .env.example
    
    Papel

        criar e cancelar deadlines

        armazenar eventos de domínio

        armazenar facts analíticos

        executar timeout pré-pagamento

    Arquivos mais críticos

        app/models/lifecycle.py
        app/routers/internal.py
        app/services/deadline_engine.py
        app/workers/prepayment_timeout_worker.py

7. simulator/

    simulator/
    │
    ├── main.py / app.py                   # Simulação do node/locker
    ├── mqtt/logic/etc                     # Publica ou recebe eventos do broker
    ├── requirements.txt
    └── Dockerfile

    Papel

        simular abertura de porta

        simular hardware

        simular eventos de locker

        laboratório de testes

    Quando mexer aqui

        testes sem hardware real

        simulação de erro

        comportamento IoT

8. 02_docker/

    02_docker/
    │
    ├── docker-compose.yml                 # Orquestração local da plataforma
    ├── .env / .env.*                      # Variáveis de ambiente
    ├── configs/                           # Env files por serviço
    ├── postgres_central/
    │   └── init/                          # Scripts de init do Postgres, se houver
    └── ...                                # Arquivos auxiliares
    
    Papel

        subir tudo localmente

        definir portas

        redes

        depends_on

        variáveis de ambiente

        volumes

    Arquivo mais crítico

        02_docker/docker-compose.yml
   
    Quando mexer aqui

        adicionar serviço novo

        mudar porta

        mudar variável

        healthcheck

        dependência entre serviços

9. 03_data/

    03_data/
    │
    ├── postgres_central/                  # Dados persistidos do Postgres
    ├── redis_central/                     # Dados persistidos do Redis
    ├── sqlite/                            # Bancos SQLite locais de serviços
    └── mqtt/                              # Dados/config do broker
    
    Papel

        persistência local no ambiente de desenvolvimento/lab

    Observação

        Normalmente você não mexe manualmente aqui, exceto para:

            inspecionar banco

            resetar ambiente

            limpar volume

10. 04_logs/

    04_logs/
    └── ...                                # Logs exportados/persistidos
   
    Papel

        auditoria

        troubleshooting

        histórico operacional

11. 05_backups/

    05_backups/
    └── ...                                # Backups locais e snapshots
    
    Papel

        backup de banco

        backup de SQLite

        recuperação operacional

12. docs/

    docs/
    │
    ├── architecture/
    │   ├── order_lifecycle.md             # Arquitetura do lifecycle
    │   ├── ellan_platform_architecture.md # Diagrama da plataforma
    │   ├── ellan_code_map.md              # Mapa visual do código
    │   └── ellan_folder_tree.md           # Esta árvore comentada
    │
    └── ...                                # Roadmaps, handoffs, decisões, etc.
   
    Papel

        documentação viva do sistema

13. Guia operacional rápido

    Se você quer mexer em...

        Pedido ONLINE

            order_pickup_service/app/routers/orders.py
            order_pickup_service/app/schemas/orders.py
            order_pickup_service/app/models/order.py

        Pedido KIOSK

            order_pickup_service/app/routers/kiosk.py
            order_pickup_service/app/schemas/kiosk.py
            order_pickup_service/app/models/order.py

        Pagamento

            payment_gateway/
            order_pickup_service/app/routers/internal.py

        Gaveta / locker / slot

            order_pickup_service/app/services/backend_client.py
            backend_sp/
            backend_pt/

        Timeout pré-pagamento

            backend/order_lifecycle_service/app/workers/prepayment_timeout_worker.py
            backend/order_lifecycle_service/app/services/deadline_engine.py
            order_pickup_service/app/jobs/lifecycle_events_consumer.py

        Expiração pós-pagamento

            order_pickup_service/app/jobs/expiry.py

        Pickup / QR / token

            order_pickup_service/app/routers/pickup.py
            order_pickup_service/app/models/pickup.py
            order_pickup_service/app/models/pickup_token.py

        Variáveis de ambiente

            02_docker/docker-compose.yml
            order_pickup_service/app/core/config.py
            backend/order_lifecycle_service/app/core/config.py

        Banco / models

            order_pickup_service/app/core/db.py
            order_pickup_service/app/models/
            backend/order_lifecycle_service/app/models/
            alembic/

    Criticidade por arquivo

        Muito críticos

            order_pickup_service/app/routers/orders.py
            order_pickup_service/app/routers/kiosk.py
            order_pickup_service/app/routers/internal.py
            order_pickup_service/app/jobs/lifecycle_events_consumer.py
            backend/order_lifecycle_service/app/workers/prepayment_timeout_worker.py
            backend/order_lifecycle_service/app/services/deadline_engine.py
            backend/order_lifecycle_service/app/models/lifecycle.py
            02_docker/docker-compose.yml
    
        Críticos

            order_pickup_service/app/services/backend_client.py
            order_pickup_service/app/jobs/expiry.py
            order_pickup_service/app/core/config.py
            order_pickup_service/app/core/db.py
            backend/order_lifecycle_service/app/routers/internal.py
            backend/order_lifecycle_service/app/schemas/internal.py
            backend/order_lifecycle_service/app/core/config.py

        Apoio/infra

            order_pickup_service/app/main.py
            backend/order_lifecycle_service/app/main.py
            requirements.txt
            Dockerfile
            docs/architecture/*

    Regra mental simples para não se perder

        pedido = order_pickup_service
        tempo/evento/abandono = order_lifecycle_service
        gaveta física = backend_sp/backend_pt
        pagamento = payment_gateway
        tela = frontend
        infra = 02_docker

    Recomendação prática de organização

        Vale muito a pena, no seu caso, manter este padrão:

            1. identificar o domínio
            2. abrir o serviço dono
            3. abrir router
            4. abrir schema
            5. abrir model
            6. abrir service/job
            7. só então alterar

14. <EOF>

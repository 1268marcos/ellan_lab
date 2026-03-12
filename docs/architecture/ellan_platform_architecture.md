📘 ELLAN Platform — Arquitetura Completa

Visão Geral

   A plataforma ELLAN Locker Platform é composta por múltiplos serviços desacoplados responsáveis por:

      pedidos

      pagamentos

      controle de lockers

      lifecycle operacional

      eventos

      analytics

      IoT

   A arquitetura foi desenhada para suportar:

      múltiplas regiões

      múltiplos operadores

      lockers próprios ou licenciados (SaaS)

1. Diagrama Geral da Plataforma
                         ┌──────────────────────────┐
                         │        FRONTEND          │
                         │                          │
                         │  Dashboard Operacional   │
                         │  KIOSK Interface         │
                         │  Cliente Web / Mobile    │
                         └─────────────┬────────────┘
                                       │
                                       ▼
                        ┌─────────────────────────┐
                        │     PAYMENT GATEWAY     │
                        │                         │
                        │   PIX / MBWay / Card   │
                        │   Antifraude            │
                        │   Idempotência          │
                        └─────────────┬───────────┘
                                      │
                                      ▼
                     ┌────────────────────────────────┐
                     │       ORDER PICKUP SERVICE     │
                     │                                │
                     │ criação de pedidos             │
                     │ reserva de slot                │
                     │ confirmação de pagamento       │
                     │ geração de QR pickup           │
                     │ consumo de eventos lifecycle   │
                     └───────────────┬────────────────┘
                                     │
                                     │ cria deadlines
                                     ▼
               ┌────────────────────────────────────────┐
               │        ORDER LIFECYCLE SERVICE         │
               │                                        │
               │ lifecycle_deadlines                    │
               │ domain_events                          │
               │ analytics_facts                        │
               └───────────────┬────────────────────────┘
                               │
                               │ executa deadlines
                               ▼
               ┌────────────────────────────────────────┐
               │         LIFECYCLE WORKERS              │
               │                                        │
               │ prepayment timeout                     │
               │ postpayment expiry                     │
               │ compensações                           │
               └───────────────┬────────────────────────┘
                               │
                               ▼
               ┌────────────────────────────────────────┐
               │          EVENT CONSUMERS               │
               │                                        │
               │ order_pickup_service                   │
               │ analytics pipeline                     │
               └────────────────────────────────────────┘

2. Backend Regional (Lockers)

    Cada região possui um backend responsável por controlar os lockers físicos.

                        ┌──────────────────────────────┐
                        │         BACKEND_SP           │
                        │                              │
                        │ gerenciamento de lockers     │
                        │ estado de slots              │
                        │ abertura de portas           │
                        │ iluminação                   │
                        └─────────────┬────────────────┘
                                    │
                                    ▼
                        ┌──────────────────────────────┐
                        │         BACKEND_PT           │
                        │                              │
                        │ gerenciamento de lockers     │
                        │ estado de slots              │
                        │ abertura de portas           │
                        └──────────────────────────────┘

    Esses backends recebem comandos do:

    order_pickup_service

3. Camada de Lockers

    Os lockers físicos possuem controladores conectados.

                    ┌──────────────────────────┐
                    │        LOCKER NODE       │
                    │                          │
                    │ microcontrolador         │
                    │ sensores de porta        │
                    │ leds                     │
                    │ relés                    │
                    └───────────┬──────────────┘
                                │
                                ▼
                        MQTT / HTTP
                                │
                                ▼
                    ┌──────────────────────────┐
                    │        SIMULATOR         │
                    │ (lab environment)        │
                    └──────────────────────────┘

4. Camada IoT

    Comunicação entre backend e lockers.

                ┌──────────────────────────┐
                │        MQTT BROKER       │
                │                          │
                │ eventos de sensores      │
                │ comandos de portas       │
                │ telemetria               │
                └─────────────┬────────────┘
                                │
                                ▼
                        LOCKER CONTROLLERS

5. Banco Central
                    ┌────────────────────────────┐
                    │        POSTGRESQL          │
                    │                            │
                    │ lifecycle_deadlines        │
                    │ domain_events              │
                    │ analytics_facts            │
                    │ pedidos                    │
                    │ usuários                   │
                    └────────────────────────────┘

    Também existem:

    Redis → cache / idempotência
    SQLite → antifraude local gateway

6. Camada de Analytics

    Analytics é gerado automaticamente pelos eventos.

                    ┌────────────────────────────┐
                    │       ANALYTICS FACTS      │
                    │                            │
                    │ abandono de carrinho      │
                    │ conversão de pagamento    │
                    │ tempo médio de pickup     │
                    │ utilização de lockers     │
                    └─────────────┬─────────────┘
                                │
                                ▼
                        DASHBOARD OPERACIONAL

7. Fluxo Completo de Pedido
Cliente cria pedido
Frontend
   ↓
Payment Gateway
   ↓
order_pickup_service
Reserva de locker
order_pickup_service
   ↓
backend_regional
   ↓
locker_allocate()
Criação de deadline
order_pickup_service
   ↓
order_lifecycle_service
   ↓
lifecycle_deadlines
Worker executa timeout
lifecycle_worker
   ↓
domain_events
   ↓
analytics_facts
Serviço consome evento
order_pickup_service
   ↓
expira pedido
libera slot

8. Estrutura Atual da Plataforma
ELLAN PLATFORM
│
├── frontend
│
├── payment_gateway
│
├── backend_sp
├── backend_pt
│
├── order_pickup_service
│
├── order_lifecycle_service
│
├── order_lifecycle_worker
│
├── mqtt_broker
│
├── redis
│
└── postgres

9. Escalabilidade

    A arquitetura suporta facilmente:

    expansão geográfica
    backend_es
    backend_fr
    backend_br
    operadores SaaS
    operator_A
    operator_B
    operator_C
    novos canais
    APP MOBILE
    DELIVERY INTEGRATION
    MARKETPLACES10. Evoluções futuras

    A arquitetura permite adicionar facilmente:

    Event Bus real
    Kafka
    RabbitMQ
    Redis Streams
    Observabilidade
    Prometheus
    Grafana
    OpenTelemetry
    IA operacional

    Previsão de:

    demanda
    reposição de produtos
    falha de lockers

11. Conclusão

    A plataforma ELLAN agora possui:

    ✔ arquitetura orientada a eventos
    ✔ serviços desacoplados
    ✔ suporte a múltiplas regiões
    ✔ suporte a SaaS de lockers
    ✔ base para analytics operacional

    Isso transforma o sistema em uma plataforma escalável de logística urbana com lockers inteligentes.

12. 💡 Recomendação importante

    Guarde este diagrama como documento oficial da arquitetura.

    Ele será extremamente útil quando o sistema crescer.

13. <EOF>

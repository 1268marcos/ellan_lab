# ROADMAP — ELLAN Lab Locker

## Objetivo deste roadmap

Este documento organiza a execução técnica do projeto **ELLAN Lab Locker** nas próximas fases prioritárias, com foco em:

* destravar o fluxo real de pedidos
* ganhar visibilidade operacional no dashboard
* criar um ambiente KIOSK de simulação
* consolidar o catálogo em uma única fonte de verdade
* preparar a base para a regra comercial de crédito de 50%

---

## Contexto técnico atual

### Stack e serviços

* `backend_sp` → porta externa `8201`, interna `8000`
* `backend_pt` → porta externa `8202`, interna `8000`
* `payment_gateway` → porta externa `8000`
* `order_pickup_service` → porta externa `8003`
* `mqtt` → externa `1884`, interna `1883`
* `redis`
* `postgres`

### Convenção arquitetural

* portas **internas** sempre `8000`
* portas **externas** apenas fachada / compose
* frontend via **Vite proxy**:

  * `/api/sp`
  * `/api/pt`
  * `/api/gw`
* objetivo: evitar CORS e manter integração limpa em dev

### Capacidades já existentes

#### Locker / alocação

Backends já possuem:

* `/locker/allocate`
* `/allocations/{id}/commit`
* `/allocations/{id}/release`
* `/locker/slots`
* `/slots/{slot}/open`
* `/slots/{slot}/light/on`
* `/slots/{slot}/set-state`

#### Online pickup

* `POST /internal/orders/{order_id}/payment-confirm`

  * cria `PickupToken` no modelo ponteiro (`token_id`)
  * gera `manual_code` de 6 dígitos
  * janela de 2 horas
* QR rotativo em:

  * `/me/pickups/{pickup_id}/qr`
* payload rotativo no formato:

  * `{pickup_id, token_id, ctr, exp, sig}`

#### Legado ainda existente

* `pickup.py` mantém endpoint legado:

  * `/orders/{order_id}/pickup-token`
* comportamento legado:

  * gera `manual_code` de 6 dígitos
  * sem TTL de 10 minutos consistente no novo modelo
  * invalida tokens anteriores

#### Expiração automática

* `expiry.py` definitivo já está rodando
* comportamento atual:

  * marca `Order = EXPIRED`
  * marca `Allocation = EXPIRED`
  * aplica `OUT_OF_STOCK`
  * executa `locker_release`

#### Ambiente DEV

* bypass auth habilitado no `order_pickup_service`
* fallback de preço para SKU desconhecido habilitado

---

# Estratégia de priorização

## Ordem oficial de implementação

1. **IV — order-id dinâmico no frontend**
2. **I — lista de pedidos online no dashboard**
3. **V — ambiente KIOSK de simulação**
4. **III — catálogo com fonte única**
5. **II — crédito 50%**

## Racional da ordem

Essa sequência foi escolhida para primeiro:

* remover travas artificiais do fluxo
* ganhar observabilidade operacional
* testar um segundo canal (KIOSK) em cima de uma base já enxergável
* consolidar catálogo depois que os fluxos estiverem claros
* deixar regra comercial/financeira por último

---

# FASE 1 — IV — Order-id dinâmico no frontend

## Objetivo

Eliminar qualquer uso de `order_id` hardcoded no frontend e fazer o fluxo trabalhar com o pedido real criado em tempo de execução.

## Resultado esperado

O frontend cria ou seleciona um pedido válido e usa esse mesmo `order_id` em todas as etapas seguintes:

* pagamento
* consulta de status
* geração de pickup
* exibição operacional

## Dependências

### Pré-requisitos

* endpoint de criação de pedido funcional
* endpoint de consulta de pedido funcional ou parcialmente funcional
* `POST /internal/orders/{order_id}/payment-confirm` operacional

### Dependências anteriores

* nenhuma

## Endpoints afetados

* endpoint de criação de pedido
* endpoint de leitura de pedido
* `POST /internal/orders/{order_id}/payment-confirm`
* eventual endpoint legado `/orders/{order_id}/pickup-token`
* eventual endpoint de status do pedido

## Tabelas / domínios afetados

* `orders`
* `allocations`
* `pickup_tokens` ou estrutura equivalente
* `order_items` se houver uso direto na UI

## Arquivos provavelmente afetados

### Frontend

* tela de compra online
* componentes que hoje carregam `order_id` fixo
* serviço HTTP / client API
* estado global/local do pedido atual
* tela de status do pedido / pickup

### Backend

* response model do endpoint de criação de pedido
* validação de `payment-confirm`
* serialização de dados mínimos do pedido

## Tarefas

* [ ] localizar todos os usos de `order_id` fixo no frontend
* [ ] substituir por `order_id` retornado pelo backend
* [ ] centralizar o pedido atual em estado único
* [ ] propagar `order_id` para pagamento
* [ ] propagar `order_id` para pickup
* [ ] propagar `order_id` para consulta de status
* [ ] exibir `order_id` atual em tela de debug operacional
* [ ] revisar comportamento em refresh/reload
* [ ] validar fluxo em `SP`
* [ ] validar fluxo em `PT`

## Critérios de aceite

* [ ] não existe mais `order_id` hardcoded no frontend
* [ ] um pedido recém-criado consegue ser pago usando seu próprio ID
* [ ] o pickup gerado corresponde ao pedido recém-criado
* [ ] o fluxo funciona em SP e PT
* [ ] logs de frontend/backend mostram o mesmo `order_id` ponta a ponta

## Status

**TODO**

---

# FASE 2 — I — Lista de pedidos online no dashboard

## Objetivo

Criar visibilidade operacional de pedidos online em tempo quase real, permitindo acompanhar o ciclo do pedido do início ao fim.

## Resultado esperado

Dashboard mostra pedidos online com estados coerentes, inclusive expiração automática e informações de alocação/pickup.

## Dependências

### Pré-requisitos

* Fase 1 concluída ou suficientemente estável

### Dependências técnicas

* endpoint de listagem agregada
* dados mínimos de `orders`, `allocations` e `pickup` acessíveis

## Endpoints afetados

### Novos

* `GET /dashboard/orders` ou equivalente

### Existentes possivelmente reutilizados

* `GET /orders`
* `GET /orders/{id}`

## Tabelas / domínios afetados

* `orders`
* `allocations`
* `pickup_tokens`
* `order_items` opcional
* tabela de eventos/logs opcional

## DTO mínimo recomendado

Cada linha deve devolver, idealmente já agregada:

* `order_id`
* `region`
* `channel`
* `status`
* `payment_status`
* `allocation_id`
* `allocation_state`
* `slot`
* `manual_code`
* `pickup_id`
* `created_at`
* `paid_at`
* `expires_at`
* `picked_up_at`

## Arquivos provavelmente afetados

### Backend

* router de dashboard
* service/query de listagem de pedidos
* schema/DTO de resposta

### Frontend

* página de dashboard operacional
* tabela de pedidos
* filtros por região/status/canal
* badges visuais de estado

## Tarefas

* [ ] definir contrato do DTO de dashboard
* [ ] implementar query agregada no backend
* [ ] criar endpoint de listagem com paginação simples
* [ ] adicionar filtros por `region`
* [ ] adicionar filtros por `status`
* [ ] adicionar filtros por `channel`
* [ ] montar tabela no dashboard
* [ ] aplicar badges visuais para estados críticos
* [ ] validar pedidos pagos
* [ ] validar pedidos com pickup gerado
* [ ] validar pedidos expirados após job automático

## Critérios de aceite

* [ ] dashboard exibe pedidos online reais
* [ ] pedidos pagos aparecem como pagos
* [ ] pedidos com pickup mostram `manual_code` / `pickup_id` quando aplicável
* [ ] pedidos expirados aparecem como expirados
* [ ] filtros por região e status funcionam
* [ ] não há divergência evidente entre dashboard e banco

## Status

**TODO**

---

# FASE 3 — V — Ambiente KIOSK de simulação

## Objetivo

Criar um ambiente controlado para simular o fluxo KIOSK de ponta a ponta, sem depender do fluxo online.

## Resultado esperado

O sistema consegue criar e concluir pedidos KIOSK simulados, incluindo pagamento, alocação, abertura de slot e retirada.

## Dependências

### Pré-requisitos

* Fase 1 concluída
* Fase 2 recomendada para visibilidade operacional

### Dependências técnicas

* `Order.channel` distinguindo `ONLINE` e `KIOSK`
* separação clara entre estados do fluxo online e do fluxo kiosk

## Endpoints afetados

### Novos ou adaptados

* `POST /kiosk/orders`
* `POST /kiosk/orders/{id}/pay`
* `POST /kiosk/orders/{id}/complete`
* eventual `POST /kiosk/orders/{id}/cancel`
* eventual `POST /kiosk/orders/{id}/timeout`

### Integração com endpoints já existentes

* `/locker/allocate`
* `/allocations/{id}/commit`
* `/allocations/{id}/release`
* `/slots/{slot}/open`

## Tabelas / domínios afetados

* `orders`
* `allocations`
* `payments` se existir
* `pickup_events` ou equivalente
* `kiosk_sessions` opcional

## Estados sugeridos para KIOSK

* `CREATED`
* `PAID`
* `DISPENSING`
* `READY_FOR_PICKUP`
* `PICKED_UP`
* `ABANDONED`
* `EXPIRED`

## Arquivos provavelmente afetados

### Backend

* model enum de `OrderChannel`
* model enum de `OrderStatus`
* routers / services de pedido kiosk
* integração com alocação e slot

### Frontend

* nova rota `/kiosk-sim`
* fluxo visual isolado do online
* ações de pagamento simulado e retirada

## Tarefas

* [ ] definir contrato funcional do KIOSK simulado
* [ ] revisar `Order.channel` e estados associados
* [ ] criar endpoint de criação de pedido KIOSK
* [ ] criar endpoint de pagamento simulado
* [ ] integrar alocação automática
* [ ] integrar abertura de slot
* [ ] criar rota `/kiosk-sim`
* [ ] permitir simular sucesso
* [ ] permitir simular falha
* [ ] permitir simular timeout / abandono
* [ ] exibir pedidos KIOSK no dashboard

## Critérios de aceite

* [ ] é possível criar pedido KIOSK independentemente do fluxo online
* [ ] pagamento simulado altera o status corretamente
* [ ] a alocação é feita corretamente
* [ ] o slot pode ser aberto no fluxo simulado
* [ ] retirada conclui o pedido
* [ ] timeout/abandono não deixa allocation presa
* [ ] dashboard diferencia `ONLINE` e `KIOSK`

## Status

**TODO**

---

# FASE 4 — III — Catálogo com fonte única

## Objetivo

Substituir a dependência operacional de `catalog.py` por uma única fonte de verdade para catálogo, preço, região, canal e idioma.

## Resultado esperado

Frontend, gateway e backends passam a consumir a mesma base lógica de catálogo.

## Decisão arquitetural recomendada

### Preferência

**Tabela no Postgres**

### Motivos

* melhor suporte a SP/PT
* melhor suporte a múltiplos canais
* preços distintos por contexto
* ativação/desativação sem deploy de código
* caminho mais sólido para operação futura

## Dependências

### Pré-requisitos

* Fases 1 e 2 estáveis
* Fase 3 recomendada para já pensar em catálogo por canal

## Endpoints afetados

### Novos

* `GET /catalog`
* `GET /catalog/{sku}` opcional

### Consultas recomendadas

* `GET /catalog?region=SP&channel=ONLINE&lang=pt-BR`
* `GET /catalog?region=PT&channel=KIOSK&lang=pt-PT`

## Tabelas / domínios afetados

### Opção MVP: tabela única

`catalog_items`

* `id`
* `sku`
* `name`
* `description`
* `region`
* `channel`
* `price_cents`
* `currency`
* `active`
* `sort_order`
* `image_url` opcional
* `created_at`
* `updated_at`

### Evolução futura

* separar item base
* separar preço por contexto
* separar localização/tradução por idioma

## Arquivos provavelmente afetados

### Backend

* migration de catálogo
* seed inicial
* service/repository de catálogo
* validação de SKU no gateway/backend

### Frontend

* tela/lista de produtos
* carregamento do catálogo por região/canal
* remoção de hardcode visual

## Tarefas

* [ ] definir modelo inicial do catálogo
* [ ] criar migration de `catalog_items`
* [ ] criar seed inicial SP/PT
* [ ] criar endpoint `/catalog`
* [ ] adaptar frontend para consumir `/catalog`
* [ ] adaptar gateway para validar SKU pela fonte única
* [ ] adaptar backend para validar SKU pela fonte única
* [ ] reduzir dependência de `catalog.py`
* [ ] revisar fallback de SKU desconhecido em DEV

## Critérios de aceite

* [ ] frontend carrega itens a partir da fonte única
* [ ] SP e PT podem ter catálogo/preço próprios
* [ ] ONLINE e KIOSK podem divergir sem hacks
* [ ] SKU inválido deixa de depender de fallback inseguro
* [ ] alteração de catálogo não exige alteração de frontend

## Status

**TODO**

---

# FASE 5 — II — Crédito 50%

## Objetivo

Implementar a regra comercial de crédito de 50% com rastreabilidade, previsibilidade e aplicação correta no checkout.

## Hipótese operacional usada neste roadmap

O crédito será tratado como saldo monetário rastreável, armazenado em carteira/ledger, aplicável em compra conforme regra definida pela operação.

## Dependências

### Pré-requisitos

* Fase 4 preferencialmente concluída
* fluxos de pedido e pagamento estáveis
* dashboard já mostrando pedidos com consistência

## Endpoints afetados

### Novos

* `POST /credits/grant`
* `GET /me/credits`
* `POST /checkout/apply-credit`
* `GET /credits/ledger`

## Tabelas / domínios afetados

### Proposta mínima

`credits_wallet`

* `id`
* `customer_id`
* `balance_cents`
* `updated_at`

`credits_ledger`

* `id`
* `wallet_id`
* `order_id` opcional
* `type` (`GRANT`, `RESERVE`, `CONSUME`, `REVERSE`, `EXPIRE`)
* `amount_cents`
* `reason`
* `created_at`

## Regras de negócio que precisam ser fechadas

* [ ] quando o crédito nasce
* [ ] sobre qual base ele é calculado
* [ ] se expira
* [ ] se pode ser usado parcialmente
* [ ] se pode combinar com desconto
* [ ] como reverte em cancelamento/estorno
* [ ] como aparece no dashboard

## Arquivos provavelmente afetados

### Backend

* migrations de wallet/ledger
* service de crédito
* integração com checkout/pagamento
* trilha de auditoria

### Frontend

* exibição de saldo
* aplicação do crédito no checkout
* exibição do abatimento

### Dashboard

* exibição de uso de crédito por pedido
* exibição de eventos relevantes do ledger

## Tarefas

* [ ] fechar definição mínima da regra de negócio
* [ ] criar migrations de wallet/ledger
* [ ] criar emissão manual/dev de crédito
* [ ] criar consulta de saldo
* [ ] integrar aplicação de crédito no checkout
* [ ] impedir saldo negativo
* [ ] registrar ledger de consumo/reversão
* [ ] refletir uso de crédito no dashboard
* [ ] testar cancelamento/reversão

## Critérios de aceite

* [ ] crédito pode ser emitido e consultado
* [ ] crédito pode ser aplicado sem gerar saldo negativo
* [ ] pedido registra o abatimento com clareza
* [ ] pagamento final reflete o desconto corretamente
* [ ] reversão funciona quando aplicável
* [ ] dashboard mostra uso de crédito de forma auditável

## Status

**TODO**

---

# Dependências consolidadas

## Ordem oficial

`IV → I → V → III → II`

## Leitura prática

* **IV** destrava o fluxo real
* **I** dá visibilidade operacional ao fluxo real
* **V** expande para outro canal sem perder controle
* **III** consolida base de catálogo em arquitetura sustentável
* **II** entra por último por envolver regra comercial/financeira

---

# Checklist executivo por sprint

## Sprint 1 — Fluxo real sem hardcode

* [ ] remover `order_id` fixo
* [ ] propagar pedido real para pagamento/pickup
* [ ] validar SP/PT

## Sprint 2 — Observabilidade

* [ ] endpoint de listagem
* [ ] tabela no dashboard
* [ ] filtros
* [ ] validação de expiração visível

## Sprint 3 — KIOSK simulado

* [ ] endpoints kiosk
* [ ] tela `/kiosk-sim`
* [ ] integração com alocação
* [ ] timeout/abandono

## Sprint 4 — Catálogo único

* [ ] migration + seed
* [ ] endpoint `/catalog`
* [ ] frontend consumindo catálogo
* [ ] descontinuação progressiva de `catalog.py`

## Sprint 5 — Crédito 50%

* [ ] wallet + ledger
* [ ] emissão
* [ ] consumo
* [ ] dashboard/auditoria

---

# Riscos principais

## 1. Mistura entre fluxo legado e novo

O endpoint legado `/orders/{order_id}/pickup-token` pode causar confusão se o frontend alternar entre os dois modelos.

### Mitigação

* definir explicitamente qual fluxo é oficial no frontend
* manter legado apenas como compatibilidade técnica temporária

## 2. Dashboard sem contrato agregado

Se o backend não devolver um DTO consolidado, o frontend acumula lógica de negócio indevida.

### Mitigação

* criar DTO específico de dashboard

## 3. KIOSK virar uma cópia improvisada do online

Isso cria dívida técnica rapidamente.

### Mitigação

* compartilhar base de domínio, mas separar estados e UX

## 4. Catálogo parcialmente centralizado

Se frontend usa um catálogo e gateway valida outro, haverá divergência operacional.

### Mitigação

* uma única fonte de leitura para todos os serviços

## 5. Crédito entrar antes da estabilidade

Regras financeiras adicionadas cedo demais tendem a multiplicar inconsistências.

### Mitigação

* manter crédito como última fase

---

# Definition of Done global desta etapa

A etapa será considerada bem-sucedida quando, em ambiente de desenvolvimento, o time conseguir executar o roteiro abaixo sem intervenção manual anômala:

* [ ] criar pedido online real
* [ ] pagar pedido com `order_id` dinâmico
* [ ] visualizar pedido no dashboard
* [ ] gerar pickup válido
* [ ] validar expiração automática quando aplicável
* [ ] confirmar refletividade correta dos estados
* [ ] criar pedido KIOSK simulado
* [ ] concluir fluxo KIOSK
* [ ] trocar catálogo sem editar frontend
* [ ] aplicar crédito com rastreabilidade

---

# Convenção de status

Usar estes status por fase e por subtarefa:

* `TODO`
* `DOING`
* `BLOCKED`
* `DONE`

Sugestão: atualizar este documento ao final de cada sprint e sempre que houver mudança relevante na arquitetura do fluxo.

---

# Próximo foco recomendado

Começar imediatamente por:

## Próxima execução

**FASE 1 — IV — Order-id dinâmico no frontend**

Esse item é o desbloqueio estrutural do restante do roadmap.

---

## Infraestrura para hospedar

Recomendado Oracle Cloud 

Configurar seu projeto Node+React+Python com Docker no Oracle Cloud Free Tier, aproveitando ao máximo os recursos gratuitos.

Visão Geral do Oracle Cloud Free Tier

Antes de começar, entenda o que você ganha gratuitamente :

Recurso	/ Especificação	/ Para o projeto

Instâncias AMD	/ 2 VMs (1/8 OCPU, 1 GB RAM cada)	/Backend SP + Backend PT

Instâncias ARM	/ Até 4 VMs (24 GB RAM total)	/ Payment Gateway + Order Pickup + Banco de dados

Armazenamento	/ 200 GB total	/ Banco de dados e volumes Docker

Banco de Dados	/ Oracle Autonomous DB (opcional)	/Alternativa ao PostgreSQL

Rede	/ 10 TB/mês de transferência	/ Tráfego dos usuários

Serviços	/ Load Balancer, Monitoring, etc. / 	Escalabilidade futura

---
## Objetivo da proteção - Evitar brute force no código manual do QRCode

Regra sugerida:
  - no máximo 5 tentativas inválidas
  - dentro de 2 minutos
  - depois bloquear por 5 minutos

Chave de bloqueio:
  - Como o endpoint não recebe totem_id, vamos usar uma chave simples por:
    region e, se disponível, o IP do cliente

---
## A proteção ficou forte demais para o seu fluxo de operação
Ela protege contra brute force, mas hoje está com granularidade muito ampla.

No estado atual, o sistema entende assim:

“Esse cliente/IP na região SP tentou códigos errados demais; então vou bloquear 
qualquer novo código por alguns minutos.”

Para segurança pura isso é aceitável.
Para operação real e testes, fica ruim.

Arquivo: 01_source/order_pickup_service/app/routers/pickup.py
Funcionalidade que foi alterada:
    def _manual_redeem_key(region: str, request: Request) -> str:
        return f"{region}:{_client_ip(request)}"
Nova funcionalidade:
    def _manual_redeem_key(region: str, manual_code: str, request: Request) -> str:
        return f"{region}:{manual_code}:{_client_ip(request)}"
Resultado esperado dessa mudança:
    Se você:
      - errar um código manual específico várias vezes, ele será bloqueado
      - mas um novo pedido com novo código continuará utilizável
Isso fica muito mais compatível com o seu caso de uso.

Observação de segurança: 
    Mesmo assim, um atacante ainda poderia tentar vários códigos diferentes.

    Então a evolução ideal depois seria uma combinação de:
      - limite por manual_code + IP
      - e um limite mais amplo, mais brando, por region + IP

    Exemplo:
      - 5 tentativas no mesmo código → bloqueia aquele código/IP
      - 30 tentativas totais em 10 min → bloqueia o IP/região

    Mas eu não faria isso agora.
    Agora só o ajuste da chave, para não atrapalhar a operação.


# 08/03/2026
# STATUS ATUAL — FASE 1 e FASE 2

## FASE 1 — IV — Order-id dinâmico no frontend

### Status geral
**PARCIALMENTE CONCLUÍDA**

### O que já foi concluído
- `order_id` do pedido atual passou a vir do backend na criação do pedido
- o frontend do dashboard mantém um **pedido atual** em estado único (`currentOrder`)
- o pagamento usa o `order_id` real em:
  - `POST /internal/orders/{order_id}/payment-confirm`
- o dashboard exibe `order_id` no bloco operacional de pedido atual
- a lista/tabela de pedidos permite selecionar um pedido real e carregá-lo como pedido atual
- o fluxo principal do dashboard deixou de depender de `order_id` fixo

### O que está parcial
- pickup:
  - o fluxo está melhor e usa dados do pedido atual
  - mas ainda falta comprovação final de coerência ponta a ponta entre `order_id`, `pickup_id` e geração de pickup
- consulta de status:
  - existe acompanhamento pelo dashboard/lista
  - mas não foi formalizado um fluxo dedicado de leitura por `GET /orders/{id}` no frontend
- remoção total de `order_id` hardcoded:
  - no dashboard principal, sim
  - no frontend inteiro, ainda não foi feita varredura completa

### O que ainda falta
- revisar comportamento em refresh/reload
- validar fluxo completo em `SP`
- validar fluxo completo em `PT`
- confirmar por logs frontend/backend o mesmo `order_id` ponta a ponta
- varrer o restante do frontend em busca de qualquer `order_id` fixo remanescente

### Checklist consolidado
- [~] localizar todos os usos de `order_id` fixo no frontend
- [x] substituir por `order_id` retornado pelo backend no fluxo principal
- [x] centralizar o pedido atual em estado único
- [x] propagar `order_id` para pagamento
- [~] propagar `order_id` para pickup
- [~] propagar `order_id` para consulta de status
- [x] exibir `order_id` atual em tela de debug operacional
- [ ] revisar comportamento em refresh/reload
- [ ] validar fluxo em `SP`
- [ ] validar fluxo em `PT`

### Critérios de aceite — situação atual
- [~] não existe mais `order_id` hardcoded no frontend
- [x] um pedido recém-criado consegue ser pago usando seu próprio ID
- [~] o pickup gerado corresponde ao pedido recém-criado
- [ ] o fluxo funciona em SP e PT
- [ ] logs de frontend/backend mostram o mesmo `order_id` ponta a ponta

### Próximos passos para fechar a Fase 1
1. varrer o frontend inteiro por `order_id` hardcoded
2. testar fluxo completo em `SP`
3. testar fluxo completo em `PT`
4. validar refresh/reload
5. confirmar rastreabilidade por logs ponta a ponta

---

## FASE 2 — I — Lista de pedidos online no dashboard

### Status geral
**PARCIALMENTE CONCLUÍDA — AVANÇADA**

### O que já foi concluído
- existe listagem real de pedidos no dashboard
- há filtro por:
  - `region`
  - `status`
- o dashboard já mostra campos operacionais relevantes:
  - `order_id`
  - `region`
  - `channel`
  - `status`
  - `allocation_id`
  - `allocation_state`
  - `slot`
  - `amount_cents`
  - `payment_method`
  - `created_at`
  - `paid_at`
  - `pickup_deadline_at`
  - `picked_up_at`
- existem badges visuais para estados críticos
- o bloco `Pedidos online` já está operacional
- existe botão `Mostrar/Ocultar`
- o dashboard segue a decisão de UX de **não usar polling automático para pedidos**

### O que está parcial
- paginação:
  - houve tentativa de migrar para paginação real no backend
  - no momento a paginação **não está estável/validada**
- filtro por `channel`:
  - o backend aceita
  - o frontend ainda não expõe esse filtro de forma consolidada
- validação de pedidos pagos:
  - o status aparece
  - falta fechamento formal de testes operacionais

### O que ainda falta
- corrigir e validar a paginação real
- decidir e implementar no DTO de listagem, se necessário:
  - `manual_code`
  - `pickup_id`
  - `payment_status` separado ou não
- validar pedidos com pickup gerado
- validar pedidos expirados após job automático
- comparar dashboard x banco para verificar coerência
- definir se o endpoint continuará sendo `GET /orders` ou se haverá `GET /dashboard/orders` dedicado

### Checklist consolidado
- [~] definir contrato final do DTO de dashboard
- [x] implementar query/listagem agregada equivalente
- [~] criar endpoint de listagem com paginação simples
- [x] adicionar filtros por `region`
- [x] adicionar filtros por `status`
- [~] adicionar filtros por `channel`
- [x] montar tabela no dashboard
- [x] aplicar badges visuais para estados críticos
- [~] validar pedidos pagos
- [ ] validar pedidos com pickup gerado
- [ ] validar pedidos expirados após job automático

### Critérios de aceite — situação atual
- [x] dashboard exibe pedidos online reais
- [x] pedidos pagos aparecem como pagos
- [ ] pedidos com pickup mostram `manual_code` / `pickup_id` quando aplicável
- [ ] pedidos expirados aparecem como expirados
- [x] filtros por região e status funcionam
- [ ] não há divergência evidente entre dashboard e banco

### Próximos passos para fechar a Fase 2
1. estabilizar paginação real backend + frontend
2. decidir contrato final do DTO de pedidos online
3. incluir `manual_code` e `pickup_id` na listagem, se mantido como requisito operacional
4. validar expirados após job automático
5. validar coerência dashboard x banco
6. opcionalmente expor filtro por `channel` no frontend

---

## RESUMO EXECUTIVO

### FASE 1 — IV
**Parcialmente concluída**
- fluxo principal com `order_id` dinâmico no dashboard: **sim**
- cobertura total do frontend + validação final: **não**

### FASE 2 — I
**Parcialmente concluída e avançada**
- lista operacional real: **sim**
- paginação estável de ponta a ponta: **não**
- pickup info completa na listagem (`manual_code` / `pickup_id`): **não**
- validação de expirados: **não**

---

## PRÓXIMA PRIORIDADE RECOMENDADA
1. corrigir a paginação real
2. fechar o contrato final do DTO da lista de pedidos
3. validar pickup e expiração
4. só então marcar Fase 2 como concluída
5. depois fazer a varredura final da Fase 1 no frontend inteiro


# 09/03/2026

# CHECKLIST EXECUTIVO — ELLAN Lab Locker
**Data de referência:** 09/03/2026  
**Objetivo:** consolidar o estado atual, fechar as pendências críticas e orientar a sequência de execução sem reabrir decisões já tomadas.

---

# 1. RESUMO EXECUTIVO

## Situação geral
O projeto avançou de forma consistente em três eixos principais:

1. **`order_id` dinâmico no frontend**
2. **lista real de pedidos online no dashboard**
3. **novo domínio real de `Pickup`**

O fluxo principal deixou de depender do MVP simplificado e já opera com entidades reais:

- `Order`
- `Allocation`
- `Pickup`
- `PickupToken`

Hoje já foi validado, em uso real, que:
- o pedido é criado com `order_id` real
- o pagamento usa `order_id` real
- o `pickup_id` é separado de `order_id`
- a listagem do dashboard exibe pedidos reais
- o gateway respeita a moeda correta por região:
  - `PT -> EUR`
  - `SP -> BRL`

---

# 2. STATUS EXECUTIVO POR FRENTE

## 2.1 FASE 1 — IV — `order_id` dinâmico no frontend
**Status:** **QUASE CONCLUÍDA**

### Já concluído
- [x] `order_id` do pedido atual vem do backend
- [x] `currentOrder` centralizado no dashboard
- [x] pagamento usa `POST /internal/orders/{order_id}/payment-confirm`
- [x] dashboard exibe `order_id` real
- [x] seleção de pedido real na listagem
- [x] fluxo principal deixou de depender de `order_id` fixo
- [x] valor do pedido atual ficou congelado corretamente após criação
- [x] horário por região corrigido
- [x] moeda por região corrigida no gateway

### Ainda falta
- [ ] varrer o frontend inteiro em busca de `order_id` hardcoded remanescente
- [ ] validar refresh/reload do dashboard
- [ ] validar formalmente o fluxo em `SP`
- [ ] consolidar rastreabilidade por logs ponta a ponta

### Critério de aceite para fechar
- [ ] não existe mais `order_id` hardcoded no frontend
- [ ] fluxo funciona em `PT`
- [ ] fluxo funciona em `SP`
- [ ] logs frontend/backend mostram o mesmo `order_id` ponta a ponta
- [ ] refresh/reload não quebra o pedido atual

---

## 2.2 FASE 2 — I — Lista de pedidos online no dashboard
**Status:** **QUASE CONCLUÍDA**

### Já concluído
- [x] listagem real de pedidos no dashboard
- [x] filtros por `region`
- [x] filtros por `status`
- [x] exibição de campos operacionais essenciais
- [x] bloco `Pedidos online` operacional
- [x] paginação visual validada
- [x] `pickup_id` aparece na listagem
- [x] `expires_at` aparece na listagem
- [x] `picked_up_at` aparece na listagem
- [x] dashboard operacional sem polling automático para pedidos
- [x] cards em tela menor
- [x] pedido atual destacado por status

### Ainda falta
- [ ] decidir se `manual_code` deve aparecer na listagem
- [ ] validar pedidos expirados após job automático
- [ ] validar coerência dashboard x banco
- [ ] decidir se o endpoint seguirá como `GET /orders` ou se haverá endpoint dedicado no futuro
- [ ] opcionalmente expor filtro por `channel` no frontend

### Critério de aceite para fechar
- [ ] pedidos expirados aparecem corretamente no dashboard
- [ ] não há divergência evidente entre dashboard e banco
- [ ] pedidos com pickup mostram os campos esperados
- [ ] paginação segue estável em uso real

---

## 2.3 Domínio real de `Pickup`
**Status:** **IMPLANTADO E PARCIALMENTE VALIDADO**

### Já concluído
- [x] model `Pickup` criado
- [x] `PickupToken` migrado para `pickup_id`
- [x] separação real entre:
  - [x] `order.id`
  - [x] `pickup.id`
  - [x] `allocation.id`
- [x] `internal.py` ajustado
- [x] `pickup.py` ajustado
- [x] `orders.py` ajustado
- [x] `expiry.py` ajustado
- [x] `order_pickup_service` sobe normalmente
- [x] pagamento já retorna `pickup_id` real
- [x] expiração já foi integrada a `Pickup.status`

### Ainda falta validar formalmente
- [ ] pagamento -> pickup ativo
- [ ] QR gerado com `pickup_id` real
- [ ] regeneração de código manual com `current_token_id` correto
- [ ] retirada por QR
- [ ] retirada por código manual
- [ ] estados finais coerentes após retirada
- [ ] estados coerentes após expiração automática
- [ ] estados coerentes após release manual/interno

### Critério de aceite para fechar
- [ ] `order.id != pickup.id`
- [ ] `pickup.status = ACTIVE` após pagamento
- [ ] `pickup.status = REDEEMED` após retirada
- [ ] `order.status = PICKED_UP` após retirada
- [ ] `allocation.state = PICKED_UP` após retirada
- [ ] `order.status = EXPIRED` após expiração
- [ ] `pickup.status = EXPIRED` após expiração
- [ ] `allocation.state = EXPIRED` após expiração
- [ ] `pickup.status = CANCELLED` após release interno
- [ ] `allocation.state = RELEASED` após release interno

---

# 3. PRINCIPAIS PROBLEMAS JÁ IDENTIFICADOS

## 3.1 Pedido `PAYMENT_PENDING` envelhecido
### Situação
Um pedido antigo pode:
- falhar no `locker_commit`
- cair em `reallocate`
- falhar novamente no `locker_allocate`

### Status
- [x] backend ajustado para devolver erro operacional estruturado
- [ ] frontend ainda precisa tratar isso melhor

### Próxima ação
- [ ] ajustar o dashboard para limpar `currentOrder` quando vier:
  - `REALLOCATE_CONFLICT`
  - `LOCKER_COMMIT_FAILED`
  - `COMMIT_AFTER_REALLOCATE_FAILED`

---

## 3.2 Estados antigos ainda inconsistentes
### Situação
Há registros antigos com combinação como:
- `order.status = PICKED_UP`
- `pickup.status = REDEEMED`
- `allocation_state = OPENED_FOR_PICKUP`

### Possíveis causas
- dados antigos
- serviço sem restart após patch
- fluxo antigo executado antes das correções

### Próxima ação
- [ ] validar com pedidos novos criados após os patches
- [ ] não usar registros antigos como referência final de aceite

---

## 3.3 Frontend ainda precisa hardening operacional
### Ainda falta
- [ ] tratar falhas de pagamento com reserva expirada
- [ ] orientar operador a criar novo pedido
- [ ] limpar estado local quando o pedido se torna inviável
- [ ] revisar comportamento em refresh/reload

---

# 4. PRIORIDADES EXECUTIVAS

## PRIORIDADE 1 — Fechar a validação ponta a ponta do domínio `Pickup`
### Objetivo
Transformar “funciona parcialmente” em “formalmente aceito”.

### Checklist
- [ ] criar pedido ONLINE novo em `PT`
- [ ] pagar imediatamente
- [ ] confirmar `order_id != pickup_id`
- [ ] gerar QR
- [ ] regenerar código manual
- [ ] retirar por QR ou manual
- [ ] confirmar estados finais
- [ ] repetir a mesma validação em `SP`

---

## PRIORIDADE 2 — Endurecer tratamento de erro no frontend
### Objetivo
Evitar que o operador continue tentando pagar pedido inviável.

### Checklist
- [ ] tratar `REALLOCATE_CONFLICT`
- [ ] tratar `LOCKER_COMMIT_FAILED`
- [ ] tratar `COMMIT_AFTER_REALLOCATE_FAILED`
- [ ] limpar `currentOrder`
- [ ] exibir mensagem operacional objetiva
- [ ] orientar criação de novo pedido/gaveta

---

## PRIORIDADE 3 — Validar expiração automática
### Objetivo
Confirmar coerência entre `Order`, `Pickup`, `Allocation` e dashboard.

### Checklist
- [ ] criar pedido ONLINE
- [ ] pagar
- [ ] forçar expiração / rodar job
- [ ] validar:
  - [ ] `order.status = EXPIRED`
  - [ ] `pickup.status = EXPIRED`
  - [ ] `allocation.state = EXPIRED`
- [ ] validar reflexo no dashboard

---

## PRIORIDADE 4 — Repetir a rodada completa em `SP`
### Objetivo
Garantir que o fluxo não ficou validado só em `PT`.

### Checklist
- [ ] criar pedido em `SP`
- [ ] pagar em `SP`
- [ ] validar moeda `BRL`
- [ ] validar horário/região
- [ ] validar pickup real
- [ ] validar retirada
- [ ] validar listagem
- [ ] validar expiração

---

## PRIORIDADE 5 — Varredura final do frontend
### Objetivo
Eliminar acoplamentos antigos do MVP.

### Checklist
- [ ] procurar `order_id` hardcoded
- [ ] procurar `currency` indevida no payload
- [ ] revisar fluxos ainda dependentes de estado antigo
- [ ] revisar refresh/reload
- [ ] revisar mensagens operacionais de erro

---

# 5. ORDEM RECOMENDADA DE EXECUÇÃO

## Etapa 1
- [ ] validar um fluxo completo novo em `PT` até retirada final

## Etapa 2
- [ ] validar expiração automática em `PT`

## Etapa 3
- [ ] ajustar `LockerDashboard.jsx` para erros de reserva stale / reallocate

## Etapa 4
- [ ] repetir todos os testes em `SP`

## Etapa 5
- [ ] fazer varredura final de hardcodes e dependências antigas no frontend

## Etapa 6
- [ ] consolidar aceite formal da Fase 1
- [ ] consolidar aceite formal da Fase 2
- [ ] consolidar aceite formal do domínio `Pickup`

---

# 6. CHECKLIST DE ACEITE FINAL

## Pedido / pagamento
- [ ] pedido é criado com `order_id` real
- [ ] pagamento usa `order_id` real
- [ ] pedido pago vira `PAID_PENDING_PICKUP`

## Pickup
- [ ] `pickup_id` é criado após pagamento
- [ ] `pickup_id` é diferente de `order_id`
- [ ] `pickup.current_token_id` é atualizado corretamente
- [ ] QR usa `pickup_id` real

## Retirada
- [ ] retirada manual funciona
- [ ] retirada por QR funciona
- [ ] `pickup.status = REDEEMED`
- [ ] `order.status = PICKED_UP`
- [ ] `allocation.state = PICKED_UP`

## Expiração
- [ ] job automático expira pedidos corretamente
- [ ] `order.status = EXPIRED`
- [ ] `pickup.status = EXPIRED`
- [ ] `allocation.state = EXPIRED`

## Release
- [ ] release interno funciona
- [ ] `pickup.status = CANCELLED`
- [ ] `allocation.state = RELEASED`

## Dashboard
- [ ] lista mostra pedidos reais
- [ ] paginação estável
- [ ] `pickup_id` aparece corretamente
- [ ] `expires_at` aparece corretamente
- [ ] `picked_up_at` aparece corretamente
- [ ] dashboard não diverge do banco

## Região / moeda / horário
- [ ] `PT -> EUR`
- [ ] `SP -> BRL`
- [ ] horário renderizado conforme a região
- [ ] backend e frontend coerentes em PT e SP

---

# 7. DECISÃO EXECUTIVA

## Fase 1 — `order_id` dinâmico
**Situação:** pode caminhar para encerramento após validações finais.

## Fase 2 — lista de pedidos online
**Situação:** pode caminhar para encerramento após validação de expirados e coerência com banco.

## Domínio real de `Pickup`
**Situação:** arquitetura correta aprovada; falta fechamento operacional completo.

---

# 8. CONCLUSÃO

O projeto já saiu do estágio de MVP travado em simplificações perigosas e entrou em um estágio operacional mais realista.

A arquitetura central agora está correta:
- pedido real
- pickup real
- allocation real
- token real

O foco neste momento **não é redesenhar arquitetura**.  
O foco é:

- [ ] fechar validação ponta a ponta
- [ ] endurecer o frontend para erro operacional
- [ ] repetir a rodada em `SP`
- [ ] consolidar aceite final

---


# 09/03/2026 17:30

# 2. STATUS EXECUTIVO POR FRENTE

## 2.1 FASE 1 — IV — `order_id` dinâmico no frontend
**Status:** **OPERACIONAL / EM FECHAMENTO**

### Concluído
- [x] `order_id` do pedido atual vem do backend
- [x] `currentOrder` centralizado no dashboard
- [x] pagamento usa `POST /internal/orders/{order_id}/payment-confirm`
- [x] dashboard exibe `order_id` real
- [x] seleção de pedido real na listagem
- [x] fluxo principal deixou de depender de `order_id` fixo
- [x] valor do pedido atual ficou congelado corretamente após criação
- [x] horário por região corrigido
- [x] moeda por região corrigida no gateway
- [x] fluxo principal validado em ambiente limpo de teste
- [x] tratamento operacional básico para pedido inviável no dashboard

### Pendências de fechamento
- [ ] varrer o frontend inteiro em busca de `order_id` hardcoded remanescente
- [ ] validar refresh/reload do dashboard
- [ ] consolidar rastreabilidade por logs ponta a ponta
- [ ] registrar aceite formal em `PT`
- [ ] registrar aceite formal em `SP`

### Critério de aceite para encerrar
- [ ] não existe mais `order_id` hardcoded no frontend
- [x] fluxo principal funciona em ambiente validado
- [ ] fluxo formalmente evidenciado em `PT`
- [ ] fluxo formalmente evidenciado em `SP`
- [ ] logs frontend/backend mostram o mesmo `order_id` ponta a ponta
- [ ] refresh/reload não quebra o pedido atual

---

## 2.2 FASE 2 — I — Lista de pedidos online no dashboard
**Status:** **OPERACIONAL / EM FECHAMENTO**

### Concluído
- [x] listagem real de pedidos no dashboard
- [x] filtros por `region`
- [x] filtros por `status`
- [x] exibição de campos operacionais essenciais
- [x] bloco `Pedidos online` operacional
- [x] paginação visual validada
- [x] `pickup_id` aparece na listagem
- [x] `expires_at` aparece na listagem
- [x] `picked_up_at` aparece na listagem
- [x] dashboard operacional sem polling automático para pedidos
- [x] cards em tela menor
- [x] pedido atual destacado por status
- [x] badges visuais de `pickup_status` e `allocation_state`
- [x] destaque visual para pedidos expirados e retirados
- [x] resumo operacional acima do JSON bruto

### Pendências de fechamento
- [ ] decidir se `manual_code` deve aparecer na listagem
- [ ] validar formalmente pedidos expirados após job automático
- [ ] validar coerência dashboard x banco em cenários de expiração e retirada
- [ ] decidir se o endpoint seguirá como `GET /orders` ou se haverá endpoint dedicado no futuro
- [ ] opcionalmente expor filtro por `channel` no frontend

### Critério de aceite para encerrar
- [ ] pedidos expirados aparecem corretamente no dashboard
- [ ] não há divergência evidente entre dashboard e banco
- [x] pedidos com pickup mostram os campos essenciais esperados
- [x] paginação segue estável no fluxo validado
- [ ] paginação segue estável em uso real prolongado

---

## 2.3 Domínio real de `Pickup`
**Status:** **IMPLANTADO E VALIDADO OPERACIONALMENTE**

### Concluído
- [x] model `Pickup` criado
- [x] `PickupToken` migrado para `pickup_id`
- [x] separação real entre:
  - [x] `order.id`
  - [x] `pickup.id`
  - [x] `allocation.id`
- [x] `internal.py` ajustado
- [x] `pickup.py` ajustado
- [x] `orders.py` ajustado
- [x] `expiry.py` ajustado
- [x] `order_pickup_service` sobe normalmente
- [x] pagamento já retorna `pickup_id` real
- [x] expiração já foi integrada a `Pickup.status`
- [x] QR opera com `pickup_id` real
- [x] regeneração manual respeita `current_token_id`
- [x] fluxo ponta a ponta validado em ambiente resetado

### Fechamento formal ainda desejável
- [ ] registrar evidência formal de:
  - [ ] pagamento -> pickup ativo
  - [ ] QR gerado com `pickup_id` real
  - [ ] regeneração de código manual com `current_token_id` correto
  - [ ] retirada por QR
  - [ ] retirada por código manual
  - [ ] estados finais coerentes após retirada
  - [ ] estados coerentes após expiração automática
  - [ ] estados coerentes após release manual/interno

### Critério de aceite para encerrar
- [x] `order.id != pickup.id`
- [x] `pickup.status = ACTIVE` após pagamento
- [x] `pickup.status = REDEEMED` após retirada
- [x] `order.status = PICKED_UP` após retirada
- [x] `allocation.state = PICKED_UP` após retirada
- [x] `order.status = EXPIRED` após expiração
- [x] `pickup.status = EXPIRED` após expiração
- [x] `allocation.state = EXPIRED` após expiração
- [x] `pickup.status = CANCELLED` após release interno
- [x] `allocation.state = RELEASED` após release interno

---

# 3. PRINCIPAIS PROBLEMAS IDENTIFICADOS E ESTADO ATUAL

## 3.1 Pedido `PAYMENT_PENDING` envelhecido
### Situação
Um pedido antigo pode:
- falhar no `locker_commit`
- cair em `reallocate`
- falhar novamente no `locker_allocate`

### Estado atual
- [x] backend ajustado para devolver erro operacional estruturado
- [x] frontend endurecido para tratar erro operacional principal
- [x] dashboard limpa `currentOrder` quando o pedido fica inviável

### Tipos já tratados
- [x] `REALLOCATE_CONFLICT`
- [x] `LOCKER_COMMIT_FAILED`
- [x] `COMMIT_AFTER_REALLOCATE_FAILED`

### Próxima ação
- [ ] revisar UX final dessas mensagens em uso prolongado
- [ ] validar refresh/reload após falha operacional

---

## 3.2 Registros antigos inconsistentes
### Situação
Havia registros antigos com combinação como:
- `order.status = PICKED_UP`
- `pickup.status = REDEEMED`
- `allocation_state = OPENED_FOR_PICKUP`

### Leitura atual
- [x] tratado como legado de testes anteriores / estados antigos
- [x] ambiente foi resetado para validação limpa
- [x] não usar registros antigos como referência de aceite final

### Próxima ação
- [ ] manter validações futuras sempre em ambiente limpo ou claramente controlado

---

## 3.3 Frontend operacional
### Situação anterior
Faltava hardening para:
- reserva expirada
- pedido stale
- leitura visual rápida de estados

### Estado atual
- [x] falhas operacionais principais tratadas
- [x] operador orientado a criar novo pedido quando necessário
- [x] estado local é limpo quando o pedido se torna inviável
- [x] dashboard mais operacional e menos “debug raw”

### Ainda falta
- [ ] revisar comportamento em refresh/reload
- [ ] varredura final do frontend por acoplamentos antigos

---

# 4. PRIORIDADES EXECUTIVAS

## PRIORIDADE 1 — Fechamento formal de aceite
### Objetivo
Transformar o que já está operacional em aceite documentado.

### Checklist
- [ ] registrar evidência final de fluxo em `PT`
- [ ] registrar evidência final de fluxo em `SP`
- [ ] consolidar checklist de aceite da Fase 1
- [ ] consolidar checklist de aceite da Fase 2
- [ ] consolidar checklist de aceite do domínio `Pickup`

---

## PRIORIDADE 2 — Validar expiração automática no dashboard
### Objetivo
Confirmar coerência entre `Order`, `Pickup`, `Allocation` e UI.

### Checklist
- [ ] criar pedido ONLINE
- [ ] pagar
- [ ] forçar expiração / rodar job
- [ ] validar:
  - [ ] `order.status = EXPIRED`
  - [ ] `pickup.status = EXPIRED`
  - [ ] `allocation.state = EXPIRED`
- [ ] validar reflexo visual no dashboard

---

## PRIORIDADE 3 — Fechamento de comportamento de refresh/reload
### Objetivo
Garantir robustez do painel no uso real.

### Checklist
- [ ] validar reload com pedido `PAYMENT_PENDING`
- [ ] validar reload com pedido `PAID_PENDING_PICKUP`
- [ ] validar reload com pedido `PICKED_UP`
- [ ] validar reload com pedido `EXPIRED`
- [ ] confirmar recomposição correta de `currentOrder`

---

## PRIORIDADE 4 — Varredura final do frontend
### Objetivo
Eliminar resíduos do MVP e fechar a camada principal de operação.

### Checklist
- [ ] procurar `order_id` hardcoded
- [ ] procurar `currency` indevida no payload
- [ ] revisar fluxos ainda dependentes de estado antigo
- [ ] revisar mensagens operacionais finais
- [ ] revisar pontos fora do `LockerDashboard.jsx`

---

## PRIORIDADE 5 — Preparar próxima frente de produto
### Objetivo
Com a base estável, avançar para o backlog de negócio.

### Candidatos naturais
- [ ] crédito 50%
- [ ] catálogo real de bolos
- [ ] KIOSK simulado
- [ ] ajustes operacionais complementares

---

# 5. ORDEM RECOMENDADA DE EXECUÇÃO

## Etapa 1
- [ ] validar e registrar evidência formal de fluxo completo em `PT`

## Etapa 2
- [ ] validar e registrar evidência formal de fluxo completo em `SP`

## Etapa 3
- [ ] validar expiração automática refletindo corretamente no dashboard

## Etapa 4
- [ ] validar refresh/reload do dashboard em estados críticos

## Etapa 5
- [ ] fazer varredura final de hardcodes e dependências antigas no frontend

## Etapa 6
- [ ] consolidar aceite formal da Fase 1
- [ ] consolidar aceite formal da Fase 2
- [ ] consolidar aceite formal do domínio `Pickup`

## Etapa 7
- [ ] iniciar a próxima frente de produto sobre base já estabilizada

---

# 6. CHECKLIST DE ACEITE FINAL

## Pedido / pagamento
- [x] pedido é criado com `order_id` real
- [x] pagamento usa `order_id` real
- [x] pedido pago vira `PAID_PENDING_PICKUP`

## Pickup
- [x] `pickup_id` é criado após pagamento
- [x] `pickup_id` é diferente de `order_id`
- [x] `pickup.current_token_id` é atualizado corretamente
- [x] QR usa `pickup_id` real

## Retirada
- [x] retirada manual funciona
- [x] retirada por QR funciona
- [x] `pickup.status = REDEEMED`
- [x] `order.status = PICKED_UP`
- [x] `allocation.state = PICKED_UP`

## Expiração
- [x] job automático expira pedidos corretamente
- [x] `order.status = EXPIRED`
- [x] `pickup.status = EXPIRED`
- [x] `allocation.state = EXPIRED`

## Release
- [x] release interno funciona
- [x] `pickup.status = CANCELLED`
- [x] `allocation.state = RELEASED`

## Dashboard
- [x] lista mostra pedidos reais
- [x] paginação estável no fluxo validado
- [x] `pickup_id` aparece corretamente
- [x] `expires_at` aparece corretamente
- [x] `picked_up_at` aparece corretamente
- [ ] dashboard não diverge do banco em todos os cenários finais documentados

## Região / moeda / horário
- [x] `PT -> EUR`
- [x] `SP -> BRL`
- [x] horário renderizado conforme a região
- [ ] backend e frontend formalmente evidenciados em PT e SP

---

# 7. DECISÃO EXECUTIVA

## Fase 1 — `order_id` dinâmico
**Situação:** operacionalmente resolvida; falta fechamento formal.

## Fase 2 — lista de pedidos online
**Situação:** operacionalmente resolvida; falta fechamento de bordas e aceite formal.

## Domínio real de `Pickup`
**Situação:** arquitetura aprovada e fluxo validado; falta apenas consolidação documental.

---

# 8. CONCLUSÃO

O projeto já saiu do estágio de MVP com simplificações perigosas e entrou em um estágio operacional real.

A arquitetura central está correta:
- pedido real
- pickup real
- allocation real
- token real

O foco agora **não é redesenhar arquitetura**.  
O foco é:

- [ ] fechar aceite formal
- [ ] validar expiração visual no dashboard
- [ ] validar refresh/reload
- [ ] fazer a varredura final do frontend
- [ ] preparar a próxima frente de produto

---

# 09/03/2026 - 17:50

# FASE 3 — V — AMBIENTE KIOSK DE SIMULAÇÃO
**Objetivo:** permitir simular a compra no kiosk do início ao fim, com fluxo próprio, estados coerentes e ambiente repetível de teste.

---

# 1. OBJETIVO EXECUTIVO

Criar um ambiente de simulação KIOSK que permita validar, de forma controlada:

- seleção de produto
- seleção/alocação de gaveta
- pagamento kiosk
- confirmação interna
- abertura/liberação da gaveta
- estados finais do pedido kiosk

Sem depender do fluxo online e sem hacks manuais.

---

# 2. RESULTADO ESPERADO AO FINAL DA FASE

Ao final desta fase, deve ser possível:

1. abrir uma interface/página de simulação kiosk
2. escolher região
3. escolher produto/SKU
4. escolher gaveta ou deixar alocação automática
5. pagar no modo kiosk
6. confirmar o pagamento no backend
7. abrir/liberar a gaveta corretamente
8. ver o pedido kiosk refletido com estados coerentes
9. repetir o teste quantas vezes quiser em ambiente limpo

---

# 3. ESCOPO DA FASE

## Entra nesta fase
- fluxo de pedido KIOSK
- fluxo de pagamento KIOSK
- tela/ambiente de simulação KIOSK
- integração com alocação de gaveta
- coerência de estados para `OrderChannel.KIOSK`
- validação em `PT` e `SP`

## Não entra nesta fase
- catálogo final com fonte única
- crédito 50%
- refinamento avançado de analytics
- UX final de produção do kiosk
- integrações de recibo completas, salvo o mínimo necessário

---

# 4. PREMISSAS JÁ EXISTENTES

A base já validada e disponível:
- `order_pickup_service` funcional
- `payment_gateway` funcional
- `Pickup` real já implantado para fluxo online
- dashboard operacional funcionando
- reset DEV consolidado
- erro operacional de pedido stale já tratado no dashboard principal

---

# 5. VISÃO DE DOMÍNIO DO FLUXO KIOSK

## Diferença central para ONLINE
### ONLINE
- pedido é pago
- fica aguardando retirada
- gera `Pickup`
- usa QR / código manual
- retirada posterior

### KIOSK
- pedido é criado e pago no próprio terminal
- não precisa gerar `Pickup` para retirada futura
- após confirmação de pagamento, a gaveta pode ser aberta/liberada no mesmo fluxo
- o pedido tende a terminar mais perto de “dispensado/retirado no ato”

## Consequência prática
O fluxo KIOSK precisa ser validado como fluxo próprio, e não “adaptação improvisada do online”.

---

# 6. SUBETAPAS TÉCNICAS

# 6.1 SUBETAPA A — Mapeamento do fluxo KIOSK atual
## Objetivo
Descobrir exatamente o que já existe e o que está incompleto.

## Validar
- como o backend cria pedido KIOSK hoje
- se já há `OrderChannel.KIOSK` funcional
- como `payment-confirm` trata kiosk
- quais estados finais hoje são usados no kiosk
- se existe frontend/tela kiosk já iniciada

## Arquivos prioritários para leitura
- `01_source/order_pickup_service/app/models/order.py`
- `01_source/order_pickup_service/app/routers/orders.py`
- `01_source/order_pickup_service/app/routers/internal.py`
- frontend atual que simula pagamento kiosk, se existir
- qualquer `App.jsx` ou página antiga usada para simulação

## Entrega esperada
- mapa “estado atual vs estado desejado”
- lista de gaps reais

---

# 6.2 SUBETAPA B — Definir contrato do pedido KIOSK
## Objetivo
Fechar o payload mínimo do kiosk.

## Decidir
- kiosk escolhe `region`
- kiosk escolhe `sku_id`
- kiosk usa `totem_id`
- kiosk permite `desired_slot` ou deixa automático?
- kiosk coleta:
  - nada
  - telefone
  - e-mail
  - consentimento
- valor vem de onde nesta fase:
  - temporariamente digitado
  - ou já via regra atual

## Contrato mínimo recomendado
- `region`
- `totem_id`
- `sku_id`
- `desired_slot` opcional
- `channel = KIOSK`
- `amount_cents` enquanto catálogo único ainda não existir

## Entrega esperada
- payload fechado
- sem ambiguidade entre online e kiosk

---

# 6.3 SUBETAPA C — Fechar backend de criação de pedido KIOSK
## Objetivo
Garantir que o pedido kiosk nasce corretamente.

## Esperado
- `Order.channel = KIOSK`
- `Order.status = PAYMENT_PENDING`
- `Allocation.state = RESERVED_PENDING_PAYMENT`
- `user_id = null` quando aplicável
- uso coerente de campos guest quando necessário

## Arquivos prováveis
- `01_source/order_pickup_service/app/routers/orders.py`
- `01_source/order_pickup_service/app/schemas/orders.py`

## Critério de aceite
- pedido kiosk é criado sem hacks
- alocação existe
- status inicial correto

---

# 6.4 SUBETAPA D — Fechar confirmação de pagamento KIOSK
## Objetivo
Garantir que o fluxo kiosk fecha corretamente após o pagamento.

## Regra desejada
Para KIOSK:
- não criar `Pickup` de retirada futura
- não gerar QR/código manual
- confirmar pagamento
- commitar a allocation
- abrir/liberar a gaveta
- atualizar estado final coerente

## Validar no `internal.py`
Hoje o ramo KIOSK deve fazer algo como:
- `order.mark_as_picked_up()` ou equivalente do fluxo imediato
- `allocation.state = OPENED_FOR_PICKUP`
- `locker_commit(...)`
- `locker_light_on(...)`
- `locker_open(...)`

## Revisão importante
Decidir o estado final correto do kiosk:
- manter `OPENED_FOR_PICKUP` como transitório
- e depois fechar como `PICKED_UP`
- ou aceitar um fluxo kiosk mais simples nesta fase

## Recomendação
Nesta fase, buscar coerência mínima:
- pagamento confirmado
- gaveta aberta
- estado final rastreável

## Arquivo prioritário
- `01_source/order_pickup_service/app/routers/internal.py`

## Critério de aceite
- pagamento kiosk não tenta criar pickup online
- abertura da gaveta acontece
- estados não ficam ambíguos

---

# 6.5 SUBETAPA E — Construir interface de simulação KIOSK
## Objetivo
Criar uma página/ambiente próprio para testar KIOSK do início ao fim.

## Requisitos mínimos da tela
- escolher região (`PT` / `SP`)
- escolher SKU
- escolher gaveta opcionalmente
- escolher método de pagamento
- criar pedido kiosk
- pagar pedido kiosk
- mostrar resposta operacional
- mostrar estado final

## Recomendação de arquitetura
Criar uma página separada do dashboard principal, para não poluir a UX operacional existente.

## Nome sugerido
- `KioskSimulator.jsx`
ou
- `KioskCheckout.jsx`

## Fluxo da UI
1. operador escolhe região
2. operador escolhe sku/produto
3. operador define gaveta opcional
4. cria pedido kiosk
5. paga
6. acompanha retorno
7. valida abertura/liberação

## Critério de aceite
- teste repetível sem depender do dashboard online
- leitura clara do fluxo kiosk

---

# 6.6 SUBETAPA F — Validar estados do pedido KIOSK
## Objetivo
Fechar a semântica dos estados kiosk.

## O que precisa ficar claro
- status inicial
- status após pagamento
- status após abertura
- status final

## Risco
O kiosk pode acabar reaproveitando estados pensados para online e ficar semanticamente estranho.

## Recomendação
Definir explicitamente:
- qual é o estado final do pedido kiosk
- qual é o estado final da allocation kiosk
- se `picked_up_at` representa corretamente o fluxo kiosk no ato

## Critério de aceite
- leitura do banco e da UI faz sentido sem precisar “interpretar manualmente”

---

# 6.7 SUBETAPA G — Validar fluxo completo em PT e SP
## Objetivo
Fechar a fase com evidência real.

## Rodada mínima
### PT
- criar pedido kiosk
- pagar
- abrir gaveta
- validar estados finais

### SP
- criar pedido kiosk
- pagar
- abrir gaveta
- validar estados finais

## Validar também
- moeda por região
- horário por região
- backend correto
- slot correto

## Critério de aceite
- o mesmo fluxo funciona nas duas regiões

---

# 6.8 SUBETAPA H — Documentar runbook e aceite
## Objetivo
Deixar a fase repetível e transmissível.

## Entregáveis
- checklist de validação kiosk
- handoff do que foi implementado
- runbook de teste kiosk
- critérios de aceite formal da fase

---

# 7. ARQUIVOS MAIS PROVÁVEIS A ENTRAR PRIMEIRO

## Backend
- `01_source/order_pickup_service/app/models/order.py`
- `01_source/order_pickup_service/app/routers/orders.py`
- `01_source/order_pickup_service/app/routers/internal.py`
- `01_source/order_pickup_service/app/schemas/orders.py`

## Frontend
- nova página kiosk, por exemplo:
  - `01_source/frontend/src/pages/KioskSimulator.jsx`
ou equivalente
- eventual ajuste de rotas:
  - `01_source/frontend/src/App.jsx`
ou onde a navegação estiver definida

## Gateway
- `01_source/payment_gateway/...` apenas se houver diferença de payload/método kiosk

---

# 8. ORDEM TÉCNICA RECOMENDADA

## Passo 1
Mapear o fluxo kiosk já existente no backend.

## Passo 2
Fechar o contrato do pedido kiosk.

## Passo 3
Ajustar backend de criação e confirmação de pagamento kiosk.

## Passo 4
Criar a página de simulação kiosk.

## Passo 5
Validar fluxo ponta a ponta em PT.

## Passo 6
Validar fluxo ponta a ponta em SP.

## Passo 7
Documentar aceite da fase.

---

# 9. CHECKLIST EXECUTIVO DA FASE V

## Backend
- [ ] pedido KIOSK nasce corretamente
- [ ] allocation do kiosk nasce corretamente
- [ ] pagamento kiosk confirma corretamente
- [ ] fluxo kiosk não tenta criar pickup online
- [ ] gaveta abre/libera corretamente
- [ ] estados finais kiosk ficam coerentes

## Frontend / Simulação
- [ ] existe tela própria de simulação kiosk
- [ ] fluxo é legível e repetível
- [ ] operador consegue testar sem hacks
- [ ] respostas operacionais são claras

## Validação regional
- [ ] fluxo validado em `PT`
- [ ] fluxo validado em `SP`
- [ ] moeda correta por região
- [ ] horário correto por região

## Aceite final
- [ ] runbook de teste kiosk documentado
- [ ] handoff atualizado
- [ ] fase pronta para encerrar e abrir a fase de catálogo

---

# 10. RISCOS DA FASE

## 1. Misturar online e kiosk demais
Risco de fluxo kiosk ficar dependente de conceitos do online.

## 2. Estado final mal definido
Risco de “parecer funcionar”, mas ficar sem semântica clara no banco.

## 3. Simulação kiosk virar apenas atalho de pagamento
Risco de não representar o fluxo real de operação kiosk.

## 4. Hardcodes temporários virarem permanentes
Como o catálogo único ainda não existe, a fase precisa ser feita sem consolidar gambiarra estrutural.

---

# 11. DECISÃO TÉCNICA RECOMENDADA

A FASE 3 — V deve ser implementada com foco em:

- fluxo próprio
- tela própria
- estados claros
- mínima dependência do online
- sem tentar resolver catálogo definitivo agora

Em resumo:
**primeiro fechar a simulação kiosk funcional e coerente; depois ligar isso à fonte única de catálogo na fase seguinte.**

---

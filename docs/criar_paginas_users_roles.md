# Cursor/Claude Prompt - Criar/Implementar páginas de gerenciamento para   USERS & ROLES & SECURITY   http://localhost:5173/v1 (@01_source/frontend) http://localhost:5174/v0 (@01_source/frontend_v0)
 
**Contexto:** `@02_docker/complete_schema_20260525_a.sql` e `@01_source/order_pickup_service` e `@01_source/backend/runtime`

**Requisições:**

1. Atuar como engenheiro de software/desenvolvedor com larga experiência no mercado de LOCKERS e seu gerenciamento em todos os níveis.
2. Implementar/codar as páginas (novas ou atualizar) para gerenciar as tabelas relacionadas ao domínio     USERS & ROLES & SECURITY
3. Manter padrão UI
4. Manter o padrão em UX/CX e alinhar as novas páginas ao padrão OPS no frontend v0 das outras telas OPS (referência: Payment Gateway e Marketplace).
5. Criar as páginas segundo o padrão adotado no projeto para OPS ou seguir o padrão `@01_source\frontend` ou desenvolver um novo
6. Use FastAPI + SQLAlchemy + PostgreSQL
7. Criar novas entidades para atender o que é pedido resolvendo problemas que não foram visualizados.
8. Endpoints: CRUD USERS & ROLES & SECURITY (RELACIONAR COM OUTROS DOMÍNIOS) (e outros associados com o projeto), webhook config, api key rotation entre outras possibilidades (que sejam necessárias)
9. Inserir Dados (seed) para as tabelas é obrigatório
10. Realizar Testes
11. Atualizar Menus (criar novos menus e não apenas itens para agrupar melhor) em http://localhost:5173/v1 e http://localhost:5174/v0


**Referências:** 
a-) Redes locker / hardware: SwipBox, Cleveron, Pickup (PL), Bloq.it, Quadient, Packeta, Vinted Go
b-) Carriers globais: InPost, DPD, DHL, USPS, Royal Mail, La Poste, Colissimo, Hermes DE, Yodel, Swiss Post, Australia Post, Blue Dart, Bring, PostNord
c-) Operadores de Rede de Lockers: DPD, USPS, DHL Packstation, InPost Parcel Lockers
d-) Marketplaces: Magalu, Mercado Livre, Worten, El Corte Inglés, Amazon US (Hub), Walmart, Rakuten, Cdiscount, OTTO, Flipkart (+ Shopee, Shein, Temu, TikTok Shop já no catálogo)
e-) Redes de Pontos de Coleta: Ponto Magalu, Mercado Livre, Worten, Corte Inglés Collection Point
f-) Agregadores / hubs: Cainiao, Parcel2Go, EasyPost, Shippo, Intelipost, Melhor Envio

**Restrições:** Sem explicação, sem raciocínio, sem diff. Apenas código + comandos + resultado.



1o. PROMPT
Codar o pedido em @docs/criar_paginas_users_role.md. Ter como referência @02_docker/complete_schema_20260525_a.sql 

2o. PROMPT
Buscar criar mais páginas ou seções para  USERS & ROLES & SECURITY (RELACIONAR COM OUTROS DOMÍNIOS) . Se necessário criar tabelas e relações para termos nível profissional/mundial.

3O. PROMPT
Considerar InPost, DHL, Magalu, MercadoLivre, Amazon, DPD, Correios, CTT, WORTEN, EL CORTE INGLES entre outros players do segmento de LOCKERS em nível mundial para rever e para complementar USERS & ROLES & SECURITY (RELACIONAR COM OUTROS DOMÍNIOS) 
 
4o. PROMPT
Pensar em outros players (redes de locker, carriers globais, Operadores de Rede de Lockers, marketplaces, Redes de Pontos de Coleta, agregadores/hubs, food delivery) que atuam no mercado e como integrar além dos citados. Se necessário criar tabelas e relações para termos o projeto em nível profissional/mundial.

5o. PROMPT
Desenvolver funcionalidades não previstas para valorizar o projeto. Se necessário criar tabelas e relações para termos o projeto em nível profissional/mundial.

6o. PROMPT
Atualizar menus com as páginas criadas. Aplicar Migrações

7o. PROMPT
Codar novas possibilidades dentro do domínio USERS & ROLES & SECURITY (RELACIONAR COM OUTROS DOMÍNIOS)  que não visualizei e deveria ser implementado

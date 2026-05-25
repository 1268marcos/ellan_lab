# Cursor/Claude Prompt - Criar/Implementar páginas de gerenciamento para    ORDERS/PEDIDOS    http://localhost:5173/v1 (@01_source/frontend) http://localhost:5174/v0 (@01_source/frontend_v0)
 
**Contexto:** `@02_docker/complete_schema_20260525_d.sql`

**Requisições:**
1. Atuar como : a- Engenheiro de Software, b-Especiailsta em banco de dados, c- Programador, d-Especialista Fiscal e Contábil, e- Administrador e Gestor, g-Usuário comum, h-Advogado Brasil e Mundial, i-Especialista em Segurança. Essas personas possuem larga experiência no mercado de LOCKERS em todos os níveis.
2. Implementar/codar as páginas (novas ou atualizar) para gerenciar as tabelas relacionadas ao domínio ORDERS/PEDIDOS. 
3. Criar os endpoints de integrações (atuais e futuras)
4. Manter padrão consistente e compatível de melhores práticas de UI
5. Manter o padrão em UX/CX e alinhar as novas páginas ao padrão OPS no frontend v0 das outras telas OPS (referência: Fiscal).
6. Criar as páginas segundo o padrão adotado no projeto para OPS ou seguir o padrão `@01_source\frontend`
7. Use FastAPI + SQLAlchemy + PostgreSQL
8. Criar novas entidades para atender o que é pedido resolvendo problemas que não foram visualizados.
9. Criar os Endpoints: CRUD ORDERS/PEDIDOS (e outros), webhook config, api key rotation entre outras possibilidades (que sejam necessárias)
10. Seedar as tabelas e enumeradores (Inserir Dados)
11. Realizar Testes
12. Atualizar Menus (criar novos menus e não apenas itens para agrupar melhor) em http://localhost:5173/v1 e http://localhost:5174/v0

**Referências:** 
a-) Redes locker / hardware: SwipBox, Cleveron, Pickup (PL), Bloq.it, Quadient, Packeta, Vinted Go
b-) Carriers globais: InPost, DPD, DHL, USPS, Royal Mail, La Poste, Colissimo, Hermes DE, Yodel, Swiss Post, Australia Post, Blue Dart, Bring, PostNord
c-) Operadores de Rede de Lockers: DPD, USPS, DHL Packstation, InPost Parcel Lockers
d-) Marketplaces: Magalu, Mercado Livre, Worten, El Corte Inglés, Amazon US (Hub), Walmart, Rakuten, Cdiscount, OTTO, Flipkart (+ Shopee, Shein, Temu, TikTok Shop já no catálogo)
e-) Redes de Pontos de Coleta: Ponto Magalu, Mercado Livre, Worten, Corte Inglés Collection Point
f-) Agregadores / hubs: Cainiao, Parcel2Go, EasyPost, Shippo, Intelipost, Melhor Envio

**Restrições:** Sem explicação, sem raciocínio, sem diff. Apenas código + comandos + resultado.

1o. PROMPT
Codar o pedido em @docs/criar_paginas_orders_pedidos.md. Ter como referência o documento @02_docker/complete_schema_20260525_d.sql 

2o. PROMPT
Buscar criar mais páginas ou seções para ORDERS/PEDIDOS. Se necessário criar tabelas e relações para termos nível profissional/mundial.

3o. PROMPT
Considerar InPost, DHL, Magalu, MercadoLivre, Amazon, DPD, Correios, CTT, WORTEN, EL CORTE INGLES entre outros players do segmento de LOCKERS em nível mundial para rever e para complementar ORDERS/PEDIDOS
 
4o. PROMPT
Pensar em outros players (redes de locker, carriers globais, Operadores de Rede de Lockers, marketplaces, Redes de Pontos de Coleta, agregadores/hubs, food delivery) que atuam no mercado e como integrar além dos citados. Se necessário, criar tabelas e relações para termos o projeto em nível profissional/mundial.

5o. PROMPT
Desenvolver funcionalidades não previstas para valorizar o projeto. Se necessário criar tabelas e relações para termos o projeto em nível profissional/mundial.

6o. PROMPT
Atualizar menus com as páginas criadas.

7o. PROMPT
Codar novas possibilidades dentro do domínio ORDERS/PEDIDOS que não visualizei e deveria ser implementado
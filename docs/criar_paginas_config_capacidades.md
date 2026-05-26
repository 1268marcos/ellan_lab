# Cursor/Claude Prompt - Criar/Implementar páginas de gerenciamento para  Configuração de Capacidade (Capability) http://localhost:5173/v1 (@01_source/frontend) http://localhost:5174/v0 (@01_source/frontend_v0)

**Contexto:** `@02_docker/complete_schema_20260526_a.sql`

**Requisições:**
1. Atuar como : a-Engenheiro de Software, b-Especialista em banco de dados, c-Dev Programador, d-Especialista Fiscal,  e-Especialista Contábil, f-Administrador, g- Gestor, h-Usuário comum, i-Advogado, j-Especialista em Segurança da Informação. Todas essas personas possuem larga experiência no mercado de LOCKERS e TECNOLOGIA e da cadeia associada ao projeto.
2. Implementar, ou seja, codar as páginas novas ou atualizar anteriores para gerenciar as tabelas relacionadas ao domínio  Configuração de Capacidade (Capability).
3. Criar os endpoints de integrações e atualizar os atuais, se necessários.
4. Criar os Endpoints:  Configuração de Capacidade (Capability) (e outros), webhook config, api key rotation entre outras possibilidades (que sejam necessárias)
5. Manter padrão consistente e compatível de melhores práticas de UI
6. Manter o padrão em UX/CX e alinhar as novas páginas ao padrão OPS no frontend v0 e padrão frontend v1.
7. Usar FastAPI + SQLAlchemy + PostgreSQL
8. Criar novas entidades para atender o que é pedido resolvendo problemas que não foram visualizados.
9. Seedar as tabelas e enumeradores (Inserir Dados)
10. Realizar Testes
11. Atualizar os Menus (criar novos menus e não apenas itens para agrupar melhor) em http://localhost:5173/v1 e http://localhost:5174/v0

**Referências:**
a-) Redes locker / hardware. Exemplo: SwipBox, Cleveron, Pickup (PL), Bloq.it, Quadient, Packeta, Vinted Go
b-) Carriers globais. Exemplo: InPost, DPD, DHL, USPS, Royal Mail, La Poste, Colissimo, Hermes DE, Yodel, Swiss Post, Australia Post, Blue Dart, Bring, PostNord
c-) Operadores de Rede de Lockers. Exemplo: DPD, USPS, DHL Packstation, InPost Parcel Lockers
d-) Marketplaces. Exemplo: Magalu, Mercado Livre, Worten, El Corte Inglés, Amazon US (Hub), Walmart, Rakuten, Cdiscount, OTTO, Flipkart (+ Shopee, Shein, Temu, TikTok Shop já no catálogo)
e-) Redes de Pontos de Coleta. Exemplo: Ponto Magalu, Mercado Livre, Worten, Corte Inglés Collection Point
f-) Agregadores / hubs. Exemplo: Cainiao, Parcel2Go, EasyPost, Shippo, Intelipost, Melhor Envio

**Restrições:** Sem explicação, sem raciocínio, sem diff. Apenas código + comandos + resultado.
1o. PROMPT: Codar o pedido em @docs/criar_paginas_config_capacidades.md. Ter como referência o documento @02_docker/complete_schema_20260526_a.sql

2o. PROMPT: Buscar criar mais páginas ou seções para Configuração de Capacidade (Capability). Se necessário criar tabelas e relações para termos nível profissional/mundial. **Restrições:** Sem explicação, sem raciocínio, sem diff. Apenas código + comandos + resultado. **Requisição:** Realizar Testes.

3o. PROMPT: Considerar InPost, DHL, Magalu, MercadoLivre, Amazon, DPD, Correios, CTT, WORTEN, EL CORTE INGLES entre outros players do segmento de LOCKERS em nível mundial para rever e para complementar  Configuração de Capacidade (Capability) **Restrições:** Sem explicação, sem raciocínio, sem diff. Apenas código + comandos + resultado. **Requisição:** Realizar Testes.

4o. PROMPT: Pensar em outros players (redes de locker, carriers globais, Operadores de Rede de Lockers, marketplaces, Redes de Pontos de Coleta, agregadores/hubs, food delivery) que atuam no mercado e como integrar além dos citados. Se necessário, criar tabelas e relações para termos o projeto em nível profissional/mundial. **Restrições:** Sem explicação, sem raciocínio, sem diff. Apenas código + comandos + resultado. **Requisição:** Realizar Testes.

5o. PROMPT: Desenvolver funcionalidades não previstas para valorizar o projeto. Se necessário criar tabelas e relações para termos o projeto em nível profissional/mundial. **Restrições:** Sem explicação, sem raciocínio, sem diff. Apenas código + comandos + resultado. **Requisição:** Realizar Testes.

6o. PROMPT: Atualizar menus com as páginas criadas.
7o. PROMPT: Codar novas possibilidades dentro do domínio  Configuração de Capacidade (Capability) que não visualizei e devem ser implementados para melhor eficiência e uso do projeto.



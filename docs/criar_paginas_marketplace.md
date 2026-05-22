# Cursor/Claude Prompt - Criar/Implementar páginas de gerenciamento para    marketplace   http://localhost:5173/v1 (@01_source/frontend) http://localhost:5174/v0 (@01_source/frontend_v0)
 
**Contexto:** `@02_docker/complete_schema_20260521_c.sql` e `@01_source/order_pickup_service` e `@01_source/backend/runtime`

**Requisições:**

1. Implementar/codar as páginas (novas ou atualizar) para gerenciar as tabelas relacionadas ao domínio     marketplace
2. Manter padrão UI
3. Manter o padrão em UX/CX
4. Criar as páginas segundo o padrão adotado no projeto para OPS ou seguir o padrão `@01_source\frontend` ou desenvolver um novo
5. Use FastAPI + SQLAlchemy + PostgreSQL
6. Criar novas entidades para atender o que é pedido resolvendo problemas que não foram visualizados.
7. Endpoints: CRUD partners, webhook config, api key rotation entre outras possibilidades (que sejam necessárias)
8. Inserir Dados (seed) para as tabelas
9. Realizar Testes
10. Atualizar Menus (criar novos menus e não apenas itens para agrupar melhor) em http://localhost:5173/v1 e http://localhost:5174/v0

**Restrições:** Sem explicação, sem raciocínio, sem diff. Apenas código + comandos + resultado.


PROMPT
Codar o pedido em @docs/criar_paginas_marketplace.md. Ter como referência @02_docker/complete_schema_20260521_c.sql 


Buscar mais páginas ou seções para Marketplace. Se necessário criar tabelas e relações para termos nível profissional.
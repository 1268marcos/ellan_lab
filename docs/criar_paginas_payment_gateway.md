# Cursor/Claude Prompt - Criar/Implementar páginas de gerenciamento para payment_gateway http://localhost:5173/v1 (@01_source/frontend) http://localhost:5174/v0 (@01_source/frontend_v0)
 
**Contexto:** `@02_docker/complete_schema_20260521_c.sql` e `@01_source/payment_gateway`

**Requisições:**

1. Implementar as páginas para gerenciar as tabelas de tenant e suas associações
2. Manter padrão UI
3. Ser compatível em UX/CX
4. Criar as páginas segundo o padrão adotado no projeto para OPS ou melhor o padrão `@01_source\frontend`
5. Use FastAPI + SQLAlchemy + PostgreSQL
6. Criar novas entidades para atender o que é pedido resolvendo problemas que não foram visualizados.
7. Endpoints: CRUD partners, webhook config, api key rotation entre outras possibilidades (que sejam necessárias)
8. Inserir Dados (seed) para as tabelas
9. Realizar Testes
10. Atualizar Menus (criar novos para agrupar melhor) em http://localhost:5173/v1 e http://localhost:5174/v0

**Restrições:** Sem explicação, sem raciocínio, sem diff. Apenas código + comandos + resultado.
# RESET_DEV.md
**Projeto:** ELLAN Lab Locker  
**Objetivo:** resetar o ambiente de desenvolvimento/teste com segurança, sem quebrar a estrutura de diretórios usada pelos serviços.

---

# 1. QUANDO USAR

Use este reset antes de uma nova rodada de validação quando houver risco de contaminação por dados antigos, por exemplo:

- pedidos antigos interferindo na leitura atual
- estados antigos de `Allocation`, `Pickup` e `Order`
- Redis com chaves de testes anteriores
- SQLite com histórico velho de gateway ou retirada
- necessidade de revalidar o fluxo do zero

---

# 2. IMPORTANTE

## Este reset é para ambiente DEV / TESTE
**Não usar em produção.**

## Cuidado principal
No projeto atual, alguns serviços usam arquivos SQLite em subpastas específicas:

- `../03_data/sqlite/order_pickup/orders.db`
- `../03_data/sqlite/gateway/events.db`

Se você apagar `../03_data/sqlite/*` com `rm -rf`, pode remover também as pastas e causar erro como:

```text
sqlite3.OperationalError: unable to open database file
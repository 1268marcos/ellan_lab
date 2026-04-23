from __future__ import annotations

AUTHORIZATION_POLICY_MD = """
## Politica de autorizacao (fonte unica)

Esta secao e a referencia oficial da API para autorizacao por role.
Frontend e backend devem seguir exatamente estas regras.

### Regra base

- Usuario autenticado sem registro ativo em `public.user_roles` e tratado como **`usuario_comum`** (papel implicito).
- `usuario_comum` **nao** possui acesso operacional.
- Endpoints operacionais exigem roles explicitas via guard `require_user_roles`.

### Matriz usuario -> role -> endpoints permitidos/bloqueados

| Usuario | Roles ativas | Permitidos | Bloqueados |
|---|---|---|---|
| `admin.operacao@ellanlab.com` | `admin_operacao (GLOBAL)` | `/public/*`, `/dev-admin/*`, `/dev-admin/base/*` | Nenhum no escopo atual |
| `suporte@ellanlab.com` | `suporte (GLOBAL)` | `/public/*`, `/dev-admin/base/*` | `/dev-admin/*` (exceto base) |
| `auditoria@ellanlab.com` | `auditoria (GLOBAL)` | `/public/*`, `/dev-admin/*`, `/dev-admin/base/*` | Nenhum no escopo atual |
| Ex.: `m00.marcos@gmail.com` | *(sem role ativa => `usuario_comum` implicito)* | `/public/*` | `/dev-admin/*`, `/dev-admin/base/*` |

### Regras tecnicas vigentes

- `/dev-admin/*`: permitido para `admin_operacao` ou `auditoria`.
- `/dev-admin/base/*`: permitido para `admin_operacao`, `auditoria` ou `suporte`.
- `/public/auth/me/roles`: retorna as roles ativas do usuario logado (lista vazia para `usuario_comum`).

### Anti-efeito-colateral em fluxos DEV

Quando houver etapa protegida por role em fluxo composto, a autorizacao deve ser validada
antes de criar pedido/reservar slot/aplicar credito. Se isso nao for possivel, o backend deve
executar compensacao transacional completa.
"""


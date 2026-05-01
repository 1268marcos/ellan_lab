# Instruções para o Claude
- Sempre explique o que vai fazer ANTES de modificar
- Mantenha as explicações curtas e diretas
- Pergunte se quiser confirmar algo importante
- Use commits descritivos

# Em vez de gastar horas escrevendo testes chatos:
claude "escreva testes para o módulo de autenticação, execute e corrija falhas"
claude "como eu resolveria esta issue?"
claude "explique como este código funciona"
claude "adicione comentários explicativos"

# Ou para documentação que você sempre adia:
claude "gere documentação básica para as funções neste arquivo"

# Durante a sessão, quando aprender algo importante:
/remember "Sempre usar a biblioteca X para validação neste projeto"
O Claude guarda isso para TODAS as sessões futuras.

# Backend `billing_fiscal_service` — pytest (path correto)
O binário **não** está no `PATH` global; use o venv do serviço e `PYTHONPATH` para o pacote `app`:
```bash
cd 01_source/backend/billing_fiscal_service
PYTHONPATH=. .venv/bin/pytest tests/ -q
```
Alternativa: `/home/marcos/ellan_lab/.venv/bin/pytest` com o mesmo `cd` e `PYTHONPATH=.` .

# Três backends — `pytest --collect-only` de uma vez
Na raiz do repo: `make test-collect` (billing + order_pickup + payment_gateway). O
`payment_gateway` precisa do **seu** `.venv` com `pip install -r requirements.txt` (não
misturar com o venv do billing). CI: `.github/workflows/backend-test-collect.yml`.

# Contrato pagamento → runtime / lifecycle
`make test-payment-contract` — pytest em slice gateway (`LockerBackendClient`) + pickup
(`LifecycleClient` + hook interno). Deploy mínimo Compose: `deploy/compose-minimal-stack.sh`;
baseline cloud: `deploy/README.md` + `deploy/ecs/taskdef-payment-gateway.example.json`.
E2E compose (desenho): `docs/E2E_PAYMENT_MINIMAL_STACK_DESIGN.md`.

# Dicas de ouro para sua produtividade
    - Desafio do TDAH	        Solução com Claude Code
    - Dificuldade de começar    Comece com claude "explique este código"
    - Perder o foco no meio	    Use tasks pequenas e vá commitando
    - Esquecer contexto	        O Claude lembra tudo da sessão
    - Sobrecarga de opções	    Comece com UM comando por vez
    - Impaciência	            Veja o Claude trabalhando em tempo real
    - Use o Claude como pair programmer que te acompanha, não como substituto. Você mantém o controle, ele faz o trabalho pesado e repetitivo.

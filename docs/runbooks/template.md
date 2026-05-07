# <Nome do Gap> MVP Runbook

Owner: <FE|BE|FISC|QA>  
Contato emergencia: <canal/pessoa de plantao>  
Servico(s): `<paths>`

## Escopo MVP

- Smoke test: comando unico retorna 200/JSON esperado.
- E2E test: script automatizado executa fluxo principal.
- Runbook: como testar, como reverter, owner, contato emergencia.

## Contrato MVP

Base path: `<endpoint-base>`

Endpoints ou comandos principais:

- `<metodo> <path>`
  - Retorno esperado: `<status/campo esperado>`

## Como testar

```bash
# Smoke
<comando>

# E2E
<comando>
```

## Como reverter

1. <passo de rollback>
2. <passo de rollback>
3. <validacao pos-rollback>

## Owner

- Owner tecnico: <FE|BE|FISC|QA>
- Backup: <FE|BE|FISC|QA>

## Contato emergencia

- Canal: <canal>
- Janela de atendimento: <janela>

## Evidencia esperada

```text
<saida esperada>
```

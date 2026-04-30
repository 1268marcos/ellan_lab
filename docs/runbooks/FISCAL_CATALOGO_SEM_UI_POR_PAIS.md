# Runbook: catálogo fiscal global sem UI de gestão por país

Este runbook descreve como operar e evoluir o **catálogo de países**, a **onda FG-1** (stubs, fixtures, matriz de cenários) e gates de qualidade **sem** depender de uma tela administrativa dedicada por país. O objetivo é governança por **repositório**, **APIs de leitura** e **CI**.

## Princípios

1. **Fonte única versionada** — Países da onda FG-1, adapters stub, autoridade curta e regiões permitidas vivem em `01_source/backend/billing_fiscal_service/app/config/fiscal_fg1_wave.py`. O catálogo enriquecido (moeda, timezone, protocolo, etc.) permanece em `app/services/fiscal_global_catalog_service.py`; o escopo da onda filtra o catálogo usando a mesma lista de códigos, evitando listas duplicadas.
2. **Mudança = PR** — Inclusão ou ajuste de país passa por revisão de código, histórico Git e (quando existir) checklist de produto/compliance.
3. **Automação em vez de formulário** — Fixtures materializadas por script; validação de contrato por função de serviço reutilizável em CI ou job manual.

## Quando usar este runbook

- Incluir ou remover um país da **onda FG-1** (stub + fixtures + escopo API).
- Responder auditoria: “como sabemos que a matriz está completa?”.
- Planejar transição futura para **CRUD admin** sem reescrever o modelo de dados.

## Artefatos no repositório

| Artefato | Local | Responsabilidade |
|----------|--------|------------------|
| Lista da onda + adapter + authority + regiões | `app/config/fiscal_fg1_wave.py` | Ordem dos países; nomes de adapter stub; região default e valores aceitos em simulate |
| Itens do catálogo global (campos de negócio) | `app/services/fiscal_global_catalog_service.py` | Nome, autoridade longa, document types, protocolo, moeda, timezone, tier |
| Matriz canônica de cenários (9 linhas) | `build_fiscal_global_scenario_matrix()` no mesmo módulo do catálogo | Igual para todos os países |
| Lógica stub, inventário, envelope | `app/services/fiscal_fg1_stub_service.py` | Consome o módulo de config; não duplicar mapas fora dele |
| JSONs de fixture | `fixtures/fiscal/fg1/<cc>/<op>/<scenario>.json` | Gerados pelo script abaixo |

## Procedimento: adicionar um país à onda FG-1

1. **Catálogo** — Em `fiscal_global_catalog_service.py`, adicione um objeto em `items` com os campos alinhados aos países existentes (código ISO, região comercial, autoridade, protocolo, etc.).
2. **Config da onda** — Em `app/config/fiscal_fg1_wave.py`:
   - Acrescente o código em `FG1_WAVE_COUNTRIES` (posição define ordem em relatórios/API).
   - Preencha `FG1_ADAPTER_BY_COUNTRY`, `FG1_AUTHORITY_BY_COUNTRY`, `FG1_REGION_BY_COUNTRY` e `FG1_ALLOWED_REGIONS_BY_COUNTRY` para o novo código.
3. **Fixtures** — No diretório do serviço, com `PYTHONPATH=.`:
   ```bash
   cd 01_source/backend/billing_fiscal_service
   PYTHONPATH=. python3 scripts/write_fg1_fixtures.py
   ```
4. **Validar contrato** — Mesmo diretório:
   ```bash
   PYTHONPATH=. python3 -c "from app.services.fiscal_fg1_stub_service import validate_fg1_envelope_contract; print(validate_fg1_envelope_contract())"
   ```
   Esperado: `status` == `OK`, `error_count` == 0.
5. **APIs admin (leitura)** — Opcionalmente verificar `GET /admin/fiscal/global/fg1-wave-scope`, `.../fg1/fixture-inventory`, `.../fg1/envelope-check`, `.../fg1/coverage-gate` em ambiente com o serviço ativo.
6. **PR** — Descrever país, autoridade, motivo da inclusão na onda e evidência do envelope OK (trecho de log ou saída do comando).

## Procedimento: país só no catálogo global, fora da onda FG-1

- Mantenha o item em `build_fiscal_global_catalog()` **sem** incluir o código em `FG1_WAVE_COUNTRIES`.
- Não haverá fixtures FG-1 nem adapter stub listado para esse país até que entre na onda.

## Gate de CI (recomendado)

- Job que executa `validate_fg1_envelope_contract()` (ou teste fino que o chame) após mudanças em `fiscal_fg1_wave.py`, `fiscal_fg1_stub_service.py` ou em `fixtures/fiscal/fg1/`.
- Opcional: comparar contagem de ficheiros JSON com `len(FG1_WAVE_COUNTRIES) * 9` (número de cenários), alinhado a `build_fg1_fixture_inventory()`.

## Observabilidade e auditoria sem UI

- **Git** como registo de quem mudou o quê e quando.
- **Endpoints read-only** já previstos no grupo “Global Catalog & FG-1” no cockpit fiscal (catalog, fixtures-matrix, envelope-check, coverage-gate).
- **Export CSV/JSON** da página de países, quando ligada a `fg1-wave-scope`, para provar IN WAVE / OUT WAVE.

## Evolução futura: admin CRUD (opcional)

Quando uma UI ou API de escrita fizer sentido:

- **Persistir** em base de dados ou store de configuração, mas **gerar** ou **sincronizar** o ficheiro Python/YAML do repo em deploy (ou exportar bundle) para não perder rastreabilidade.
- Manter o **envelope check** e o **script de fixtures** como barreira; a UI não substitui validação automática.

## Referência rápida de comandos

```bash
cd 01_source/backend/billing_fiscal_service
PYTHONPATH=. python3 scripts/write_fg1_fixtures.py
PYTHONPATH=. python3 -c "from app.services.fiscal_fg1_stub_service import validate_fg1_envelope_contract as v; r=v(); print(r['status'], r['error_count'])"
```

## Donos e revisão

- Dono técnico: time fiscal/backend do `billing_fiscal_service`.
- Revisão: pelo menos uma leitura de compliance/região quando o país for novo para o produto.

---

*Última alinhamento conceitual: operação sem “página de gestão” por país — config versionada + script + CI + APIs de leitura.*

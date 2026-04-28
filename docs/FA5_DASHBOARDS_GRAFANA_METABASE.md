# FA-5 Dashboards (Grafana + Metabase) - Setup Minimo e Go-Live

## Motivacao

Fechar o item de dashboards FA-5 com stack operacional real para:

- alertas de inadimplencia e reconciliacao (Grafana),
- analise de negocio e autoatendimento (Metabase),
- exploracao de hypertables Timescale (ex.: `market_ticks` e tabelas financeiras FA-5).

## Stack minima no docker-compose

Servicos adicionados:

- `grafana` -> `http://localhost:3000`
- `metabase` -> `http://localhost:3001`

Datasource Grafana provisionado automaticamente:

- arquivo: `02_docker/grafana/provisioning/datasources/postgres-locker-central.yml`
- datasource: **Postgres Locker Central**
- Timescale habilitado: `timescaledb: true`

## Subida rapida

```bash
cd /home/marcos/ellan_lab/02_docker
docker compose up -d grafana metabase
docker compose ps
```

## Credenciais iniciais

### Grafana

- URL: `http://localhost:3000`
- user: `admin` (ou `GRAFANA_ADMIN_USER`)
- senha: `admin123` (ou `GRAFANA_ADMIN_PASSWORD`)

### Metabase

- URL: `http://localhost:3001`
- primeira execucao abre wizard de setup.

## Configurar banco no Metabase

Adicionar conexao PostgreSQL:

- host: `postgres_central`
- port: `5432`
- db: `locker_central`
- user: `admin`
- password: `admin123`

Recomendacao: habilitar native SQL editing para equipes avancadas.

## Dashboards recomendados por perfil

## Trading / Quant

- Candlestick OHLCV (1m, 5m, 1h, 1d)
- Volume profile / depth chart
- Spread bid-ask realtime
- Latencia de execucao

Ferramenta:

- Grafana para realtime e alertas
- Metabase para exploracao ad-hoc

## Risco / Compliance

- Exposicao por ativo/setor
- VaR historico rolling 95%
- Correlacao entre ativos
- Alertas de violacao de limites

Ferramenta:

- Metabase (analise), Grafana (alertas)

## Operacoes / DevOps

- Throughput de ingestao (`market_ticks`)
- Latencia de query (`pg_stat_statements`)
- Storage por chunk (`timescaledb_information.chunks`)

Ferramenta:

- Grafana (monitoramento continuo)
- Metabase (tabela comparativa e capacidade)

## Negocios / Produto

- Receita por estrategia/cliente
- Cohort de retencao
- Funil sinal -> ordem -> execucao

Ferramenta:

- Metabase (BI e compartilhamento)

## Queries base (referencias)

Arquivo de apoio existente:

- `02_docker/postgres_central/market_data/queries_grafana_metabase.sql`

Sugestao: manter este arquivo como biblioteca central de SQL para dashboards.

## Checklist de go-live (para marcar FA-5 DASH como concluido)

- [ ] `grafana` e `metabase` ativos via docker compose
- [ ] datasource Grafana conectado ao `locker_central`
- [ ] conexao Metabase com PostgreSQL configurada
- [ ] dashboard de inadimplencia publicado
- [ ] dashboard de reconciliacao publicado
- [ ] pelo menos 2 alertas ativos no Grafana (ex.: DSO alto, mismatch contábil)
- [ ] runbook/playbook FA-5 linkado no painel OPS
- [ ] evidencia de operacao registrada no acompanhamento (data + links/prints)

## Alertas minimos sugeridos (Grafana)

- DSO diario > limiar definido (ex.: 45 dias)
- Divergencias no `ledger-compat/audit` acima de limite
- Falha de smoke Timescale (`SMOKE_FAIL`)

## Proximo passo de endurecimento

- Provisionar dashboards Grafana via JSON em repositorio
- Versionar colecoes/perguntas Metabase exportadas
- Integrar alertas Grafana com webhook/Slack

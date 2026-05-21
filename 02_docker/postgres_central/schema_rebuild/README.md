# Rebuild controlado — `postgres_central` / `locker_central`

Organização do dump `complete_schema_20260517_e.sql` em **fases ordenadas**, para recriar o banco sem erros de dependência (views antes de colunas, chunks TimescaleDB do `pg_dump`, etc.).

## Relação com `db_migrations.py` (order_pickup_service)

| Pergunta | Resposta |
|----------|----------|
| O `db_migrations.py` roda durante `run_rebuild.sh`? | **Não.** Só o `psql` no container executa os `.sql` desta pasta. |
| Então por que parece que “impede”? | (1) **TimescaleDB** ausente na imagem → falha na fase `01`. (2) **Serviços ligados** no startup rodam migrações em paralelo. (3) Após rebuild, startup com `schema_migrations` vazio reexecuta migrações pesadas (`DROP MATERIALIZED VIEW`, etc.). |
| Estratégia recomendada | **Rebuild = pg_dump em fases** (esta pasta). **Runtime =** `db_migrations` só para drift incremental em bancos já vivos. |

### Fluxo correto (recriar do zero)

```bash
cd 02_docker/postgres_central/schema_rebuild

# 1) Para serviços (run_rebuild.sh faz isso por padrão com STOP_SERVICES=1)
cd ../../ && docker compose stop order_pickup_service order_pickup_domain_event_worker

# 2) Rebuild (volume novo)
DESTROY_VOLUME=1 ./run_rebuild.sh
# Se a imagem não tiver TimescaleDB ainda:
# SKIP_TIMESCALEDB=1 DESTROY_VOLUME=1 ./run_rebuild.sh

# 3) Sobe a stack
cd ../../ && docker compose up -d

# 4) order_pickup: fase 14 já marcou schema_migrations — startup não recria tudo
#    Opcional: RUN_DB_MIGRATIONS_ON_STARTUP=false no .env durante o rebuild
```

A fase **`14_seed_schema_migrations.sql`** insere os nomes das migrações Python em `schema_migrations`, para o `order_pickup_service` tratar o schema do dump como “já migrado”.

Regenerar a fase 14 após novas migrações em Python:

```bash
python3 generate_schema_migrations_seed.py
```

### Bug corrigido em `db_migrations.py`

Havia **funções duplicadas no final do arquivo** (`_ensure_columns`, `_ensure_lockers_columns`, …) que **substituíam** as versões completas usadas pelo `_auto_heal_legacy_schema`. Isso não bloqueava o rebuild SQL, mas quebrava o auto-heal no startup. As duplicatas foram removidas.

---

## Por que em fases?

O `pg_dump` mistura, na mesma sequência:

1. **Views** no meio das tabelas (ex.: `invoice_order_view` antes de `orders`)
2. **Chunks** `_timescaledb_internal.*` que não devem ser restaurados em banco novo
3. **Funções** antes das tabelas que referenciam
4. **RLS / triggers** no final (correto), mas views já falharam antes

| Ordem | Arquivo | Conteúdo |
|------|---------|----------|
| 00 | `00_preamble.sql` | `SET`, `search_path` |
| 01 | `01_extensions_schemas.sql` | PostGIS, TimescaleDB, pg_cron, schemas |
| 02 | `02_types.sql` | ENUMs / tipos |
| 03 | `03_tables.sql` | `CREATE TABLE public.*` (sem chunks Timescale) |
| 03b | `03b_column_patches.sql` | `ADD COLUMN IF NOT EXISTS` (orders, pickup_tokens) |
| 04 | `04_sequences_owned_by.sql` | sequences + `OWNED BY` |
| 04b | `04b_column_defaults.sql` | `ALTER COLUMN SET DEFAULT` |
| 05 | `05_functions.sql` | funções (após tabelas) |
| 06 | `06_constraints_pk_unique_check.sql` | PK, UNIQUE, CHECK |
| 07 | `07_indexes.sql` | índices |
| 08 | `08_foreign_keys.sql` | FKs |
| 13 | `13_timescaledb_hypertables.sql` | `create_hypertable` (ignorado se `SKIP_TIMESCALEDB=1`) |
| 09 | `09_views.sql` | todas as views |
| 10 | `10_triggers.sql` | triggers |
| 11 | `11_rls_policies.sql` | RLS |
| 12 | `12_comments_misc.sql` | comentários |
| 14 | `14_seed_schema_migrations.sql` | marca migrações Python como aplicadas |

## Recriar o banco do zero

```bash
cd 02_docker/postgres_central/schema_rebuild

DESTROY_VOLUME=1 ./run_rebuild.sh
```

Permissão em `03_data/postgres_central`:

```bash
sudo chown -R "$USER:$USER" /home/marcos/ellan_lab/03_data/
```

## Variáveis úteis

| Variável | Efeito |
|----------|--------|
| `DESTROY_VOLUME=1` | `docker compose down -v` + apaga `03_data/postgres_central` |
| `STOP_SERVICES=1` | (padrão) para containers que usam o DB antes do rebuild |
| `SKIP_TIMESCALEDB=1` | pula fase 13; ainda exige ajuste manual se fase 01 falhar |
| `ONLY_PHASE=09_views` | executa só arquivos com esse prefixo |

## Regenerar a partir de um novo pg_dump

```bash
python3 split_schema_dump.py ../../complete_schema_YYYYMMDD.sql
python3 generate_schema_migrations_seed.py
```

## Fontes

- Dump: `02_docker/complete_schema_20260517_e.sql`
- Migrações app: `01_source/order_pickup_service/app/core/db_migrations.py`
- Hypertables: `02_docker/postgres_central/ops/enable_fa5_hypertables.sql`

# ELLAN LAB — Arquitetura de Gestão Financeira

## Recomendações de Mercado Mundial para Plataformas de Locker-as-a-Service

> \*\*Documento técnico\*\* | Abril 2026 | Versão 1.0  
> Baseado na análise do schema completo `locker\_central` e arquitetura de microserviços.

\---

## 1\. DIAGNÓSTICO DO ESTADO ATUAL

### O que o ELLAN LAB já tem (pontos positivos)

O projeto já apresenta uma base financeira bem construída para o segmento B2C:

* `financial\_ledger` — livro-razão simples (single-entry) por order
* `partner\_settlement\_batches` + `partner\_settlement\_items` — liquidação de receita com parceiros
* `rental\_contracts` + `rental\_plans` — contratos de aluguel de slot
* `invoices` + `fiscal\_documents` — emissão NF-e / NFC-e (tributação B2C)
* `payment\_transactions` + `payment\_splits` — captura de pagamentos e splits
* `payment\_gateway\_risk\_events` — controle de risco em pagamento
* `reconciliation\_pending` — fila de reconciliação de pagamentos
* `partner\_performance\_metrics` — métricas de desempenho por parceiro
* `sla\_breach\_events` — rastreamento de quebras de SLA

### O que está faltando (gaps críticos identificados)

|Gap|Impacto|
|-|-|
|`financial\_ledger` usa single-entry (não double-entry)|Impossível fechar balanço contábil|
|Não há billing B2B do serviço de locker para parceiros|Receita de aluguel não é cobrada automaticamente|
|Não há gestão de CAPEX/OPEX do hardware|Não é possível calcular margem de contribuição por locker|
|Não há P\&L por locker / região / parceiro|Decisão de expansão cega|
|Não há reconhecimento de receita (ASC 606 / IFRS 15)|Risco regulatório e contábil|
|`financial\_ledger` não tem `partner\_id`|Impossível segregar receita por cliente B2B|
|Sem snapshot diário de utilização por slot|Billing por utilização não é possível|
|Sem pipeline de cobrança automática (billing engine)|Processo manual e sujeito a erro|

\---

## 2\. ARQUITETURA FINANCEIRA RECOMENDADA

### 2.1 Visão geral dos dois planos financeiros

```
┌───────────────────────────────────────────────────────────────────┐
│                        ELLAN LAB                                   │
│                                                                    │
│  ┌─────────────────────────┐   ┌──────────────────────────────┐  │
│  │   PLANO A — B2B         │   │   PLANO B — GESTÃO INTERNA   │  │
│  │   (Parceiros pagam       │   │   (P\&L, CAPEX, OPEX,        │  │
│  │    pelo locker como      │   │   MRR, fluxo de caixa,      │  │
│  │    infraestrutura)       │   │   depreciação de hardware)   │  │
│  └─────────────────────────┘   └──────────────────────────────┘  │
│                                                                    │
│  Carriers / E-commerce / Comerciantes locais                      │
└───────────────────────────────────────────────────────────────────┘
```

\---

## 3\. NOVAS TABELAS DE BANCO DE DADOS RECOMENDADAS

> Todas em PostgreSQL. Usar `gen\_random\_uuid()::text` como padrão de PK.

\---

### 3.1 PLANO A — Billing B2B (cobrar parceiros pelo uso do locker)

#### `partner\_billing\_plans`

Define o modelo comercial de cada parceiro (mensalidade fixa, por-uso, híbrido).

```sql
CREATE TABLE public.partner\_billing\_plans (
    id                      VARCHAR(36)    PRIMARY KEY DEFAULT gen\_random\_uuid()::text,
    partner\_id              VARCHAR(36)    NOT NULL,
    partner\_type            VARCHAR(20)    NOT NULL, -- ECOMMERCE | LOGISTICS | LOCAL\_MERCHANT
    plan\_name               VARCHAR(128)   NOT NULL,
    billing\_model           VARCHAR(30)    NOT NULL, -- FLAT\_MONTHLY | PER\_USE | HYBRID | REVENUE\_SHARE
    currency                VARCHAR(8)     NOT NULL DEFAULT 'BRL',

    -- Mensalidade fixa (FLAT / HYBRID)
    monthly\_fee\_cents       BIGINT,

    -- Por uso (PER\_USE / HYBRID)
    fee\_per\_delivery\_cents  BIGINT,         -- cobrado por entrega armazenada
    fee\_per\_pickup\_cents    BIGINT,         -- cobrado por retirada
    fee\_per\_day\_stored\_cents BIGINT,        -- cobrado por dia de armazenagem
    free\_storage\_hours      INTEGER DEFAULT 72, -- horas gratuitas antes de cobrar diária

    -- Revenue share (quando Ellan Lab vende pelo parceiro)
    revenue\_share\_pct       NUMERIC(6,4),

    -- Limites contratuais
    min\_monthly\_fee\_cents   BIGINT,         -- piso de cobrança mensal
    included\_deliveries\_month INTEGER,      -- franquia de entregas por mês
    overage\_fee\_cents       BIGINT,         -- fee acima da franquia

    -- Vigência
    valid\_from              DATE           NOT NULL,
    valid\_until             DATE,
    is\_active               BOOLEAN        NOT NULL DEFAULT true,
    created\_at              TIMESTAMPTZ    NOT NULL DEFAULT now(),
    updated\_at              TIMESTAMPTZ    NOT NULL DEFAULT now(),

    CONSTRAINT ck\_pbp\_billing\_model CHECK (billing\_model IN (
        'FLAT\_MONTHLY','PER\_USE','HYBRID','REVENUE\_SHARE','FREE\_TIER'
    )),
    CONSTRAINT ck\_pbp\_partner\_type CHECK (partner\_type IN (
        'ECOMMERCE','LOGISTICS','LOCAL\_MERCHANT','CARRIER'
    ))
);

CREATE INDEX idx\_pbp\_partner ON partner\_billing\_plans(partner\_id, is\_active);
```

\---

#### `partner\_billing\_cycles`

Representa cada período de faturamento (mês a mês) de um parceiro. É o coração do billing engine.

```sql
CREATE TABLE public.partner\_billing\_cycles (
    id                      VARCHAR(36)    PRIMARY KEY DEFAULT gen\_random\_uuid()::text,
    partner\_id              VARCHAR(36)    NOT NULL,
    partner\_type            VARCHAR(20)    NOT NULL,
    billing\_plan\_id         VARCHAR(36)    NOT NULL REFERENCES partner\_billing\_plans(id),
    currency                VARCHAR(8)     NOT NULL DEFAULT 'BRL',

    -- Período
    period\_start            DATE           NOT NULL,
    period\_end              DATE           NOT NULL,

    -- Contadores de uso (computados pelo billing engine)
    total\_deliveries        INTEGER        NOT NULL DEFAULT 0,
    total\_pickups           INTEGER        NOT NULL DEFAULT 0,
    total\_slot\_days         NUMERIC(10,2)  NOT NULL DEFAULT 0, -- soma de (dias × nº slots usados)
    total\_overdue\_days      NUMERIC(10,2)  NOT NULL DEFAULT 0, -- dias além do SLA

    -- Valores calculados
    base\_fee\_cents          BIGINT         NOT NULL DEFAULT 0,  -- mensalidade
    usage\_fee\_cents         BIGINT         NOT NULL DEFAULT 0,  -- custo por uso
    overage\_fee\_cents       BIGINT         NOT NULL DEFAULT 0,  -- acima da franquia
    sla\_penalty\_cents       BIGINT         NOT NULL DEFAULT 0,  -- desconto por SLA
    discount\_cents          BIGINT         NOT NULL DEFAULT 0,  -- descontos comerciais
    tax\_cents               BIGINT         NOT NULL DEFAULT 0,  -- impostos B2B (ISS, PIS, COFINS)
    total\_amount\_cents      BIGINT         NOT NULL DEFAULT 0,  -- valor líquido a cobrar

    -- Status do ciclo
    status                  VARCHAR(20)    NOT NULL DEFAULT 'OPEN',
    -- OPEN → COMPUTING → REVIEW → APPROVED → INVOICED → PAID → DISPUTED | CANCELLED

    computed\_at             TIMESTAMPTZ,
    approved\_at             TIMESTAMPTZ,
    approved\_by             VARCHAR(36),
    invoiced\_at             TIMESTAMPTZ,
    paid\_at                 TIMESTAMPTZ,
    payment\_ref             VARCHAR(128),   -- referência do pagamento recebido
    dispute\_reason          TEXT,

    notes                   TEXT,
    created\_at              TIMESTAMPTZ    NOT NULL DEFAULT now(),
    updated\_at              TIMESTAMPTZ    NOT NULL DEFAULT now(),

    CONSTRAINT ck\_pbc\_status CHECK (status IN (
        'OPEN','COMPUTING','REVIEW','APPROVED','INVOICED','PAID','DISPUTED','CANCELLED'
    )),
    CONSTRAINT uq\_pbc\_partner\_period UNIQUE (partner\_id, period\_start, period\_end)
);

CREATE INDEX idx\_pbc\_partner\_period ON partner\_billing\_cycles(partner\_id, period\_start);
CREATE INDEX idx\_pbc\_status ON partner\_billing\_cycles(status) WHERE status NOT IN ('PAID','CANCELLED');
```

\---

#### `partner\_billing\_line\_items`

Linha a linha do que foi cobrado em cada ciclo. Auditabilidade completa.

```sql
CREATE TABLE public.partner\_billing\_line\_items (
    id                      BIGSERIAL      PRIMARY KEY,
    cycle\_id                VARCHAR(36)    NOT NULL REFERENCES partner\_billing\_cycles(id),
    partner\_id              VARCHAR(36)    NOT NULL,
    locker\_id               VARCHAR(36),

    line\_type               VARCHAR(40)    NOT NULL,
    -- BASE\_FEE | DELIVERY\_FEE | STORAGE\_DAY\_FEE | OVERAGE\_FEE
    -- SLA\_PENALTY | TAX\_ISS | TAX\_PIS | TAX\_COFINS | DISCOUNT | CREDIT\_NOTE

    description             VARCHAR(255)   NOT NULL,
    reference\_id            VARCHAR(36),   -- inbound\_delivery.id, order.id, etc.
    reference\_type          VARCHAR(40),   -- DELIVERY | ORDER | SLA\_BREACH | MANUAL

    quantity                NUMERIC(10,4)  NOT NULL DEFAULT 1,
    unit\_price\_cents        BIGINT         NOT NULL,
    total\_cents             BIGINT         NOT NULL, -- quantity × unit\_price\_cents
    currency                VARCHAR(8)     NOT NULL DEFAULT 'BRL',

    period\_from             TIMESTAMPTZ,
    period\_to               TIMESTAMPTZ,

    created\_at              TIMESTAMPTZ    NOT NULL DEFAULT now(),

    CONSTRAINT ck\_pbli\_type CHECK (line\_type IN (
        'BASE\_FEE','DELIVERY\_FEE','PICKUP\_FEE','STORAGE\_DAY\_FEE','OVERAGE\_FEE',
        'SLA\_PENALTY','TAX\_ISS','TAX\_PIS','TAX\_COFINS','DISCOUNT','CREDIT\_NOTE','ADJUSTMENT'
    ))
);

CREATE INDEX idx\_pbli\_cycle ON partner\_billing\_line\_items(cycle\_id);
CREATE INDEX idx\_pbli\_reference ON partner\_billing\_line\_items(reference\_id, reference\_type);
```

\---

#### `partner\_b2b\_invoices`

NFS-e ou documento fiscal B2B emitido pela Ellan Lab para o parceiro. Diferente das `invoices` (que são NFC-e B2C).

```sql
CREATE TABLE public.partner\_b2b\_invoices (
    id                      VARCHAR(36)    PRIMARY KEY DEFAULT gen\_random\_uuid()::text,
    cycle\_id                VARCHAR(36)    NOT NULL REFERENCES partner\_billing\_cycles(id),
    partner\_id              VARCHAR(36)    NOT NULL,

    invoice\_number          VARCHAR(50),    -- número da NFS-e
    invoice\_series          VARCHAR(10),
    access\_key              VARCHAR(120),
    document\_type           VARCHAR(20)    NOT NULL DEFAULT 'NFS\_E', -- NFS\_E | BOLETO | INVOICE\_PDF

    amount\_cents            BIGINT         NOT NULL,
    tax\_cents               BIGINT         NOT NULL DEFAULT 0,
    currency                VARCHAR(8)     NOT NULL DEFAULT 'BRL',

    due\_date                DATE,
    payment\_method          VARCHAR(30),   -- BOLETO | PIX | TED | WIRE

    -- Dados do emitente (Ellan Lab)
    emitter\_cnpj            VARCHAR(18)    NOT NULL,
    emitter\_name            VARCHAR(140)   NOT NULL,

    -- Dados do tomador (parceiro)
    taker\_cnpj              VARCHAR(18),
    taker\_name              VARCHAR(140),
    taker\_email             VARCHAR(128),

    status                  VARCHAR(20)    NOT NULL DEFAULT 'DRAFT',
    -- DRAFT → ISSUED → SENT → VIEWED → PAID | OVERDUE | CANCELLED

    issued\_at               TIMESTAMPTZ,
    sent\_at                 TIMESTAMPTZ,
    paid\_at                 TIMESTAMPTZ,
    cancelled\_at            TIMESTAMPTZ,
    cancel\_reason           TEXT,

    pdf\_url                 VARCHAR(500),
    xml\_content             JSONB,
    government\_response     JSONB,

    created\_at              TIMESTAMPTZ    NOT NULL DEFAULT now(),
    updated\_at              TIMESTAMPTZ    NOT NULL DEFAULT now(),

    CONSTRAINT ck\_pbi\_status CHECK (status IN (
        'DRAFT','ISSUED','SENT','VIEWED','PAID','OVERDUE','DISPUTED','CANCELLED'
    ))
);

CREATE INDEX idx\_pbi\_partner ON partner\_b2b\_invoices(partner\_id, status);
CREATE INDEX idx\_pbi\_due ON partner\_b2b\_invoices(due\_date) WHERE status IN ('ISSUED','SENT','OVERDUE');
```

\---

#### `partner\_credit\_notes`

Notas de crédito emitidas pela Ellan Lab ao parceiro (por SLA breach, downtime, ajuste comercial).

```sql
CREATE TABLE public.partner\_credit\_notes (
    id                      VARCHAR(36)    PRIMARY KEY DEFAULT gen\_random\_uuid()::text,
    partner\_id              VARCHAR(36)    NOT NULL,
    original\_invoice\_id     VARCHAR(36)    REFERENCES partner\_b2b\_invoices(id),
    cycle\_id                VARCHAR(36)    REFERENCES partner\_billing\_cycles(id),

    reason\_code             VARCHAR(40)    NOT NULL,
    -- SLA\_BREACH | HARDWARE\_DOWNTIME | COMMERCIAL\_ADJUSTMENT | DUPLICATE | OTHER

    description             TEXT           NOT NULL,
    amount\_cents            BIGINT         NOT NULL,
    currency                VARCHAR(8)     NOT NULL DEFAULT 'BRL',

    status                  VARCHAR(20)    NOT NULL DEFAULT 'PENDING',
    -- PENDING → APPROVED → APPLIED | REFUNDED | EXPIRED

    approved\_by             VARCHAR(36),
    approved\_at             TIMESTAMPTZ,
    applied\_to\_cycle\_id     VARCHAR(36),   -- qual ciclo foi creditado
    applied\_at              TIMESTAMPTZ,
    expires\_at              TIMESTAMPTZ,

    created\_at              TIMESTAMPTZ    NOT NULL DEFAULT now(),
    updated\_at              TIMESTAMPTZ    NOT NULL DEFAULT now()
);
```

\---

#### `locker\_utilization\_snapshots`

Snapshot diário de utilização de cada locker — base de cálculo para billing por uso e análise de capacidade.

```sql
CREATE TABLE public.locker\_utilization\_snapshots (
    id                      BIGSERIAL      PRIMARY KEY,
    locker\_id               VARCHAR(36)    NOT NULL,
    snapshot\_date           DATE           NOT NULL,

    -- Capacidade
    total\_slots             INTEGER        NOT NULL,
    active\_slots            INTEGER        NOT NULL,

    -- Ocupação no final do dia
    occupied\_slots\_eod      INTEGER        NOT NULL DEFAULT 0,
    utilization\_rate\_pct    NUMERIC(5,2)   GENERATED ALWAYS AS (
                                CASE WHEN active\_slots > 0
                                THEN ROUND((occupied\_slots\_eod::NUMERIC / active\_slots) \* 100, 2)
                                ELSE 0 END
                            ) STORED,

    -- Movimentação no dia
    deliveries\_received     INTEGER        NOT NULL DEFAULT 0,
    pickups\_completed       INTEGER        NOT NULL DEFAULT 0,
    expirations             INTEGER        NOT NULL DEFAULT 0,
    returns\_generated       INTEGER        NOT NULL DEFAULT 0,

    -- Para billing por tempo de armazenagem
    total\_slot\_days\_used    NUMERIC(10,4)  NOT NULL DEFAULT 0,
    -- soma de (horas\_ocupadas / 24) por slot no dia

    -- Receita bruta gerada no dia (B2C + B2B)
    gross\_revenue\_cents     BIGINT         NOT NULL DEFAULT 0,
    b2c\_revenue\_cents       BIGINT         NOT NULL DEFAULT 0,
    b2b\_fee\_cents           BIGINT         NOT NULL DEFAULT 0, -- fee cobrado do parceiro

    -- SLA
    sla\_breaches\_count      INTEGER        NOT NULL DEFAULT 0,
    avg\_pickup\_hours        NUMERIC(6,2),

    computed\_at             TIMESTAMPTZ    NOT NULL DEFAULT now(),

    CONSTRAINT uq\_lus\_locker\_date UNIQUE (locker\_id, snapshot\_date)
);

CREATE INDEX idx\_lus\_date ON locker\_utilization\_snapshots(snapshot\_date);
CREATE INDEX idx\_lus\_locker\_date ON locker\_utilization\_snapshots(locker\_id, snapshot\_date);
```

\---

### 3.2 PLANO B — Gestão Financeira Interna da Ellan Lab

#### `financial\_ledger\_v2` — Double-Entry Bookkeeping

Substituir (ou complementar) o `financial\_ledger` existente por um modelo de partidas dobradas, que é o padrão adotado por todas as plataformas financeiras sérias (Stripe, Adyen, Airbnb).

```sql
-- Plano de contas (Chart of Accounts)
CREATE TABLE public.chart\_of\_accounts (
    id                      VARCHAR(36)    PRIMARY KEY DEFAULT gen\_random\_uuid()::text,
    code                    VARCHAR(20)    NOT NULL UNIQUE,  -- ex: '1.1.01', '4.2.03'
    name                    VARCHAR(128)   NOT NULL,
    account\_type            VARCHAR(20)    NOT NULL,
    -- ASSET | LIABILITY | EQUITY | REVENUE | EXPENSE

    normal\_balance          VARCHAR(6)     NOT NULL,
    -- DEBIT | CREDIT (define qual lado aumenta a conta)

    parent\_code             VARCHAR(20),   -- hierarquia
    is\_active               BOOLEAN        NOT NULL DEFAULT true,
    description             TEXT,
    created\_at              TIMESTAMPTZ    NOT NULL DEFAULT now(),

    CONSTRAINT ck\_coa\_type CHECK (account\_type IN (
        'ASSET','LIABILITY','EQUITY','REVENUE','EXPENSE'
    )),
    CONSTRAINT ck\_coa\_balance CHECK (normal\_balance IN ('DEBIT','CREDIT'))
);

-- Diário contábil (Journal Entries)
CREATE TABLE public.journal\_entries (
    id                      VARCHAR(36)    PRIMARY KEY DEFAULT gen\_random\_uuid()::text,
    entry\_date              DATE           NOT NULL,
    description             VARCHAR(255)   NOT NULL,
    reference\_type          VARCHAR(50),
    -- ORDER | BILLING\_CYCLE | CAPEX | OPEX | PAYROLL | ADJUSTMENT

    reference\_id            VARCHAR(36),
    currency                VARCHAR(8)     NOT NULL DEFAULT 'BRL',
    is\_posted               BOOLEAN        NOT NULL DEFAULT false,
    posted\_at               TIMESTAMPTZ,
    posted\_by               VARCHAR(36),
    created\_by              VARCHAR(36),
    created\_at              TIMESTAMPTZ    NOT NULL DEFAULT now()
);

-- Linhas do diário (Debits e Credits sempre balanceados)
CREATE TABLE public.journal\_entry\_lines (
    id                      BIGSERIAL      PRIMARY KEY,
    journal\_entry\_id        VARCHAR(36)    NOT NULL REFERENCES journal\_entries(id),
    account\_code            VARCHAR(20)    NOT NULL REFERENCES chart\_of\_accounts(code),
    side                    VARCHAR(6)     NOT NULL, -- DEBIT | CREDIT
    amount\_cents            BIGINT         NOT NULL CHECK (amount\_cents > 0),
    currency                VARCHAR(8)     NOT NULL DEFAULT 'BRL',
    memo                    VARCHAR(255),
    created\_at              TIMESTAMPTZ    NOT NULL DEFAULT now(),

    CONSTRAINT ck\_jel\_side CHECK (side IN ('DEBIT','CREDIT'))
);

-- Constraint: todo journal\_entry deve ter soma DEBIT = soma CREDIT
-- Implementar como trigger ou validação no service layer.

CREATE INDEX idx\_jel\_entry ON journal\_entry\_lines(journal\_entry\_id);
CREATE INDEX idx\_jel\_account ON journal\_entry\_lines(account\_code, journal\_entry\_id);
```

**Exemplo de plano de contas mínimo para a Ellan Lab:**

|Código|Nome|Tipo|Balanço Normal|
|-|-|-|-|
|1.1.01|Caixa e Equivalentes|ASSET|DEBIT|
|1.1.02|Contas a Receber — Parceiros|ASSET|DEBIT|
|1.2.01|Hardware — Lockers (CAPEX)|ASSET|DEBIT|
|1.2.02|(-) Depreciação Acumulada|ASSET|CREDIT|
|2.1.01|Contas a Pagar — Fornecedores|LIABILITY|CREDIT|
|2.1.02|Impostos a Recolher|LIABILITY|CREDIT|
|4.1.01|Receita — Aluguel de Locker|REVENUE|CREDIT|
|4.1.02|Receita — Compartilhamento de Receita|REVENUE|CREDIT|
|4.1.03|Receita — Taxas por Uso|REVENUE|CREDIT|
|5.1.01|Custo de Energia|EXPENSE|DEBIT|
|5.1.02|Custo de Conectividade (SIM/WiFi)|EXPENSE|DEBIT|
|5.1.03|Custo de Manutenção|EXPENSE|DEBIT|
|5.2.01|Depreciação de Hardware|EXPENSE|DEBIT|
|5.3.01|Custos de Gateway de Pagamento|EXPENSE|DEBIT|
|5.3.02|Custos de Emissão Fiscal|EXPENSE|DEBIT|

\---

#### `ellanlab\_hardware\_assets`

Inventário e depreciação dos lockers físicos (CAPEX).

```sql
CREATE TABLE public.ellanlab\_hardware\_assets (
    id                      VARCHAR(36)    PRIMARY KEY DEFAULT gen\_random\_uuid()::text,
    locker\_id               VARCHAR(36)    REFERENCES lockers(id),
    asset\_tag               VARCHAR(64)    NOT NULL UNIQUE,
    asset\_type              VARCHAR(30)    NOT NULL DEFAULT 'LOCKER\_UNIT',
    description             VARCHAR(255)   NOT NULL,

    -- Custo
    acquisition\_cost\_cents  BIGINT         NOT NULL,
    currency                VARCHAR(8)     NOT NULL DEFAULT 'BRL',
    acquisition\_date        DATE           NOT NULL,
    supplier                VARCHAR(128),
    invoice\_ref             VARCHAR(64),    -- NF de compra

    -- Depreciação
    depreciation\_method     VARCHAR(20)    NOT NULL DEFAULT 'STRAIGHT\_LINE',
    -- STRAIGHT\_LINE | DECLINING\_BALANCE | UNITS\_OF\_PRODUCTION

    useful\_life\_months      INTEGER        NOT NULL DEFAULT 60, -- 5 anos padrão
    residual\_value\_cents    BIGINT         NOT NULL DEFAULT 0,
    depreciation\_start\_date DATE,

    -- Estado atual
    current\_book\_value\_cents BIGINT,       -- atualizado mensalmente
    status                  VARCHAR(20)    NOT NULL DEFAULT 'ACTIVE',
    -- ACTIVE | MAINTENANCE | RETIRED | WRITTEN\_OFF | SOLD | LEASED

    retired\_at              DATE,
    retire\_reason           VARCHAR(255),

    installation\_address    JSONB,
    metadata\_json           JSONB          NOT NULL DEFAULT '{}',
    created\_at              TIMESTAMPTZ    NOT NULL DEFAULT now(),
    updated\_at              TIMESTAMPTZ    NOT NULL DEFAULT now()
);

CREATE INDEX idx\_eha\_locker ON ellanlab\_hardware\_assets(locker\_id);
CREATE INDEX idx\_eha\_status ON ellanlab\_hardware\_assets(status);
```

\---

#### `ellanlab\_depreciation\_schedule`

Cronograma mensal de depreciação por ativo.

```sql
CREATE TABLE public.ellanlab\_depreciation\_schedule (
    id                      BIGSERIAL      PRIMARY KEY,
    asset\_id                VARCHAR(36)    NOT NULL REFERENCES ellanlab\_hardware\_assets(id),
    period\_month            CHAR(7)        NOT NULL, -- ex: '2026-04'
    book\_value\_start\_cents  BIGINT         NOT NULL,
    depreciation\_cents      BIGINT         NOT NULL,
    book\_value\_end\_cents    BIGINT         NOT NULL,
    is\_posted               BOOLEAN        NOT NULL DEFAULT false,
    journal\_entry\_id        VARCHAR(36),   -- lançamento contábil associado
    computed\_at             TIMESTAMPTZ    NOT NULL DEFAULT now(),

    CONSTRAINT uq\_eds\_asset\_period UNIQUE (asset\_id, period\_month)
);
```

\---

#### `ellanlab\_opex\_entries`

Registro de despesas operacionais por locker/região (energia, conectividade, manutenção).

```sql
CREATE TABLE public.ellanlab\_opex\_entries (
    id                      VARCHAR(36)    PRIMARY KEY DEFAULT gen\_random\_uuid()::text,
    locker\_id               VARCHAR(36),   -- NULL = despesa geral da empresa
    cost\_center             VARCHAR(64),   -- ex: 'LOCKER\_SP\_01', 'TI\_INFRA', 'FISCAL'
    category                VARCHAR(40)    NOT NULL,
    -- ENERGY | CONNECTIVITY | MAINTENANCE | CLEANING | INSURANCE
    -- PLATFORM\_FEES | PAYMENT\_GATEWAY | FISCAL\_ISSUANCE | HEADCOUNT | RENT | OTHER

    description             VARCHAR(255)   NOT NULL,
    amount\_cents            BIGINT         NOT NULL,
    currency                VARCHAR(8)     NOT NULL DEFAULT 'BRL',

    competence\_month        CHAR(7)        NOT NULL, -- mês de competência
    supplier                VARCHAR(128),
    invoice\_ref             VARCHAR(64),
    payment\_date            DATE,

    account\_code            VARCHAR(20),   -- conta do plano de contas
    journal\_entry\_id        VARCHAR(36),
    is\_recurring            BOOLEAN        NOT NULL DEFAULT false,
    approved\_by             VARCHAR(36),
    created\_by              VARCHAR(36)    NOT NULL,
    created\_at              TIMESTAMPTZ    NOT NULL DEFAULT now(),
    updated\_at              TIMESTAMPTZ    NOT NULL DEFAULT now()
);

CREATE INDEX idx\_eoe\_locker\_month ON ellanlab\_opex\_entries(locker\_id, competence\_month);
CREATE INDEX idx\_eoe\_category ON ellanlab\_opex\_entries(category, competence\_month);
```

\---

#### `ellanlab\_monthly\_pnl`

P\&L consolidado mensal por locker e por empresa — snapshot para dashboards e relatórios.

```sql
CREATE TABLE public.ellanlab\_monthly\_pnl (
    id                      BIGSERIAL      PRIMARY KEY,
    period\_month            CHAR(7)        NOT NULL,
    locker\_id               VARCHAR(36),   -- NULL = totais da empresa

    -- RECEITAS
    revenue\_rental\_cents         BIGINT  NOT NULL DEFAULT 0, -- mensalidade do parceiro
    revenue\_per\_use\_cents        BIGINT  NOT NULL DEFAULT 0, -- billing por uso
    revenue\_b2c\_cents            BIGINT  NOT NULL DEFAULT 0, -- venda direta ao usuário final
    revenue\_overage\_cents        BIGINT  NOT NULL DEFAULT 0, -- excedentes
    revenue\_total\_cents          BIGINT  NOT NULL DEFAULT 0,

    -- DEDUÇÕES
    credit\_notes\_cents           BIGINT  NOT NULL DEFAULT 0, -- notas de crédito emitidas
    refunds\_cents                BIGINT  NOT NULL DEFAULT 0, -- devoluções B2C
    sla\_penalties\_cents          BIGINT  NOT NULL DEFAULT 0, -- penalidades por SLA
    net\_revenue\_cents            BIGINT  NOT NULL DEFAULT 0,

    -- CUSTOS DIRETOS
    opex\_energy\_cents            BIGINT  NOT NULL DEFAULT 0,
    opex\_connectivity\_cents      BIGINT  NOT NULL DEFAULT 0,
    opex\_maintenance\_cents       BIGINT  NOT NULL DEFAULT 0,
    opex\_payment\_gateway\_cents   BIGINT  NOT NULL DEFAULT 0,
    opex\_fiscal\_issuance\_cents   BIGINT  NOT NULL DEFAULT 0,
    depreciation\_cents           BIGINT  NOT NULL DEFAULT 0,
    opex\_total\_cents             BIGINT  NOT NULL DEFAULT 0,

    -- MARGENS
    gross\_profit\_cents           BIGINT  NOT NULL DEFAULT 0, -- net\_revenue - opex\_total
    gross\_margin\_pct             NUMERIC(5,2),

    -- Métricas operacionais (desnormalizado para performance de dashboard)
    active\_lockers               INTEGER NOT NULL DEFAULT 0,
    total\_deliveries             INTEGER NOT NULL DEFAULT 0,
    avg\_utilization\_pct          NUMERIC(5,2),
    arpl\_cents                   BIGINT,  -- Average Revenue Per Locker

    computed\_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    is\_final                     BOOLEAN NOT NULL DEFAULT false, -- false até o fechamento do mês

    CONSTRAINT uq\_emp\_month\_locker UNIQUE (period\_month, locker\_id)
);

CREATE INDEX idx\_emp\_period ON ellanlab\_monthly\_pnl(period\_month);
```

\---

#### `ellanlab\_revenue\_recognition`

Reconhecimento de receita ao longo do tempo (ASC 606 / IFRS 15). Crítico para contratos de aluguel multi-mês.

```sql
CREATE TABLE public.ellanlab\_revenue\_recognition (
    id                      BIGSERIAL      PRIMARY KEY,
    source\_type             VARCHAR(40)    NOT NULL,
    -- BILLING\_CYCLE | RENTAL\_CONTRACT | PARTNER\_PREPAYMENT

    source\_id               VARCHAR(36)    NOT NULL,
    partner\_id              VARCHAR(36),
    locker\_id               VARCHAR(36),

    total\_contract\_cents    BIGINT         NOT NULL,  -- valor total do contrato
    recognition\_period      CHAR(7)        NOT NULL,  -- mês de reconhecimento

    recognized\_cents        BIGINT         NOT NULL,  -- quanto reconhecer neste mês
    deferred\_cents          BIGINT         NOT NULL DEFAULT 0, -- saldo diferido restante

    is\_posted               BOOLEAN        NOT NULL DEFAULT false,
    journal\_entry\_id        VARCHAR(36),
    posted\_at               TIMESTAMPTZ,

    created\_at              TIMESTAMPTZ    NOT NULL DEFAULT now(),

    CONSTRAINT uq\_err\_source\_period UNIQUE (source\_type, source\_id, recognition\_period)
);
```

\---

#### `financial\_kpi\_daily`

Snapshots diários de KPIs financeiros para alimentar dashboards em tempo quase-real.

```sql
CREATE TABLE public.financial\_kpi\_daily (
    id                      BIGSERIAL      PRIMARY KEY,
    kpi\_date                DATE           NOT NULL,
    scope\_type              VARCHAR(20)    NOT NULL DEFAULT 'COMPANY',
    -- COMPANY | LOCKER | PARTNER | REGION

    scope\_id                VARCHAR(36),   -- locker\_id ou partner\_id, NULL para COMPANY

    -- Receita
    gmv\_cents               BIGINT         NOT NULL DEFAULT 0,  -- Gross Merchandise Value
    net\_revenue\_cents       BIGINT         NOT NULL DEFAULT 0,
    mrr\_cents               BIGINT         NOT NULL DEFAULT 0,  -- MRR estimado

    -- Atividade
    new\_orders              INTEGER        NOT NULL DEFAULT 0,
    completed\_pickups       INTEGER        NOT NULL DEFAULT 0,
    failed\_payments         INTEGER        NOT NULL DEFAULT 0,
    refunds\_count           INTEGER        NOT NULL DEFAULT 0,
    refunds\_cents           BIGINT         NOT NULL DEFAULT 0,

    -- Utilização
    active\_lockers          INTEGER        NOT NULL DEFAULT 0,
    avg\_utilization\_pct     NUMERIC(5,2),

    -- Saúde financeira
    accounts\_receivable\_cents BIGINT       NOT NULL DEFAULT 0, -- a receber de parceiros
    overdue\_invoices\_count  INTEGER        NOT NULL DEFAULT 0,

    computed\_at             TIMESTAMPTZ    NOT NULL DEFAULT now(),

    CONSTRAINT uq\_fkd\_date\_scope UNIQUE (kpi\_date, scope\_type, scope\_id)
);
```

\---

## 4\. ARQUITETURA DO BILLING ENGINE

A recomendação é criar um microserviço dedicado: `billing\_service`.

```
Eventos de domínio (domain\_event\_outbox)
    ↓
billing\_event\_consumer
    ↓ 
\[accumula em partner\_billing\_line\_items]
    ↓
billing\_cycle\_compute\_worker (roda à meia-noite todo dia)
    ↓
\[fecha partner\_billing\_cycles mensalmente]
    ↓
billing\_approval\_workflow (review manual ou automático)
    ↓
b2b\_invoice\_issuer\_worker
    ↓
\[emite NFS-e + envia ao parceiro por email/webhook]
    ↓
payment\_reconciliation\_worker
    ↓
\[marca como PAID no recebimento]
    ↓
revenue\_recognition\_worker
    ↓
\[lança em journal\_entries]
```

**Princípios do Billing Engine (melhores práticas mundiais):**

* **Idempotência total**: Cada cálculo de linha deve ser re-executável sem duplicar valores. Usar `dedupe\_key` baseado em `(partner\_id, reference\_id, line\_type)`.
* **Audit trail imutável**: Linhas de billing nunca são deletadas, apenas anuladas com linha negativa.
* **Separação de concerns**: O engine calcula, humano aprova, worker emite. Nunca automatizar 100% sem revisão nos primeiros 6 meses.
* **Moeda em centavos**: Já praticado no projeto — manter.
* **Timezone UTC no storage, localtime na apresentação**: Já praticado — manter.

\---

## 5\. KPIs — MÉTRICAS DE DESEMPENHO FINANCEIRO

### 5.1 KPIs para o Portal do Parceiro

|KPI|Definição|Frequência|
|-|-|-|
|**GMV Mensal**|Valor bruto de todas as transações do parceiro|Diário|
|**Faturamento a Receber**|Valor da fatura do ciclo atual|Mensal|
|**Taxa de Utilização do Locker**|% de slots ocupados / slots disponíveis|Diário|
|**Tempo Médio de Retirada**|Avg horas entre stored\_at e picked\_up\_at|Semanal|
|**Taxa de Conformidade SLA**|% de entregas dentro do SLA contratado|Semanal|
|**Taxa de Expiração**|% de entregas expiradas sem retirada|Mensal|
|**Custo por Entrega**|(Fee de armazenagem + uso) / total\_deliveries|Mensal|
|**Webhooks Success Rate**|% de webhooks entregues com sucesso|Diário|

### 5.2 KPIs Internos da Ellan Lab

#### Receita

|KPI|Definição|Meta de Mercado|
|-|-|-|
|**MRR** (Monthly Recurring Revenue)|Soma das receitas mensais recorrentes dos parceiros|Crescimento M/M ≥ 10%|
|**ARR**|MRR × 12|—|
|**ARPL** (Avg Revenue Per Locker)|Net Revenue / Nº de lockers ativos|—|
|**Net Revenue Retention**|(MRR mês N / MRR mês N-12)|≥ 110% (best-in-class)|
|**Revenue Mix**|% de cada fonte: aluguel / por-uso / B2C|—|

#### Custo e Margem

|KPI|Definição|Referência|
|-|-|-|
|**Gross Margin por Locker**|(Net Revenue - OPEX direto) / Net Revenue|Melhores: ≥ 60%|
|**EBITDA por Locker**|Gross Profit - Overhead alocado|—|
|**Payback Period**|CAPEX do locker / Gross Profit mensal|Meta: ≤ 18 meses|
|**LTV do Parceiro**|Gross Profit esperado durante toda a vida do contrato|—|
|**CAC** (Customer Acquisition Cost)|Custo de onboarding + comercial / novos parceiros|—|
|**LTV:CAC Ratio**|LTV / CAC|≥ 3:1 saudável|

#### Saúde do Portfólio

|KPI|Definição|Alert|
|-|-|-|
|**Dias de Recebimento (DSO)**|Média de dias para receber após fatura emitida|> 45 dias = risco|
|**Taxa de Inadimplência**|Valor vencido > 60 dias / Total faturado|> 5% = crítico|
|**Churn de Parceiros**|Parceiros cancelados / total do mês anterior|> 2% = crítico|

#### Operacional / Erro

|KPI|Definição|Alert|
|-|-|-|
|**Taxa de Falha de Emissão Fiscal**|invoices com status FAILED / total|> 1% = alerta|
|**Taxa de Reconciliação Pendente**|reconciliation\_pending OPEN / orders|> 0.5%|
|**Taxa de Falha de Webhook B2B**|partner\_webhook\_deliveries FAILED / total|> 2%|
|**Billing Cycle Compute Time**|Tempo para calcular um ciclo completo|> 30 min = alerta|
|**Dead Letter Rate**|invoices em DEAD\_LETTER / total|> 0.1%|

\---

## 6\. FERRAMENTAS RECOMENDADAS

### 6.1 Stack de Observabilidade Financeira

```
┌─────────────────────────────────────────────────────────────────┐
│  COLETA              ARMAZENAMENTO         VISUALIZAÇÃO         │
│                                                                  │
│  PostgreSQL ─────→  TimescaleDB        ─→  Grafana              │
│  (financial\_kpi\_     (hypertable para      (dashboards ops       │
│   daily, snapshots)   séries temporais)     e financeiro)        │
│                                                                  │
│  Microserviços ──→  Prometheus         ─→  Grafana Alerting      │
│  (métricas de        (métricas de          (alertas PagerDuty/   │
│   billing engine)    runtime)              Slack)                │
│                                                                  │
│  PostgreSQL ──────→ dbt Core           ─→  Metabase             │
│  (tabelas raw)       (transformações        (portal financeiro    │
│                       e modelos de dados)   para parceiros e     │
│                                             equipe interna)      │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Ferramentas detalhadas

|Ferramenta|Papel|Motivo|
|-|-|-|
|**dbt Core** (open-source)|Transformação de dados e camada semântica de métricas|Padrão mundial para data pipelines analíticos. Define modelos `partner\_revenue\_monthly`, `locker\_pnl`, etc. Versiona SQL como código.|
|**Metabase** (open-source)|Dashboard financeiro para parceiros e equipe|Self-hosted, interface amigável para não-técnicos, embutível no portal do parceiro via iframe com autenticação. Alternativa: Apache Superset.|
|**Grafana**|Dashboards operacionais em tempo real|Já amplamente adotado com Prometheus. Excelente para billing engine health, latência de workers, fila de retries.|
|**Prometheus**|Métricas de runtime dos workers|Exportar métricas como: `billing\_cycle\_compute\_duration\_seconds`, `b2b\_invoice\_issue\_total`, `credit\_note\_applied\_total`.|
|**Apache Airflow** (ou Prefect)|Orquestração do billing pipeline|Scheduling do `billing\_cycle\_compute\_worker`, `depreciation\_worker`, `pnl\_snapshot\_worker`, `kpi\_daily\_worker`.|
|**TimescaleDB**|Extensão PostgreSQL para time-series|Ativar em `financial\_kpi\_daily` e `locker\_utilization\_snapshots` para queries analíticas 10-100× mais rápidas.|
|**Great Expectations**|Validação de qualidade de dados financeiros|Garantir que `sum(DEBIT) = sum(CREDIT)` em todo `journal\_entry`, que `billing\_cycle.total\_amount\_cents = sum(line\_items)`, etc.|

### 6.3 Ativar TimescaleDB (já usa PostgreSQL 15)

```sql
-- No init do banco
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Converter tabelas de séries temporais
SELECT create\_hypertable(
    'locker\_utilization\_snapshots', 
    'snapshot\_date', 
    chunk\_time\_interval => INTERVAL '1 month'
);

SELECT create\_hypertable(
    'financial\_kpi\_daily', 
    'kpi\_date', 
    chunk\_time\_interval => INTERVAL '1 month'
);
```

\---

## 7\. PORTAL FINANCEIRO DO PARCEIRO — APIs Recomendadas

Expor via `billing\_service` (novo microserviço):

```
GET  /v1/partners/{id}/billing/current-cycle
     → Ciclo atual: valor acumulado, linha a linha, previsão de faturamento

GET  /v1/partners/{id}/billing/cycles?year=2026
     → Histórico de ciclos de faturamento

GET  /v1/partners/{id}/invoices?status=PAID\&from=2026-01-01
     → Faturas emitidas pela Ellan Lab

GET  /v1/partners/{id}/credit-notes
     → Créditos disponíveis e histórico

GET  /v1/partners/{id}/lockers/utilization?month=2026-04
     → Utilização por locker: entregas, retiradas, ocupação, SLA

GET  /v1/partners/{id}/kpis/dashboard
     → KPIs consolidados: GMV, conformidade SLA, custo por entrega

POST /v1/partners/{id}/billing/cycles/{cycle\_id}/dispute
     → Abrir contestação de fatura
```

\---

## 8\. ROADMAP DE IMPLEMENTAÇÃO RECOMENDADO

### Fase 1 — Fundação (4–6 semanas)

Prioridade máxima, sem isso o billing não fecha.

1. Criar `partner\_billing\_plans` e migrar dados de `ecommerce\_partners.revenue\_share\_pct`
2. Criar `partner\_billing\_cycles` e `partner\_billing\_line\_items`
3. Criar `locker\_utilization\_snapshots` + worker diário de snapshot
4. Criar `chart\_of\_accounts` e `journal\_entries` / `journal\_entry\_lines`
5. Refatorar `financial\_ledger` para lançar também em `journal\_entry\_lines` (double-entry)

### Fase 2 — Billing Engine (6–8 semanas)

6. Billing event consumer (consome domain events → linha de billing)
7. `billing\_cycle\_compute\_worker` (fecha ciclo mensalmente com idempotência)
8. `partner\_b2b\_invoices` + integração com emissor NFS-e
9. Portal do parceiro: APIs de billing + Metabase embedded

### Fase 3 — Gestão Interna (4–6 semanas)

10. `ellanlab\_hardware\_assets` + `ellanlab\_depreciation\_schedule` + worker mensal
11. `ellanlab\_opex\_entries` + interface de lançamento para o time de operações
12. `ellanlab\_monthly\_pnl` + worker de consolidação
13. `ellanlab\_revenue\_recognition` (contratos multi-mês)

### Fase 4 — Analytics \& Observabilidade (4 semanas)

14. Ativar TimescaleDB nas tabelas de séries
15. dbt models: `partner\_revenue\_monthly`, `locker\_pnl`, `company\_mrr\_trend`
16. Grafana: dashboard operacional do billing engine
17. Metabase: dashboard financeiro interno
18. Great Expectations: suite de testes de qualidade de dados financeiros

\---

## 9\. BOAS PRÁTICAS DE PROGRAMAÇÃO — RESUMO EXECUTIVO

|Princípio|Implementação|
|-|-|
|**Double-entry bookkeeping**|Todo lançamento financeiro gera par DEBIT/CREDIT|
|**Idempotência em billing**|`dedupe\_key` em todas as linhas de cobrança|
|**Imutabilidade de registros**|Nunca `DELETE` em dados financeiros; usar `is\_voided` + linha de estorno|
|**Separação de concerns**|billing\_service isolado, nunca acoplado ao order\_lifecycle\_service|
|**Event-driven billing**|Billing reage a events do domain\_event\_outbox, não faz polling de orders|
|**Aprovação humana**|Ciclos de billing passam por REVIEW antes de INVOICED (primeiros 6 meses)|
|**Auditoria completa**|Toda mudança de status em ciclo/fatura registra `changed\_by` e `changed\_at`|
|**Multi-moeda desde o dia 1**|Armazenar `currency` em toda tabela financeira (BRL, EUR, USD)|
|**Fuso horário**|Storage UTC, apresentação em timezone do parceiro/locker|
|**Testes de dados**|Great Expectations ou dbt tests validando invariantes financeiros|

\---

*Documento gerado para uso interno do time de desenvolvimento — ELLAN LAB © 2026*





*Excelente iniciativa estruturar o ELLAN LAB com visão de longo prazo e padrão global. O documento apresentado demonstra maturidade técnica e clareza sobre os gaps existentes, mas como avaliador, preciso destacar pontos críticos que podem inviabilizar a implementação ou gerar risco financeiro/regulatório se não forem ajustados.*



*Abaixo minha avaliação estruturada, dividida em: (1) pontos fortes, (2) riscos e correções obrigatórias, (3) recomendações incrementais de melhoria, (4) nova tabela crítica ausente, (5) sugestão de priorização diferente.*



*1. PONTOS FORTES (o que está excelente)*

*✅ Double-entry accounting – substituir financial\_ledger single-entry é mandatório.*

*✅ Separação B2B × B2C – partner\_b2b\_invoices distinta de invoices (B2C) evita confusão fiscal.*

*✅ Utilization snapshots diários – base sólida para billing por uso e análise de capacidade.*

*✅ Depreciação de hardware – raro em plataformas de locker, mas essencial para P\&L real.*

*✅ Event-driven billing com idempotência – padrão Stripe/Adyen.*

*✅ KPIs bem definidos – especialmente LTV:CAC, DSO, churn.*



*2. RISCOS E CORREÇÕES OBRIGATÓRIAS (antes de qualquer implementação)*

*❌ CRÍTICO 1: locker\_utilization\_snapshots usa DATE como única chave temporal, mas lockers operam 24h e SLA é por hora*

*Problema:*

*Um item entregue às 23h59 ocupa o slot por 1 minuto no dia D, mas gera cobrança de dia inteiro se seu free\_storage\_hours = 72. Além disso, SLA breach (ex: retirada após 48h) precisa de precisão horária.*



*Correção obrigatória:*



*sql*

*-- Adicionar à tabela existente, sem quebrar compatibilidade*

*ALTER TABLE public.locker\_utilization\_snapshots* 

*ADD COLUMN snapshot\_hour TIMESTAMPTZ,  -- opcional, mas para granularidade fina*

*ADD COLUMN total\_slot\_hours\_used NUMERIC(10,4) NOT NULL DEFAULT 0;*



*-- Nova tabela para rastreamento por hora (billing mais justo)*

*CREATE TABLE public.locker\_slot\_hourly\_occupancy (*

&#x20;   *id                      BIGSERIAL PRIMARY KEY,*

&#x20;   *locker\_id               VARCHAR(36) NOT NULL,*

&#x20;   *slot\_number             INTEGER NOT NULL,*

&#x20;   *hour\_bucket             TIMESTAMPTZ NOT NULL,  -- início da hora (UTC)*

&#x20;   *is\_occupied             BOOLEAN NOT NULL,*

&#x20;   *delivery\_id             VARCHAR(36),*

&#x20;   *occupied\_duration\_minutes INTEGER NOT NULL DEFAULT 0,*

&#x20;   *created\_at              TIMESTAMPTZ NOT NULL DEFAULT now()*

*);*



*CREATE INDEX idx\_lsho\_locker\_hour ON locker\_slot\_hourly\_occupancy(locker\_id, hour\_bucket);*

*-- Reter apenas 90 dias (billing mensal + 2 meses para reconciliação)*

*SELECT create\_hypertable('locker\_slot\_hourly\_occupancy', 'hour\_bucket',* 

&#x20;   *chunk\_time\_interval => INTERVAL '1 day',* 

&#x20;   *retention\_policy => INTERVAL '90 days');*

*Por que isso é crítico:*

*Com apenas snapshot diário, você subfaturará parceiros que usam poucas horas em um dia e superfaturará os que usam 23h.*



*❌ CRÍTICO 2: partner\_billing\_cycles não tem locker\_id no nível do ciclo, apenas nas line items*

*Problema:*

*Um parceiro pode ter 10 lockers, cada um com uso diferente. Sem locker\_id no cabeçalho do ciclo, você não consegue:*



*Gerar fatura por locker (exigido por muitos contratos B2B)*



*Calcular ARPL por parceiro*



*Identificar locker problemático (baixa utilização, mas parceiro paga mesma mensalidade)*



*Correção:*



*sql*

*ALTER TABLE public.partner\_billing\_cycles* 

*ADD COLUMN locker\_id VARCHAR(36) REFERENCES lockers(id);*



*-- Remover UNIQUE antigo e criar novo composto*

*DROP INDEX uq\_pbc\_partner\_period;*

*CREATE UNIQUE INDEX uq\_pbc\_partner\_locker\_period* 

*ON partner\_billing\_cycles(partner\_id, locker\_id, period\_start, period\_end)* 

*WHERE locker\_id IS NOT NULL;*



*-- Para ciclos sem locker específico (contratos globais), manter locker\_id NULL*

*CREATE UNIQUE INDEX uq\_pbc\_partner\_global\_period* 

*ON partner\_billing\_cycles(partner\_id, period\_start, period\_end)* 

*WHERE locker\_id IS NULL;*

*❌ CRÍTICO 3: Ausência de hold e escrow para pagamentos B2B (parceiros podem contestar)*

*Problema:*

*No modelo atual, ao emitir partner\_b2b\_invoices com status PAID, o dinheiro entra imediatamente no caixa. Mas se o parceiro contestar a fatura 30 dias depois (ex: "seu locker ficou 12h offline"), você não tem como reter o valor.*



*Correção (prática Stripe Connect / Airbnb):*



*sql*

*CREATE TABLE public.partner\_payment\_holds (*

&#x20;   *id                      VARCHAR(36) PRIMARY KEY DEFAULT gen\_random\_uuid()::text,*

&#x20;   *partner\_id              VARCHAR(36) NOT NULL,*

&#x20;   *invoice\_id              VARCHAR(36) NOT NULL REFERENCES partner\_b2b\_invoices(id),*

&#x20;   *hold\_amount\_cents       BIGINT NOT NULL,  -- % ou valor fixo retido*

&#x20;   *release\_schedule        VARCHAR(30) NOT NULL DEFAULT 'AFTER\_15\_DAYS',*

&#x20;   *-- AFTER\_15\_DAYS | AFTER\_30\_DAYS | UPON\_DISPUTE\_RESOLUTION*

&#x20;   *released\_at             TIMESTAMPTZ,*

&#x20;   *released\_amount\_cents   BIGINT,*

&#x20;   *dispute\_opened\_at       TIMESTAMPTZ,*

&#x20;   *dispute\_resolved\_at     TIMESTAMPTZ,*

&#x20;   *dispute\_result          VARCHAR(20),  -- IN\_FAVOR\_ELLAN | IN\_FAVOR\_PARTNER*

&#x20;   *status                  VARCHAR(20) NOT NULL DEFAULT 'HELD',*

&#x20;   *created\_at              TIMESTAMPTZ NOT NULL DEFAULT now()*

*);*

*Regra de negócio:*



*Inicialmente reter 10% de cada fatura B2B por 15 dias*



*Após 6 meses sem disputas, reduzir para 5% ou 0%*



*Isso protege contra chargebacks e disputas de SLA*



*⚠️ ALTO RISCO 4: journal\_entries sem reference\_source (pode causar duplicação contábil)*

*Problema:*

*Um mesmo reference\_id (ex: partner\_billing\_cycle.id) pode gerar múltiplos lançamentos se o worker rodar duas vezes. reference\_type não é suficiente.*



*Correção:*



*sql*

*ALTER TABLE public.journal\_entries* 

*ADD COLUMN reference\_source VARCHAR(50) NOT NULL DEFAULT 'manual',*

*ADD COLUMN dedupe\_key VARCHAR(128) UNIQUE;  -- ex: 'billing\_cycle:cycle\_123:revenue\_recognition'*



*-- Exemplo de dedupe\_key*

*-- 'billing\_cycle:cycle\_abc:invoice\_issuance'*

*-- 'depreciation:asset\_xyz:month\_2026-04'*

*-- 'opex:entry\_abc:posting'*

*E no código:*



*python*

*dedupe\_key = f"{source\_type}:{source\_id}:{event\_type}"*

*if not JournalEntry.exists(dedupe\_key):*

&#x20;   *create\_journal\_entry()*

*3. RECOMENDAÇÕES DE MELHORIAS E NOVOS ACRÉSCIMOS*

*🟢 Melhoria 1: Suporte a múltiplos gateways de pagamento por parceiro*

*Alguns parceiros (ex: grandes carriers) exigirão pagamento via TED bancário, enquanto pequenos comerciantes usarão gateway (Stripe/Adyen). Criar:*



*sql*

*CREATE TABLE public.partner\_payment\_methods (*

&#x20;   *id                      VARCHAR(36) PRIMARY KEY,*

&#x20;   *partner\_id              VARCHAR(36) NOT NULL,*

&#x20;   *method\_type             VARCHAR(30) NOT NULL,  -- BANK\_TRANSFER | CREDIT\_CARD | PIX | BOLETO*

&#x20;   *is\_default              BOOLEAN NOT NULL DEFAULT false,*

&#x20;   *bank\_account\_json       JSONB,  -- para TED*

&#x20;   *gateway\_customer\_id     VARCHAR(128), -- para Stripe/Adyen*

&#x20;   *created\_at              TIMESTAMPTZ NOT NULL DEFAULT now()*

*);*

*🟢 Melhoria 2: Billing retry com backoff exponencial para falhas de emissão fiscal*

*Adicionar à partner\_b2b\_invoices:*



*sql*

*ALTER TABLE public.partner\_b2b\_invoices*

*ADD COLUMN retry\_count INTEGER NOT NULL DEFAULT 0,*

*ADD COLUMN last\_retry\_at TIMESTAMPTZ,*

*ADD COLUMN next\_retry\_at TIMESTAMPTZ,*

*ADD COLUMN failure\_reason TEXT;*

*E worker:*



*Falha na SEFAZ → retry após 5min, 15min, 1h, 6h, 24h*



*Após 5 falhas → notificação humana via Slack/PagerDuty*



*🟢 Melhoria 3: Custos variáveis por região (energia, conectividade)*

*Diferente de ellanlab\_opex\_entries (entrada manual), criar tabela de fatores de custo dinâmicos:*



*sql*

*CREATE TABLE public.regional\_opex\_factors (*

&#x20;   *id                      VARCHAR(36) PRIMARY KEY,*

&#x20;   *region                  VARCHAR(64) NOT NULL,*

&#x20;   *factor\_type             VARCHAR(30) NOT NULL,  -- ENERGY\_PRICE\_KWH | CONNECTIVITY\_MONTHLY*

&#x20;   *unit                    VARCHAR(20),*

&#x20;   *cost\_per\_unit\_cents     NUMERIC(10,4) NOT NULL,*

&#x20;   *valid\_from              DATE NOT NULL,*

&#x20;   *valid\_to                DATE,*

&#x20;   *created\_at              TIMESTAMPTZ NOT NULL DEFAULT now()*

*);*

*Assim o P\&L por locker pode ser calculado automaticamente (energia = consumo médio estimado × preço regional), sem entrada manual todo mês.*



*🟢 Melhoria 4: Simulador de faturamento para parceiros (antes de assinar contrato)*

*Não é tabela de banco, mas feature obrigatória para plataforma padrão mundial:*



*API POST /v1/partners/billing/simulate*



*Input: locker\_ids\[], estimated\_deliveries\_per\_day, estimated\_pickup\_within\_hours*



*Output: projeção de fatura mensal (min, média, max) baseada no partner\_billing\_plans*



*Isso reduz disputas e churn inicial.*



*4. NOVA TABELA CRÍTICA AUSENTE: partner\_webhook\_delivery\_logs (para SLA financeiro)*

*Seu parceiro precisa saber exatamente quando você notificou sobre uma entrega. Se o webhook falhar, ele pode contestar a cobrança.*



*sql*

*CREATE TABLE public.partner\_webhook\_delivery\_logs (*

&#x20;   *id                      BIGSERIAL PRIMARY KEY,*

&#x20;   *partner\_id              VARCHAR(36) NOT NULL,*

&#x20;   *event\_type              VARCHAR(40) NOT NULL,  -- DELIVERY\_ARRIVED | PICKUP\_COMPLETED*

&#x20;   *event\_id                VARCHAR(36) NOT NULL,  -- inbound\_delivery.id, order.id*

&#x20;   *webhook\_url             VARCHAR(500) NOT NULL,*

&#x20;   *http\_method             VARCHAR(10) NOT NULL DEFAULT 'POST',*

&#x20;   *request\_headers         JSONB,*

&#x20;   *request\_body            JSONB,*

&#x20;   *response\_status         INTEGER,*

&#x20;   *response\_body           TEXT,*

&#x20;   *retry\_count             INTEGER NOT NULL DEFAULT 0,*

&#x20;   *success                 BOOLEAN NOT NULL,*

&#x20;   *delivered\_at            TIMESTAMPTZ,*

&#x20;   *created\_at              TIMESTAMPTZ NOT NULL DEFAULT now(),*

&#x20;   

&#x20;   *-- Para SLA financeiro: se webhook falhou, parceiro pode pedir crédito*

&#x20;   *is\_disputed             BOOLEAN NOT NULL DEFAULT false,*

&#x20;   *credit\_note\_id          VARCHAR(36) REFERENCES partner\_credit\_notes(id)*

*);*



*CREATE INDEX idx\_pwdl\_partner\_event ON partner\_webhook\_delivery\_logs(partner\_id, event\_type, event\_id);*

*CREATE INDEX idx\_pwdl\_success ON partner\_webhook\_delivery\_logs(success) WHERE success = false;*

*5. PRIORIZAÇÃO REVISADA (mais segura para produção)*

*O roadmap original está bom, mas eu reordenaria para reduzir risco financeiro:*



*Fase	Duração	Entregáveis	Prioridade*

*0 — Fundação crítica	2 semanas	locker\_slot\_hourly\_occupancy, partner\_payment\_holds, dedupe\_key em journal\_entries	🔴 ALTA*

*1 — Billing B2B seguro	4 semanas	partner\_billing\_\*, partner\_webhook\_delivery\_logs, emissão NFS-e com retry	🟠 ALTA*

*2 — Double-entry + CAPEX	4 semanas	chart\_of\_accounts, journal\_entries, ellanlab\_hardware\_assets, depreciação	🟡 MÉDIA*

*3 — Portal parceiro + KPIs	3 semanas	APIs de simulação, dashboards Metabase, KPIs de SLA financeiro	🟢 MÉDIA*

*4 — Otimizações	2 semanas	TimescaleDB, dbt, testes Great Expectations	🔵 BAIXA*

*6. CONCLUSÃO DA AVALIAÇÃO*

*Nota técnica: 8.5/10*

*Nota de risco financeiro se implementar como está: 6/10 (os 3 críticos podem gerar disputas milionárias)*



*Resumo executivo:*



*✅ O documento está muito acima da média e demonstra conhecimento sólido.*



*❌ Falta granularidade horária para billing justo (corrigir antes do MVP).*



*❌ Falta mecanismo de hold/escrow para disputas (imprescindível B2B).*



*✅ A separação B2B/B2C, depreciação e double-entry são exemplares.*



*🟡 Recomendo adicionar webhook delivery logs como requisito legal.*



*Ação imediata:*

*Antes de escrever uma linha de código do billing engine, implemente a tabela locker\_slot\_hourly\_occupancy e o worker de snapshot a cada hora. Isso permitirá que você cobre pelo uso real e defenda sua fatura em caso de disputa judicial.*



*Caso corrija os 3 pontos críticos, o ELLAN LAB estará no mesmo nível de Stripe e Adyen em termos de arquitetura financeira para marketplace de infraestrutura física.*



*Estou à disposição para revisar a segunda versão do documento.*



